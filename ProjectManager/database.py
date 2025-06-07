"""
統合データベース操作
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

class DatabaseManager:
    """統合データベース管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self.setup_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """データベース接続の取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def setup_database(self):
        """データベースの初期設定"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # プロジェクトテーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
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
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # タスクテーブル
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
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
                    )
                ''')
                
                conn.commit()
                self.logger.info("データベースの初期設定が完了しました")
                
        except Exception as e:
            self.logger.error(f"データベース設定エラー: {e}")
            raise
    
    # プロジェクト操作
    def create_project(self, project_data: Dict[str, Any]) -> int:
        """プロジェクトの作成"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO projects (
                        project_name, start_date, manager, reviewer, approver,
                        division, factory, process, line, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_data['project_name'],
                    project_data['start_date'],
                    project_data['manager'],
                    project_data['reviewer'],
                    project_data['approver'],
                    project_data.get('division'),
                    project_data.get('factory'),
                    project_data.get('process'),
                    project_data.get('line'),
                    project_data.get('status', '進行中'),
                    current_time,
                    current_time
                ))
                
                project_id = cursor.lastrowid
                conn.commit()
                return project_id
                
        except sqlite3.IntegrityError:
            raise ValueError("同名のプロジェクトが既に存在します")
        except Exception as e:
            self.logger.error(f"プロジェクト作成エラー: {e}")
            raise
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """プロジェクトの取得"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM projects WHERE project_id = ?', (project_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"プロジェクト取得エラー: {e}")
            return None
    
    def get_all_projects(self, status_filter: str = None) -> List[Dict[str, Any]]:
        """全プロジェクトの取得"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if status_filter and status_filter != "全て":
                    cursor.execute('SELECT * FROM projects WHERE status = ? ORDER BY project_id DESC', (status_filter,))
                else:
                    cursor.execute('SELECT * FROM projects ORDER BY project_id DESC')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"プロジェクト一覧取得エラー: {e}")
            return []
    
    def update_project(self, project_id: int, project_data: Dict[str, Any]):
        """プロジェクトの更新"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE projects 
                    SET project_name = ?, start_date = ?, manager = ?,
                        reviewer = ?, approver = ?, division = ?,
                        factory = ?, process = ?, line = ?, status = ?,
                        updated_at = ?
                    WHERE project_id = ?
                ''', (
                    project_data['project_name'],
                    project_data['start_date'],
                    project_data['manager'],
                    project_data['reviewer'],
                    project_data['approver'],
                    project_data.get('division'),
                    project_data.get('factory'),
                    project_data.get('process'),
                    project_data.get('line'),
                    project_data.get('status', '進行中'),
                    current_time,
                    project_id
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"プロジェクト更新エラー: {e}")
            raise
    
    def delete_project(self, project_id: int):
        """プロジェクトの削除"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))
                conn.commit()
        except Exception as e:
            self.logger.error(f"プロジェクト削除エラー: {e}")
            raise
    
    def update_project_path(self, project_id: int, project_path: str):
        """プロジェクトパスの更新"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE projects SET project_path = ? WHERE project_id = ?',
                    (project_path, project_id)
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"プロジェクトパス更新エラー: {e}")
            raise
    
    # タスク操作
    def clear_tasks(self):
        """全タスクのクリア"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM tasks')
                conn.commit()
        except Exception as e:
            self.logger.error(f"タスククリアエラー: {e}")
            raise
    
    def insert_tasks(self, tasks_data: List[Dict[str, Any]]):
        """タスクの一括挿入"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                task_values = [
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
                
                cursor.executemany('''
                    INSERT INTO tasks (
                        task_name, task_start_date, task_finish_date,
                        task_status, task_milestone, task_assignee, 
                        task_work_hours, project_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', task_values)
                
                conn.commit()
        except Exception as e:
            self.logger.error(f"タスク一括挿入エラー: {e}")
            raise
    
    def get_dashboard_data(self) -> List[Dict[str, Any]]:
        """ダッシュボードデータの取得"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        p.project_id, p.project_name, p.manager, p.division, 
                        p.factory, p.process, p.line, p.status, p.created_at,
                        t.task_id, t.task_name, t.task_start_date, 
                        t.task_finish_date, t.task_status, t.task_milestone,
                        t.task_assignee, t.task_work_hours
                    FROM projects p
                    LEFT JOIN tasks t ON p.project_name = t.project_name
                    ORDER BY p.project_id, t.task_id
                ''')
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"ダッシュボードデータ取得エラー: {e}")
            return []