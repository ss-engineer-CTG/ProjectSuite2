"""
ProjectManagerSuiteのメインエントリーポイント
ProjectManagerを中心に他のアプリケーション(CreateProjectList)を統合管理
"""

import sys
import traceback
import logging
from pathlib import Path
from typing import Optional

# アプリケーションのルートディレクトリを特定
if getattr(sys, 'frozen', False):
    # PyInstallerで実行ファイル化した場合
    APP_ROOT = Path(sys._MEIPASS)
    
    # アプリケーションディレクトリをPYTHONPATHに追加
    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))
else:
    # 開発環境での実行
    # main_ProjectManager.pyはProjectManagerフォルダ内にあるため、
    # ProjectManagerフォルダの親ディレクトリをルートとする
    APP_ROOT = Path(__file__).parent.parent
    
    # 開発環境ではプロジェクトルートをPYTHONPATHに追加
    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))

# コアモジュールのインポート
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.config_manager import ConfigManager
from ProjectManager.src.core.log_manager import LogManager, get_logger
from ProjectManager.src.core.error_handler import ErrorHandler, ApplicationError
from ProjectManager.src.core.project_database_manager import ProjectDatabaseManager

# サービスモジュールのインポート
from ProjectManager.src.services.task_loader import TaskLoader
from ProjectManager.src.services.gantt_chart_manager import GanttChartManager

# UIモジュールのインポート
from ProjectManager.src.ui.dashboard_gui import DashboardGUI

# ロガーの取得
logger = get_logger(__name__)

def initialize_app() -> Optional[ProjectDatabaseManager]:
    """
    アプリケーションの初期化処理
    
    Returns:
        Optional[ProjectDatabaseManager]: 初期化されたデータベースマネージャー。
                                        エラー時はNone
    """
    error_handler = ErrorHandler()
    
    try:
        # 1. パスマネージャーの初期化
        path_manager = PathManager()
        path_manager.setup_directories()
        logger.debug("パスマネージャーを初期化しました")
        
        # 2. 設定マネージャーの初期化
        config_manager = ConfigManager()
        config_manager.load_or_create_defaults()
        logger.debug("設定マネージャーを初期化しました")

        # 3. ログマネージャーの初期化
        log_manager = LogManager()
        log_manager.setup()
        logger.info("アプリケーションを開始します")
        
        # 4. 環境の検証
        path_manager.validate_environment()
        
        # 5. データベースマネージャーの初期化
        db_path = path_manager.get_path("DB_PATH")
        db_manager = ProjectDatabaseManager(db_path)
        logger.info("データベースマネージャーを初期化しました")
        
        # 6. タスクデータの読み込み
        try:
            task_loader = TaskLoader(db_manager)
            projects_count, tasks_count, errors_count = task_loader.load_tasks()
            logger.info(f"タスクデータを読み込みました: プロジェクト {projects_count}件, タスク {tasks_count}件, エラー {errors_count}件")
            
        except Exception as e:
            logger.error(f"データ読み込みエラー: {e}")
            error_handler.show_error_dialog(
                "警告",
                "データの読み込み中にエラーが発生しました。\n"
                "アプリケーションは起動しますが、データが正しく反映されていない可能性があります。"
            )
        
        # 7. ガントチャートマネージャーの初期化と更新
        try:
            gantt_manager = GanttChartManager(db_manager)
            logger.debug("ガントチャートマネージャーを初期化しました")
        except Exception as e:
            logger.error(f"ガントチャートマネージャー初期化エラー: {e}")
        
        return db_manager
        
    except ApplicationError as e:
        error_handler.handle_error(e, "初期化エラー")
    except Exception as e:
        error_msg = f"予期せぬエラーが発生しました: {e}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        error_handler.show_error_dialog("初期化エラー", error_msg)
    
    return None

def run_standalone_app(app_name: str, *args) -> int:
    """
    指定されたアプリケーションをスタンドアロンモードで実行
    
    Args:
        app_name: アプリケーション名
        *args: アプリケーションに渡す引数
        
    Returns:
        int: 終了コード
    """
    # アプリケーション定義
    apps = {
        "CreateProjectList": {
            "module": "CreateProjectList.main.document_processor_main",
            "main_func": "main"
        }
    }
    
    try:
        if app_name not in apps:
            logger.error(f"未知のアプリケーション: {app_name}")
            return 1
            
        app_info = apps[app_name]
        
        # モジュールから関数をインポートして実行
        if app_info["module"] and app_info["main_func"]:
            module = __import__(app_info["module"], fromlist=[app_info["main_func"]])
            main_func = getattr(module, app_info["main_func"])
            main_func(*args)
            return 0
        
        # ファイルを直接実行
        elif app_info["module"] and not app_info["main_func"]:
            # 他のアプリケーションの通常処理
            import subprocess
            
            module_path = app_info["module"].replace(".", str(Path.separator)) + ".py"
            full_path = APP_ROOT / module_path
            
            # サブプロセスとして実行
            process = subprocess.Popen(
                [sys.executable, str(full_path)] + list(args),
                env=sys.environ.copy()
            )
            
            # このプロセスはメインプロセスの終了を待たず独立して実行
            return 0
            
        else:
            logger.error(f"アプリケーション{app_name}の起動方法が定義されていません")
            return 1
            
    except Exception as e:
        logger.error(f"{app_name}実行エラー: {e}\n{traceback.format_exc()}")
        return 1

def main() -> None:
    """
    アプリケーションのメインエントリーポイント
    """
    # コマンドライン引数を解析
    if len(sys.argv) > 1:
        app_name = sys.argv[1]
        app_args = sys.argv[2:]
        sys.exit(run_standalone_app(app_name, *app_args))
    
    # メインアプリケーション（ProjectManager）の起動
    db_manager = None
    try:
        # アプリケーションの初期化
        db_manager = initialize_app()
        if not db_manager:
            return
        
        # GUIの起動
        app = DashboardGUI(db_manager)
        
        try:
            app.run()
        except Exception as e:
            error_handler = ErrorHandler()
            error_handler.handle_error(e, "GUI実行エラー")
        
    except Exception as e:
        logger.error(f"アプリケーション実行中にエラーが発生しました: {e}\n{traceback.format_exc()}")
        error_handler = ErrorHandler()
        error_handler.show_error_dialog("エラー", f"アプリケーション実行中にエラーが発生しました: {e}")
        
    finally:
        # クリーンアップ処理
        if db_manager:
            logger.info("アプリケーションを終了します")

if __name__ == "__main__":
    main()