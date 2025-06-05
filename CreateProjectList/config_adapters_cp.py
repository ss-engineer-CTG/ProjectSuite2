"""
CreateProjectList 設定アダプター
PathRegistry連携と親アプリケーション設定同期
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

def adapt_create_project_list_config():
    """
    CreateProjectList用の設定アダプテーション処理
    PathRegistryとの連携を確立し、親アプリケーションの設定を同期
    """
    logger = logging.getLogger(__name__)
    
    try:
        # PathRegistryの初期化・連携
        registry = _initialize_path_registry()
        if not registry:
            logger.warning("PathRegistryとの連携を確立できませんでした")
            return False
        
        # CreateProjectList固有のパス登録
        _register_cpl_paths(registry)
        
        # ProjectManager設定との同期
        _sync_with_project_manager(registry)
        
        # CoreManagerとの統合
        _integrate_with_core_manager(registry)
        
        logger.info("CreateProjectList設定アダプテーションが完了しました")
        return True
        
    except Exception as e:
        logger.error(f"設定アダプテーション処理でエラーが発生: {e}")
        return False

def _initialize_path_registry():
    """PathRegistryの初期化と取得"""
    logger = logging.getLogger(__name__)
    
    try:
        # PathRegistryのインポート試行
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
            
    except Exception as e:
        logger.error(f"PathRegistry初期化で予期しないエラー: {e}")
        return None

def _register_cpl_paths(registry):
    """CreateProjectList固有パスの登録"""
    logger = logging.getLogger(__name__)
    
    try:
        from .path_constants import PathKeys, DEFAULT_PATHS
        
        # CreateProjectList固有パスをPathRegistryに登録
        cpl_paths = {
            PathKeys.CPL_DIR: DEFAULT_PATHS.get(PathKeys.CPL_DIR),
            PathKeys.CPL_CONFIG_DIR: DEFAULT_PATHS.get(PathKeys.CPL_CONFIG_DIR),
            PathKeys.CPL_CONFIG_PATH: str(Path(DEFAULT_PATHS.get(PathKeys.CPL_CONFIG_DIR, "")) / "config.json"),
            PathKeys.CPL_TEMP_DIR: DEFAULT_PATHS.get(PathKeys.CPL_TEMP_DIR),
            PathKeys.CPL_CACHE_DIR: DEFAULT_PATHS.get(PathKeys.CPL_CACHE_DIR),
        }
        
        registered_count = 0
        for key, default_path in cpl_paths.items():
            if default_path:
                try:
                    # 既存パスがない場合のみデフォルトを登録
                    existing_path = registry.get_path(key)
                    if not existing_path:
                        registry.register_path(key, default_path)
                        registered_count += 1
                        logger.debug(f"パス登録: {key} = {default_path}")
                except Exception as e:
                    logger.warning(f"パス登録失敗 {key}: {e}")
        
        logger.info(f"CreateProjectList固有パスを{registered_count}件登録しました")
        
    except Exception as e:
        logger.error(f"CreateProjectList固有パス登録エラー: {e}")

def _sync_with_project_manager(registry):
    """ProjectManager設定との同期"""
    logger = logging.getLogger(__name__)
    
    try:
        from .path_constants import PathKeys
        
        # ProjectManagerから取得すべき重要パス
        pm_paths = {
            PathKeys.PM_DB_PATH: "ProjectManagerデータベースパス",
            PathKeys.PM_DATA_DIR: "ProjectManagerデータディレクトリ", 
            PathKeys.PM_TEMPLATES_DIR: "ProjectManagerテンプレートディレクトリ",
            PathKeys.OUTPUT_BASE_DIR: "プロジェクト出力ベースディレクトリ",
            PathKeys.LOGS_DIR: "ログディレクトリ",
        }
        
        synced_count = 0
        for path_key, description in pm_paths.items():
            try:
                pm_path = registry.get_path(path_key)
                if pm_path and Path(pm_path).exists():
                    logger.debug(f"ProjectManagerパス取得: {path_key} = {pm_path}")
                    synced_count += 1
                else:
                    logger.debug(f"ProjectManagerパス未設定: {path_key}")
            except Exception as e:
                logger.warning(f"ProjectManagerパス取得失敗 {path_key}: {e}")
        
        logger.info(f"ProjectManager設定と{synced_count}件同期しました")
        
        # 特別処理：データベースパスの検証
        _validate_database_path(registry)
        
    except Exception as e:
        logger.error(f"ProjectManager設定同期エラー: {e}")

def _validate_database_path(registry):
    """データベースパスの検証と自動検出"""
    logger = logging.getLogger(__name__)
    
    try:
        from .path_constants import PathKeys
        
        # 1. PathRegistryから取得試行
        db_path = registry.get_path(PathKeys.PM_DB_PATH)
        
        if db_path and Path(db_path).exists():
            logger.info(f"データベースパス確認済み: {db_path}")
            return
        
        # 2. 標準的な場所での自動検出
        potential_paths = [
            # ユーザードキュメント内
            Path.home() / "Documents" / "ProjectSuite" / "ProjectManager" / "data" / "projects.db",
            Path.home() / "Documents" / "ProjectSuite" / "data" / "projects.db",
            
            # デスクトップ内
            Path.home() / "Desktop" / "ProjectSuite" / "ProjectManager" / "data" / "projects.db",
            Path.home() / "Desktop" / "ProjectManager" / "data" / "projects.db",
            
            # アプリケーションディレクトリ内
            Path(__file__).parent.parent / "ProjectManager" / "data" / "projects.db",
            Path(__file__).parent.parent / "data" / "projects.db",
        ]
        
        for potential_path in potential_paths:
            if potential_path.exists():
                registry.register_path(PathKeys.PM_DB_PATH, str(potential_path))
                logger.info(f"データベースパスを自動検出: {potential_path}")
                return
        
        logger.warning("データベースパスを自動検出できませんでした")
        
    except Exception as e:
        logger.error(f"データベースパス検証エラー: {e}")

def _integrate_with_core_manager(registry):
    """CoreManagerとの統合"""
    logger = logging.getLogger(__name__)
    
    try:
        # CoreManagerインスタンスの取得
        from .core_manager import CoreManager
        core_manager = CoreManager.get_instance()
        
        # PathRegistryから設定を同期
        _sync_paths_to_core_manager(registry, core_manager)
        
        # CoreManagerの設定をPathRegistryに逆同期
        _sync_core_manager_to_registry(core_manager, registry)
        
        logger.info("CoreManagerとPathRegistryの統合が完了しました")
        
    except Exception as e:
        logger.error(f"CoreManager統合エラー: {e}")

def _sync_paths_to_core_manager(registry, core_manager):
    """PathRegistryからCoreManagerへの設定同期"""
    logger = logging.getLogger(__name__)
    
    try:
        from .path_constants import PathKeys
        
        # データベースパス同期
        db_path = registry.get_path(PathKeys.PM_DB_PATH)
        if db_path and not core_manager.get_db_path():
            core_manager.set_db_path(db_path)
            logger.debug(f"データベースパス同期: {db_path}")
        
        # テンプレートディレクトリ同期（入力フォルダのデフォルト）
        templates_dir = registry.get_path(PathKeys.PM_TEMPLATES_DIR)
        if templates_dir and not core_manager.get_input_folder():
            core_manager.set_input_folder(templates_dir)
            logger.debug(f"テンプレートディレクトリ同期: {templates_dir}")
        
        # 出力ベースディレクトリ同期
        output_base = registry.get_path(PathKeys.OUTPUT_BASE_DIR)
        if output_base and not core_manager.get_output_folder():
            core_manager.set_output_folder(output_base)
            logger.debug(f"出力ベースディレクトリ同期: {output_base}")
        
    except Exception as e:
        logger.error(f"PathRegistry→CoreManager同期エラー: {e}")

def _sync_core_manager_to_registry(core_manager, registry):
    """CoreManagerからPathRegistryへの逆同期"""
    logger = logging.getLogger(__name__)
    
    try:
        from .path_constants import PathKeys
        
        # CoreManagerで設定されているパスをPathRegistryに登録
        paths_to_sync = [
            (PathKeys.PM_DB_PATH, core_manager.get_db_path()),
            (PathKeys.CPL_INPUT_FOLDER, core_manager.get_input_folder()),
            (PathKeys.CPL_OUTPUT_FOLDER, core_manager.get_output_folder()),
        ]
        
        synced_count = 0
        for path_key, path_value in paths_to_sync:
            if path_value:
                try:
                    existing_path = registry.get_path(path_key)
                    if not existing_path or existing_path != path_value:
                        registry.register_path(path_key, path_value)
                        synced_count += 1
                        logger.debug(f"CoreManager→PathRegistry同期: {path_key} = {path_value}")
                except Exception as e:
                    logger.warning(f"逆同期失敗 {path_key}: {e}")
        
        if synced_count > 0:
            logger.info(f"CoreManager→PathRegistry逆同期: {synced_count}件")
        
    except Exception as e:
        logger.error(f"CoreManager→PathRegistry逆同期エラー: {e}")

def get_registry_status() -> Dict[str, Any]:
    """PathRegistry連携状態の取得（デバッグ用）"""
    try:
        from .path_constants import PathKeys
        
        registry = _initialize_path_registry()
        if not registry:
            return {"status": "disconnected", "error": "PathRegistry not available"}
        
        # 重要パスの状態確認
        important_paths = [
            PathKeys.PM_DB_PATH,
            PathKeys.PM_TEMPLATES_DIR,
            PathKeys.OUTPUT_BASE_DIR,
            PathKeys.CPL_CONFIG_DIR,
            PathKeys.LOGS_DIR,
        ]
        
        status = {
            "status": "connected",
            "registry_available": True,
            "paths": {}
        }
        
        for path_key in important_paths:
            try:
                path_value = registry.get_path(path_key)
                path_exists = bool(path_value and Path(path_value).exists())
                status["paths"][path_key] = {
                    "value": path_value,
                    "exists": path_exists
                }
            except Exception as e:
                status["paths"][path_key] = {
                    "value": None,
                    "error": str(e)
                }
        
        return status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "registry_available": False
        }

def reset_registry_paths():
    """PathRegistry内のCreateProjectList関連パスをリセット"""
    logger = logging.getLogger(__name__)
    
    try:
        registry = _initialize_path_registry()
        if not registry:
            logger.error("PathRegistryが利用できません")
            return False
        
        from .path_constants import PathKeys
        
        # CreateProjectList関連パスをクリア
        cpl_keys = [
            PathKeys.CPL_DIR,
            PathKeys.CPL_CONFIG_DIR,
            PathKeys.CPL_CONFIG_PATH,
            PathKeys.CPL_TEMP_DIR,
            PathKeys.CPL_CACHE_DIR,
            PathKeys.CPL_INPUT_FOLDER,
            PathKeys.CPL_OUTPUT_FOLDER,
        ]
        
        cleared_count = 0
        for key in cpl_keys:
            try:
                if registry.get_path(key):
                    registry.unregister_path(key)
                    cleared_count += 1
                    logger.debug(f"パスクリア: {key}")
            except Exception as e:
                logger.warning(f"パスクリア失敗 {key}: {e}")
        
        logger.info(f"PathRegistry内CreateProjectListパスを{cleared_count}件クリアしました")
        
        # デフォルトパスを再登録
        _register_cpl_paths(registry)
        
        return True
        
    except Exception as e:
        logger.error(f"PathRegistryパスリセットエラー: {e}")
        return False

def migrate_legacy_config():
    """レガシー設定の移行処理"""
    logger = logging.getLogger(__name__)
    
    try:
        # 旧バージョンの設定ファイル検索
        legacy_config_paths = [
            Path.home() / "Documents" / "CreateProjectList" / "config.json",
            Path.home() / "AppData" / "Local" / "CreateProjectList" / "config.json",
            Path(__file__).parent / "legacy_config.json",
        ]
        
        migrated = False
        for legacy_path in legacy_config_paths:
            if legacy_path.exists():
                try:
                    # CoreManagerに移行
                    from .core_manager import CoreManager
                    core_manager = CoreManager.get_instance()
                    
                    success = core_manager.import_config(str(legacy_path))
                    if success:
                        # バックアップとして残す
                        backup_path = legacy_path.with_suffix('.migrated.bak')
                        legacy_path.rename(backup_path)
                        
                        logger.info(f"レガシー設定を移行: {legacy_path} -> {backup_path}")
                        migrated = True
                        break
                        
                except Exception as e:
                    logger.error(f"レガシー設定移行エラー {legacy_path}: {e}")
        
        if not migrated:
            logger.debug("移行すべきレガシー設定が見つかりませんでした")
        
        return migrated
        
    except Exception as e:
        logger.error(f"レガシー設定移行処理エラー: {e}")
        return False

def cleanup_temp_registry_entries():
    """一時的なPathRegistryエントリのクリーンアップ"""
    logger = logging.getLogger(__name__)
    
    try:
        registry = _initialize_path_registry()
        if not registry:
            return False
        
        # 一時的なエントリパターン
        temp_patterns = [
            "CPL_TEMP_",
            "TEMP_CPL_",
            "_TEMP",
            "_CACHE_TEMP",
        ]
        
        # すべてのパスを取得してクリーンアップ対象を特定
        cleaned_count = 0
        try:
            all_paths = registry.get_all_paths()
            for path_key in all_paths:
                if any(pattern in path_key for pattern in temp_patterns):
                    try:
                        registry.unregister_path(path_key)
                        cleaned_count += 1
                        logger.debug(f"一時エントリクリーンアップ: {path_key}")
                    except Exception as e:
                        logger.warning(f"一時エントリクリーンアップ失敗 {path_key}: {e}")
        except AttributeError:
            # get_all_paths()メソッドが存在しない場合はスキップ
            logger.debug("PathRegistry.get_all_paths()メソッドが利用できません")
        
        if cleaned_count > 0:
            logger.info(f"一時PathRegistryエントリを{cleaned_count}件クリーンアップしました")
        
        return True
        
    except Exception as e:
        logger.error(f"一時PathRegistryエントリクリーンアップエラー: {e}")
        return False

# === 公開API ===

def initialize_adapters():
    """アダプター初期化（メイン処理）"""
    return adapt_create_project_list_config()

def get_adaptation_status():
    """アダプテーション状態取得"""
    return get_registry_status()

def reset_adapters():
    """アダプター設定リセット"""
    return reset_registry_paths()

def cleanup_adapters():
    """アダプター関連クリーンアップ"""
    return cleanup_temp_registry_entries()

# === デバッグ・ユーティリティ ===

def debug_path_resolution():
    """パス解決状況のデバッグ出力"""
    logger = logging.getLogger(__name__)
    
    try:
        from .path_constants import PathKeys, DEFAULT_PATHS
        
        registry = _initialize_path_registry()
        
        logger.info("=== CreateProjectList パス解決デバッグ ===")
        
        # PathRegistry状態
        if registry:
            logger.info("PathRegistry: 利用可能")
            
            important_keys = [
                PathKeys.PM_DB_PATH,
                PathKeys.PM_TEMPLATES_DIR,
                PathKeys.OUTPUT_BASE_DIR,
                PathKeys.CPL_CONFIG_DIR,
            ]
            
            for key in important_keys:
                try:
                    registry_path = registry.get_path(key)
                    default_path = DEFAULT_PATHS.get(key)
                    
                    logger.info(f"  {key}:")
                    logger.info(f"    PathRegistry: {registry_path}")
                    logger.info(f"    Default: {default_path}")
                    
                    if registry_path:
                        exists = Path(registry_path).exists()
                        logger.info(f"    存在確認: {exists}")
                        
                except Exception as e:
                    logger.error(f"    エラー: {e}")
        else:
            logger.warning("PathRegistry: 利用不可")
        
        # CoreManager状態
        try:
            from .core_manager import CoreManager
            core_manager = CoreManager.get_instance()
            
            logger.info("CoreManager:")
            logger.info(f"  DB Path: {core_manager.get_db_path()}")
            logger.info(f"  Input Folder: {core_manager.get_input_folder()}")
            logger.info(f"  Output Folder: {core_manager.get_output_folder()}")
            
        except Exception as e:
            logger.error(f"CoreManager取得エラー: {e}")
        
        logger.info("=== デバッグ出力完了 ===")
        
    except Exception as e:
        logger.error(f"デバッグ出力エラー: {e}")

if __name__ == "__main__":
    # デバッグ実行
    logging.basicConfig(level=logging.DEBUG)
    debug_path_resolution()