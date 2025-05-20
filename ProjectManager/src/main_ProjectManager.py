"""
ProjectManagerSuiteのメインエントリーポイント
ProjectManagerを中心に他のアプリケーション(CreateProjectList)を統合管理
"""

import os
import sys
import logging
import traceback
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from tkinter import messagebox

# アプリケーションのルートディレクトリを特定
if getattr(sys, 'frozen', False):
    # PyInstallerで実行ファイル化した場合
    APP_ROOT = Path(sys._MEIPASS)
    
    # アプリケーションディレクトリをPYTHONPATHに追加
    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))
else:
    # 開発環境での実行
    APP_ROOT = Path(__file__).parent

# デフォルト設定ファイルの初期内容
DEFAULT_SETTINGS_CONTENT = """default_project_name=新規プロジェクト
default_manager=山田太郎
default_reviewer=鈴木一郎
default_approver=佐藤部長
default_division=D001
default_factory=F001
default_process=P001
default_line=L001"""

# 適切な形式でインポート
try:
    # ユーティリティのインポート
    try:
        from utils.path_utils import get_app_root, ensure_directory
        from utils.dependency_checker import check_python_version
    except ImportError:
        # utils モジュールが使えない場合のフォールバック
        def get_app_root():
            return APP_ROOT
            
        def ensure_directory(path):
            path.mkdir(parents=True, exist_ok=True)
            return path
            
        def check_python_version(min_version=(3, 8, 0)):
            return sys.version_info[:3] >= min_version
    
    # パッケージからのインポートを試みる
    from ProjectManager.src.core.config import Config
    from ProjectManager.src.core.database import DatabaseManager
    from ProjectManager.src.ui.dashboard import DashboardGUI
    from ProjectManager.src.services.task_loader import TaskLoader
except ImportError:
    # 相対パスからのインポートを試みる
    sys.path.insert(0, str(APP_ROOT))
    from ProjectManager.src.core.config import Config
    from ProjectManager.src.core.database import DatabaseManager
    from ProjectManager.src.ui.dashboard import DashboardGUI
    from ProjectManager.src.services.task_loader import TaskLoader

def create_default_settings_file(file_path: Path) -> bool:
    """
    デフォルト設定ファイルを作成する
    
    Args:
        file_path: 設定ファイルのパス
        
    Returns:
        bool: 成功した場合True
    """
    try:
        # 親ディレクトリが存在することを確認
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ファイルが既に存在する場合は上書きしない
        if file_path.exists():
            logging.debug(f"デフォルト設定ファイルは既に存在します: {file_path}")
            return True
            
        # デフォルト設定ファイルを作成
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_SETTINGS_CONTENT)
            
        logging.info(f"デフォルト設定ファイルを作成しました: {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"デフォルト設定ファイル作成エラー: {e}")
        return False

def setup_logging() -> None:
    """
    ログ設定を初期化する
    
    ログファイルとコンソールの両方に出力を設定
    """
    try:
        # ログディレクトリの作成
        user_log_dir = Path.home() / "Documents" / "ProjectSuite" / "logs"
        user_log_dir.mkdir(parents=True, exist_ok=True)
        log_file = user_log_dir / "app.log"
        
        # ログハンドラーの設定
        handlers = [
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
        
        # ログフォーマットの設定
        formatter = logging.Formatter(Config.LOG_FORMAT)
        for handler in handlers:
            handler.setFormatter(formatter)
        
        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        
        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
        # 新しいハンドラーを追加
        for handler in handlers:
            root_logger.addHandler(handler)
            
        logging.info("ログ設定を初期化しました")
        
    except Exception as e:
        print(f"ログ設定の初期化に失敗しました: {e}")
        raise

def setup_environment() -> None:
    """
    アプリケーション環境のセットアップ
    
    - ディレクトリ構造の確認と作成
    - 設定ファイルの確認
    """
    try:
        # プロジェクトSuiteディレクトリの準備
        user_docs_dir = Path.home() / "Documents" / "ProjectSuite"
        user_docs_dir.mkdir(parents=True, exist_ok=True)
                
        # デフォルト設定ファイルの作成
        defaults_path = user_docs_dir / "defaults.txt"
        create_default_settings_file(defaults_path)
        
        # ProjectManagerSuite環境の確認
        ensure_directory(APP_ROOT / "logs")
        
        # デスクトップのprojectsフォルダーも作成
        desktop_projects_dir = Path.home() / "Desktop" / "projects"
        desktop_projects_dir.mkdir(parents=True, exist_ok=True)
                
        # Pythonバージョンの確認
        if not check_python_version():
            print("警告: Python 3.8.0以上を推奨します")
            
    except Exception as e:
        print(f"環境設定エラー: {e}")
        raise

def initialize_app() -> Optional[DatabaseManager]:
    """
    アプリケーションの初期化処理
    
    Returns:
        Optional[DatabaseManager]: 初期化されたデータベースマネージャー。
                                 エラー時はNone
    """
    try:
        # 環境のセットアップ
        setup_environment()
        
        # ディレクトリ構造の作成
        Config.setup_directories()
        
        # ユーザードキュメントディレクトリのdefaults.txtを確認
        user_docs_dir = Path.home() / "Documents" / "ProjectSuite"
        defaults_file = user_docs_dir / "defaults.txt"
        create_default_settings_file(defaults_file)
        
        # ログ設定
        setup_logging()
        logging.info("アプリケーションを開始します")
        
        # 環境の検証
        Config.validate_environment()
        
        # データベースマネージャーの初期化とマイグレーション
        db_manager = DatabaseManager(Config.DB_PATH)
        logging.info("データベースマネージャーを初期化しました")
        
        # タスクデータの読み込み
        try:
            task_loader = TaskLoader(db_manager)
            task_loader.load_tasks()
            logging.info("タスクデータを読み込みました")
            
        except Exception as e:
            logging.error(f"データ読み込みエラー: {e}\n{traceback.format_exc()}")
            messagebox.showwarning(
                "警告",
                "データの読み込み中にエラーが発生しました。\n"
                "アプリケーションは起動しますが、データが正しく反映されていない可能性があります。"
            )
        
        return db_manager
        
    except FileNotFoundError as e:
        error_msg = f"必要なファイルが見つかりません: {e}"
        logging.error(error_msg)
        messagebox.showerror("初期化エラー", error_msg)
    except PermissionError as e:
        error_msg = f"アクセス権限がありません: {e}"
        logging.error(error_msg)
        messagebox.showerror("初期化エラー", error_msg)
    except ValueError as e:
        error_msg = f"設定値が不正です: {e}"
        logging.error(error_msg)
        messagebox.showerror("初期化エラー", error_msg)
    except Exception as e:
        error_msg = f"予期せぬエラーが発生しました: {e}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        messagebox.showerror("初期化エラー", error_msg)
    
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
            print(f"未知のアプリケーション: {app_name}")
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
            
            module_path = app_info["module"].replace(".", os.path.sep) + ".py"
            full_path = APP_ROOT / module_path
            
            # サブプロセスとして実行
            process = subprocess.Popen(
                [sys.executable, str(full_path)] + list(args),
                env=os.environ.copy()
            )
            
            # このプロセスはメインプロセスの終了を待たず独立して実行
            return 0
            
        else:
            print(f"アプリケーション{app_name}の起動方法が定義されていません")
            return 1
            
    except Exception as e:
        print(f"{app_name}実行エラー: {e}\n{traceback.format_exc()}")
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
    
    # ユーザードキュメントディレクトリのdefaults.txtを確認
    user_docs_dir = Path.home() / "Documents" / "ProjectSuite"
    defaults_file = user_docs_dir / "defaults.txt"
    create_default_settings_file(defaults_file)
    
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
            error_msg = f"GUIの実行中にエラーが発生しました: {e}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("エラー", error_msg)
        
    except Exception as e:
        error_msg = f"アプリケーション実行中にエラーが発生しました: {e}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        messagebox.showerror("エラー", error_msg)
        
    finally:
        # クリーンアップ処理
        if db_manager:
            logging.info("アプリケーションを終了します")

if __name__ == "__main__":
    main()