"""ProjectManager UIモジュール

ユーザーインターフェース関連のクラス群です。
"""

from ProjectManager.src.ui.base_ui_component import BaseUIComponent
from ProjectManager.src.ui.dashboard_gui import DashboardGUI
from ProjectManager.src.ui.project_list_view import ProjectListView
from ProjectManager.src.ui.project_card import ProjectCard
from ProjectManager.src.ui.path_config_dialog import PathConfigDialog
from ProjectManager.src.ui.project_path_dialog import ProjectPathDialog

__all__ = [
    'BaseUIComponent',
    'DashboardGUI',
    'ProjectListView',
    'ProjectCard',
    'PathConfigDialog',
    'ProjectPathDialog'
]

# バージョン情報
__version__ = '1.1.0'