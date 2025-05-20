"""設定管理クラス"""

import os
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

# デフォルト設定ファイルの初期内容
DEFAULT_SETTINGS_CONTENT = """default_project_name=新規プロジェクト
default_manager=山田太郎
default_reviewer=鈴木一郎
default_approver=佐藤部長
default_division=D001
default_factory=F001
default_process=P001
default_line=L001"""

# PathRegistry をインポート
from PathRegistry import PathRegistry, get_path, ensure_dir

class Config:
    # 実行パスに関わらず動作するように設定
    if getattr(sys, 'frozen', False):
        # PyInstallerで実行ファイル化した場合
        ROOT_DIR = Path(sys._MEIPASS)
    else:
        # 通常のPython実行の場合
        ROOT_DIR = Path(__file__).parent.parent.parent
    
    # ユーザードキュメントディレクトリのパス
    USER_DOC_DIR = Path.home() / "Documents" / "ProjectSuite"
    
    # データディレクトリ（ユーザードキュメントを優先）
    DATA_DIR = USER_DOC_DIR
    
    # プロジェクトルートパスを定義（柔軟に対応）
    PROJECT_ROOT = ROOT_DIR
    
    # マスターディレクトリ
    MASTER_DIR = USER_DOC_DIR / "ProjectManager" / "data" / 'master'
    
    # マスタデータファイル
    MASTER_DATA_FILE = MASTER_DIR / 'factory_info.csv'
    
    # データベース設定
    DB_PATH = USER_DOC_DIR / "ProjectManager" / "data" / 'projects.db'
    
    # マスターフォルダのパス
    MASTER_FOLDER = USER_DOC_DIR / "ProjectManager" / "data" / 'templates' / 'project'
    
    # デフォルト設定ファイルのパス
    DEFAULT_SETTINGS_FILE = USER_DOC_DIR / "defaults.txt"
    
    # 出力先ベースディレクトリ（動的に解決）
    @classmethod
    def get_output_base_dir(cls):
        """
        出力先ベースディレクトリを取得
        
        Returns:
            Path: 出力先ベースディレクトリのパス
        """
        try:
            # PathRegistryからOUTPUT_BASE_DIRを直接取得
            # エイリアス処理はPathRegistry内部で実行されるため、PROJECTS_DIRの確認は不要
            registry = PathRegistry.get_instance()
            output_dir = registry.get_path("OUTPUT_BASE_DIR")
            if output_dir:
                return Path(output_dir)
            
            # カスタムパスが設定されていない場合はデフォルトパスを返す
            # デスクトップのprojectsフォルダを返すように変更
            return Path.home() / "Desktop" / "projects"
        except ImportError:
            # PathRegistryが使えない場合はデフォルトパスを返す
            # デスクトップのprojectsフォルダを返すように変更
            return Path.home() / "Desktop" / "projects"
    
    # プロパティとして定義
    @property
    def OUTPUT_BASE_DIR(self):
        return self.get_output_base_dir()
    
    # ダッシュボードCSV出力設定
    DASHBOARD_EXPORT_DIR = USER_DOC_DIR / "ProjectManager" / "data" / 'exports'
    DASHBOARD_EXPORT_FILE = DASHBOARD_EXPORT_DIR / 'dashboard.csv'
    PROJECTS_EXPORT_FILE = DASHBOARD_EXPORT_DIR / 'projects.csv'
    
    # メタデータ関連の設定
    METADATA_FOLDER_NAME = "999. metadata"
    TASK_FILE_NAME = "tasks.csv"
    
    # ログファイルパス (ログはユーザードキュメントディレクトリに保存)
    LOG_FILE = USER_DOC_DIR / 'logs' / 'app.log'
    
    # ログ設定
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    
    # アプリケーション設定
    APP_NAME = "案件管理フォルダ自動生成システム"
    APP_VERSION = "1.0.0"
    
    # フォルダ作成関連の設定
    MAX_FOLDER_NAME_LENGTH = 255  # Windowsの制限に合わせる
    FOLDER_NAME_SEPARATOR = '_'   # フォルダ名の区切り文字
    
    # ドキュメント処理関連の設定
    DOCUMENT_PROCESSOR = {
        'template_dir': MASTER_FOLDER,
        'output_dir': None,  # 動的に解決されるため初期値はNone
        'temp_dir': USER_DOC_DIR / 'temp',
        'supported_extensions': ['.doc', '.docx', '.xls', '.xlsx', '.xlsm'],
        'default_encoding': 'utf-8',
        'backup_enabled': True,
        'backup_dir': USER_DOC_DIR / 'backup'
    }

    @classmethod
    def setup_directories(cls):
        """必要なディレクトリを作成"""
        # PathRegistryに登録
        registry = PathRegistry.get_instance()
        
        # デフォルト設定ファイルの作成
        cls.ensure_default_settings_file()
        
        # 基本パス登録
        registry.register_path("DATA_DIR", str(cls.DATA_DIR))
        registry.register_path("MASTER_DIR", str(cls.MASTER_DIR))
        registry.register_path("MASTER_FOLDER", str(cls.MASTER_FOLDER))
        
        # 出力ディレクトリは動的に解決
        output_dir = cls.get_output_base_dir()
        registry.register_path("OUTPUT_BASE_DIR", str(output_dir))
        
        registry.register_path("DASHBOARD_EXPORT_DIR", str(cls.DASHBOARD_EXPORT_DIR))
        registry.register_path("DASHBOARD_EXPORT_FILE", str(cls.DASHBOARD_EXPORT_FILE))
        registry.register_path("PROJECTS_EXPORT_FILE", str(cls.PROJECTS_EXPORT_FILE))
        registry.register_path("DB_PATH", str(cls.DB_PATH))
        registry.register_path("DEFAULT_SETTINGS_FILE", str(cls.DEFAULT_SETTINGS_FILE))
        
        # 環境変数にも登録
        os.environ["PMSUITE_DASHBOARD_FILE"] = str(cls.DASHBOARD_EXPORT_FILE)
        os.environ["PMSUITE_DASHBOARD_DATA_DIR"] = str(cls.DASHBOARD_EXPORT_DIR)
        os.environ["PMSUITE_DB_PATH"] = str(cls.DB_PATH)
        os.environ["PMSUITE_DATA_DIR"] = str(cls.DATA_DIR)
        
        # ディレクトリ作成（PathRegistryを使用）
        directories = [
            "DATA_DIR",
            "MASTER_DIR",
            "MASTER_FOLDER",
            "OUTPUT_BASE_DIR",
            "DASHBOARD_EXPORT_DIR",
            "TEMP_DIR",
            "BACKUP_DIR",
            "LOGS_DIR"
        ]
        
        for directory in directories:
            registry.ensure_directory(directory)
            
        # ドキュメント処理設定の出力先を更新
        cls.DOCUMENT_PROCESSOR['output_dir'] = output_dir

    @classmethod
    def ensure_default_settings_file(cls) -> None:
        """デフォルト設定ファイルの存在を確認し、必要に応じて作成"""
        try:
            if not cls.DEFAULT_SETTINGS_FILE.exists():
                # 親ディレクトリの存在を確認
                cls.DEFAULT_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
                
                # デフォルト設定ファイルを作成
                with open(cls.DEFAULT_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    f.write(DEFAULT_SETTINGS_CONTENT)
                
                logging.info(f"デフォルト設定ファイルを作成しました: {cls.DEFAULT_SETTINGS_FILE}")
            else:
                logging.debug(f"デフォルト設定ファイルは既に存在します: {cls.DEFAULT_SETTINGS_FILE}")
                
        except Exception as e:
            logging.error(f"デフォルト設定ファイル作成エラー: {e}")

    @classmethod
    def get_setting(cls, key: str, default: Any = None) -> Any:
        """
        設定値を取得する
        
        Args:
            key: 設定キー
            default: デフォルト値（設定が存在しない場合に返される）
            
        Returns:
            設定値（存在しない場合はデフォルト値）
        """
        try:
            # デフォルト設定ファイルからの読み込みを優先
            if cls.DEFAULT_SETTINGS_FILE.exists():
                with open(cls.DEFAULT_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            try:
                                setting_key, value = line.split('=', 1)
                                if setting_key.strip() == key:
                                    return value.strip()
                            except ValueError:
                                continue
            
            # ConfigManager経由で設定を取得
            try:
                from ProjectManager.src.core.config_manager import ConfigManager
                config_manager = ConfigManager()
                config = config_manager.get_config()
                
                # プレフィックスを削除して検索
                plain_key = key.replace('default_', '')
                
                if config and 'defaults' in config and plain_key in config['defaults']:
                    return config['defaults'][plain_key]
            except Exception as e:
                logging.warning(f"ConfigManager経由の設定取得に失敗: {e}")
                    
            return default
        except Exception as e:
            logging.warning(f"設定の読み込みに失敗しました: {e}")
            return default

    @classmethod
    def validate_environment(cls):
        """環境の検証"""
        # PathRegistryを使った検証
        registry = PathRegistry.get_instance()
        issues = []
        
        # デフォルト設定ファイルの確認
        if not cls.DEFAULT_SETTINGS_FILE.exists():
            try:
                cls.ensure_default_settings_file()
                logging.info(f"デフォルト設定ファイルを作成しました: {cls.DEFAULT_SETTINGS_FILE}")
            except Exception as e:
                issues.append(f"デフォルト設定ファイルの作成に失敗しました: {e}")
        
        # マスタデータファイルの存在確認
        master_data_file = registry.get_path("MASTER_DATA_FILE", str(cls.MASTER_DATA_FILE))
        if not Path(master_data_file).exists():
            issues.append(f"マスタデータファイルが見つかりません: {master_data_file}")
        
        # マスターテンプレートフォルダの存在確認
        master_folder = registry.get_path("MASTER_FOLDER", str(cls.MASTER_FOLDER))
        if not Path(master_folder).exists():
            issues.append(f"マスターテンプレートフォルダが見つかりません: {master_folder}")
        
        # プロジェクト出力ディレクトリの存在確認と作成
        output_dir = cls.get_output_base_dir()
        if not output_dir.exists():
            try:
                os.makedirs(output_dir)
                logging.info(f"プロジェクト出力ディレクトリを作成しました: {output_dir}")
            except Exception as e:
                issues.append(f"プロジェクト出力ディレクトリの作成に失敗しました: {e}")
            
        # 書き込み権限の確認
        data_dir = registry.get_path("DATA_DIR", str(cls.DATA_DIR))
        try:
            test_file = Path(data_dir) / '.write_test'
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            issues.append(f"データディレクトリへの書き込み権限がありません: {e}")
            
        # 問題がある場合は例外を発生
        if issues:
            raise ValueError("\n".join(issues))

    @classmethod
    def get_project_metadata_path(cls, project_name: str) -> Path:
        """
        プロジェクトのメタデータディレクトリパスを取得
        
        Args:
            project_name: プロジェクト名
            
        Returns:
            Path: メタデータディレクトリのパス
        """
        # 出力先を動的に解決
        output_dir = cls.get_output_base_dir()
        return output_dir / project_name / cls.METADATA_FOLDER_NAME

    @classmethod
    def get_project_task_file_path(cls, project_name: str) -> Path:
        """
        プロジェクトのタスクファイルパスを取得
        
        Args:
            project_name: プロジェクト名
            
        Returns:
            Path: タスクファイルのパス
        """
        return cls.get_project_metadata_path(project_name) / cls.TASK_FILE_NAME

    @classmethod
    def get_config_as_dict(cls) -> Dict[str, Any]:
        """
        設定を辞書形式で取得
        
        Returns:
            Dict[str, Any]: 設定辞書
        """
        # PathRegistryから最新の値を取得
        registry = PathRegistry.get_instance()
        
        # 出力先を動的に解決
        output_dir = cls.get_output_base_dir()
        
        return {
            'base_dir': registry.get_path("ROOT", str(cls.ROOT_DIR)),
            'data_dir': registry.get_path("DATA_DIR", str(cls.DATA_DIR)),
            'master_dir': registry.get_path("MASTER_DIR", str(cls.MASTER_DIR)),
            'output_dir': str(output_dir),
            'db_path': registry.get_path("DB_PATH", str(cls.DB_PATH)),
            'log_file': registry.get_path("LOG_FILE", str(cls.LOG_FILE)),
            'default_settings_file': registry.get_path("DEFAULT_SETTINGS_FILE", str(cls.DEFAULT_SETTINGS_FILE)),
            'document_processor': cls.DOCUMENT_PROCESSOR
        }