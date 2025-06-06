"""
コア機能統合管理（本番環境用簡素版）
設定・DB・パス管理のシンプル統合
"""
import logging
import sqlite3
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

class CoreManager:
    """コア機能統合管理クラス（シングルトン）"""
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CoreManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 設定データ
        self.config: Dict[str, Any] = {}
        self.config_file: Optional[Path] = None
        
        # 初期化
        self._initialize_config()
        self._setup_logging()
        
        self.logger.info("CoreManager initialized")
    
    @classmethod
    def get_instance(cls):
        """シングルトンインスタンス取得"""
        return cls()
    
    def _initialize_config(self):
        """設定初期化"""
        try:
            from CreateProjectList.path_constants import get_config_path
            
            # 設定ファイルパス
            self.config_file = get_config_path()
            
            # デフォルト設定
            self.config = self._get_default_config()
            
            # 設定ファイル読み込み
            self._load_config()
            
        except Exception as e:
            self.logger.error(f"設定初期化エラー: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定取得"""
        from CreateProjectList.path_constants import get_default_path, PathKeys
        
        return {
            'db_path': get_default_path(PathKeys.PM_DB_PATH),
            'last_input_folder': get_default_path(PathKeys.PM_TEMPLATES_DIR),
            'last_output_folder': get_default_path(PathKeys.OUTPUT_BASE_DIR),
            'replacement_rules': [
                {"search": "#案件名#", "replace": "project_name"},
                {"search": "#作成日#", "replace": "start_date"},
                {"search": "#工場#", "replace": "factory"},
                {"search": "#工程#", "replace": "process"},
                {"search": "#ライン#", "replace": "line"},
                {"search": "#作成者#", "replace": "manager"},
                {"search": "#確認者#", "replace": "reviewer"},
                {"search": "#承認者#", "replace": "approver"},
                {"search": "#事業部#", "replace": "division"}
            ],
            'temp_dir': get_default_path(PathKeys.CPL_TEMP_DIR),
            'last_update': datetime.now().isoformat()
        }
    
    def _load_config(self):
        """設定ファイル読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # デフォルト設定とマージ
                default_config = self._get_default_config()
                for key in default_config:
                    if key not in loaded_config:
                        loaded_config[key] = default_config[key]
                
                self.config.update(loaded_config)
                self.logger.info(f"設定を読み込み: {self.config_file}")
            else:
                self._save_config()
                self.logger.info("デフォルト設定で新規作成")
                
        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
    
    def _save_config(self):
        """設定ファイル保存"""
        try:
            # ディレクトリ作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 更新日時設定
            self.config['last_update'] = datetime.now().isoformat()
            
            # 保存
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"設定を保存: {self.config_file}")
            
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
    
    def _setup_logging(self):
        """ログ設定"""
        try:
            from CreateProjectList.path_constants import get_default_path, PathKeys
            
            log_dir = Path(get_default_path(PathKeys.LOGS_DIR))
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / 'document_processor.log'
            
            # ログハンドラーが既に設定されている場合はスキップ
            root_logger = logging.getLogger()
            if any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
                return
            
            # ファイルハンドラー設定
            file_handler = logging.FileHandler(str(log_file), encoding='utf-8', mode='a')
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            ))
            root_logger.addHandler(file_handler)
            
            self.logger.info(f"ログファイル設定: {log_file}")
            
        except Exception as e:
            print(f"ログ設定エラー: {e}")
    
    # === 設定管理メソッド ===
    
    def get_db_path(self) -> str:
        """データベースパス取得"""
        return self.config.get('db_path', '')
    
    def set_db_path(self, path: str):
        """データベースパス設定"""
        self.config['db_path'] = str(Path(path).resolve()) if path else ''
        self._save_config()
    
    def get_input_folder(self) -> str:
        """入力フォルダパス取得"""
        return self.config.get('last_input_folder', '')
    
    def set_input_folder(self, path: str):
        """入力フォルダパス設定"""
        self.config['last_input_folder'] = str(Path(path).resolve()) if path else ''
        self._save_config()
    
    def get_output_folder(self) -> str:
        """出力フォルダパス取得"""
        return self.config.get('last_output_folder', '')
    
    def set_output_folder(self, path: str):
        """出力フォルダパス設定"""
        self.config['last_output_folder'] = str(Path(path).resolve()) if path else ''
        self._save_config()
    
    def get_temp_dir(self) -> str:
        """一時ディレクトリパス取得"""
        temp_dir = self.config.get('temp_dir', '')
        if not temp_dir:
            from CreateProjectList.path_constants import get_default_path, PathKeys
            temp_dir = get_default_path(PathKeys.CPL_TEMP_DIR)
            self.config['temp_dir'] = temp_dir
        
        # ディレクトリ作成
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        return temp_dir
    
    def get_replacement_rules(self) -> List[Dict[str, str]]:
        """置換ルール取得"""
        return self.config.get('replacement_rules', [])
    
    def set_replacement_rules(self, rules: List[Dict[str, str]]):
        """置換ルール設定"""
        self.config['replacement_rules'] = rules
        self._save_config()
    
    # === データベース操作メソッド ===
    
    def test_database_connection(self) -> bool:
        """データベース接続テスト"""
        try:
            db_path = self.get_db_path()
            if not db_path or not Path(db_path).exists():
                return False
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
                
        except Exception as e:
            self.logger.error(f"データベース接続テストエラー: {e}")
            return False
    
    def get_database_connection(self) -> sqlite3.Connection:
        """データベース接続取得"""
        db_path = self.get_db_path()
        if not db_path:
            raise ValueError("データベースパスが設定されていません")
        
        if not Path(db_path).exists():
            raise FileNotFoundError(f"データベースファイルが存在しません: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_project_data(self, project_id: int) -> Optional[Dict[str, Any]]:
        """プロジェクトデータ取得"""
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT project_id, project_name, start_date, factory, process, line, 
                           manager, reviewer, approver, division
                    FROM projects 
                    WHERE project_id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"プロジェクトデータ取得エラー: {e}")
            return None
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """全プロジェクト取得"""
        try:
            with self.get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT project_id, project_name, start_date, factory, process, line,
                           manager, reviewer, approver, division
                    FROM projects 
                    ORDER BY start_date DESC, project_id DESC
                """)
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"プロジェクト一覧取得エラー: {e}")
            return []
    
    def cleanup_temp_files(self):
        """一時ファイルのクリーンアップ"""
        try:
            temp_dir = Path(self.get_temp_dir())
            if temp_dir.exists():
                for item in temp_dir.glob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        import shutil
                        shutil.rmtree(item)
                self.logger.info(f"一時ファイルをクリーンアップ: {temp_dir}")
        except Exception as e:
            self.logger.error(f"一時ファイルクリーンアップエラー: {e}")
    
    def __del__(self):
        """デストラクタ"""
        try:
            self.cleanup_temp_files()
        except:
            pass