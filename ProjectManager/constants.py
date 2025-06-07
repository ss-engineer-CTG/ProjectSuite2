"""
定数定義
"""

# アプリケーション情報
APP_NAME = "ProjectManager"
APP_VERSION = "2.0.0"
WINDOW_TITLE = "プロジェクト管理ダッシュボード"

# ステータス定義
PROJECT_STATUSES = ["進行中", "完了", "中止"]
TASK_STATUSES = ["未着手", "進行中", "完了", "中止"]
FILTER_OPTIONS = ["進行中", "全て"]

# 文字列長制限
MAX_PROJECT_NAME_LENGTH = 100
MAX_PERSON_NAME_LENGTH = 50

# 必須フィールド
REQUIRED_PROJECT_FIELDS = ['project_name', 'start_date', 'manager', 'reviewer', 'approver']

# 日付形式
DATE_FORMAT = '%Y-%m-%d'

# エンコーディング
ENCODING_OPTIONS = ['utf-8', 'utf-8-sig', 'cp932']

# フォルダ設定
METADATA_FOLDER_NAME = "999. metadata"

# UI設定
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
PADDING_SMALL = 5
PADDING_MEDIUM = 10
PADDING_LARGE = 20