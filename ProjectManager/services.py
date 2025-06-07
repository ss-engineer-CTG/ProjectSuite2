"""
統合ビジネスロジック
"""

import csv
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from models import Project, Task
from database import DatabaseManager
from config import Config
from utils import ErrorHandler, FileUtils, PathUtils, Validator

class ProjectService:
    """プロジェクト操作サービス"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db_manager = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def create_project(self, project_data: Dict[str, Any]) -> Optional[int]:
        """プロジェクトの作成"""
        try:
            # データ検証
            is_valid, errors = Validator.validate_project_data(project_data)
            if not is_valid:
                ErrorHandler.show_warning("\n".join(errors))
                return None
            
            # データベースにプロジェクトを作成
            project_id = self.db_manager.create_project(project_data)
            
            # プロジェクトフォルダを作成
            project_folder = self._create_project_folder(project_data)
            if project_folder:
                self.db_manager.update_project_path(project_id, str(project_folder))
            
            self.logger.info(f"プロジェクトを作成: {project_data['project_name']}")
            return project_id
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト作成")
            return None
    
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """プロジェクトの更新"""
        try:
            is_valid, errors = Validator.validate_project_data(project_data)
            if not is_valid:
                ErrorHandler.show_warning("\n".join(errors))
                return False
            
            self.db_manager.update_project(project_id, project_data)
            self.logger.info(f"プロジェクトを更新: ID {project_id}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト更新")
            return False
    
    def delete_project(self, project_id: int) -> bool:
        """プロジェクトの削除"""
        try:
            project = self.db_manager.get_project(project_id)
            if not project:
                ErrorHandler.show_warning("プロジェクトが見つかりません")
                return False
            
            if not ErrorHandler.confirm_dialog(
                f"プロジェクト '{project['project_name']}' を削除してもよろしいですか？"
            ):
                return False
            
            # プロジェクトフォルダの削除
            if project.get('project_path'):
                self._delete_project_folder(Path(project['project_path']))
            
            self.db_manager.delete_project(project_id)
            self.logger.info(f"プロジェクトを削除: {project['project_name']}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト削除")
            return False
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """プロジェクトの取得"""
        return self.db_manager.get_project(project_id)
    
    def get_all_projects(self, status_filter: str = "全て") -> List[Dict[str, Any]]:
        """プロジェクト一覧の取得"""
        return self.db_manager.get_all_projects(status_filter)
    
    def _create_project_folder(self, project_data: Dict[str, Any]) -> Optional[Path]:
        """プロジェクトフォルダの作成"""
        try:
            output_base_dir = Path(self.config.get_path('output_base'))
            folder_name = PathUtils.create_project_folder_name(project_data)
            project_folder = PathUtils.ensure_unique_path(output_base_dir, folder_name)
            
            project_folder.mkdir(parents=True, exist_ok=True)
            self._copy_template_if_exists(project_folder)
            
            return project_folder
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクトフォルダ作成")
            return None
    
    def _copy_template_if_exists(self, project_folder: Path):
        """テンプレート構造のコピー"""
        template_dir = Path(self.config.get_path('templates'))
        if template_dir.exists():
            FileUtils.copy_directory(template_dir, project_folder)
    
    def _delete_project_folder(self, folder_path: Path):
        """プロジェクトフォルダの削除"""
        try:
            if folder_path.exists():
                shutil.rmtree(folder_path)
        except Exception as e:
            self.logger.warning(f"フォルダ削除エラー: {e}")

class TaskService:
    """タスク処理サービス"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db_manager = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def load_all_tasks(self) -> bool:
        """全プロジェクトのタスク読み込み"""
        try:
            self.logger.info("タスクデータの読み込みを開始")
            
            self.db_manager.clear_tasks()
            projects = self.db_manager.get_all_projects()
            
            all_tasks = []
            for project in projects:
                tasks = self._load_project_tasks(project)
                all_tasks.extend(tasks)
            
            if all_tasks:
                self.db_manager.insert_tasks(all_tasks)
            
            self.logger.info(f"タスク読み込み完了: {len(all_tasks)}件")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "タスク読み込み")
            return False
    
    def _load_project_tasks(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個別プロジェクトのタスク読み込み"""
        project_name = project['project_name']
        project_path = project.get('project_path')
        
        if not project_path:
            return []
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            return []
        
        # メタデータディレクトリの検索
        metadata_dir = project_dir / "999. metadata"
        if not metadata_dir.exists():
            return []
        
        return self._process_csv_files(metadata_dir, project_name)
    
    def _process_csv_files(self, metadata_dir: Path, project_name: str) -> List[Dict[str, Any]]:
        """CSVファイルの処理"""
        tasks = []
        
        for csv_file in metadata_dir.glob('*.csv'):
            try:
                file_tasks = self._process_single_csv(csv_file, project_name)
                tasks.extend(file_tasks)
            except Exception as e:
                self.logger.error(f"CSVファイル処理エラー {csv_file}: {e}")
                continue
        
        return tasks
    
    def _process_single_csv(self, csv_file: Path, project_name: str) -> List[Dict[str, Any]]:
        """単一CSVファイルの処理"""
        try:
            data = FileUtils.read_csv_with_encoding(csv_file)
            
            if not data:
                return []
            
            # 必須カラムの確認
            required_columns = ['task_name', 'task_start_date', 'task_finish_date', 
                              'task_status', 'task_milestone']
            
            if not all(col in data[0] for col in required_columns):
                return []
            
            valid_tasks = []
            for row in data:
                task = self._convert_row_to_task(row, project_name)
                if task:
                    valid_tasks.append(task)
            
            return valid_tasks
            
        except Exception as e:
            self.logger.error(f"CSV読み込みエラー {csv_file}: {e}")
            return []
    
    def _convert_row_to_task(self, row: Dict[str, Any], project_name: str) -> Optional[Dict[str, Any]]:
        """行データのタスクオブジェクト変換"""
        try:
            task = {
                'task_name': str(row.get('task_name', '')).strip(),
                'task_start_date': str(row.get('task_start_date', '')).strip(),
                'task_finish_date': str(row.get('task_finish_date', '')).strip(),
                'task_status': self._normalize_status(str(row.get('task_status', '')).strip()),
                'task_milestone': str(row.get('task_milestone', '')).strip(),
                'task_assignee': str(row.get('task_assignee', '')).strip(),
                'project_name': project_name
            }
            
            # 工数の処理
            try:
                task['task_work_hours'] = float(row.get('task_work_hours', 0))
            except (ValueError, TypeError):
                task['task_work_hours'] = 0
            
            # データ検証
            is_valid, _ = Validator.validate_task_data(task)
            return task if is_valid else None
            
        except Exception:
            return None
    
    def _normalize_status(self, status: str) -> str:
        """ステータスの正規化"""
        status_mapping = {
            '未開始': '未着手',
            '作業中': '進行中',
            '終了': '完了',
            '停止': '中止',
            '中断': '中止'
        }
        return status_mapping.get(status, status if status in ['未着手', '進行中', '完了', '中止'] else '未着手')

class ExportService:
    """データエクスポートサービス"""
    
    def __init__(self, db_manager: DatabaseManager, config: Config):
        self.db_manager = db_manager
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def export_dashboard_data(self) -> bool:
        """ダッシュボードデータのエクスポート"""
        try:
            data = self.db_manager.get_dashboard_data()
            if not data:
                return False
            
            processed_data = self._process_export_data(data)
            export_path = Path(self.config.get_path('exports')) / "dashboard.csv"
            
            FileUtils.write_csv(export_path, processed_data)
            self.logger.info(f"ダッシュボードデータをエクスポート: {export_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "ダッシュボードエクスポート")
            return False
    
    def export_projects_data(self) -> bool:
        """プロジェクトデータのエクスポート"""
        try:
            projects = self.db_manager.get_all_projects()
            if not projects:
                return False
            
            processed_data = self._process_export_data(projects)
            export_path = Path(self.config.get_path('exports')) / "projects.csv"
            
            FileUtils.write_csv(export_path, processed_data)
            self.logger.info(f"プロジェクトデータをエクスポート: {export_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクトエクスポート")
            return False
    
    def export_all_data(self) -> bool:
        """全データの一括エクスポート"""
        dashboard_success = self.export_dashboard_data()
        projects_success = self.export_projects_data()
        
        if dashboard_success or projects_success:
            ErrorHandler.show_info("データエクスポートが完了しました")
            return True
        return False
    
    def _process_export_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """エクスポートデータの加工"""
        processed_data = []
        for row in data:
            processed_row = {}
            for key, value in row.items():
                processed_row[key] = "未設定" if value is None or value == "" else str(value)
            processed_data.append(processed_row)
        return processed_data

class InitializationService:
    """初期化サービス"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.init_flag_file = Path(config.get_path('data')) / '.initialized'
    
    def initialize_if_needed(self):
        """必要に応じて初期化を実行"""
        if self.init_flag_file.exists():
            return
        
        try:
            self.logger.info("初期化を開始します")
            
            # 初期データの検索とコピー
            initial_data_path = self._find_initial_data()
            if initial_data_path:
                self._copy_initial_data(initial_data_path)
            
            # 初期化完了のマーク
            self._mark_initialization_complete()
            
        except Exception as e:
            self.logger.error(f"初期化エラー: {e}")
    
    def _find_initial_data(self) -> Optional[Path]:
        """初期データフォルダの検索"""
        search_dirs = [
            Path.home() / "Documents",
            Path.home() / "Desktop", 
            Path.home() / "Downloads"
        ]
        
        for search_dir in search_dirs:
            for item in search_dir.rglob("*initialdata_ProjectManager*"):
                if item.is_dir():
                    self.logger.info(f"初期データフォルダを発見: {item}")
                    return item
        
        return None
    
    def _copy_initial_data(self, source_path: Path):
        """初期データのコピー"""
        try:
            destination_path = Path(self.config.get_path('data'))
            
            # projectsフォルダは特別処理（デスクトップにコピー）
            projects_folder = source_path / "projects"
            if projects_folder.exists():
                desktop_projects = Path.home() / "Desktop" / "projects"
                if not desktop_projects.exists():
                    FileUtils.copy_directory(projects_folder, desktop_projects)
                    self.config.set_path('output_base', str(desktop_projects))
            
            # その他のファイルをdataディレクトリにコピー
            for item in source_path.iterdir():
                if item.name != "projects" and not item.name.startswith('.'):
                    dest_item = destination_path / item.name
                    if item.is_file():
                        shutil.copy2(item, dest_item)
                    elif item.is_dir():
                        FileUtils.copy_directory(item, dest_item)
            
            self.logger.info("初期データのコピーが完了しました")
            
        except Exception as e:
            self.logger.error(f"初期データコピーエラー: {e}")
    
    def _mark_initialization_complete(self):
        """初期化完了のマーク"""
        try:
            self.init_flag_file.parent.mkdir(parents=True, exist_ok=True)
            self.init_flag_file.touch()
            self.logger.info("初期化が完了しました")
        except Exception as e:
            self.logger.error(f"初期化完了マークエラー: {e}")