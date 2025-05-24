"""タスクデータの読み込みと処理を行うモジュール"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.file_utils import FileUtils
from ProjectManager.src.core.task_validator import TaskValidator
from ProjectManager.src.core.error_handler import FileError, ValidationError


class TaskLoader:
    """タスクデータ読み込みサービス"""
    
    def __init__(self, db_manager):
        """
        タスクローダーの初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        self.path_manager = PathManager()
        self.file_utils = FileUtils()
        self.task_validator = TaskValidator()
        
    def load_tasks(self) -> Tuple[int, int, int]:
        """
        全プロジェクトのタスクデータを読み込んでデータベースに登録
        
        Returns:
            Tuple[int, int, int]: (処理したプロジェクト数, 登録したタスク数, エラー数)
        """
        try:
            self.logger.info("タスクデータの読み込みを開始します")
            
            # 1. タスクテーブルのクリア
            self.db_manager.clear_tasks()
            self.logger.info("既存のタスクデータをクリアしました")
            
            all_tasks = []
            projects_count = 0
            errors_count = 0
            
            # 2. プロジェクト一覧を取得
            projects = self.db_manager.get_all_projects()
            projects_count = len(projects)
            self.logger.info(f"{projects_count}件のプロジェクトを取得しました")
            
            # 3. 各プロジェクトのタスクを処理
            for project in projects:
                try:
                    # project_pathが設定されている場合はそのパスを使用
                    if project.get('project_path'):
                        project_dir = Path(project['project_path'])
                    else:
                        # 後方互換性のため、従来のパスも確認
                        output_base_dir = self.path_manager.get_path("OUTPUT_BASE_DIR")
                        project_dir = output_base_dir / project['project_name']
                    
                    if not project_dir.exists():
                        self.logger.warning(f"プロジェクトディレクトリが存在しません: {project_dir}")
                        continue
                        
                    metadata_dir = self.path_manager.get_project_metadata_path(project_dir)
                    if not metadata_dir.exists():
                        self.logger.warning(f"メタデータディレクトリが存在しません: {metadata_dir}")
                        continue
                    
                    # CSVファイルの処理
                    project_tasks, project_errors = self._process_project_csv_files(
                        metadata_dir, project['project_name']
                    )
                    all_tasks.extend(project_tasks)
                    errors_count += project_errors
                    
                except Exception as e:
                    errors_count += 1
                    self.logger.error(f"プロジェクト '{project['project_name']}' の処理中にエラーが発生: {e}")
                    continue
            
            # 4. タスクデータの一括登録
            tasks_count = 0
            if all_tasks:
                tasks_count = self.db_manager.insert_tasks(all_tasks)
                self.logger.info(f"合計 {tasks_count} 件のタスクを読み込みました")
                
                # 5. ダッシュボードの更新
                self.db_manager.update_dashboard()
                self.logger.info("ダッシュボードテーブルを更新しました")
            else:
                self.logger.warning("読み込み可能なタスクデータが見つかりませんでした")
                
            return projects_count, tasks_count, errors_count
                
        except Exception as e:
            self.logger.error(f"タスクデータ読み込みエラー: {e}")
            raise
            
    def _process_project_csv_files(
        self, metadata_dir: Path, project_name: str
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        プロジェクトのCSVファイルを処理
        
        Args:
            metadata_dir: メタデータディレクトリのパス
            project_name: プロジェクト名
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: (処理したタスクデータのリスト, エラー数)
        """
        valid_tasks = []
        error_count = 0
        
        try:
            # CSVファイルの検索と処理
            csv_files = self.file_utils.find_files(metadata_dir, "*.csv")
            if not csv_files:
                self.logger.warning(f"CSVファイルが見つかりません: {metadata_dir}")
                return [], 0

            for csv_file in csv_files:
                try:
                    # CSVファイルの読み込み
                    df = self.file_utils.read_csv(
                        csv_file,
                        dtype=str,
                        na_filter=True
                    )
                    
                    # 必要なカラムの存在確認
                    required_columns = [
                        'task_name', 'task_start_date', 'task_finish_date', 
                        'task_status', 'task_milestone'
                    ]
                    
                    # オプショナルなカラム
                    optional_columns = [
                        'task_assignee', 'task_work_hours'
                    ]
                    
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    if missing_columns:
                        self.logger.error(
                            f"必要なカラムが不足しています: {csv_file}, "
                            f"不足カラム: {', '.join(missing_columns)}"
                        )
                        error_count += 1
                        continue
                    
                    # データフレームを辞書のリストに変換
                    task_dicts = df.to_dict('records')
                    
                    # プロジェクト名の追加
                    for task in task_dicts:
                        task['project_name'] = project_name
                    
                    # タスクデータの検証と正規化
                    normalized_tasks, invalid_tasks = self.task_validator.validate_and_normalize_tasks(task_dicts)
                    
                    # 有効なタスクを追加
                    valid_tasks.extend(normalized_tasks)
                    
                    # エラー数を集計
                    error_count += len(invalid_tasks)
                    
                    # 処理結果のサマリーを出力
                    self.logger.info(
                        f"ファイル {csv_file} の処理完了: "
                        f"総行数 {len(task_dicts)}, "
                        f"有効 {len(normalized_tasks)}, "
                        f"エラー {len(invalid_tasks)}"
                    )
                    
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"CSVファイル処理エラー {csv_file}: {e}")
                    continue
                    
            return valid_tasks, error_count
            
        except Exception as e:
            self.logger.error(f"メタデータディレクトリ処理エラー {metadata_dir}: {e}")
            return [], 1