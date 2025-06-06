"""
ファイル操作の基本処理（本番環境用簡素版）
KISS原則: シンプルなファイル操作のみ
"""

import csv
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from core.constants import ValidationConstants, InitializationConstants

class FileManager:
    """ファイル操作の基本管理クラス"""
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def ensure_directory(path: Path) -> Path:
        """ディレクトリの確保"""
        try:
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            FileManager.logger.error(f"ディレクトリ作成エラー {path}: {e}")
            raise
    
    @staticmethod
    def copy_directory_recursive(source: Path, destination: Path, 
                                preserve_structure: bool = True) -> Tuple[int, int]:
        """ディレクトリの再帰的コピー（パフォーマンス最適化版）"""
        try:
            source = Path(source)
            destination = Path(destination)
            
            if not source.exists():
                raise FileNotFoundError(f"コピー元が存在しません: {source}")
            
            copied_count = 0
            error_count = 0
            
            # コピー先ディレクトリの作成
            FileManager.ensure_directory(destination)
            
            FileManager.logger.info(f"ディレクトリコピー開始: {source} -> {destination}")
            
            # ファイル・ディレクトリの一括取得（効率化）
            all_items = []
            try:
                all_items = list(source.rglob('*'))
                FileManager.logger.debug(f"コピー対象アイテム数: {len(all_items)}")
            except Exception as e:
                FileManager.logger.error(f"アイテム一覧取得エラー: {e}")
                return 0, 1
            
            # ディレクトリ優先でソート（親ディレクトリを先に作成）
            directories = [item for item in all_items if item.is_dir()]
            files = [item for item in all_items if item.is_file()]
            
            # ディレクトリの作成
            for directory in directories:
                try:
                    if FileManager._should_exclude_file(directory):
                        continue
                        
                    relative_path = directory.relative_to(source)
                    dest_dir = destination / relative_path
                    FileManager.ensure_directory(dest_dir)
                    
                except Exception as e:
                    error_count += 1
                    FileManager.logger.error(f"ディレクトリ作成エラー {directory}: {e}")
                    continue
            
            # ファイルのコピー
            for file_item in files:
                try:
                    if FileManager._should_exclude_file(file_item):
                        continue
                    
                    if not FileManager._check_file_size(file_item):
                        FileManager.logger.warning(f"ファイルサイズが大きすぎます: {file_item}")
                        error_count += 1
                        continue
                    
                    relative_path = file_item.relative_to(source)
                    dest_file = destination / relative_path
                    
                    # 親ディレクトリの確保
                    FileManager.ensure_directory(dest_file.parent)
                    
                    # ファイルコピー
                    shutil.copy2(file_item, dest_file)
                    copied_count += 1
                    
                    if copied_count % 100 == 0:  # 進捗ログ
                        FileManager.logger.debug(f"コピー進捗: {copied_count}ファイル完了")
                        
                except Exception as e:
                    error_count += 1
                    FileManager.logger.error(f"ファイルコピーエラー {file_item}: {e}")
                    continue
            
            FileManager.logger.info(f"ディレクトリコピー完了: 成功 {copied_count}, エラー {error_count}")
            return copied_count, error_count
            
        except Exception as e:
            FileManager.logger.error(f"ディレクトリコピーエラー {source} -> {destination}: {e}")
            raise
    
    @staticmethod
    def _should_exclude_file(file_path: Path) -> bool:
        """ファイル除外判定（強化版）"""
        import fnmatch
        
        file_name = file_path.name
        
        # 除外パターンとのマッチング
        for pattern in InitializationConstants.EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        
        # 隠しファイルの除外（初期化ファイルは除く）
        if file_name.startswith('.') and file_name not in ['.initialized']:
            return True
        
        # システムディレクトリの除外
        if file_path.is_dir():
            dir_name_lower = file_name.lower()
            for exclude_dir in InitializationConstants.EXCLUDE_DIRECTORIES:
                if exclude_dir.lower() in dir_name_lower:
                    return True
        
        return False
    
    @staticmethod
    def _check_file_size(file_path: Path) -> bool:
        """ファイルサイズチェック"""
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            return size_mb <= InitializationConstants.MAX_COPY_SIZE_MB
        except Exception:
            return True  # サイズ取得に失敗した場合は許可
    
    @staticmethod
    def get_directory_size(directory: Path) -> int:
        """ディレクトリサイズの取得（バイト）"""
        try:
            total_size = 0
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except Exception:
                        continue
            return total_size
        except Exception as e:
            FileManager.logger.error(f"ディレクトリサイズ取得エラー {directory}: {e}")
            return 0
    
    @staticmethod
    def read_csv_with_encoding(file_path: Path) -> Tuple[List[Dict[str, Any]], str]:
        """エンコーディング自動判定でCSV読み込み"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが存在しません: {file_path}")
        
        last_error = None
        for encoding in ValidationConstants.ENCODING_OPTIONS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    data = list(reader)
                
                FileManager.logger.info(f"CSV読み込み成功: {file_path} ({encoding})")
                return data, encoding
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                last_error = e
                FileManager.logger.error(f"CSV読み込みエラー ({encoding}): {e}")
                continue
        
        error_msg = f"CSV読み込み失敗: {file_path}"
        if last_error:
            error_msg += f" - {last_error}"
        raise ValueError(error_msg)
    
    @staticmethod
    def write_csv(file_path: Path, data: List[Dict[str, Any]], encoding: str = 'utf-8-sig'):
        """CSV書き込み"""
        try:
            file_path = Path(file_path)
            FileManager.ensure_directory(file_path.parent)
            
            if not data:
                FileManager.logger.warning(f"書き込むデータが空です: {file_path}")
                return
            
            with open(file_path, 'w', newline='', encoding=encoding) as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            FileManager.logger.info(f"CSV書き込み完了: {file_path}")
            
        except Exception as e:
            FileManager.logger.error(f"CSV書き込みエラー {file_path}: {e}")
            raise
    
    @staticmethod
    def check_file_permissions(file_path: Path) -> bool:
        """ファイル書き込み権限の確認"""
        try:
            file_path = Path(file_path)
            test_file = file_path / '.write_test' if file_path.is_dir() else file_path.parent / '.write_test'
            
            # テストファイルの作成・削除
            test_file.touch()
            test_file.unlink()
            
            return True
            
        except Exception as e:
            FileManager.logger.error(f"書き込み権限確認エラー {file_path}: {e}")
            return False
    
    @staticmethod
    def safe_remove_directory(directory: Path) -> bool:
        """安全なディレクトリ削除"""
        try:
            directory = Path(directory)
            if directory.exists() and directory.is_dir():
                shutil.rmtree(directory)
                FileManager.logger.info(f"ディレクトリを削除: {directory}")
                return True
            return False
        except Exception as e:
            FileManager.logger.error(f"ディレクトリ削除エラー {directory}: {e}")
            return False