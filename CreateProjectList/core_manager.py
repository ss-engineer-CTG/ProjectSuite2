"""
コア機能統合管理
設定・DB・ログ・パス管理を統合
"""
import logging
import sqlite3
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import shutil

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
        
        # データベース関連
        self.db_path: Optional[str] = None
        self._db_lock = threading.Lock()
        
        # PathRegistry参照
        self.registry = None
        
        # 初期化
        self._initialize_path_registry()
        self._initialize_config()
        self._setup_logging()
        
        self.logger.info("CoreManager initialized")
    
    @classmethod
    def get_instance(cls):
        """シングルトンインスタンス取得"""
        return cls()
    
    def _initialize_path_registry(self):
        """PathRegistry初期化"""
        try:
            from CreateProjectList.path_constants import PathKeys
            
            # PathRegistryのインポート試行
            try:
                from PathRegistry import PathRegistry
                self.registry = PathRegistry.get_instance()
                self.logger.info("PathRegistry連携を初期化しました")
            except ImportError:
                self.logger.warning("PathRegistryが利用できません")
                
        except Exception as e:
            self.logger.error(f"PathRegistry初期化エラー: {e}")
    
    def _initialize_config(self):
        """設定初期化"""
        try:
            # 設定ファイルパスの決定
            self.config_file = self._get_config_file_path()
            
            # デフォルト設定
            self.config = self._get_default_config()
            
            # 設定ファイル読み込み
            self._load_config()
            
            # パス情報の同期
            self._sync_with_registry()
            
        except Exception as e:
            self.logger.error(f"設定初期化エラー: {e}")
            self.config = self._get_default_config()
    
    def _get_config_file_path(self) -> Path:
        """設定ファイルパス取得"""
        # PathRegistryから取得を試行
        if self.registry:
            try:
                from CreateProjectList.path_constants import PathKeys
                config_path = self.registry.get_path(PathKeys.CPL_CONFIG_PATH)
                if config_path:
                    return Path(config_path)
            except Exception:
                pass
        
        # デフォルトパス
        user_docs = Path.home() / "Documents" / "ProjectSuite"
        config_dir = user_docs / "CreateProjectList" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        return config_dir / "config.json"
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定取得"""
        return {
            'db_path': '',
            'last_input_folder': '',
            'last_output_folder': '',
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
            'temp_dir': str(Path(tempfile.gettempdir()) / "CreateProjectList"),
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
            # バックアップ作成
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix('.bak')
                shutil.copy2(self.config_file, backup_path)
            
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
    
    def _sync_with_registry(self):
        """PathRegistryとの同期"""
        if not self.registry:
            return
            
        try:
            from CreateProjectList.path_constants import PathKeys
            
            # データベースパス
            db_path = self.registry.get_path(PathKeys.PM_DB_PATH)
            if db_path and not self.config.get('db_path'):
                self.config['db_path'] = db_path
                self.logger.info(f"PathRegistryからDBパスを同期: {db_path}")
            
            # 入力フォルダ
            input_folder = self.registry.get_path(PathKeys.PM_TEMPLATES_DIR)
            if input_folder and not self.config.get('last_input_folder'):
                self.config['last_input_folder'] = input_folder
                self.logger.info(f"PathRegistryから入力フォルダを同期: {input_folder}")
            
            # 出力フォルダ
            output_folder = self.registry.get_path(PathKeys.OUTPUT_BASE_DIR)
            if output_folder and not self.config.get('last_output_folder'):
                self.config['last_output_folder'] = output_folder
                self.logger.info(f"PathRegistryから出力フォルダを同期: {output_folder}")
            
            # 一時ディレクトリ
            temp_dir = self.registry.get_path(PathKeys.CPL_TEMP_DIR)
            if temp_dir:
                self.config['temp_dir'] = temp_dir
                
        except Exception as e:
            self.logger.error(f"PathRegistry同期エラー: {e}")
    
    def _setup_logging(self):
        """ログ設定"""
        try:
            # ログディレクトリ
            if self.registry:
                try:
                    from CreateProjectList.path_constants import PathKeys
                    logs_dir = self.registry.get_path(PathKeys.LOGS_DIR)
                    if logs_dir:
                        log_dir = Path(logs_dir)
                    else:
                        log_dir = Path.home() / "Documents" / "ProjectSuite" / "logs"
                except Exception:
                    log_dir = Path.home() / "Documents" / "ProjectSuite" / "logs"
            else:
                log_dir = Path.home() / "Documents" / "ProjectSuite" / "logs"
            
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
        self.db_path = self.config['db_path']
        self._save_config()
        
        # PathRegistryにも登録
        if self.registry and path:
            try:
                from CreateProjectList.path_constants import PathKeys
                self.registry.register_path(PathKeys.PM_DB_PATH, self.config['db_path'])
            except Exception as e:
                self.logger.error(f"PathRegistry登録エラー: {e}")
    
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
            temp_dir = str(Path(tempfile.gettempdir()) / "CreateProjectList")
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
    
    # === ユーティリティメソッド ===
    
    def normalize_path(self, path: str) -> str:
        """パス正規化"""
        try:
            return str(Path(path).resolve()) if path else ""
        except Exception:
            return path
    
    def is_valid_path(self, path: str) -> bool:
        """パス妥当性確認"""
        try:
            Path(path).resolve()
            return True
        except Exception:
            return False
    
    def ensure_directory(self, path: str) -> bool:
        """ディレクトリ存在確認・作成"""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.logger.error(f"ディレクトリ作成エラー {path}: {e}")
            return False
    
    def cleanup_temp_files(self):
        """一時ファイルのクリーンアップ"""
        try:
            temp_dir = Path(self.get_temp_dir())
            if temp_dir.exists():
                for item in temp_dir.glob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                self.logger.info(f"一時ファイルをクリーンアップ: {temp_dir}")
        except Exception as e:
            self.logger.error(f"一時ファイルクリーンアップエラー: {e}")
    
    def get_config_info(self) -> Dict[str, Any]:
        """設定情報取得（デバッグ用）"""
        return {
            'config_file': str(self.config_file),
            'db_path': self.get_db_path(),
            'input_folder': self.get_input_folder(),
            'output_folder': self.get_output_folder(),
            'temp_dir': self.get_temp_dir(),
            'rules_count': len(self.get_replacement_rules()),
            'last_update': self.config.get('last_update', 'Unknown')
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """設定の妥当性検証"""
        validation = {}
        
        try:
            # データベースパス検証
            db_path = self.get_db_path()
            validation['db_path_exists'] = bool(db_path and Path(db_path).exists())
            validation['db_connection'] = self.test_database_connection()
            
            # フォルダパス検証
            input_folder = self.get_input_folder()
            validation['input_folder_exists'] = bool(input_folder and Path(input_folder).exists())
            
            output_folder = self.get_output_folder()
            validation['output_folder_valid'] = bool(output_folder and self.is_valid_path(output_folder))
            
            # 置換ルール検証
            rules = self.get_replacement_rules()
            validation['rules_valid'] = all(
                isinstance(rule, dict) and 'search' in rule and 'replace' in rule
                for rule in rules
            )
            validation['rules_count'] = len(rules)
            
            # 一時ディレクトリ検証
            temp_dir = self.get_temp_dir()
            validation['temp_dir_writable'] = self.ensure_directory(temp_dir)
            
        except Exception as e:
            self.logger.error(f"設定検証エラー: {e}")
            validation['validation_error'] = str(e)
        
        return validation
    
    def reset_to_defaults(self):
        """設定をデフォルトにリセット"""
        try:
            # バックアップ作成
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix(f'.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                shutil.copy2(self.config_file, backup_path)
                self.logger.info(f"設定バックアップ作成: {backup_path}")
            
            # デフォルト設定に戻す
            self.config = self._get_default_config()
            
            # PathRegistryとの再同期
            self._sync_with_registry()
            
            # 保存
            self._save_config()
            
            self.logger.info("設定をデフォルトにリセットしました")
            
        except Exception as e:
            self.logger.error(f"設定リセットエラー: {e}")
            raise
    
    def export_config(self, export_path: str) -> bool:
        """設定のエクスポート"""
        try:
            export_file = Path(export_path)
            
            # エクスポートデータ準備
            export_data = {
                'config': self.config.copy(),
                'export_date': datetime.now().isoformat(),
                'version': '2.0.0'
            }
            
            # パスの相対化（ポータブル性向上）
            if export_data['config'].get('db_path'):
                export_data['config']['db_path'] = '<USER_DATA>/ProjectManager/data/projects.db'
            if export_data['config'].get('last_input_folder'):
                export_data['config']['last_input_folder'] = '<TEMPLATES_DIR>'
            if export_data['config'].get('last_output_folder'):
                export_data['config']['last_output_folder'] = '<OUTPUT_DIR>'
            
            # エクスポート実行
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"設定をエクスポート: {export_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定エクスポートエラー: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """設定のインポート"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                raise FileNotFoundError(f"インポートファイルが存在しません: {import_file}")
            
            # インポートデータ読み込み
            with open(import_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'config' not in import_data:
                raise ValueError("無効なインポートファイル形式です")
            
            # 現在の設定をバックアップ
            backup_path = self.config_file.with_suffix(f'.bak_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
            shutil.copy2(self.config_file, backup_path)
            
            # 設定の適用
            imported_config = import_data['config']
            
            # パスの復元
            if self.registry:
                try:
                    from CreateProjectList.path_constants import PathKeys
                    
                    if imported_config.get('db_path') == '<USER_DATA>/ProjectManager/data/projects.db':
                        db_path = self.registry.get_path(PathKeys.PM_DB_PATH)
                        if db_path:
                            imported_config['db_path'] = db_path
                    
                    if imported_config.get('last_input_folder') == '<TEMPLATES_DIR>':
                        templates_dir = self.registry.get_path(PathKeys.PM_TEMPLATES_DIR)
                        if templates_dir:
                            imported_config['last_input_folder'] = templates_dir
                    
                    if imported_config.get('last_output_folder') == '<OUTPUT_DIR>':
                        output_dir = self.registry.get_path(PathKeys.OUTPUT_BASE_DIR)
                        if output_dir:
                            imported_config['last_output_folder'] = output_dir
                            
                except Exception as e:
                    self.logger.warning(f"パス復元エラー: {e}")
            
            # デフォルト設定とマージ
            default_config = self._get_default_config()
            for key in default_config:
                if key not in imported_config:
                    imported_config[key] = default_config[key]
            
            self.config = imported_config
            self._save_config()
            
            self.logger.info(f"設定をインポート: {import_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"設定インポートエラー: {e}")
            return False
    
    def __del__(self):
        """デストラクタ"""
        try:
            self.cleanup_temp_files()
        except:
            pass