"""パス管理を一元化するモジュール"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

class PathManager:
    """パス管理を一元化するシングルトンクラス"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(PathManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        
        # アプリケーションのルートディレクトリを特定
        if getattr(sys, 'frozen', False):
            # PyInstallerで実行ファイル化した場合
            self.app_root = Path(sys._MEIPASS)
        else:
            # 開発環境での実行
            self.app_root = Path(__file__).parent.parent.parent
        
        # ユーザードキュメントディレクトリのパス
        self.user_doc_dir = Path.home() / "Documents" / "ProjectSuite"
        
        # パスのエイリアス辞書
        self.paths = {
            "APP_ROOT": self.app_root,
            "USER_DOCS": self.user_doc_dir,
            "DATA_DIR": self.user_doc_dir,
            
            # デフォルトのプロジェクト出力先（後で上書き可能）
            "OUTPUT_BASE_DIR": Path.home() / "Desktop" / "projects",
            
            # ログディレクトリ
            "LOGS_DIR": self.user_doc_dir / "logs",
            
            # 各種ディレクトリ
            "MASTER_DIR": self.user_doc_dir / "ProjectManager" / "data" / "master",
            "TEMPLATES_DIR": self.user_doc_dir / "ProjectManager" / "data" / "templates",
            "EXPORTS_DIR": self.user_doc_dir / "ProjectManager" / "data" / "exports",
            "TEMP_DIR": self.user_doc_dir / "temp",
            "BACKUP_DIR": self.user_doc_dir / "backup",
            
            # ファイルパス
            "DB_PATH": self.user_doc_dir / "ProjectManager" / "data" / "projects.db",
            "MASTER_DATA_FILE": self.user_doc_dir / "ProjectManager" / "data" / "master" / "factory_info.csv",
            "DEFAULT_SETTINGS_FILE": self.user_doc_dir / "defaults.txt",
            "DASHBOARD_EXPORT_FILE": self.user_doc_dir / "ProjectManager" / "data" / "exports" / "dashboard.csv",
            "PROJECTS_EXPORT_FILE": self.user_doc_dir / "ProjectManager" / "data" / "exports" / "projects.csv",
        }
        
        # メタデータ関連の設定
        self.metadata_folder_name = "999. metadata"
        self.task_file_name = "tasks.csv"
        
        # 環境変数からの上書き
        self._load_from_environment()
    
    def _load_from_environment(self) -> None:
        """環境変数からパス設定を読み込む"""
        # 環境変数によるカスタムディレクトリの上書き
        if "PMSUITE_DATA_DIR" in os.environ:
            custom_data_dir = Path(os.environ["PMSUITE_DATA_DIR"])
            self.paths["DATA_DIR"] = custom_data_dir
            
            # 関連パスも更新
            self.paths["MASTER_DIR"] = custom_data_dir / "ProjectManager" / "data" / "master"
            self.paths["TEMPLATES_DIR"] = custom_data_dir / "ProjectManager" / "data" / "templates"
            self.paths["EXPORTS_DIR"] = custom_data_dir / "ProjectManager" / "data" / "exports"
            self.paths["DB_PATH"] = custom_data_dir / "ProjectManager" / "data" / "projects.db"
            self.paths["MASTER_DATA_FILE"] = custom_data_dir / "ProjectManager" / "data" / "master" / "factory_info.csv"
            
        if "PMSUITE_OUTPUT_DIR" in os.environ:
            self.paths["OUTPUT_BASE_DIR"] = Path(os.environ["PMSUITE_OUTPUT_DIR"])
    
    def get_path(self, alias: str, default: Optional[Union[str, Path]] = None) -> Path:
        """
        エイリアスからパスを取得
        
        Args:
            alias: パスのエイリアス
            default: デフォルト値（エイリアスが存在しない場合に返される）
            
        Returns:
            Path: 対応するパスオブジェクト
        """
        if alias in self.paths:
            return self.paths[alias]
        elif default is not None:
            return Path(default)
        else:
            self.logger.warning(f"未定義のパスエイリアス: {alias}")
            return Path()
    
    def register_path(self, alias: str, path: Union[str, Path]) -> None:
        """
        パスエイリアスを登録
        
        Args:
            alias: パスのエイリアス
            path: 登録するパス
        """
        self.paths[alias] = Path(path)
        self.logger.debug(f"パスエイリアスを登録しました: {alias} -> {path}")
    
    def update_output_dir(self, output_dir: Union[str, Path]) -> None:
        """
        出力ディレクトリを更新
        
        Args:
            output_dir: 新しい出力ディレクトリパス
        """
        output_dir_path = Path(output_dir)
        self.paths["OUTPUT_BASE_DIR"] = output_dir_path
        
        # 環境変数にも設定
        os.environ["PMSUITE_OUTPUT_DIR"] = str(output_dir_path)
        
        self.logger.info(f"出力ディレクトリを更新しました: {output_dir_path}")
    
    def ensure_directory(self, alias: str) -> Path:
        """
        指定されたエイリアスのディレクトリが存在することを確認し、
        存在しない場合は作成する
        
        Args:
            alias: ディレクトリのエイリアス
            
        Returns:
            Path: 確認/作成されたディレクトリのパス
        """
        directory = self.get_path(alias)
        if not directory.exists():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"ディレクトリを作成しました: {directory}")
            except Exception as e:
                self.logger.error(f"ディレクトリ作成エラー: {e}")
                raise
        return directory
    
    def setup_directories(self) -> None:
        """基本ディレクトリ構造をセットアップ"""
        directories = [
            "USER_DOCS",
            "LOGS_DIR",
            "DATA_DIR",
            "MASTER_DIR",
            "TEMPLATES_DIR",
            "EXPORTS_DIR",
            "TEMP_DIR",
            "BACKUP_DIR",
            "OUTPUT_BASE_DIR"
        ]
        
        for alias in directories:
            self.ensure_directory(alias)
        
        # 環境変数にも登録
        os.environ["PMSUITE_DASHBOARD_FILE"] = str(self.get_path("DASHBOARD_EXPORT_FILE"))
        os.environ["PMSUITE_DASHBOARD_DATA_DIR"] = str(self.get_path("EXPORTS_DIR"))
        os.environ["PMSUITE_DB_PATH"] = str(self.get_path("DB_PATH"))
        os.environ["PMSUITE_DATA_DIR"] = str(self.get_path("DATA_DIR"))
        
        self.logger.info("ディレクトリ構造をセットアップしました")
    
    def validate_environment(self) -> None:
        """環境の検証"""
        issues = []
        
        # 必須ディレクトリの存在確認
        required_dirs = [
            "OUTPUT_BASE_DIR",
            "LOGS_DIR",
            "DATA_DIR",
            "MASTER_DIR"
        ]
        
        for alias in required_dirs:
            path = self.get_path(alias)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"必須ディレクトリを作成しました: {path}")
                except Exception as e:
                    issues.append(f"必須ディレクトリの作成に失敗しました: {path}, エラー: {e}")
        
        # マスタデータファイルの存在確認
        master_data_file = self.get_path("MASTER_DATA_FILE")
        if not master_data_file.exists():
            issues.append(f"マスタデータファイルが見つかりません: {master_data_file}")
        
        # デフォルト設定ファイルの確認
        default_settings_file = self.get_path("DEFAULT_SETTINGS_FILE")
        if not default_settings_file.exists():
            try:
                from ProjectManager.src.core.config_manager import ConfigManager
                config_manager = ConfigManager()
                config_manager.create_default_settings_file()
                self.logger.info(f"デフォルト設定ファイルを作成しました: {default_settings_file}")
            except Exception as e:
                issues.append(f"デフォルト設定ファイルの作成に失敗しました: {e}")
        
        # 書き込み権限の確認
        try:
            data_dir = self.get_path("DATA_DIR")
            test_file = data_dir / '.write_test'
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            issues.append(f"データディレクトリへの書き込み権限がありません: {e}")
        
        # 問題がある場合は例外を発生
        if issues:
            from ProjectManager.src.core.error_handler import ApplicationError
            raise ApplicationError("環境検証エラー", "\n".join(issues))
    
    def get_project_metadata_path(self, project_path: Union[str, Path]) -> Path:
        """
        プロジェクトのメタデータディレクトリパスを取得
        
        Args:
            project_path: プロジェクトディレクトリのパス
            
        Returns:
            Path: メタデータディレクトリのパス
        """
        return Path(project_path) / self.metadata_folder_name
    
    def get_project_task_file_path(self, project_path: Union[str, Path]) -> Path:
        """
        プロジェクトのタスクファイルパスを取得
        
        Args:
            project_path: プロジェクトディレクトリのパス
            
        Returns:
            Path: タスクファイルのパス
        """
        return self.get_project_metadata_path(project_path) / self.task_file_name
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """
        パスを正規化する
        
        Args:
            path: 正規化するパス
            
        Returns:
            Path: 正規化されたパス
        """
        return Path(path).resolve()