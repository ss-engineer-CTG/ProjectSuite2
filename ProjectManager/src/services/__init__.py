"""ProjectManager サービスモジュール

ビジネスロジックを実装するサービスクラス群です。
"""

from ProjectManager.src.services.task_loader import TaskLoader
from ProjectManager.src.services.gantt_chart_manager import GanttChartManager

__all__ = [
    'TaskLoader',
    'GanttChartManager'
]

# バージョン情報
__version__ = '1.1.0'