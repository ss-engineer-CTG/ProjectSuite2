"""
パス操作ユーティリティ（本番環境用簡素版）
パス管理原則: パス結合・正規化・検証の基本処理のみ
"""

import os
import re
import logging
from pathlib import Path
from typing import Union

class PathManager:
    """パス操作の基本管理クラス"""
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def join_path(*args) -> Path:
        """安全なパス結合"""
        if not args:
            return Path()
        
        base_path = Path(args[0])
        for part in args[1:]:
            if part:
                base_path = base_path / part
        
        return base_path
    
    @staticmethod
    def normalize_path(path: Union[str, Path]) -> Path:
        """パスの正規化"""
        try:
            path = Path(path)
            return path.resolve()
        except Exception as e:
            PathManager.logger.error(f"パス正規化エラー {path}: {e}")
            return Path(path)
    
    @staticmethod
    def validate_path(path: Union[str, Path], must_exist: bool = False,
                     must_be_dir: bool = False, must_be_file: bool = False) -> bool:
        """パスの検証"""
        try:
            path = Path(path)
            
            if must_exist and not path.exists():
                return False
            
            if must_be_dir and path.exists() and not path.is_dir():
                return False
            
            if must_be_file and path.exists() and not path.is_file():
                return False
            
            return True
            
        except Exception as e:
            PathManager.logger.error(f"パス検証エラー {path}: {e}")
            return False
    
    @staticmethod
    def sanitize_path_component(component: str) -> str:
        """パス構成要素の無害化"""
        if not component:
            return "unnamed"
        
        # Windows用無効文字を置換
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', component.strip())
        
        # 連続するアンダースコアを単一に
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 前後のアンダースコア・ドットを除去
        sanitized = sanitized.strip('_. ')
        
        # Windowsの予約語チェック
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        if sanitized.upper() in reserved_names:
            sanitized = f"_{sanitized}"
        
        # 空になった場合のフォールバック
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized
    
    @staticmethod
    def create_project_folder_name(project_data: dict) -> str:
        """プロジェクトフォルダ名の生成"""
        components = []
        
        # 階層情報の追加
        hierarchy_fields = ['division', 'factory', 'process', 'line']
        for field in hierarchy_fields:
            value = project_data.get(field, '').strip()
            if value:
                components.append(PathManager.sanitize_path_component(value))
        
        # プロジェクト基本情報の追加
        essential_fields = ['project_name', 'start_date', 'manager']
        for field in essential_fields:
            value = project_data.get(field, '').strip()
            if value:
                components.append(PathManager.sanitize_path_component(value))
        
        # フォルダ名の結合
        folder_name = '_'.join(filter(None, components))
        
        # 長すぎる場合は切り詰め
        max_length = 200
        if len(folder_name) > max_length:
            folder_name = folder_name[:max_length].rstrip('_')
        
        return folder_name or "unnamed_project"
    
    @staticmethod
    def ensure_unique_path(base_path: Path, desired_name: str) -> Path:
        """一意なパスの確保（重複回避）"""
        base_path = Path(base_path)
        target_path = base_path / desired_name
        
        if not target_path.exists():
            return target_path
        
        # 重複する場合は番号を付与
        counter = 1
        name_parts = desired_name.rsplit('.', 1)
        
        if len(name_parts) == 2:
            base_name, extension = name_parts
            pattern = base_name + "_{}." + extension
        else:
            base_name = desired_name
            pattern = base_name + "_{}"
        
        while target_path.exists():
            new_name = pattern.format(counter)
            target_path = base_path / new_name
            counter += 1
            
            # 無限ループ防止
            if counter > 1000:
                import time
                timestamp = int(time.time())
                new_name = f"{base_name}_{timestamp}"
                target_path = base_path / new_name
                break
        
        return target_path