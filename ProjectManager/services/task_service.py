"""
タスク処理サービス
KISS原則: シンプルなタスク処理
DRY原則: タスク関連処理の統合
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.unified_config import UnifiedConfig
from core.database import DatabaseManager
from core.constants import AppConstants
from utils.file_utils import FileManager
from utils.validators import Validator
from utils.error_handler import ErrorHandler, FileErrorHandler

class TaskService:
    """タスク処理の統合サービス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
    
    def load_all_tasks(self) -> bool:
        """全プロジェクトのタスク読み込み"""
        try:
            self.logger.info("タスクデータの読み込みを開始")
            
            # 既存タスクのクリア
            self.db_manager.clear_tasks()
            
            # プロジェクト一覧を取得
            projects = self.db_manager.get_all_projects()
            
            all_tasks = []
            processed_count = 0
            error_count = 0
            
            for project in projects:
                try:
                    tasks = self._load_project_tasks(project)
                    all_tasks.extend(tasks)
                    processed_count += 1
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"プロジェクト '{project['project_name']}' のタスク読み込みエラー: {e}")
                    continue
            
            # タスクの一括登録
            if all_tasks:
                self.db_manager.insert_tasks(all_tasks)
                
                # ダッシュボードの更新
                self.db_manager.update_dashboard()
            
            self.logger.info(f"タスク読み込み完了: 処理済み {processed_count}/{len(projects)} プロジェクト, "
                           f"読み込みタスク数 {len(all_tasks)}, エラー {error_count}")
            
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "タスク一括読み込み")
            return False
    
    def _load_project_tasks(self, project: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個別プロジェクトのタスク読み込み"""
        project_name = project['project_name']
        project_path = project.get('project_path')
        
        if not project_path:
            self.logger.warning(f"プロジェクトパスが未設定: {project_name}")
            return []
        
        project_dir = Path(project_path)
        if not project_dir.exists():
            self.logger.warning(f"プロジェクトディレクトリが存在しません: {project_dir}")
            return []
        
        # メタデータディレクトリの検索
        metadata_dir = project_dir / AppConstants.METADATA_FOLDER_NAME
        if not metadata_dir.exists():
            self.logger.debug(f"メタデータディレクトリが存在しません: {metadata_dir}")
            return []
        
        # CSVファイルの処理
        return self._process_csv_files(metadata_dir, project_name)
    
    def _process_csv_files(self, metadata_dir: Path, project_name: str) -> List[Dict[str, Any]]:
        """CSVファイルの処理"""
        tasks = []
        
        try:
            # CSVファイルの検索
            csv_files = list(metadata_dir.glob('*.csv'))
            if not csv_files:
                self.logger.debug(f"CSVファイルが見つかりません: {metadata_dir}")
                return []
            
            for csv_file in csv_files:
                try:
                    file_tasks = self._process_single_csv(csv_file, project_name)
                    tasks.extend(file_tasks)
                    
                except Exception as e:
                    FileErrorHandler.handle_file_error(e, str(csv_file), "CSVファイル処理", False)
                    continue
            
            return tasks
            
        except Exception as e:
            ErrorHandler.handle_error(e, f"CSVファイル処理 ({metadata_dir})", show_dialog=False)
            return []
    
    def _process_single_csv(self, csv_file: Path, project_name: str) -> List[Dict[str, Any]]:
        """単一CSVファイルの処理"""
        try:
            # CSVファイルの読み込み
            data, encoding = FileManager.read_csv_with_encoding(csv_file)
            
            if not data:
                self.logger.debug(f"CSVファイルが空です: {csv_file}")
                return []
            
            # 必須カラムの存在確認
            required_columns = ['task_name', 'task_start_date', 'task_finish_date', 
                              'task_status', 'task_milestone']
            
            first_row = data[0]
            missing_columns = [col for col in required_columns if col not in first_row]
            
            if missing_columns:
                self.logger.warning(f"必須カラムが不足 {csv_file}: {', '.join(missing_columns)}")
                return []
            
            # タスクデータの変換・検証
            valid_tasks = []
            error_count = 0
            
            for row_index, row in enumerate(data):
                try:
                    task = self._convert_row_to_task(row, project_name)
                    if task:
                        valid_tasks.append(task)
                    else:
                        error_count += 1
                        
                except Exception as e:
                    error_count += 1
                    self.logger.warning(f"行 {row_index + 2} 処理エラー ({csv_file}): {e}")
                    continue
            
            self.logger.info(f"CSV処理完了 {csv_file}: 有効タスク {len(valid_tasks)}, エラー {error_count}")
            return valid_tasks
            
        except Exception as e:
            FileErrorHandler.handle_file_error(e, str(csv_file), "CSV読み込み", False)
            return []
    
    def _convert_row_to_task(self, row: Dict[str, Any], project_name: str) -> Optional[Dict[str, Any]]:
        """行データのタスクオブジェクト変換"""
        try:
            # 基本タスクデータの作成
            task = {
                'task_name': str(row.get('task_name', '')).strip(),
                'task_start_date': str(row.get('task_start_date', '')).strip(),
                'task_finish_date': str(row.get('task_finish_date', '')).strip(),
                'task_status': str(row.get('task_status', '')).strip(),
                'task_milestone': str(row.get('task_milestone', '')).strip(),
                'project_name': project_name
            }
            
            # オプショナルフィールドの追加
            task['task_assignee'] = str(row.get('task_assignee', '')).strip()
            
            # 工数の処理
            work_hours = row.get('task_work_hours', 0)
            try:
                task['task_work_hours'] = float(work_hours) if work_hours else 0
            except (ValueError, TypeError):
                task['task_work_hours'] = 0
            
            # データ検証
            is_valid, errors = Validator.validate_task_data(task)
            if not is_valid:
                self.logger.warning(f"タスクデータ検証エラー: {', '.join(errors)}")
                return None
            
            # ステータスの正規化
            task['task_status'] = self._normalize_task_status(task['task_status'])
            
            return task
            
        except Exception as e:
            self.logger.warning(f"タスク変換エラー: {e}")
            return None
    
    def _normalize_task_status(self, status: str) -> str:
        """タスクステータスの正規化"""
        if status in AppConstants.TASK_STATUSES:
            return status
        
        # ステータスの正規化ルール
        status_mapping = {
            '未開始': '未着手',
            '作業中': '進行中',
            '終了': '完了',
            '停止': '中止',
            '中断': '中止'
        }
        
        normalized = status_mapping.get(status, '未着手')
        if normalized != status:
            self.logger.debug(f"ステータスを正規化: {status} -> {normalized}")
        
        return normalized
    
    def export_tasks_to_csv(self, project_id: Optional[int] = None) -> bool:
        """タスクのCSVエクスポート"""
        try:
            # タスクデータの取得
            if project_id:
                project = self.db_manager.get_project(project_id)
                if not project:
                    ErrorHandler.handle_warning("プロジェクトが見つかりません", "タスクエクスポート")
                    return False
                
                # 特定プロジェクトのタスクを取得（ここではダッシュボードテーブルから取得）
                tasks = self._get_project_tasks(project['project_name'])
                export_filename = f"tasks_{project['project_name']}.csv"
            else:
                # 全タスクを取得
                tasks = self._get_all_tasks()
                export_filename = "all_tasks.csv"
            
            if not tasks:
                ErrorHandler.handle_info("エクスポートするタスクがありません", "タスクエクスポート")
                return False
            
            # CSVファイルに出力
            export_dir = Path(self.config.get_path('EXPORTS_DIR'))
            export_path = export_dir / export_filename
            
            FileManager.write_csv(export_path, tasks)
            
            ErrorHandler.handle_info(f"タスクをエクスポートしました: {export_path}", 
                                   "タスクエクスポート", show_dialog=True)
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "タスクエクスポート")
            return False
    
    def _get_project_tasks(self, project_name: str) -> List[Dict[str, Any]]:
        """特定プロジェクトのタスク取得"""
        try:
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT task_id, task_name, task_start_date, task_finish_date,
                           task_status, task_milestone, task_assignee, task_work_hours,
                           project_name
                    FROM tasks
                    WHERE project_name = ?
                    ORDER BY task_start_date
                ''', (project_name,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"プロジェクトタスク取得エラー: {e}")
            return []
    
    def _get_all_tasks(self) -> List[Dict[str, Any]]:
        """全タスクの取得"""
        try:
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT task_id, task_name, task_start_date, task_finish_date,
                           task_status, task_milestone, task_assignee, task_work_hours,
                           project_name
                    FROM tasks
                    ORDER BY project_name, task_start_date
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"全タスク取得エラー: {e}")
            return []
    
    def get_task_statistics(self, project_name: Optional[str] = None) -> Dict[str, Any]:
        """タスク統計情報の取得"""
        try:
            if project_name:
                tasks = self._get_project_tasks(project_name)
            else:
                tasks = self._get_all_tasks()
            
            stats = {
                'total': len(tasks),
                'by_status': {},
                'by_milestone': {},
                'total_work_hours': 0
            }
            
            # 統計の計算
            for task in tasks:
                # ステータス別
                status = task.get('task_status', '不明')
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # マイルストーン別
                milestone = task.get('task_milestone', '未設定')
                stats['by_milestone'][milestone] = stats['by_milestone'].get(milestone, 0) + 1
                
                # 工数合計
                work_hours = task.get('task_work_hours', 0)
                if isinstance(work_hours, (int, float)):
                    stats['total_work_hours'] += work_hours
            
            return stats
            
        except Exception as e:
            ErrorHandler.handle_error(e, "タスク統計取得", show_dialog=False)
            return {'total': 0, 'by_status': {}, 'by_milestone': {}, 'total_work_hours': 0}