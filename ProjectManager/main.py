"""
ProjectManager 最適化版メインエントリーポイント
統合設定管理とシンプルな起動処理
"""

import sys
import logging
from pathlib import Path

# 最適化されたコアモジュールをインポート
from core.constants import AppConstants
from core.unified_config import UnifiedConfig
from core.database import DatabaseManager
from ui.dashboard import DashboardGUI
from services.project_service import ProjectService
from utils.error_handler import ErrorHandler

def setup_logging():
    """ログシステムの初期化"""
    try:
        # UnifiedConfigのインスタンスを作成
        config = UnifiedConfig()
        log_dir = Path(config.get_path('LOGS_DIR'))
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format=AppConstants.LOG_FORMAT,
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
        # 統合設定の初期化
        config = UnifiedConfig()
        config.setup_directories()
        
        # データベースの初期化
        db_manager = DatabaseManager(config.get_path('DB_PATH'))
        
        # プロジェクトサービスの初期化
        project_service = ProjectService(db_manager)
        
        logging.info("アプリケーションの初期化が完了しました")
        return db_manager, project_service
        
    except Exception as e:
        ErrorHandler.handle_critical_error(e, "アプリケーション初期化エラー")
        return None, None

def main():
    """メイン実行関数"""
    try:
        # ログ設定
        setup_logging()
        
        # アプリケーション初期化
        db_manager, project_service = initialize_app()
        if not db_manager:
            return
        
        # GUI起動
        app = DashboardGUI(db_manager, project_service)
        app.run()
        
    except KeyboardInterrupt:
        logging.info("ユーザーによる中断")
    except Exception as e:
        ErrorHandler.handle_critical_error(e, "アプリケーション実行エラー")
    finally:
        logging.info("アプリケーションを終了します")

if __name__ == "__main__":
    main()