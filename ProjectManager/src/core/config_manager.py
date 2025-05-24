"""設定管理を一元化するモジュール"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from ProjectManager.src.core.path_manager import PathManager

# デフォルト設定ファイルの初期内容
DEFAULT_SETTINGS_CONTENT = """default_project_name=新規プロジェクト
default_manager=山田太郎
default_reviewer=鈴木一郎
default_approver=佐藤部長
default_division=D001
default_factory=F001
default_process=P001
default_line=L001"""

class ConfigManager:
    """設定管理を一元化するシングルトンクラス"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化
        
        Args:
            config_path: 設定ファイルのパス（省略時はデフォルトパス）
        """
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        
        # パスマネージャーの取得
        self.path_manager = PathManager()
        
        # 設定ファイルのパス
        if config_path:
            self.config_file = Path(config_path)
        else:
            # デフォルトの設定ファイルパス
            self.config_file = self.path_manager.get_path("USER_DOCS") / "config.json"
        
        # デフォルト設定ファイルのパス
        self.defaults_file = self.path_manager.get_path("DEFAULT_SETTINGS_FILE")
        
        # 必要なディレクトリを作成
        self._ensure_directories()
        
        # デフォルト設定ファイルを確認
        self.create_default_settings_file()
        
        # configフォルダがない場合は作成を試みる
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # 権限エラーの場合は一時ディレクトリに変更
            import tempfile
            self.config_file = Path(tempfile.gettempdir()) / "projectsuite_config.json"
            self.logger.warning(f"設定ファイルを一時ディレクトリに変更: {self.config_file}")
        
        # 設定の読み込み
        self.config = self._load_config()
    
    def _ensure_directories(self) -> None:
        """必要なディレクトリを作成"""
        try:
            # ユーザードキュメントのProjectSuiteディレクトリを作成
            self.path_manager.ensure_directory("USER_DOCS")
                
        except Exception as e:
            self.logger.error(f"ディレクトリ作成エラー: {e}")
    
    def create_default_settings_file(self) -> bool:
        """
        デフォルト設定ファイルの存在を確認し、必要に応じて作成
        
        Returns:
            bool: 正常に処理が完了した場合はTrue
        """
        try:
            if not self.defaults_file.exists():
                # 親ディレクトリの存在を確認
                self.defaults_file.parent.mkdir(parents=True, exist_ok=True)
                
                # デフォルト設定ファイルを作成
                with open(self.defaults_file, 'w', encoding='utf-8') as f:
                    f.write(DEFAULT_SETTINGS_CONTENT)
                
                self.logger.info(f"デフォルト設定ファイルを作成しました: {self.defaults_file}")
            else:
                self.logger.debug(f"デフォルト設定ファイルは既に存在します: {self.defaults_file}")
            
            return True
                
        except Exception as e:
            self.logger.error(f"デフォルト設定ファイル作成エラー: {e}")
            return False
    
    def _load_config(self) -> Dict[str, Any]:
        """
        設定ファイルから設定を読み込む
        
        Returns:
            Dict[str, Any]: 設定データ
        """
        # デフォルト設定ファイルからの設定を読み込む
        default_settings = self._load_default_settings()
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.info(f"設定を読み込みました: {self.config_file}")
                    
                    # デフォルト設定がない場合は追加
                    if 'defaults' not in config:
                        config['defaults'] = default_settings
                    else:
                        # デフォルト設定をマージ
                        for key, value in default_settings.items():
                            if key not in config['defaults']:
                                config['defaults'][key] = value
                    
                    return config
            except Exception as e:
                self.logger.error(f"設定読み込みエラー: {e}")
        
        # デフォルト設定
        return self._get_default_config(default_settings)
    
    def _load_default_settings(self) -> Dict[str, Any]:
        """
        デフォルト設定ファイルから設定を読み込む
        
        Returns:
            Dict[str, Any]: デフォルト設定データ
        """
        default_settings = {}
        
        try:
            if self.defaults_file.exists():
                with open(self.defaults_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                key, value = line.split('=', 1)
                                plain_key = key.strip().replace('default_', '')
                                default_settings[plain_key] = value.strip()
                            except ValueError:
                                continue
            else:
                # デフォルト設定ファイルがない場合は作成
                self.create_default_settings_file()
                
                # 作成したファイルから読み込み直す
                if self.defaults_file.exists():
                    with open(self.defaults_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                try:
                                    key, value = line.split('=', 1)
                                    plain_key = key.strip().replace('default_', '')
                                    default_settings[plain_key] = value.strip()
                                except ValueError:
                                    continue
        except Exception as e:
            self.logger.error(f"デフォルト設定読み込みエラー: {e}")
        
        # 必須のデフォルト値がない場合は追加
        if not default_settings:
            default_settings = {
                'project_name': '新規プロジェクト',
                'manager': '山田太郎',
                'reviewer': '鈴木一郎',
                'approver': '佐藤部長',
                'division': 'D001',
                'factory': 'F001',
                'process': 'P001',
                'line': 'L001'
            }
        
        return default_settings
    
    def _get_default_config(self, default_settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        デフォルト設定を取得
        
        Args:
            default_settings: デフォルト設定ファイルから読み込んだ設定
            
        Returns:
            Dict[str, Any]: デフォルト設定
        """
        # パスマネージャからパスを取得
        user_doc_dir = self.path_manager.get_path("USER_DOCS")
        output_base_dir = self.path_manager.get_path("OUTPUT_BASE_DIR")
        
        return {
            'paths': {
                'output_base_dir': str(output_base_dir),
                'user_data_dir': str(user_doc_dir),
                'logs_dir': str(self.path_manager.get_path("LOGS_DIR")),
                'master_dir': str(self.path_manager.get_path("MASTER_DIR")),
                'templates_dir': str(self.path_manager.get_path("TEMPLATES_DIR")),
                'exports_dir': str(self.path_manager.get_path("EXPORTS_DIR")),
                'db_path': str(self.path_manager.get_path("DB_PATH"))
            },
            'defaults': default_settings,
            'app': {
                'appearance': 'dark',
                'language': 'ja',
                'last_updated': datetime.now().isoformat()
            }
        }
    
    def save_config(self) -> None:
        """設定ファイルの保存"""
        try:
            # 最終更新日時の更新
            if 'app' not in self.config:
                self.config['app'] = {}
            self.config['app']['last_updated'] = datetime.now().isoformat()
            
            # 設定の保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"設定を保存しました: {self.config_file}")
            
            # パスマネージャーに通知
            if 'paths' in self.config:
                for key, value in self.config['paths'].items():
                    normalized_key = key.upper()
                    # output_base_dirの場合はOUTPUT_BASE_DIRとして登録
                    if key == 'output_base_dir':
                        self.path_manager.register_path("OUTPUT_BASE_DIR", value)
                    else:
                        # その他のパスはそのまま登録
                        self.path_manager.register_path(normalized_key, value)
                    
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
            raise
    
    def get_config(self) -> Dict[str, Any]:
        """
        現在の設定を取得
        
        Returns:
            Dict[str, Any]: 現在の設定
        """
        return self.config
    
    def get_setting(self, section: str, key: str, default: Any = None) -> Any:
        """
        設定値を取得
        
        Args:
            section: 設定セクション
            key: 設定キー
            default: デフォルト値
            
        Returns:
            Any: 設定値
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set_setting(self, section: str, key: str, value: Any) -> None:
        """
        設定値を設定
        
        Args:
            section: 設定セクション
            key: 設定キー
            value: 設定値
        """
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        
        # 特定の設定はパスマネージャーにも反映
        if section == 'paths':
            normalized_key = key.upper()
            # output_base_dirの場合はOUTPUT_BASE_DIRとして登録
            if key == 'output_base_dir':
                self.path_manager.register_path("OUTPUT_BASE_DIR", value)
            else:
                self.path_manager.register_path(normalized_key, value)
        
        # デフォルト設定の変更の場合はファイルに反映
        if section == 'defaults':
            self._update_default_settings_file(key, value)
        
        self.save_config()
    
    def _update_default_settings_file(self, key: str, value: str) -> None:
        """
        デフォルト設定ファイルを更新
        
        Args:
            key: 設定キー
            value: 設定値
        """
        try:
            if not self.defaults_file.exists():
                # 親ディレクトリの存在を確認
                self.defaults_file.parent.mkdir(parents=True, exist_ok=True)
                
                # デフォルト設定ファイルを新規作成
                with open(self.defaults_file, 'w', encoding='utf-8') as f:
                    f.write(f"default_{key}={value}\n")
                
                self.logger.info(f"デフォルト設定ファイルを作成しました: {self.defaults_file}")
                return
            
            # 既存の設定ファイルを読み込み
            settings = {}
            with open(self.defaults_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            setting_key, setting_value = line.split('=', 1)
                            settings[setting_key.strip()] = setting_value.strip()
                        except ValueError:
                            continue
            
            # 設定を更新
            settings[f"default_{key}"] = value
            
            # 設定を書き戻し
            with open(self.defaults_file, 'w', encoding='utf-8') as f:
                for setting_key, setting_value in settings.items():
                    f.write(f"{setting_key}={setting_value}\n")
            
            self.logger.info(f"デフォルト設定ファイルを更新しました: {key}={value}")
            
        except Exception as e:
            self.logger.error(f"デフォルト設定ファイル更新エラー: {e}")
    
    def update_output_dir(self, output_dir: str) -> None:
        """
        出力ディレクトリを更新
        
        Args:
            output_dir: 新しい出力ディレクトリパス
        """
        # 設定更新
        self.set_setting('paths', 'output_base_dir', output_dir)
        
        # パスマネージャーにも反映
        self.path_manager.update_output_dir(output_dir)
            
        self.logger.info(f"出力ディレクトリを更新しました: {output_dir}")
    
    def load_or_create_defaults(self) -> None:
        """デフォルト設定ファイルが存在しない場合は作成し、設定を読み込む"""
        if not self.defaults_file.exists():
            self.create_default_settings_file()
        
        # 設定の読み込み
        self.config = self._load_config()
        self.logger.debug("設定をロードしました")