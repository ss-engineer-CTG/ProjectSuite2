"""
マスターデータ管理クラス
KISS原則: シンプルなCSV読み込み・検証
DRY原則: データ取得処理の統合
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
import csv

from .constants import ValidationConstants

class MasterDataManager:
    """マスターデータ管理クラス"""
    
    def __init__(self, master_file_path: Path):
        self.master_file_path = Path(master_file_path)
        self.logger = logging.getLogger(__name__)
        self.master_data = []
        self.load_master_data()
    
    def load_master_data(self):
        """マスターデータの読み込み"""
        if not self.master_file_path.exists():
            self.logger.warning(f"マスターデータファイルが存在しません: {self.master_file_path}")
            return
        
        try:
            # エンコーディングを試行して読み込み
            for encoding in ValidationConstants.ENCODING_OPTIONS:
                try:
                    with open(self.master_file_path, 'r', encoding=encoding) as f:
                        reader = csv.DictReader(f)
                        self.master_data = list(reader)
                    
                    self._validate_master_data()
                    self.logger.info(f"マスターデータを正常に読み込みました ({encoding})")
                    return
                    
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.logger.error(f"マスターデータ読み込みエラー ({encoding}): {e}")
                    continue
            
            self.logger.error("マスターデータの読み込みに失敗しました")
            
        except Exception as e:
            self.logger.error(f"マスターデータ処理エラー: {e}")
    
    def _validate_master_data(self):
        """マスターデータの検証"""
        if not self.master_data:
            return
        
        required_columns = [
            'division_code', 'division_name',
            'factory_code', 'factory_name',
            'process_code', 'process_name',
            'line_code', 'line_name'
        ]
        
        first_row = self.master_data[0]
        missing_columns = [col for col in required_columns if col not in first_row]
        
        if missing_columns:
            raise ValueError(f"必要なカラムが不足: {', '.join(missing_columns)}")
    
    def get_divisions(self) -> List[Dict[str, str]]:
        """事業部一覧の取得"""
        if not self.master_data:
            return []
        
        divisions = {}
        for row in self.master_data:
            code = row.get('division_code', '')
            name = row.get('division_name', '')
            if code and name:
                divisions[code] = {'code': code, 'name': name}
        
        return list(divisions.values())
    
    def get_factories(self, division_code: Optional[str] = None) -> List[Dict[str, str]]:
        """工場一覧の取得"""
        if not self.master_data:
            return []
        
        factories = {}
        for row in self.master_data:
            if division_code and row.get('division_code') != division_code:
                continue
                
            code = row.get('factory_code', '')
            name = row.get('factory_name', '')
            if code and name:
                factories[code] = {'code': code, 'name': name}
        
        return list(factories.values())
    
    def get_processes(self, division_code: Optional[str] = None, 
                     factory_code: Optional[str] = None) -> List[Dict[str, str]]:
        """工程一覧の取得"""
        if not self.master_data:
            return []
        
        processes = {}
        for row in self.master_data:
            if division_code and row.get('division_code') != division_code:
                continue
            if factory_code and row.get('factory_code') != factory_code:
                continue
                
            code = row.get('process_code', '')
            name = row.get('process_name', '')
            if code and name:
                processes[code] = {'code': code, 'name': name}
        
        return list(processes.values())
    
    def get_lines(self, division_code: Optional[str] = None,
                 factory_code: Optional[str] = None,
                 process_code: Optional[str] = None) -> List[Dict[str, str]]:
        """ライン一覧の取得"""
        if not self.master_data:
            return []
        
        lines = {}
        for row in self.master_data:
            if division_code and row.get('division_code') != division_code:
                continue
            if factory_code and row.get('factory_code') != factory_code:
                continue
            if process_code and row.get('process_code') != process_code:
                continue
                
            code = row.get('line_code', '')
            name = row.get('line_name', '')
            if code and name:
                lines[code] = {'code': code, 'name': name}
        
        return list(lines.values())
    
    def validate_combination(self, division_code: str, factory_code: str,
                           process_code: str, line_code: str) -> bool:
        """選択組み合わせの検証"""
        if not self.master_data:
            return False
        
        for row in self.master_data:
            if (row.get('division_code') == division_code and
                row.get('factory_code') == factory_code and
                row.get('process_code') == process_code and
                row.get('line_code') == line_code):
                return True
        
        return False
    
    def get_name_by_code(self, code: str, code_type: str) -> Optional[str]:
        """コードから名前を取得"""
        if not self.master_data:
            return None
        
        code_column = f"{code_type}_code"
        name_column = f"{code_type}_name"
        
        for row in self.master_data:
            if row.get(code_column) == code:
                return row.get(name_column)
        
        return None