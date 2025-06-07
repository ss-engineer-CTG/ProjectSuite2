"""
ProjectManager 軽量化版メインエントリーポイント
"""

import sys
import logging
from pathlib import Path

from config import Config
from database import DatabaseManager
from services import ProjectService, TaskService, ExportService, InitializationService
from ui.main_window import MainWindow
from utils import ErrorHandler

def setup_logging():
    """ログシステムの初期化"""
    try:
        config = Config()
        log_dir = Path(config.get_path('logs'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'app.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info("アプリケーションを開始します")
        
    except Exception as e:
        print(f"ログ設定の初期化に失敗: {e}")
        raise

def initialize_app():
    """アプリケーションの初期化"""
    try:
        # 設定の初期化
        config = Config()
        config.setup_directories()
        
        # 初期化サービスの実行
        init_service = InitializationService(config)
        init_service.initialize_if_needed()
        
        # データベースの初期化
        db_manager = DatabaseManager(config.get_path('database'))
        
        # サービスの初期化
        project_service = ProjectService(db_manager, config)
        task_service = TaskService(db_manager, config)
        export_service = ExportService(db_manager, config)
        
        logging.info("アプリケーションの初期化が完了しました")
        return config, db_manager, project_service, task_service, export_service
        
    except Exception as e:
        ErrorHandler.handle_critical_error(e, "アプリケーション初期化")
        return None, None, None, None, None

def main():
    """メイン実行関数"""
    try:
        # ログ設定
        setup_logging()
        
        # アプリケーション初期化
        config, db_manager, project_service, task_service, export_service = initialize_app()
        if not db_manager:
            return
        
        # GUI起動
        app = MainWindow(config, project_service, task_service, export_service)
        app.run()
        
    except KeyboardInterrupt:
        logging.info("ユーザーによる中断")
    except Exception as e:
        ErrorHandler.handle_critical_error(e, "アプリケーション実行")
    finally:
        logging.info("アプリケーションを終了します")

if __name__ == "__main__":
    main()