"""
統合設定管理クラス
Config + ConfigManager + PathRegistry の機能を統合
KISS原則: シンプルな設定管理
DRY原則: 設定管理機能の統合
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .constants import AppConstants, PathConstants

class UnifiedConfig:
    """統合設定管理クラス"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self._config_cache = {}
        self._path_registry = {}
        
        # パスレジストリの初期化
        self._initialize_path_registry()
        
        # 設定の読み込み
        self.load_config()
    
    def _initialize_path_registry(self):
        """パスレジストリの初期化"""
        self._path_registry = {
            'ROOT_DIR': str(PathConstants.ROOT_DIR),
            'USER_DOC_DIR': str(PathConstants.USER_DOC_DIR),
            'DATA_DIR': str(PathConstants.DATA_DIR),
            'MASTER_DIR': str(PathConstants.MASTER_DIR),
            'TEMPLATES_DIR': str(PathConstants.TEMPLATES_DIR),
            'EXPORTS_DIR': str(PathConstants.EXPORTS_DIR),
            'LOGS_DIR': str(PathConstants.LOGS_DIR),
            'DB_PATH': str(PathConstants.DB_PATH),
            'MASTER_DATA_PATH': str(PathConstants.MASTER_DATA_PATH),
            'DASHBOARD_EXPORT_PATH': str(PathConstants.DASHBOARD_EXPORT_PATH),
            'PROJECTS_EXPORT_PATH': str(PathConstants.PROJECTS_EXPORT_PATH),
            'DEFAULTS_FILE': str(PathConstants.DEFAULTS_FILE),
            'CONFIG_FILE': str(PathConstants.CONFIG_FILE),
        }
        
        # 出力ディレクトリの動的解決
        self._resolve_output_directory()
    
    def _resolve_output_directory(self):
        """出力ディレクトリの動的解決"""
        # カスタム出力パスの確認
        custom_path = self._get_custom_output_path()
        if custom_path and Path(custom_path).exists():
            output_dir = custom_path
        else:
            # デフォルトパス
            output_dir = str(Path.home() / "Desktop" / "projects")
        
        self._path_registry['OUTPUT_BASE_DIR'] = output_dir
        
        # 環境変数にも設定
        os.environ['PMSUITE_OUTPUT_DIR'] = output_dir
    
    def _get_custom_output_path(self) -> Optional[str]:
        """カスタム出力パスの取得"""
        try:
            # defaults.txt から読み込み
            defaults_file = Path(self._path_registry['DEFAULTS_FILE'])
            if defaults_file.exists():
                with open(defaults_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('custom_projects_dir='):
                            return line.split('=', 1)[1].strip()
            
            # config.json から読み込み
            config_file = Path(self._path_registry['CONFIG_FILE'])
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('paths', {}).get('output_base_dir')
                    
        except Exception as e:
            self.logger.warning(f"カスタム出力パスの取得に失敗: {e}")
        
        return None
    
    def get_path(self, key: str, default: str = None) -> str:
        """パスの取得"""
        return self._path_registry.get(key, default)
    
    def register_path(self, key: str, path: str):
        """パスの登録"""
        self._path_registry[key] = str(path)
        
        # 特定のパスは環境変数にも設定
        if key == 'OUTPUT_BASE_DIR':
            os.environ['PMSUITE_OUTPUT_DIR'] = path
        elif key == 'DB_PATH':
            os.environ['PMSUITE_DB_PATH'] = path
    
    def setup_directories(self):
        """必要なディレクトリの作成"""
        directories = [
            'DATA_DIR', 'MASTER_DIR', 'TEMPLATES_DIR', 
            'EXPORTS_DIR', 'LOGS_DIR', 'OUTPUT_BASE_DIR'
        ]
        
        for dir_key in directories:
            dir_path = Path(self.get_path(dir_key))
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"ディレクトリを作成/確認: {dir_path}")
            except Exception as e:
                self.logger.error(f"ディレクトリ作成エラー {dir_path}: {e}")
                raise
    
    def load_config(self):
        """設定の読み込み"""
        # defaults.txt の読み込み
        self._load_defaults()
        
        # config.json の読み込み
        self._load_json_config()
    
    def _load_defaults(self):
        """defaults.txt の読み込み"""
        defaults_file = Path(self.get_path('DEFAULTS_FILE'))
        if not defaults_file.exists():
            self._create_default_config()
            return
        
        try:
            with open(defaults_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self._config_cache[key.strip()] = value.strip()
                        
        except Exception as e:
            self.logger.error(f"defaults.txt 読み込みエラー: {e}")
    
    def _load_json_config(self):
        """config.json の読み込み"""
        config_file = Path(self.get_path('CONFIG_FILE'))
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    json_config = json.load(f)
                    self._config_cache.update(json_config)
            except Exception as e:
                self.logger.error(f"config.json 読み込みエラー: {e}")
    
    def _create_default_config(self):
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
        defaults_file = Path(self.get_path('DEFAULTS_FILE'))
        try:
            defaults_file.parent.mkdir(parents=True, exist_ok=True)
            with open(defaults_file, 'w', encoding='utf-8') as f:
                f.write(defaults_content)
            self.logger.info(f"デフォルト設定ファイルを作成: {defaults_file}")
        except Exception as e:
            self.logger.error(f"デフォルト設定ファイル作成エラー: {e}")
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """設定値の取得"""
        return self._config_cache.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """設定値の設定"""
        self._config_cache[key] = value
        self.save_config()
    
    def save_config(self):
        """設定の保存"""
        config_file = Path(self.get_path('CONFIG_FILE'))
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_cache, f, ensure_ascii=False, indent=2)
            self.logger.info("設定を保存しました")
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
    
    def update_output_directory(self, new_path: str):
        """出力ディレクトリの更新"""
        self.register_path('OUTPUT_BASE_DIR', new_path)
        self.set_setting('custom_projects_dir', new_path)
        
        # defaults.txt にも保存
        self._save_to_defaults('custom_projects_dir', new_path)
    
    def _save_to_defaults(self, key: str, value: str):
        """defaults.txt への個別設定保存"""
        defaults_file = Path(self.get_path('DEFAULTS_FILE'))
        try:
            lines = []
            key_found = False
            
            if defaults_file.exists():
                with open(defaults_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            # 既存の設定を更新または追加
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}\n'
                    key_found = True
                    break
            
            if not key_found:
                lines.append(f'{key}={value}\n')
            
            with open(defaults_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
        except Exception as e:
            self.logger.error(f"defaults.txt 保存エラー: {e}")