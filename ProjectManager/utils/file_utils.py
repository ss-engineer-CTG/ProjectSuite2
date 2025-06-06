"""
ファイル操作の基本処理（本番環境用簡素版）
KISS原則: シンプルなファイル操作のみ
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from core.constants import ValidationConstants

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