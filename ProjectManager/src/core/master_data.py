"""マスターデータ管理モジュール"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, TypedDict
from datetime import datetime

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.file_utils import FileUtils
from ProjectManager.src.core.error_handler import ValidationError

class MasterDataEntry(TypedDict):
    code: str
    name: str

class MasterDataManager:
    """マスターデータ管理クラス"""
    
    def __init__(self, master_file_path: Optional[Path] = None):
        """
        マスターデータ管理クラスの初期化
        
        Args:
            master_file_path (Optional[Path]): マスターデータCSVファイルのパス（省略時は自動設定）
        """
        self.logger = get_logger(__name__)
        self.path_manager = PathManager()
        self.file_utils = FileUtils()
        
        # マスターファイルパスの設定
        if master_file_path:
            self.master_file_path = Path(master_file_path)
        else:
            self.master_file_path = self.path_manager.get_path("MASTER_DATA_FILE")
        
        self.master_data: Optional[pd.DataFrame] = None
        self.last_updated: Optional[datetime] = None
        
        self.load_master_data()
    
    def load_master_data(self) -> None:
        """
        マスターデータをCSVファイルから読み込む
        
        Raises:
            ValidationError: データの読み込みまたは検証に失敗した場合
        """
        try:
            # CSVファイルを読み込み
            self.master_data = self.file_utils.read_csv(
                self.master_file_path,
                dtype=str  # 全てのカラムを文字列として読み込み
            )
            
            # データの検証
            self._validate_master_data()
            
            self.last_updated = datetime.now()
            self.logger.info(f"マスターデータを正常に読み込みました")
            
        except Exception as e:
            error_msg = f"マスターデータの読み込みに失敗しました: {e}"
            self.logger.error(error_msg)
            raise ValidationError("マスターデータエラー", error_msg)
            
    def _validate_master_data(self) -> None:
        """
        マスターデータの妥当性検証
        
        Raises:
            ValidationError: 必要なカラムが存在しない場合
        """
        required_columns = [
            'division_code', 'division_name',
            'factory_code', 'factory_name',
            'process_code', 'process_name',
            'line_code', 'line_name'
        ]
        
        missing_columns = [col for col in required_columns 
                          if col not in self.master_data.columns]
                          
        if missing_columns:
            error_msg = f"必要なカラムがありません: {', '.join(missing_columns)}"
            self.logger.error(error_msg)
            raise ValidationError("マスターデータエラー", error_msg)

    def get_divisions(self) -> List[MasterDataEntry]:
        """
        事業部の一覧を取得
        
        Returns:
            List[MasterDataEntry]: 事業部情報のリスト
        """
        if self.master_data is None:
            return []
        
        divisions = self.master_data[['division_code', 'division_name']].drop_duplicates()
        return [
            {'code': row['division_code'], 'name': row['division_name']}
            for _, row in divisions.iterrows()
        ]
    
    def get_factories(self, division_code: Optional[str] = None) -> List[MasterDataEntry]:
        """
        工場の一覧を取得
        
        Args:
            division_code: フィルタリングする事業部コード（Noneの場合は全て取得）
            
        Returns:
            List[MasterDataEntry]: 工場情報のリスト
        """
        if self.master_data is None:
            return []
        
        factories = self.master_data[['division_code', 'factory_code', 'factory_name']]
        if division_code is not None:  # Noneの場合はフィルタリングしない
            factories = factories[factories['division_code'] == division_code]
        
        factories = factories[['factory_code', 'factory_name']].drop_duplicates()
        return [
            {'code': row['factory_code'], 'name': row['factory_name']}
            for _, row in factories.iterrows()
        ]
    
    def get_processes(self, division_code: Optional[str] = None,
                     factory_code: Optional[str] = None) -> List[MasterDataEntry]:
        """
        工程の一覧を取得
        
        Args:
            division_code: フィルタリングする事業部コード（Noneの場合は全て取得）
            factory_code: フィルタリングする工場コード（Noneの場合は全て取得）
            
        Returns:
            List[MasterDataEntry]: 工程情報のリスト
        """
        if self.master_data is None:
            return []
        
        processes = self.master_data[
            ['division_code', 'factory_code', 'process_code', 'process_name']
        ]
        
        if division_code is not None:
            processes = processes[processes['division_code'] == division_code]
        
        if factory_code is not None:
            processes = processes[processes['factory_code'] == factory_code]
        
        processes = processes[['process_code', 'process_name']].drop_duplicates()
        return [
            {'code': row['process_code'], 'name': row['process_name']}
            for _, row in processes.iterrows()
        ]
    
    def get_lines(self, division_code: Optional[str] = None,
                 factory_code: Optional[str] = None,
                 process_code: Optional[str] = None) -> List[MasterDataEntry]:
        """
        ラインの一覧を取得
        
        Args:
            division_code: フィルタリングする事業部コード（Noneの場合は全て取得）
            factory_code: フィルタリングする工場コード（Noneの場合は全て取得）
            process_code: フィルタリングする工程コード（Noneの場合は全て取得）
            
        Returns:
            List[MasterDataEntry]: ライン情報のリスト
        """
        if self.master_data is None:
            return []
        
        lines = self.master_data[
            ['division_code', 'factory_code', 'process_code', 'line_code', 'line_name']
        ]
        
        if division_code is not None:
            lines = lines[lines['division_code'] == division_code]
        
        if factory_code is not None:
            lines = lines[lines['factory_code'] == factory_code]
        
        if process_code is not None:
            lines = lines[lines['process_code'] == process_code]
        
        lines = lines[['line_code', 'line_name']].drop_duplicates()
        return [
            {'code': row['line_code'], 'name': row['line_name']}
            for _, row in lines.iterrows()
        ]
    
    def validate_combination(self, division_code: str, factory_code: str,
                           process_code: str, line_code: str) -> bool:
        """
        選択された組み合わせが有効かチェック
        
        Args:
            division_code: 事業部コード
            factory_code: 工場コード
            process_code: 工程コード
            line_code: ラインコード
            
        Returns:
            bool: 組み合わせが有効な場合True
        """
        if self.master_data is None:
            return False
        
        filtered = self.master_data[
            (self.master_data['division_code'] == division_code) &
            (self.master_data['factory_code'] == factory_code) &
            (self.master_data['process_code'] == process_code) &
            (self.master_data['line_code'] == line_code)
        ]
        
        return len(filtered) > 0
    
    def get_name_by_code(self, code: str, type_name: str) -> Optional[str]:
        """
        コードに対応する名前を取得
        
        Args:
            code: 検索するコード
            type_name: 検索する項目タイプ (division/factory/process/line)
            
        Returns:
            Optional[str]: 対応する名前。見つからない場合はNone
        """
        if self.master_data is None:
            return None
        
        code_col = f"{type_name}_code"
        name_col = f"{type_name}_name"
        
        if code_col not in self.master_data.columns or name_col not in self.master_data.columns:
            return None
        
        filtered = self.master_data[self.master_data[code_col] == code]
        if len(filtered) > 0:
            return filtered.iloc[0][name_col]
        
        return None

    def reload_master_data(self) -> None:
        """マスターデータの再読み込み"""
        self.load_master_data()