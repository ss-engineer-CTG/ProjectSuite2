"""
パス関連の定数定義（本番環境用簡素版）
KISS・DRY・YAGNI原則に基づく最小限実装
"""

from pathlib import Path
from typing import Dict

class PathKeys:
    """パス定数定義クラス"""
    
    # === 基本パス ===
    USER_DATA_DIR = "USER_DATA_DIR"
    OUTPUT_BASE_DIR = "OUTPUT_BASE_DIR"
    
    # === CreateProjectList関連パス ===
    CPL_DIR = "CPL_DIR"
    CPL_CONFIG_DIR = "CPL_CONFIG_DIR"
    CPL_CONFIG_PATH = "CPL_CONFIG_PATH"
    CPL_TEMP_DIR = "CPL_TEMP_DIR"
    
    # === ProjectManager関連パス ===
    PM_DATA_DIR = "PM_DATA_DIR"
    PM_DB_PATH = "PM_DB_PATH"
    PM_TEMPLATES_DIR = "PM_TEMPLATES_DIR"
    
    # === 共通パス ===
    LOGS_DIR = "LOGS_DIR"

# === デフォルトパス定義 ===
DEFAULT_PATHS: Dict[str, str] = {
    # ユーザーベースパス
    PathKeys.USER_DATA_DIR: str(Path.home() / "Documents" / "ProjectSuite"),
    
    # CreateProjectList関連
    PathKeys.CPL_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList"),
    PathKeys.CPL_CONFIG_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList" / "config"),
    PathKeys.CPL_TEMP_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList" / "temp"),
    
    # ProjectManager関連
    PathKeys.PM_DATA_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data"),
    PathKeys.PM_TEMPLATES_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data" / "templates"),
    PathKeys.PM_DB_PATH: str(Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data" / "projects.db"),
    
    # 共通パス
    PathKeys.OUTPUT_BASE_DIR: str(Path.home() / "Desktop" / "projects"),
    PathKeys.LOGS_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "logs"),
}

def get_default_path(key: str) -> str:
    """デフォルトパスを取得"""
    return DEFAULT_PATHS.get(key, "")

def get_config_path() -> Path:
    """設定ファイルパスを取得"""
    config_dir = Path(DEFAULT_PATHS[PathKeys.CPL_CONFIG_DIR])
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"