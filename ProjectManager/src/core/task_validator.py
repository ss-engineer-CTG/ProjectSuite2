"""タスクデータの検証ロジックを提供するモジュール"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.error_handler import ValidationError

class TaskValidator:
    """タスクデータの検証ロジック"""
    
    def __init__(self):
        """初期化"""
        self.logger = get_logger(__name__)
        
        # 有効なステータス値
        self.valid_statuses = ['未着手', '進行中', '完了', '中止']
    
    def validate_task(self, task: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        タスクデータの検証
        
        Args:
            task: 検証するタスクデータ
            
        Returns:
            Tuple[bool, List[str]]: (検証結果, エラーメッセージのリスト)
            検証結果がTrueの場合、エラーメッセージは空リスト
        """
        errors = []
        
        # 1. 必須フィールドの存在確認
        required_fields = [
            'task_name', 'task_start_date', 'task_finish_date',
            'task_status', 'task_milestone', 'project_name'
        ]
        
        for field in required_fields:
            if field not in task:
                errors.append(f"必須フィールド {field} が不足しています")
            elif task[field] is None or str(task[field]).strip() == '':
                errors.append(f"必須フィールド {field} が空です")
        
        # 必須フィールドが不足している場合は以降のチェックをスキップ
        if errors:
            return False, errors
        
        # 2. 日付形式の検証
        for date_field in ['task_start_date', 'task_finish_date']:
            if not self._validate_date_format(task[date_field]):
                errors.append(f"{date_field}の形式が不正です: {task[date_field]}")
        
        # 3. 開始日と終了日の整合性確認
        if not errors:  # 日付形式が正しい場合のみチェック
            if not self._validate_date_range(task['task_start_date'], task['task_finish_date']):
                errors.append(
                    f"開始日 {task['task_start_date']} が終了日 {task['task_finish_date']} より後になっています"
                )
        
        # 4. ステータスの検証
        if task['task_status'] not in self.valid_statuses:
            errors.append(
                f"無効なステータスです: {task['task_status']}, "
                f"有効な値: {', '.join(self.valid_statuses)}"
            )
        
        # 5. 工数の検証
        if 'task_work_hours' in task and task['task_work_hours'] is not None:
            try:
                work_hours = float(task['task_work_hours'])
                if work_hours < 0:
                    errors.append(f"工数は0以上の値でなければなりません: {work_hours}")
            except (ValueError, TypeError):
                errors.append(f"工数は数値でなければなりません: {task['task_work_hours']}")
        
        # 検証結果の返却
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _validate_date_format(self, date_str: str) -> bool:
        """
        日付形式の検証
        
        Args:
            date_str: 検証する日付文字列
            
        Returns:
            bool: 日付形式が正しい場合はTrue
        """
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            # YYYY/MM/DD形式もサポート
            try:
                datetime.strptime(date_str, '%Y/%m/%d')
                return True
            except ValueError:
                return False
    
    def _validate_date_range(self, start_date: str, end_date: str) -> bool:
        """
        開始日と終了日の整合性確認
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            bool: 開始日が終了日以前の場合はTrue
        """
        try:
            # 日付形式に応じて変換
            if '-' in start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start = datetime.strptime(start_date, '%Y/%m/%d')
                
            if '-' in end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end = datetime.strptime(end_date, '%Y/%m/%d')
            
            return start <= end
            
        except ValueError:
            # 日付変換に失敗した場合は別のバリデーションでエラーになるのでここではTrue
            return True
    
    def normalize_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        タスクデータの正規化
        
        Args:
            task: 正規化するタスクデータ
            
        Returns:
            Dict[str, Any]: 正規化されたタスクデータ
        """
        normalized = task.copy()
        
        # 文字列フィールドのトリミング
        for field in ['task_name', 'task_status', 'task_milestone', 'task_assignee', 'project_name']:
            if field in normalized and normalized[field] is not None:
                normalized[field] = str(normalized[field]).strip()
        
        # 日付フォーマットの正規化（YYYY/MM/DD -> YYYY-MM-DD）
        for date_field in ['task_start_date', 'task_finish_date']:
            if date_field in normalized and normalized[date_field] is not None:
                if '/' in normalized[date_field]:
                    try:
                        date_obj = datetime.strptime(normalized[date_field], '%Y/%m/%d')
                        normalized[date_field] = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        # 変換に失敗した場合はそのまま
                        pass
        
        # ステータスの正規化（大文字小文字、全角半角の差異を吸収）
        if 'task_status' in normalized and normalized['task_status'] is not None:
            status = normalized['task_status'].strip()
            # ステータスの正規化ロジック（必要に応じて実装）
            # 例: '未着手' と '未着手　' を同一視する
            
            # 無効なステータスの場合は '未着手' にする
            if status not in self.valid_statuses:
                self.logger.warning(f"無効なステータス '{status}' を '未着手' に置換します")
                normalized['task_status'] = '未着手'
        
        # 工数の正規化
        if 'task_work_hours' in normalized:
            if normalized['task_work_hours'] is None or normalized['task_work_hours'] == '':
                normalized['task_work_hours'] = 0
            else:
                try:
                    normalized['task_work_hours'] = float(normalized['task_work_hours'])
                except (ValueError, TypeError):
                    self.logger.warning(f"無効な工数値 '{normalized['task_work_hours']}' を 0 に置換します")
                    normalized['task_work_hours'] = 0
        else:
            normalized['task_work_hours'] = 0
        
        # 担当者の正規化
        if 'task_assignee' not in normalized or normalized['task_assignee'] is None:
            normalized['task_assignee'] = ''
        
        return normalized
    
    def validate_and_normalize_tasks(self, tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        複数のタスクデータを検証して正規化する
        
        Args:
            tasks: 検証・正規化するタスクデータのリスト
            
        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: 
            (有効なタスクのリスト, 無効なタスクのリスト)
        """
        valid_tasks = []
        invalid_tasks = []
        
        for i, task in enumerate(tasks):
            try:
                # まず正規化
                normalized_task = self.normalize_task(task)
                
                # 次に検証
                is_valid, errors = self.validate_task(normalized_task)
                
                if is_valid:
                    valid_tasks.append(normalized_task)
                else:
                    # エラー情報を付加
                    invalid_task = normalized_task.copy()
                    invalid_task['_errors'] = errors
                    invalid_task['_row_index'] = i + 2  # ヘッダー行 + 0-indexを1-indexに変換
                    invalid_tasks.append(invalid_task)
                    
                    self.logger.warning(
                        f"タスクバリデーションエラー（行 {i + 2}）: {', '.join(errors)}"
                    )
                    
            except Exception as e:
                self.logger.error(f"タスク処理エラー（行 {i + 2}）: {e}")
                
                # エラー情報を付加
                error_task = task.copy() if isinstance(task, dict) else {'_raw': str(task)}
                error_task['_errors'] = [f"処理エラー: {e}"]
                error_task['_row_index'] = i + 2
                invalid_tasks.append(error_task)
        
        return valid_tasks, invalid_tasks