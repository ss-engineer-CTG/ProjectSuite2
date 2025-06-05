"""
パス関連の定数定義
KISS・DRY・YAGNI原則に基づく簡素化版
"""

from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional

class PathKeys:
    """パス定数定義クラス（すべて定数として定義）"""
    
    # === 基本パス ===
    ROOT = "ROOT"
    USER_DATA_DIR = "USER_DATA_DIR"
    DATA_DIR = "DATA_DIR"
    
    # === 出力/プロジェクトパス ===
    OUTPUT_BASE_DIR = "OUTPUT_BASE_DIR"
    PROJECTS_DIR = "PROJECTS_DIR"  # OUTPUT_BASE_DIRのエイリアス
    
    # === CreateProjectList関連パス ===
    CPL_DIR = "CPL_DIR"
    CPL_CONFIG_DIR = "CPL_CONFIG_DIR"
    CPL_CONFIG_PATH = "CPL_CONFIG_PATH"
    CPL_TEMP_DIR = "CPL_TEMP_DIR"
    CPL_TEMPLATES_DIR = "CPL_TEMPLATES_DIR"
    CPL_CACHE_DIR = "CPL_CACHE_DIR"
    CPL_INPUT_FOLDER = "CPL_INPUT_FOLDER"
    CPL_OUTPUT_FOLDER = "CPL_OUTPUT_FOLDER"
    
    # === ProjectManager関連パス ===
    PM_DATA_DIR = "PM_DATA_DIR"
    PM_MASTER_DIR = "PM_MASTER_DIR"
    PM_DB_PATH = "PM_DB_PATH"
    PM_TEMPLATES_DIR = "PM_TEMPLATES_DIR"
    PM_OUTPUT_BASE_DIR = "PM_OUTPUT_BASE_DIR"
    
    # === 後方互換性のためのエイリアス ===
    DB_PATH = "DB_PATH"  # PM_DB_PATHのエイリアス
    TEMPLATES_DIR = "TEMPLATES_DIR"  # PM_TEMPLATES_DIRのエイリアス
    
    # === 共通パス ===
    LOGS_DIR = "LOGS_DIR"
    TEMP_DIR = "TEMP_DIR"
    BACKUP_DIR = "BACKUP_DIR"
    EXPORTS_DIR = "EXPORTS_DIR"

class PathType(Enum):
    """パスタイプの列挙型（簡素化）"""
    
    ROOT = auto()         # ルートディレクトリ
    CONFIG = auto()       # 設定ディレクトリ
    DATA = auto()         # データディレクトリ
    OUTPUT = auto()       # 出力ディレクトリ
    TEMPLATE = auto()     # テンプレートディレクトリ
    TEMP = auto()         # 一時ディレクトリ
    LOG = auto()          # ログディレクトリ
    DATABASE = auto()     # データベースファイル
    UNKNOWN = auto()      # 不明なパスタイプ

# === パスタイプ判定関数（KISS原則に基づく簡素化） ===
def get_path_type(key: str) -> PathType:
    """
    パスキーからパスタイプを取得
    
    Args:
        key: パスキー
        
    Returns:
        PathType: パスタイプ
    """
    key_upper = key.upper()
    
    # 簡単なマッピング（複雑なロジックを排除）
    type_mapping = {
        'ROOT': PathType.ROOT,
        'CONFIG': PathType.CONFIG,
        'DATA': PathType.DATA,
        'OUTPUT': PathType.OUTPUT,
        'TEMPLATE': PathType.TEMPLATE,
        'TEMP': PathType.TEMP,
        'LOG': PathType.LOG,
        'DATABASE': PathType.DATABASE,
    }
    
    # キーワードベースの判定
    for keyword, path_type in type_mapping.items():
        if keyword in key_upper:
            return path_type
    
    # DB関連の特別判定
    if 'DB' in key_upper or 'DATABASE' in key_upper:
        return PathType.DATABASE
    
    # 出力関連の特別判定
    if any(term in key_upper for term in ['OUTPUT', 'PROJECT']):
        return PathType.OUTPUT
    
    # テンプレート関連の特別判定
    if any(term in key_upper for term in ['TEMPLATE', 'INPUT']):
        return PathType.TEMPLATE
    
    return PathType.UNKNOWN

# === デフォルトパス定義（一元管理） ===
DEFAULT_PATHS: Dict[str, str] = {
    # ユーザーベースパス
    PathKeys.USER_DATA_DIR: str(Path.home() / "Documents" / "ProjectSuite"),
    
    # CreateProjectList関連
    PathKeys.CPL_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList"),
    PathKeys.CPL_CONFIG_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList" / "config"),
    PathKeys.CPL_TEMP_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList" / "temp"),
    PathKeys.CPL_CACHE_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "CreateProjectList" / "cache"),
    
    # ProjectManager関連（想定値）
    PathKeys.PM_DATA_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data"),
    PathKeys.PM_TEMPLATES_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data" / "templates"),
    PathKeys.PM_DB_PATH: str(Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data" / "projects.db"),
    
    # 共通パス
    PathKeys.OUTPUT_BASE_DIR: str(Path.home() / "Desktop" / "projects"),
    PathKeys.LOGS_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "logs"),
    PathKeys.TEMP_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "temp"),
    PathKeys.BACKUP_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "backup"),
    PathKeys.EXPORTS_DIR: str(Path.home() / "Documents" / "ProjectSuite" / "exports"),
}

def get_default_path(key: str) -> Optional[str]:
    """
    デフォルトパスを取得
    
    Args:
        key: パスキー
        
    Returns:
        Optional[str]: デフォルトパス（存在しない場合はNone）
    """
    return DEFAULT_PATHS.get(key)

def get_all_default_paths() -> Dict[str, str]:
    """
    全デフォルトパスを取得
    
    Returns:
        Dict[str, str]: 全デフォルトパスの辞書
    """
    return DEFAULT_PATHS.copy()

def is_valid_path_key(key: str) -> bool:
    """
    有効なパスキーか判定
    
    Args:
        key: パスキー
        
    Returns:
        bool: 有効な場合True
    """
    # PathKeysクラスの属性として存在するかチェック
    return hasattr(PathKeys, key)

def get_related_paths(base_key: str) -> Dict[str, str]:
    """
    関連パスを取得（階層関係にあるパス）
    
    Args:
        base_key: ベースとなるパスキー
        
    Returns:
        Dict[str, str]: 関連パスの辞書
    """
    related = {}
    
    # 簡単な関連性マッピング
    relations = {
        PathKeys.USER_DATA_DIR: [PathKeys.CPL_DIR, PathKeys.PM_DATA_DIR, PathKeys.LOGS_DIR],
        PathKeys.CPL_DIR: [PathKeys.CPL_CONFIG_DIR, PathKeys.CPL_TEMP_DIR, PathKeys.CPL_CACHE_DIR],
        PathKeys.PM_DATA_DIR: [PathKeys.PM_TEMPLATES_DIR, PathKeys.PM_DB_PATH],
    }
    
    if base_key in relations:
        for related_key in relations[base_key]:
            default_path = get_default_path(related_key)
            if default_path:
                related[related_key] = default_path
    
    return related

# === パス検証ユーティリティ ===
def validate_path_structure(base_path: str) -> Dict[str, bool]:
    """
    パス構造の検証
    
    Args:
        base_path: ベースパス
        
    Returns:
        Dict[str, bool]: 検証結果
    """
    validation = {}
    base = Path(base_path)
    
    try:
        validation['base_exists'] = base.exists()
        validation['base_is_dir'] = base.is_dir() if base.exists() else False
        validation['base_writable'] = True
        
        # 書き込み可能性テスト
        if base.exists() and base.is_dir():
            try:
                test_file = base / '.write_test'
                test_file.touch()
                test_file.unlink()
                validation['base_writable'] = True
            except:
                validation['base_writable'] = False
        
        # 必要なサブディレクトリの存在確認
        required_subdirs = ['config', 'temp', 'logs']
        for subdir in required_subdirs:
            subdir_path = base / subdir
            validation[f'{subdir}_exists'] = subdir_path.exists()
            validation[f'{subdir}_is_dir'] = subdir_path.is_dir() if subdir_path.exists() else False
    
    except Exception as e:
        validation['validation_error'] = str(e)
    
    return validation

def create_standard_directory_structure(base_path: str) -> Dict[str, bool]:
    """
    標準ディレクトリ構造の作成
    
    Args:
        base_path: ベースパス
        
    Returns:
        Dict[str, bool]: 作成結果
    """
    creation_results = {}
    base = Path(base_path)
    
    # 標準ディレクトリ構造
    standard_dirs = [
        'CreateProjectList',
        'CreateProjectList/config',
        'CreateProjectList/temp',
        'CreateProjectList/cache',
        'ProjectManager/data',
        'ProjectManager/data/templates',
        'logs',
        'temp',
        'backup',
        'exports'
    ]
    
    for dir_path in standard_dirs:
        try:
            full_path = base / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            creation_results[dir_path] = True
        except Exception as e:
            creation_results[dir_path] = False
            creation_results[f'{dir_path}_error'] = str(e)
    
    return creation_results

# === エイリアス管理（DRY原則） ===
PATH_ALIASES: Dict[str, str] = {
    # 後方互換性エイリアス
    PathKeys.DB_PATH: PathKeys.PM_DB_PATH,
    PathKeys.TEMPLATES_DIR: PathKeys.PM_TEMPLATES_DIR,
    PathKeys.PROJECTS_DIR: PathKeys.OUTPUT_BASE_DIR,
    
    # 短縮エイリアス
    'CONFIG': PathKeys.CPL_CONFIG_DIR,
    'TEMP': PathKeys.CPL_TEMP_DIR,
    'LOGS': PathKeys.LOGS_DIR,
    'DB': PathKeys.PM_DB_PATH,
    'TEMPLATES': PathKeys.PM_TEMPLATES_DIR,
    'OUTPUT': PathKeys.OUTPUT_BASE_DIR,
}

def resolve_alias(key: str) -> str:
    """
    エイリアスを実際のキーに解決
    
    Args:
        key: パスキー（エイリアス可能）
        
    Returns:
        str: 解決されたパスキー
    """
    return PATH_ALIASES.get(key, key)

def get_all_aliases() -> Dict[str, str]:
    """
    全エイリアスを取得
    
    Returns:
        Dict[str, str]: エイリアス辞書
    """
    return PATH_ALIASES.copy()