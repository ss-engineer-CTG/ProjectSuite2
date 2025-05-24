"""プロジェクト特化のデータベース操作を提供するモジュール"""

import re
import os
import shutil
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from ProjectManager.src.core.database_base import DatabaseBaseManager
from ProjectManager.src.core.error_handler import DatabaseError
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.file_utils import FileUtils

class ProjectDatabaseManager(DatabaseBaseManager):
    """
    プロジェクト特化のデータベース操作を提供するクラス
    データベース接続・操作を統括し、プロジェクトとタスクの管理を行う
    """
    
    def __init__(self, db_path: Path):
        """
        プロジェクトデータベースマネージャーの初期化
        
        Args:
            db_path (Path): データベースファイルのパス
        """
        super().__init__(db_path)
        self.logger = get_logger(__name__)
        self.path_manager = PathManager()
        self.file_utils = FileUtils()
        
        # データベース初期設定
        self.setup_database()
    
    def setup_database(self) -> None:
        """データベースとテーブルの初期設定"""
        try:
            # プロジェクトテーブルのセットアップ
            self._setup_projects_table()
            
            # タスクテーブルのセットアップ
            self._setup_tasks_table()
            
            # ダッシュボードテーブルのセットアップ
            self._setup_dashboard_table()
            
            # タスクテーブルのマイグレーション
            self._migrate_tasks_table()
            
            self.logger.info("データベースの初期設定が完了しました")
            
        except Exception as e:
            error_msg = f"データベース設定エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def _setup_projects_table(self) -> None:
        """プロジェクトテーブルの設定"""
        if not self.table_exists('projects'):
            query = '''
                CREATE TABLE projects (
                    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT NOT NULL UNIQUE,
                    start_date TEXT NOT NULL,
                    manager TEXT NOT NULL,
                    reviewer TEXT NOT NULL,
                    approver TEXT NOT NULL,
                    division TEXT,
                    factory TEXT,
                    process TEXT,
                    line TEXT,
                    status TEXT NOT NULL DEFAULT '進行中' CHECK(status IN ('進行中', '完了', '中止')),
                    project_path TEXT,
                    ganttchart_path TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            '''
            self.execute_update(query)
            self.logger.info("projectsテーブルを作成しました")
        else:
            # project_path列が存在するか確認
            if not self.column_exists('projects', 'project_path'):
                self.add_column('projects', 'project_path', 'TEXT')
            
            # ガントチャートパス列の追加
            if not self.column_exists('projects', 'ganttchart_path'):
                self.add_column('projects', 'ganttchart_path', 'TEXT')
            
            # 既存のマイグレーションも実行
            self._check_and_migrate_projects_table()
    
    def _setup_tasks_table(self) -> None:
        """タスクテーブルの設定"""
        if not self.table_exists('tasks'):
            query = '''
                CREATE TABLE tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    task_start_date TEXT NOT NULL,
                    task_finish_date TEXT NOT NULL,
                    task_status TEXT NOT NULL CHECK(task_status IN ('未着手', '進行中', '完了', '中止')),
                    task_milestone TEXT NOT NULL,
                    task_assignee TEXT,
                    task_work_hours REAL,
                    project_name TEXT NOT NULL,
                    FOREIGN KEY (project_name) REFERENCES projects(project_name)
                        ON UPDATE CASCADE
                        ON DELETE CASCADE
                )
            '''
            self.execute_update(query)
            self.logger.info("tasksテーブルを作成しました")
    
    def _setup_dashboard_table(self) -> None:
        """ダッシュボードテーブルの設定"""
        if not self.table_exists('dashboard'):
            query = '''
                CREATE TABLE dashboard (
                    project_id INTEGER,
                    project_name TEXT,
                    manager TEXT,
                    division TEXT,
                    factory TEXT,
                    process TEXT,
                    line TEXT,
                    status TEXT,
                    created_at TEXT,
                    task_id INTEGER,
                    task_name TEXT,
                    task_start_date TEXT,
                    task_finish_date TEXT,
                    task_status TEXT,
                    task_milestone TEXT,
                    task_assignee TEXT,
                    task_work_hours REAL
                )
            '''
            self.execute_update(query)
            self.logger.info("dashboardテーブルを作成しました")
    
    def _migrate_tasks_table(self) -> None:
        """tasksテーブルのマイグレーション"""
        try:
            # task_milestone列がない場合はテーブルを再作成
            if not self.column_exists('tasks', 'task_milestone'):
                with self.connection() as conn:
                    cursor = conn.cursor()
                    
                    # 一時テーブルの作成
                    cursor.execute('''
                        CREATE TABLE tasks_temp (
                            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            task_name TEXT NOT NULL,
                            task_start_date TEXT NOT NULL,
                            task_finish_date TEXT NOT NULL,
                            task_status TEXT NOT NULL CHECK(task_status IN ('未着手', '進行中', '完了', '中止')),
                            task_milestone TEXT NOT NULL,
                            task_assignee TEXT,
                            task_work_hours REAL,
                            project_name TEXT NOT NULL,
                            FOREIGN KEY (project_name) REFERENCES projects(project_name)
                                ON UPDATE CASCADE
                                ON DELETE CASCADE
                        )
                    ''')
                    
                    # データの移行
                    cursor.execute('''
                        INSERT INTO tasks_temp (
                            task_id, task_name, task_start_date, task_finish_date,
                            task_status, task_milestone, task_assignee, task_work_hours, project_name
                        )
                        SELECT 
                            task_id, task_name, task_start_date, task_finish_date,
                            task_status, '未設定' as task_milestone, '' as task_assignee, 0 as task_work_hours, project_name
                        FROM tasks
                    ''')
                    
                    # 元のテーブルを削除し、一時テーブルをリネーム
                    cursor.execute('DROP TABLE tasks')
                    cursor.execute('ALTER TABLE tasks_temp RENAME TO tasks')
                    
                    conn.commit()
                    self.logger.info("tasksテーブルのマイグレーションが完了しました")
            
            else:
                # task_assignee列がなければ追加
                if not self.column_exists('tasks', 'task_assignee'):
                    self.add_column('tasks', 'task_assignee', 'TEXT')
                
                # task_work_hours列がなければ追加
                if not self.column_exists('tasks', 'task_work_hours'):
                    self.add_column('tasks', 'task_work_hours', 'REAL')
                
        except Exception as e:
            error_msg = f"タスクテーブルのマイグレーションでエラーが発生: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def _check_and_migrate_projects_table(self) -> None:
        """プロジェクトテーブルの構造確認とマイグレーション"""
        # project_idカラムの確認
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(projects)")
            columns = {row['name'] for row in cursor.fetchall()}
            
            if 'id' in columns and 'project_id' not in columns:
                self.logger.info("プロジェクトテーブルのマイグレーションを開始します")
                
                # 一時テーブルの作成と移行
                cursor.execute('''
                    CREATE TABLE projects_temp (
                        project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_name TEXT NOT NULL UNIQUE,
                        start_date TEXT NOT NULL,
                        manager TEXT NOT NULL,
                        reviewer TEXT NOT NULL,
                        approver TEXT NOT NULL,
                        division TEXT,
                        factory TEXT,
                        process TEXT,
                        line TEXT,
                        status TEXT NOT NULL DEFAULT '進行中' CHECK(status IN ('進行中', '完了', '中止')),
                        project_path TEXT,
                        ganttchart_path TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                cursor.execute('''
                    INSERT INTO projects_temp 
                    SELECT 
                        id as project_id,
                        project_name,
                        start_date,
                        manager,
                        reviewer,
                        approver,
                        division,
                        factory,
                        process,
                        line,
                        status,
                        NULL as project_path,
                        NULL as ganttchart_path,
                        created_at,
                        updated_at
                    FROM projects
                ''')
                
                cursor.execute('DROP TABLE projects')
                cursor.execute('ALTER TABLE projects_temp RENAME TO projects')
                
                conn.commit()
                self.logger.info("プロジェクトテーブルのマイグレーションが完了しました")
    
    def insert_project(self, project_data: Dict[str, Any]) -> int:
        """
        新規プロジェクトの登録
        
        Args:
            project_data: プロジェクトデータ
            
        Returns:
            int: 生成されたプロジェクトID
        """
        try:
            # 1. プロジェクト情報の登録
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            query = '''
                INSERT INTO projects (
                    project_name, start_date, manager, reviewer, approver,
                    division, factory, process, line, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params = (
                project_data['project_name'],
                project_data['start_date'],
                project_data['manager'],
                project_data['reviewer'],
                project_data['approver'],
                project_data.get('division'),
                project_data.get('factory'),
                project_data.get('process'),
                project_data.get('line'),
                current_time,
                current_time
            )
            
            project_id = self.execute_insert(query, params)
            
            # 2. プロジェクトフォルダの作成
            project_folder = self._create_project_folder(project_data)
            
            # 3. プロジェクトパスの更新
            update_query = 'UPDATE projects SET project_path = ? WHERE project_id = ?'
            self.execute_update(update_query, (str(project_folder), project_id))
            
            # 4. ダッシュボードの更新
            self.update_dashboard()
            
            return project_id
            
        except Exception as e:
            error_msg = f"プロジェクト登録エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def _create_project_folder(self, project_data: Dict[str, Any]) -> Path:
        """
        プロジェクトフォルダを作成
        
        Args:
            project_data: プロジェクトデータ
            
        Returns:
            Path: 作成したフォルダのパス
        """
        try:
            # フォルダ名の生成
            folder_components = [
                str(project_data.get(key, '')) for key in ['division', 'factory', 'process', 'line']
            ]
            folder_components.extend([
                project_data['project_name'],
                project_data['start_date'],
                project_data['manager']
            ])
            
            # 空の値を除外し、フォルダ名を生成
            folder_name = '_'.join(filter(None, folder_components))
            folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
            
            # 出力先ディレクトリの取得（動的に解決）
            output_base_dir = self.path_manager.get_path("OUTPUT_BASE_DIR")
            project_folder = output_base_dir / folder_name
            
            # フォルダが既に存在する場合は連番を付与
            base_folder_name = folder_name
            counter = 1
            while project_folder.exists():
                folder_name = f"{base_folder_name}_{counter}"
                project_folder = output_base_dir / folder_name
                counter += 1
            
            # プロジェクトフォルダのみを作成
            os.makedirs(project_folder, exist_ok=True)
            
            # メタデータフォルダも作成
            metadata_folder = self.path_manager.get_project_metadata_path(project_folder)
            os.makedirs(metadata_folder, exist_ok=True)
            
            self.logger.info(f"プロジェクトフォルダを作成しました: {project_folder}")
            return project_folder
                
        except Exception as e:
            error_msg = f"フォルダ作成エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("フォルダ作成エラー", error_msg)
    
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> None:
        """
        プロジェクト情報の更新
        
        Args:
            project_id: プロジェクトID
            project_data: 更新するプロジェクトデータ
        """
        try:
            # 1. 現在のプロジェクト情報を取得
            old_project = self.get_project(project_id)
            if not old_project:
                raise ValueError(f"プロジェクトが見つかりません: {project_id}")
            
            # 2. プロジェクト情報の更新
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            query = '''
                UPDATE projects 
                SET project_name = ?, start_date = ?, manager = ?,
                    reviewer = ?, approver = ?, division = ?,
                    factory = ?, process = ?, line = ?, status = ?, 
                    updated_at = ?
                WHERE project_id = ?
            '''
            
            params = (
                project_data['project_name'],
                project_data['start_date'],
                project_data['manager'],
                project_data['reviewer'],
                project_data['approver'],
                project_data.get('division'),
                project_data.get('factory'),
                project_data.get('process'),
                project_data.get('line'),
                project_data['status'],
                current_time,
                project_id
            )
            
            self.execute_update(query, params)
            
            # 3. 古いフォルダの削除（存在する場合）
            if old_project['project_path']:
                old_path = Path(old_project['project_path'])
                if old_path.exists():
                    shutil.rmtree(old_path)
                    self.logger.info(f"古いプロジェクトフォルダを削除しました: {old_path}")
            
            # 4. 新しいフォルダの作成
            project_folder = self._create_project_folder(project_data)
            
            # 5. プロジェクトパスの更新
            update_query = 'UPDATE projects SET project_path = ? WHERE project_id = ?'
            self.execute_update(update_query, (str(project_folder), project_id))
            
            # 6. ダッシュボードの更新
            self.update_dashboard()
            
        except Exception as e:
            error_msg = f"プロジェクト更新エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def delete_project(self, project_id: int) -> None:
        """
        プロジェクトの削除
        
        Args:
            project_id: 削除するプロジェクトのID
        """
        try:
            # 1. プロジェクト情報の取得
            project = self.get_project(project_id)
            if not project:
                raise ValueError(f"プロジェクトが見つかりません: {project_id}")
            
            # 2. プロジェクトフォルダの削除
            project_path = project['project_path']
            if project_path and Path(project_path).exists():
                shutil.rmtree(project_path)
                self.logger.info(f"プロジェクトフォルダを削除しました: {project_path}")
            
            # 3. プロジェクト情報の削除
            delete_query = 'DELETE FROM projects WHERE project_id = ?'
            self.execute_update(delete_query, (project_id,))
            
            # 4. ダッシュボードの更新
            self.update_dashboard()
            
        except Exception as e:
            error_msg = f"プロジェクト削除エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        プロジェクト情報の取得
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            Optional[Dict[str, Any]]: プロジェクト情報
        """
        return self.get_by_id('projects', 'project_id', project_id)
    
    def get_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        プロジェクト名による情報取得
        
        Args:
            project_name: プロジェクト名
            
        Returns:
            Optional[Dict[str, Any]]: プロジェクト情報
        """
        query = 'SELECT * FROM projects WHERE project_name = ?'
        results = self.execute_query(query, (project_name,))
        return results[0] if results else None
    
    def get_all_projects(self, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        全プロジェクトの取得
        
        Args:
            filter_status: ステータスによるフィルタリング（オプション）
            
        Returns:
            List[Dict[str, Any]]: プロジェクト情報のリスト
        """
        if filter_status:
            query = 'SELECT * FROM projects WHERE status = ? ORDER BY project_id DESC'
            return self.execute_query(query, (filter_status,))
        else:
            return self.get_all('projects', 'project_id DESC')
    
    def clear_tasks(self) -> None:
        """タスクテーブルのデータを全て削除"""
        self.clear_table('tasks')
    
    def insert_tasks(self, tasks_data: List[Dict[str, Any]]) -> int:
        """
        タスクデータの一括登録
        
        Args:
            tasks_data: タスクデータのリスト
            
        Returns:
            int: 登録されたタスク数
        """
        try:
            # プロジェクト名の存在確認
            for task in tasks_data:
                query = 'SELECT COUNT(*) as count FROM projects WHERE project_name = ?'
                result = self.execute_query(query, (task['project_name'],))
                if result[0]['count'] == 0:
                    raise ValueError(f"プロジェクト '{task['project_name']}' が存在しません")
            
            # タスクデータの挿入
            query = '''
                INSERT INTO tasks (
                    task_name, task_start_date, task_finish_date,
                    task_status, task_milestone, task_assignee, task_work_hours, project_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''
            
            params_list = [
                (
                    task['task_name'],
                    task['task_start_date'],
                    task['task_finish_date'],
                    task['task_status'],
                    task['task_milestone'],
                    task.get('task_assignee', ''),
                    task.get('task_work_hours', 0),
                    task['project_name']
                )
                for task in tasks_data
            ]
            
            rows_affected = self.execute_many(query, params_list)
            self.logger.info(f"{len(tasks_data)}件のタスクを登録しました")
            
            return rows_affected
            
        except Exception as e:
            error_msg = f"タスク登録エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def get_tasks_by_project(self, project_name: str) -> List[Dict[str, Any]]:
        """
        プロジェクト名によるタスク取得
        
        Args:
            project_name: プロジェクト名
            
        Returns:
            List[Dict[str, Any]]: タスク情報のリスト
        """
        query = 'SELECT * FROM tasks WHERE project_name = ? ORDER BY task_start_date'
        return self.execute_query(query, (project_name,))
    
    def update_dashboard(self) -> None:
        """ダッシュボードテーブルを更新し、関連データをエクスポート"""
        try:
            # 1. 既存のデータを削除
            self.clear_table('dashboard')
            
            # 2. プロジェクトとタスクのデータを結合して挿入
            query = '''
                INSERT INTO dashboard (
                    project_id, project_name, manager, division, factory,
                    process, line, status, created_at, task_id, task_name,
                    task_start_date, task_finish_date, task_status, task_milestone,
                    task_assignee, task_work_hours
                )
                SELECT 
                    p.project_id, p.project_name, p.manager, p.division, 
                    p.factory, p.process, p.line, p.status, p.created_at,
                    t.task_id, t.task_name, t.task_start_date, 
                    t.task_finish_date, t.task_status, t.task_milestone,
                    t.task_assignee, t.task_work_hours
                FROM projects p
                LEFT JOIN tasks t ON p.project_name = t.project_name
            '''
            
            self.execute_update(query)
            
            # 3. CSVファイルへの出力
            self._export_dashboard_to_csv()
            self._export_projects_to_csv()
            
            self.logger.info("ダッシュボードとプロジェクトデータの更新が完了しました")
            
        except Exception as e:
            error_msg = f"ダッシュボード更新エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    def _export_dashboard_to_csv(self) -> None:
        """ダッシュボードデータをCSVファイルに出力"""
        try:
            # 出力ディレクトリの作成
            exports_dir = self.path_manager.ensure_directory("EXPORTS_DIR")
            
            # データの取得
            query = "SELECT * FROM dashboard ORDER BY project_id, task_id"
            dashboard_data = self.execute_query(query)
            
            # DataFrame作成
            df = pd.DataFrame(dashboard_data)
            
            # NULL値を "未設定" に変換
            df = df.fillna("未設定")
            
            # CSVファイルに出力
            dashboard_export_file = self.path_manager.get_path("DASHBOARD_EXPORT_FILE")
            df.to_csv(
                dashboard_export_file,
                index=False,
                encoding='utf-8-sig'
            )
            
            self.logger.info(f"ダッシュボードデータをCSVファイルに出力しました: {dashboard_export_file}")
            
        except Exception as e:
            error_msg = f"ダッシュボードデータのCSV出力エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データエクスポートエラー", error_msg)
    
    def _export_projects_to_csv(self) -> None:
        """プロジェクトデータをCSVファイルに出力"""
        try:
            # 出力ディレクトリの作成
            exports_dir = self.path_manager.ensure_directory("EXPORTS_DIR")
            
            # データの取得
            query = """
                SELECT 
                    project_id,
                    project_name,
                    start_date,
                    manager,
                    reviewer,
                    approver,
                    division,
                    factory,
                    process,
                    line,
                    status,
                    project_path,
                    ganttchart_path,
                    created_at,
                    updated_at
                FROM projects
                ORDER BY project_id
            """
            projects_data = self.execute_query(query)
            
            # DataFrame作成
            df = pd.DataFrame(projects_data)
            
            # NULL値を "未設定" に変換
            df = df.fillna("未設定")
            
            # CSVファイルに出力
            projects_export_file = self.path_manager.get_path("PROJECTS_EXPORT_FILE")
            df.to_csv(
                projects_export_file,
                index=False,
                encoding='utf-8-sig'
            )
            
            self.logger.info(f"プロジェクトデータをCSVファイルに出力しました: {projects_export_file}")
            
        except Exception as e:
            error_msg = f"プロジェクトデータのCSV出力エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データエクスポートエラー", error_msg)