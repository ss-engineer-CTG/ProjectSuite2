"""
統合設定管理
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any

class Config:
    """統合設定管理クラス"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self._settings = {}
        self._paths = {}
        
        # パスの初期化
        self._initialize_paths()
        
        # 設定の読み込み
        self._load_settings()
        
        self._initialized = True
    
    def _initialize_paths(self):
        """パスの初期化"""
        # ベースディレクトリ
        if hasattr(sys, 'frozen'):
            root_dir = Path(sys._MEIPASS)
        else:
            root_dir = Path(__file__).parent
        
        user_doc_dir = Path.home() / "Documents" / "ProjectSuite"
        data_dir = user_doc_dir / "ProjectManager" / "data"
        
        self._paths = {
            'root': str(root_dir),
            'user_documents': str(user_doc_dir),
            'data': str(data_dir),
            'master': str(data_dir / "master"),
            'templates': str(data_dir / "templates"),
            'exports': str(data_dir / "exports"),
            'logs': str(user_doc_dir / "logs"),
            'database': str(data_dir / "projects.db"),
            'master_data': str(data_dir / "master" / "factory_info.csv"),
            'defaults': str(root_dir / "defaults.txt"),
            'config': str(user_doc_dir / "config.json"),
            'output_base': str(Path.home() / "Desktop" / "projects"),
        }
        
        # 環境変数設定
        os.environ['PMSUITE_OUTPUT_DIR'] = self._paths['output_base']
    
    def _load_settings(self):
        """設定の読み込み"""
        # defaults.txtの読み込み
        self._load_defaults()
        
        # config.jsonの読み込み
        self._load_json_config()
    
    def _load_defaults(self):
        """defaults.txtの読み込み"""
        defaults_file = Path(self._paths['defaults'])
        if not defaults_file.exists():
            self._create_default_file()
            return
        
        try:
            with open(defaults_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self._settings[key.strip()] = value.strip()
        except Exception as e:
            self.logger.error(f"defaults.txt読み込みエラー: {e}")
    
    def _load_json_config(self):
        """config.jsonの読み込み"""
        config_file = Path(self._paths['config'])
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json_config = json.load(f)
                    self._settings.update(json_config)
            except Exception as e:
                self.logger.error(f"config.json読み込みエラー: {e}")
    
    def _create_default_file(self):
        """デフォルト設定ファイルの作成"""
        defaults_content = """# ProjectManager デフォルト設定
default_project_name=新規プロジェクト
default_manager=山田太郎
default_reviewer=鈴木一郎
default_approver=佐藤部長
default_division=D001
default_factory=F001
default_process=P001
default_line=L001
"""
        defaults_file = Path(self._paths['defaults'])
        try:
            defaults_file.parent.mkdir(parents=True, exist_ok=True)
            with open(defaults_file, 'w', encoding='utf-8') as f:
                f.write(defaults_content)
        except Exception as e:
            self.logger.error(f"デフォルト設定ファイル作成エラー: {e}")
    
    def setup_directories(self):
        """必要なディレクトリの作成"""
        directories = ['data', 'master', 'templates', 'exports', 'logs', 'output_base']
        for dir_key in directories:
            dir_path = Path(self._paths[dir_key])
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"ディレクトリ作成エラー {dir_path}: {e}")
                raise
    
    def get_path(self, key: str) -> str:
        """パスの取得"""
        return self._paths.get(key, "")
    
    def set_path(self, key: str, path: str):
        """パスの設定"""
        self._paths[key] = str(path)
        if key == 'output_base':
            os.environ['PMSUITE_OUTPUT_DIR'] = path
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """設定値の取得"""
        return self._settings.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """設定値の設定"""
        self._settings[key] = value
        self.save_config()
    
    def save_config(self):
        """設定の保存"""
        config_file = Path(self._paths['config'])
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
    
    def update_output_directory(self, new_path: str):
        """出力ディレクトリの更新"""
        self.set_path('output_base', new_path)
        self.set_setting('custom_output_dir', new_path)