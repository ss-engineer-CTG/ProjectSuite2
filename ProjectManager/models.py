"""
データモデル定義
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

@dataclass
class Project:
    """プロジェクトデータモデル"""
    project_name: str
    start_date: str
    manager: str
    reviewer: str
    approver: str
    status: str = "進行中"
    division: Optional[str] = None
    factory: Optional[str] = None
    process: Optional[str] = None
    line: Optional[str] = None
    project_path: Optional[str] = None
    project_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        """辞書型に変換"""
        return {
            'project_id': self.project_id,
            'project_name': self.project_name,
            'start_date': self.start_date,
            'manager': self.manager,
            'reviewer': self.reviewer,
            'approver': self.approver,
            'status': self.status,
            'division': self.division,
            'factory': self.factory,
            'process': self.process,
            'line': self.line,
            'project_path': self.project_path,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """辞書型から作成"""
        return cls(
            project_id=data.get('project_id'),
            project_name=data['project_name'],
            start_date=data['start_date'],
            manager=data['manager'],
            reviewer=data['reviewer'],
            approver=data['approver'],
            status=data.get('status', '進行中'),
            division=data.get('division'),
            factory=data.get('factory'),
            process=data.get('process'),
            line=data.get('line'),
            project_path=data.get('project_path'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )

@dataclass
class Task:
    """タスクデータモデル"""
    task_name: str
    task_start_date: str
    task_finish_date: str
    task_status: str
    task_milestone: str
    project_name: str
    task_assignee: str = ""
    task_work_hours: float = 0.0
    task_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """辞書型に変換"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'task_start_date': self.task_start_date,
            'task_finish_date': self.task_finish_date,
            'task_status': self.task_status,
            'task_milestone': self.task_milestone,
            'task_assignee': self.task_assignee,
            'task_work_hours': self.task_work_hours,
            'project_name': self.project_name
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """辞書型から作成"""
        return cls(
            task_id=data.get('task_id'),
            task_name=data['task_name'],
            task_start_date=data['task_start_date'],
            task_finish_date=data['task_finish_date'],
            task_status=data['task_status'],
            task_milestone=data['task_milestone'],
            task_assignee=data.get('task_assignee', ''),
            task_work_hours=data.get('task_work_hours', 0.0),
            project_name=data['project_name']
        )

@dataclass
class MasterData:
    """マスターデータモデル"""
    division_code: str
    division_name: str
    factory_code: str
    factory_name: str
    process_code: str
    process_name: str
    line_code: str
    line_name: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MasterData':
        """辞書型から作成"""
        return cls(
            division_code=data['division_code'],
            division_name=data['division_name'],
            factory_code=data['factory_code'],
            factory_name=data['factory_name'],
            process_code=data['process_code'],
            process_name=data['process_name'],
            line_code=data['line_code'],
            line_name=data['line_name']
        )