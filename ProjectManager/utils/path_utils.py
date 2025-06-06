"""
パス操作ユーティリティ（本番環境用簡素版）
パス管理原則: パス結合・正規化・検証の基本処理のみ
"""

import os
import re
import logging
import time
from pathlib import Path
from typing import Union, List, Optional

from core.constants import InitializationConstants

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
    def _should_exclude_directory(directory: Path) -> bool:
        """ディレクトリ除外判定"""
        dir_name = directory.name.lower()
        
        # 除外ディレクトリパターンのチェック
        for exclude_pattern in InitializationConstants.EXCLUDE_DIRECTORIES:
            if exclude_pattern.lower() in dir_name:
                return True
        
        # システムディレクトリの除外
        if dir_name.startswith('.') and dir_name not in ['.']:
            return True
        
        # アクセス権限のチェック
        try:
            list(directory.iterdir())
            return False
        except (PermissionError, OSError):
            return True
    
    @staticmethod
    def find_directories_by_name(search_paths: List[Path], 
                                target_name: str, 
                                max_depth: int = 4,
                                partial_match: bool = True) -> List[Path]:
        """指定名のディレクトリを複数パスから深層検索（部分一致対応）"""
        found_directories = []
        start_time = time.time()
        searched_items = 0
        
        try:
            for search_path in search_paths:
                if not search_path.exists():
                    continue
                
                PathManager.logger.debug(f"ディレクトリ検索開始: {search_path} (最大深度: {max_depth})")
                
                # タイムアウトチェック
                if time.time() - start_time > InitializationConstants.SEARCH_TIMEOUT_SECONDS:
                    PathManager.logger.warning("検索タイムアウトが発生しました")
                    break
                
                # 深度優先探索（DFS）で効率的に検索
                found_in_path = PathManager._search_directory_recursive(
                    search_path, target_name, max_depth, 0, 
                    start_time, searched_items, partial_match
                )
                
                found_directories.extend(found_in_path)
                
                # アイテム数制限チェック
                searched_items += len(found_in_path)
                if searched_items >= InitializationConstants.MAX_SEARCH_ITEMS:
                    PathManager.logger.warning("検索アイテム数制限に到達しました")
                    break
            
            if found_directories:
                PathManager.logger.info(f"検索完了: {len(found_directories)}個のディレクトリを発見")
            else:
                PathManager.logger.info("検索完了: 対象ディレクトリが見つかりませんでした")
            
            return found_directories
            
        except Exception as e:
            PathManager.logger.error(f"ディレクトリ検索エラー: {e}")
            return found_directories
    
    @staticmethod
    def _search_directory_recursive(current_path: Path, target_name: str, 
                                   max_depth: int, current_depth: int,
                                   start_time: float, searched_items: int,
                                   partial_match: bool = True) -> List[Path]:
        """再帰的ディレクトリ検索"""
        found_directories = []
        
        try:
            # タイムアウトチェック
            if time.time() - start_time > InitializationConstants.SEARCH_TIMEOUT_SECONDS:
                return found_directories
            
            # アイテム数制限チェック
            if searched_items >= InitializationConstants.MAX_SEARCH_ITEMS:
                return found_directories
            
            # 深度制限チェック
            if current_depth >= max_depth:
                return found_directories
            
            # 除外ディレクトリチェック
            if PathManager._should_exclude_directory(current_path):
                return found_directories
            
            PathManager.logger.debug(f"検索中 (深度{current_depth}): {current_path}")
            
            # 現在のディレクトリの内容を取得
            try:
                items = list(current_path.iterdir())
            except (PermissionError, OSError) as e:
                PathManager.logger.debug(f"アクセス権限エラー: {current_path} - {e}")
                return found_directories
            
            for item in items:
                # タイムアウトチェック
                if time.time() - start_time > InitializationConstants.SEARCH_TIMEOUT_SECONDS:
                    break
                
                if not item.is_dir():
                    continue
                
                # 対象ディレクトリ名とのマッチング（部分一致対応）
                if PathManager._is_target_directory_match(item.name, target_name):
                    found_directories.append(item)
                    PathManager.logger.info(f"対象ディレクトリを発見 (深度{current_depth}): {item}")
                    continue
                
                # 再帰検索（さらに深い階層）
                if current_depth < max_depth - 1:
                    try:
                        sub_found = PathManager._search_directory_recursive(
                            item, target_name, max_depth, current_depth + 1,
                            start_time, searched_items + len(found_directories),
                            partial_match
                        )
                        found_directories.extend(sub_found)
                        
                    except Exception as e:
                        PathManager.logger.debug(f"再帰検索エラー {item}: {e}")
                        continue
            
            return found_directories
            
        except Exception as e:
            PathManager.logger.error(f"再帰検索エラー {current_path}: {e}")
            return found_directories
    
    @staticmethod
    def _is_target_directory_match(directory_name: str, target_name: str) -> bool:
        """ディレクトリ名の一致判定（部分一致・大文字小文字不問）"""
        try:
            # 大文字小文字を区別しない部分一致
            dir_name_lower = directory_name.lower()
            target_name_lower = target_name.lower()
            
            # 部分一致チェック
            if target_name_lower in dir_name_lower:
                return True
            
            # より柔軟な一致パターン（アンダースコアやハイフンを無視）
            normalized_dir = re.sub(r'[_\-\s]', '', dir_name_lower)
            normalized_target = re.sub(r'[_\-\s]', '', target_name_lower)
            
            if normalized_target in normalized_dir:
                return True
            
            return False
            
        except Exception as e:
            PathManager.logger.error(f"ディレクトリ名一致判定エラー: {e}")
            return False
    
    @staticmethod
    def get_standard_search_paths() -> List[Path]:
        """標準的な検索パスの取得"""
        search_paths = []
        
        for directory in InitializationConstants.SEARCH_DIRECTORIES:
            path = Path.home() / directory
            if path.exists():
                search_paths.append(path)
        
        return search_paths
    
    @staticmethod
    def find_initial_data_directory() -> Optional[Path]:
        """初期データディレクトリの検索（部分一致対応）"""
        try:
            search_paths = PathManager.get_standard_search_paths()
            target_name = InitializationConstants.INITIAL_DATA_FOLDER_NAME
            
            found_directories = PathManager.find_directories_by_name(
                search_paths, target_name, 
                max_depth=InitializationConstants.MAX_SEARCH_DEPTH,
                partial_match=True
            )
            
            # 最初に見つかったディレクトリを返す
            if found_directories:
                PathManager.logger.info(f"初期データディレクトリを発見: {found_directories[0]}")
                if len(found_directories) > 1:
                    PathManager.logger.info(f"複数の候補が見つかりました:")
                    for i, path in enumerate(found_directories, 1):
                        PathManager.logger.info(f"  {i}. {path}")
                
                return found_directories[0]
            
            return None
            
        except Exception as e:
            PathManager.logger.error(f"初期データディレクトリ検索エラー: {e}")
            return None
    
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
    
    @staticmethod
    def copy_directory_structure(source: Path, destination: Path, 
                                copy_files: bool = False) -> bool:
        """ディレクトリ構造のコピー"""
        try:
            from utils.file_utils import FileManager
            
            if copy_files:
                copied_count, error_count = FileManager.copy_directory_recursive(
                    source, destination
                )
                return copied_count > 0
            else:
                # ディレクトリ構造のみコピー
                for item in source.rglob('*'):
                    if item.is_dir():
                        relative_path = item.relative_to(source)
                        dest_dir = destination / relative_path
                        FileManager.ensure_directory(dest_dir)
                
                return True
                
        except Exception as e:
            PathManager.logger.error(f"ディレクトリ構造コピーエラー {source} -> {destination}: {e}")
            return False