"""ファイル操作ユーティリティを提供するモジュール"""

import os
import shutil
import re
import logging
import csv
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Iterator, BinaryIO, TextIO
import pandas as pd

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.error_handler import FileError

class FileUtils:
    """ファイル操作ユーティリティクラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = get_logger(__name__)
        
        # サポートするエンコーディングリスト（優先順位順）
        self.encodings = ['utf-8', 'utf-8-sig', 'cp932', 'shift-jis']
    
    def ensure_directory(self, directory_path: Union[str, Path]) -> Path:
        """
        指定されたディレクトリが存在することを確認し、
        存在しない場合は作成する
        
        Args:
            directory_path: 確認/作成するディレクトリのパス
            
        Returns:
            Path: 確認/作成されたディレクトリのパス
        """
        path = Path(directory_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except Exception as e:
            error_msg = f"ディレクトリ作成エラー: {path}, {e}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
    
    def read_text_file(self, file_path: Union[str, Path], 
                       encoding: Optional[str] = None) -> str:
        """
        テキストファイルを読み込む
        指定されたエンコーディングで読み込めない場合は他のエンコーディングを試行
        
        Args:
            file_path: 読み込むファイルのパス
            encoding: 使用するエンコーディング（省略時は自動検出）
            
        Returns:
            str: ファイルの内容
        """
        path = Path(file_path)
        if not path.exists():
            error_msg = f"ファイルが存在しません: {path}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
        
        # エンコーディングが指定されている場合はそれを使用
        if encoding:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                error_msg = f"指定されたエンコーディング {encoding} でファイルを読み込めません: {path}"
                self.logger.error(error_msg)
                raise FileError("ファイルエラー", error_msg)
        
        # エンコーディングが指定されていない場合は自動検出
        last_error = None
        for enc in self.encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    content = f.read()
                    self.logger.debug(f"ファイルを {enc} エンコーディングで読み込みました: {path}")
                    return content
            except UnicodeDecodeError as e:
                last_error = e
                continue
        
        # すべてのエンコーディングで失敗した場合
        error_msg = f"どのエンコーディングでもファイルを読み込めません: {path}, {last_error}"
        self.logger.error(error_msg)
        raise FileError("ファイルエラー", error_msg)
    
    def write_text_file(self, file_path: Union[str, Path], content: str, 
                        encoding: str = 'utf-8') -> None:
        """
        テキストファイルに書き込む
        
        Args:
            file_path: 書き込むファイルのパス
            content: 書き込む内容
            encoding: 使用するエンコーディング
        """
        path = Path(file_path)
        try:
            # 親ディレクトリを確保
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
                
            self.logger.debug(f"ファイルに書き込みました: {path}")
            
        except Exception as e:
            error_msg = f"ファイル書き込みエラー: {path}, {e}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
    
    def copy_file(self, source_path: Union[str, Path], 
                  dest_path: Union[str, Path]) -> Path:
        """
        ファイルをコピーする
        
        Args:
            source_path: コピー元ファイルのパス
            dest_path: コピー先ファイルのパス
            
        Returns:
            Path: コピー先ファイルのパス
        """
        src = Path(source_path)
        dst = Path(dest_path)
        
        if not src.exists():
            error_msg = f"コピー元ファイルが存在しません: {src}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
        
        try:
            # 親ディレクトリを確保
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # ファイルをコピー
            shutil.copy2(src, dst)
            self.logger.debug(f"ファイルをコピーしました: {src} -> {dst}")
            
            return dst
            
        except Exception as e:
            error_msg = f"ファイルコピーエラー: {src} -> {dst}, {e}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
    
    def read_csv(self, file_path: Union[str, Path], 
                 encoding: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        CSVファイルを読み込んでDataFrameを返す
        エンコーディングが指定されていない場合は自動検出
        
        Args:
            file_path: 読み込むCSVファイルのパス
            encoding: 使用するエンコーディング（省略時は自動検出）
            **kwargs: pandas.read_csvに渡す追加の引数
            
        Returns:
            pd.DataFrame: 読み込まれたデータフレーム
        """
        path = Path(file_path)
        if not path.exists():
            error_msg = f"CSVファイルが存在しません: {path}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
        
        # エンコーディングが指定されている場合はそれを使用
        if encoding:
            try:
                df = pd.read_csv(path, encoding=encoding, **kwargs)
                return df
            except Exception as e:
                error_msg = f"CSVファイル読み込みエラー: {path}, {e}"
                self.logger.error(error_msg)
                raise FileError("ファイルエラー", error_msg)
        
        # エンコーディングが指定されていない場合は自動検出
        last_error = None
        for enc in self.encodings:
            try:
                df = pd.read_csv(path, encoding=enc, **kwargs)
                self.logger.debug(f"CSVファイルを {enc} エンコーディングで読み込みました: {path}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                last_error = e
                self.logger.warning(f"CSVファイル読み込み警告 ({enc}): {path}, {e}")
                continue
        
        # すべてのエンコーディングで失敗した場合
        error_msg = f"どのエンコーディングでもCSVファイルを読み込めません: {path}, {last_error}"
        self.logger.error(error_msg)
        raise FileError("ファイルエラー", error_msg)
    
    def write_csv(self, df: pd.DataFrame, file_path: Union[str, Path], 
                  encoding: str = 'utf-8-sig', **kwargs) -> None:
        """
        DataFrameをCSVファイルに書き込む
        
        Args:
            df: 書き込むデータフレーム
            file_path: 書き込み先ファイルのパス
            encoding: 使用するエンコーディング
            **kwargs: pandas.to_csvに渡す追加の引数
        """
        path = Path(file_path)
        try:
            # 親ディレクトリを確保
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # DataFrameをCSVに書き込み
            df.to_csv(path, encoding=encoding, **kwargs)
            self.logger.debug(f"CSVファイルに書き込みました: {path}")
            
        except Exception as e:
            error_msg = f"CSVファイル書き込みエラー: {path}, {e}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
    
    def find_files(self, directory: Union[str, Path], pattern: str, 
                   recursive: bool = True) -> List[Path]:
        """
        指定されたディレクトリから条件に合うファイルを検索
        
        Args:
            directory: 検索するディレクトリのパス
            pattern: 検索パターン（glob形式）
            recursive: サブディレクトリも検索するか
            
        Returns:
            List[Path]: 見つかったファイルのパスのリスト
        """
        base_dir = Path(directory)
        
        if not base_dir.exists():
            self.logger.warning(f"検索ディレクトリが存在しません: {base_dir}")
            return []
        
        try:
            if recursive:
                files = list(base_dir.glob(f"**/{pattern}"))
            else:
                files = list(base_dir.glob(pattern))
                
            self.logger.debug(f"{len(files)}個のファイルが見つかりました: {base_dir}/{pattern}")
            return files
            
        except Exception as e:
            error_msg = f"ファイル検索エラー: {base_dir}/{pattern}, {e}"
            self.logger.error(error_msg)
            raise FileError("ファイルエラー", error_msg)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        ファイル名から不正な文字を除去
        
        Args:
            filename: サニタイズするファイル名
            
        Returns:
            str: サニタイズされたファイル名
        """
        # Windows/Mac/Linuxで不正な文字を置換
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # 先頭と末尾の空白、ピリオドを削除
        sanitized = sanitized.strip('. ')
        
        # ファイル名が空になったら'unnamed'を返す
        if not sanitized:
            return 'unnamed'
        
        return sanitized