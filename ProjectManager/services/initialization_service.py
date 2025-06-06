"""
初期化サービス - 初期データの検出・コピー処理
KISS原則: シンプルな初期データ処理
DRY原則: 初期化ロジックの統合
YAGNI原則: 現在必要な初期化機能のみ
"""

import json
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from core.unified_config import UnifiedConfig
from core.constants import InitializationConstants
from utils.file_utils import FileManager
from utils.path_utils import PathManager
from utils.error_handler import ErrorHandler

class InitializationService:
    """初期データ処理の統合サービス"""
    
    def __init__(self):
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
        self.initialization_state_file = Path(self.config.get_path('DATA_DIR')) / InitializationConstants.INIT_STATE_FILE
    
    def initialize_application_data(self) -> bool:
        """アプリケーションデータの初期化"""
        try:
            self.logger.info("アプリケーションデータの初期化を開始")
            
            # 初期化状態の確認
            init_state = self._load_initialization_state()
            
            # 既に初期化済みかつ成功している場合はスキップ
            if self._is_initialization_complete(init_state):
                self.logger.info(f"初期化は既に完了しています（{init_state.get('completion_time')}）")
                return True
            
            # 初期化試行回数のチェック
            if self._has_exceeded_max_attempts(init_state):
                self.logger.warning("初期化試行回数が上限に達しました。初期化をスキップします")
                return True
            
            # 初期化試行回数をカウント
            attempt_count = init_state.get('attempt_count', 0) + 1
            self._update_initialization_state({
                'attempt_count': attempt_count,
                'last_attempt_time': datetime.now().isoformat(),
                'status': 'in_progress'
            })
            
            # 初期データの検出とコピー
            initial_data_path = self._find_initial_data()
            if initial_data_path:
                success = self._copy_initial_data(initial_data_path)
                if success:
                    self._mark_initialization_complete(initial_data_path)
                    self.logger.info("初期データのコピーが完了しました")
                    return True
                else:
                    self._update_initialization_state({'status': 'failed'})
                    return False
            else:
                self.logger.info("初期データが見つかりませんでした。デフォルト設定で継続します")
                self._mark_initialization_complete(None, is_default=True)
                return True
            
        except Exception as e:
            self._update_initialization_state({'status': 'error', 'error_message': str(e)})
            ErrorHandler.handle_error(e, "アプリケーションデータ初期化", show_dialog=False)
            return False
    
    def _load_initialization_state(self) -> Dict[str, Any]:
        """初期化状態の読み込み"""
        try:
            if self.initialization_state_file.exists():
                with open(self.initialization_state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"初期化状態ファイル読み込みエラー: {e}")
            return {}
    
    def _update_initialization_state(self, updates: Dict[str, Any]):
        """初期化状態の更新"""
        try:
            current_state = self._load_initialization_state()
            current_state.update(updates)
            
            FileManager.ensure_directory(self.initialization_state_file.parent)
            with open(self.initialization_state_file, 'w', encoding='utf-8') as f:
                json.dump(current_state, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"初期化状態ファイル更新エラー: {e}")
    
    def _is_initialization_complete(self, init_state: Dict[str, Any]) -> bool:
        """初期化完了判定"""
        # 従来のフラグファイルチェック
        initialization_flag = Path(self.config.get_path('DATA_DIR')) / InitializationConstants.INIT_FLAG_FILE
        if initialization_flag.exists():
            return True
        
        # 新しい状態管理での完了チェック
        return init_state.get('status') == 'completed' and init_state.get('completion_time')
    
    def _has_exceeded_max_attempts(self, init_state: Dict[str, Any]) -> bool:
        """最大試行回数超過判定"""
        attempt_count = init_state.get('attempt_count', 0)
        return attempt_count >= InitializationConstants.MAX_INITIALIZATION_ATTEMPTS
    
    def _mark_initialization_complete(self, source_path: Optional[Path], is_default: bool = False):
        """初期化完了のマーク"""
        try:
            completion_time = datetime.now().isoformat()
            
            # 新しい状態管理ファイルの更新
            completion_state = {
                'status': 'completed',
                'completion_time': completion_time,
                'source_path': str(source_path) if source_path else None,
                'is_default_initialization': is_default
            }
            self._update_initialization_state(completion_state)
            
            # 従来のフラグファイルも作成（後方互換性）
            initialization_flag = Path(self.config.get_path('DATA_DIR')) / InitializationConstants.INIT_FLAG_FILE
            FileManager.ensure_directory(initialization_flag.parent)
            
            with open(initialization_flag, 'w', encoding='utf-8') as f:
                f.write(f"初期化完了: {completion_time}\n")
                if source_path:
                    f.write(f"初期データソース: {source_path}\n")
                if is_default:
                    f.write("デフォルト初期化\n")
            
            self.logger.debug(f"初期化完了フラグを作成: {initialization_flag}")
            
        except Exception as e:
            self.logger.error(f"初期化完了マークエラー: {e}")
    
    def _find_initial_data(self) -> Optional[Path]:
        """初期データフォルダの検索（深層探索対応）"""
        try:
            search_paths = PathManager.get_standard_search_paths()
            
            # 深層探索で初期データディレクトリを検索
            found_paths = PathManager.find_directories_by_name(
                search_paths, 
                InitializationConstants.INITIAL_DATA_FOLDER_NAME,
                max_depth=InitializationConstants.MAX_SEARCH_DEPTH
            )
            
            if found_paths:
                # 最初に見つかったパスを返す
                selected_path = found_paths[0]
                self.logger.info(f"初期データフォルダを発見: {selected_path}")
                
                # 複数見つかった場合は警告
                if len(found_paths) > 1:
                    self.logger.warning(f"複数の初期データフォルダが見つかりました。最初のものを使用: {selected_path}")
                    for i, path in enumerate(found_paths[1:], 2):
                        self.logger.warning(f"  {i}番目: {path}")
                
                return selected_path
            
            self.logger.info("初期データフォルダが見つかりませんでした")
            return None
            
        except Exception as e:
            ErrorHandler.handle_error(e, "初期データ検索", show_dialog=False)
            return None
    
    def _copy_initial_data(self, source_path: Path) -> bool:
        """初期データのコピー"""
        try:
            destination_path = Path(self.config.get_path('DATA_DIR'))
            
            # コピー先ディレクトリの作成
            FileManager.ensure_directory(destination_path)
            
            # コピー元の内容確認
            source_items = list(source_path.iterdir())
            if not source_items:
                self.logger.warning(f"初期データフォルダが空です: {source_path}")
                return True
            
            self.logger.info(f"初期データをコピー中: {source_path} -> {destination_path}")
            
            # ディレクトリの再帰的コピー
            copied_count, error_count = FileManager.copy_directory_recursive(
                source_path, destination_path, preserve_structure=True
            )
            
            self.logger.info(f"初期データコピー完了: 成功 {copied_count}, エラー {error_count}")
            
            # ある程度成功していれば継続
            return copied_count > 0
            
        except Exception as e:
            ErrorHandler.handle_error(e, "初期データコピー", show_dialog=False)
            return False
    
    def reset_initialization(self) -> bool:
        """初期化状態のリセット（開発・テスト用）"""
        try:
            # 状態管理ファイルの削除
            if self.initialization_state_file.exists():
                self.initialization_state_file.unlink()
                self.logger.info("初期化状態ファイルをリセットしました")
            
            # 従来のフラグファイルの削除
            initialization_flag = Path(self.config.get_path('DATA_DIR')) / InitializationConstants.INIT_FLAG_FILE
            if initialization_flag.exists():
                initialization_flag.unlink()
                self.logger.info("初期化フラグをリセットしました")
            
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "初期化リセット", show_dialog=False)
            return False
    
    def get_initialization_status(self) -> dict:
        """初期化状態の取得"""
        try:
            init_state = self._load_initialization_state()
            initialization_flag = Path(self.config.get_path('DATA_DIR')) / InitializationConstants.INIT_FLAG_FILE
            
            status = {
                'is_initialized': self._is_initialization_complete(init_state),
                'initialization_time': init_state.get('completion_time'),
                'source_path': init_state.get('source_path'),
                'is_default_initialization': init_state.get('is_default_initialization', False),
                'attempt_count': init_state.get('attempt_count', 0),
                'last_attempt_time': init_state.get('last_attempt_time'),
                'status': init_state.get('status', 'not_started'),
                'data_directory_exists': Path(self.config.get_path('DATA_DIR')).exists(),
                'legacy_flag_exists': initialization_flag.exists(),
                'max_attempts_exceeded': self._has_exceeded_max_attempts(init_state)
            }
            
            # 初期データの現在の利用可能性
            current_initial_data = PathManager.find_initial_data_directory()
            status['initial_data_currently_available'] = current_initial_data is not None
            if current_initial_data:
                status['current_initial_data_path'] = str(current_initial_data)
            
            return status
            
        except Exception as e:
            self.logger.error(f"初期化状態取得エラー: {e}")
            return {
                'is_initialized': False,
                'status': 'error',
                'error_message': str(e)
            }
    
    def force_reinitialization(self) -> bool:
        """強制再初期化（管理者用）"""
        try:
            self.logger.warning("強制再初期化を実行します")
            
            # 初期化状態のリセット
            if not self.reset_initialization():
                return False
            
            # 再初期化の実行
            return self.initialize_application_data()
            
        except Exception as e:
            ErrorHandler.handle_error(e, "強制再初期化", show_dialog=False)
            return False