"""
アプリケーション定数とパス定義の一元管理（本番環境用簡素版）
KISS原則: 必要最小限の定数のみ
"""

import sys
from pathlib import Path

class AppConstants:
    """アプリケーション基本定数"""
    
    # アプリケーション情報
    APP_NAME = "ProjectManager"
    APP_VERSION = "2.0.0"
    
    # ログ設定
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    LOG_LEVEL = 'INFO'
    
    # UI設定
    WINDOW_SIZE_RATIO = 0.8
    FORM_WIDTH_RATIO = 0.8
    FORM_HEIGHT_RATIO = 0.8
    
    # データベース設定
    DB_FILENAME = 'projects.db'
    
    # ファイル・フォルダ設定
    METADATA_FOLDER_NAME = "999. metadata"
    TASK_FILE_NAME = "tasks.csv"
    MASTER_DATA_FILENAME = "factory_info.csv"
    
    # エクスポート設定
    DASHBOARD_EXPORT_FILENAME = "dashboard.csv"
    PROJECTS_EXPORT_FILENAME = "projects.csv"
    
    # UI文字列
    WINDOW_TITLE = "プロジェクト管理ダッシュボード"
    
    # ステータス定義
    PROJECT_STATUSES = ["進行中", "完了", "中止"]
    TASK_STATUSES = ["未着手", "進行中", "完了", "中止"]
    
    # フィルター定義
    FILTER_OPTIONS = ["進行中", "全て"]

class PathConstants:
    """パス定義の一元管理"""
    
    # 実行環境の判定
    if getattr(sys, 'frozen', False):
        ROOT_DIR = Path(sys._MEIPASS)
    else:
        ROOT_DIR = Path(__file__).parent.parent
    
    # ベースディレクトリ
    USER_DOC_DIR = Path.home() / "Documents" / "ProjectSuite"
    
    # データディレクトリ
    DATA_DIR = USER_DOC_DIR / "ProjectManager" / "data"
    
    # サブディレクトリ
    MASTER_DIR = DATA_DIR / "master"
    TEMPLATES_DIR = DATA_DIR / "templates"
    EXPORTS_DIR = DATA_DIR / "exports"
    LOGS_DIR = USER_DOC_DIR / "logs"
    
    # ファイルパス
    DB_PATH = DATA_DIR / AppConstants.DB_FILENAME
    MASTER_DATA_PATH = MASTER_DIR / AppConstants.MASTER_DATA_FILENAME
    DASHBOARD_EXPORT_PATH = EXPORTS_DIR / AppConstants.DASHBOARD_EXPORT_FILENAME
    PROJECTS_EXPORT_PATH = EXPORTS_DIR / AppConstants.PROJECTS_EXPORT_FILENAME
    
    # 設定ファイル
    DEFAULTS_FILE = ROOT_DIR / "defaults.txt"
    CONFIG_FILE = USER_DOC_DIR / "config.json"

class ValidationConstants:
    """入力検証用定数"""
    
    # 文字列長制限
    MAX_PROJECT_NAME_LENGTH = 100
    MAX_PERSON_NAME_LENGTH = 50
    MAX_CODE_LENGTH = 20
    
    # 必須フィールド
    REQUIRED_PROJECT_FIELDS = [
        'project_name', 'start_date', 'manager', 'reviewer', 'approver'
    ]
    
    # 日付形式
    DATE_FORMAT = '%Y-%m-%d'
    
    # エンコーディング
    ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'cp932']