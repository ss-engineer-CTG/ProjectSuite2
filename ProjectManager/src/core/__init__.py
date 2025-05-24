"""ProjectManager コアモジュール

基本的なユーティリティと共通機能を提供するコアモジュール群です。
"""

from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.config_manager import ConfigManager
from ProjectManager.src.core.log_manager import LogManager, get_logger
from ProjectManager.src.core.error_handler import ErrorHandler, ApplicationError
from ProjectManager.src.core.database_base import DatabaseBaseManager
from ProjectManager.src.core.project_database_manager import ProjectDatabaseManager
from ProjectManager.src.core.file_utils import FileUtils
from ProjectManager.src.core.task_validator import TaskValidator
from ProjectManager.src.core.master_data import MasterDataManager, MasterDataEntry

__all__ = [
    'PathManager',
    'ConfigManager',
    'LogManager',
    'get_logger',
    'ErrorHandler',
    'ApplicationError',
    'DatabaseBaseManager',
    'ProjectDatabaseManager',
    'FileUtils',
    'TaskValidator',
    'MasterDataManager',
    'MasterDataEntry'
]

# バージョン情報
__version__ = '1.1.0'