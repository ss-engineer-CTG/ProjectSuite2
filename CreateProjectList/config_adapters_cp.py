"""
CreateProjectList 設定アダプター（本番環境用簡素版）
PathRegistry連携の基本機能のみ
"""

import logging
from pathlib import Path

def adapt_create_project_list_config():
    """
    CreateProjectList用の設定アダプテーション処理
    基本的なPathRegistry連携のみ
    """
    logger = logging.getLogger(__name__)
    
    try:
        # PathRegistryの初期化・連携
        registry = _initialize_path_registry()
        if not registry:
            logger.warning("PathRegistryとの連携を確立できませんでした")
            return False
        
        # 基本的なパス同期
        _sync_basic_paths(registry)
        
        logger.info("CreateProjectList設定アダプテーションが完了しました")
        return True
        
    except Exception as e:
        logger.error(f"設定アダプテーション処理でエラーが発生: {e}")
        return False

def _initialize_path_registry():
    """PathRegistryの初期化と取得"""
    logger = logging.getLogger(__name__)
    
    try:
        from PathRegistry import PathRegistry
        registry = PathRegistry.get_instance()
        logger.info("PathRegistryとの連携を確立しました")
        return registry
    except ImportError:
        logger.warning("PathRegistryモジュールが見つかりません")
        return None
    except Exception as e:
        logger.error(f"PathRegistry初期化エラー: {e}")
        return None

def _sync_basic_paths(registry):
    """基本パスの同期"""
    logger = logging.getLogger(__name__)
    
    try:
        from CreateProjectList.path_constants import PathKeys, get_default_path
        
        # 基本パス同期
        basic_paths = {
            PathKeys.PM_DB_PATH: "ProjectManagerデータベースパス",
            PathKeys.PM_TEMPLATES_DIR: "テンプレートディレクトリ",
            PathKeys.OUTPUT_BASE_DIR: "出力ベースディレクトリ",
        }
        
        for path_key, description in basic_paths.items():
            try:
                # PathRegistryから取得
                registry_path = registry.get_path(path_key)
                
                # 存在しない場合はデフォルトを登録
                if not registry_path:
                    default_path = get_default_path(path_key)
                    if default_path:
                        registry.register_path(path_key, default_path)
                        logger.debug(f"デフォルトパス登録: {path_key} = {default_path}")
                        
            except Exception as e:
                logger.warning(f"パス同期失敗 {path_key}: {e}")
        
        logger.info("基本パス同期が完了しました")
        
    except Exception as e:
        logger.error(f"基本パス同期エラー: {e}")

# === 公開API ===

def initialize_adapters():
    """アダプター初期化（メイン処理）"""
    return adapt_create_project_list_config()