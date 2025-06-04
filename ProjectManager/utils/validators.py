"""
入力検証の統一処理
KISS原則: シンプルな検証ロジック
DRY原則: 重複する検証処理の統合
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from core.constants import ValidationConstants, AppConstants

class Validator:
    """入力検証の統一クラス"""
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def validate_project_data(project_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """プロジェクトデータの総合検証"""
        errors = []
        
        # 必須フィールドの検証
        for field in ValidationConstants.REQUIRED_PROJECT_FIELDS:
            if not project_data.get(field, '').strip():
                field_name = {
                    'project_name': 'プロジェクト名',
                    'start_date': '開始日',
                    'manager': '担当者',
                    'reviewer': '確認者',
                    'approver': '承認者'
                }.get(field, field)
                errors.append(f"{field_name}は必須項目です")
        
        # 個別フィールドの検証
        if project_data.get('project_name'):
            is_valid, msg = Validator.validate_project_name(project_data['project_name'])
            if not is_valid:
                errors.append(msg)
        
        if project_data.get('start_date'):
            is_valid, msg = Validator.validate_date(project_data['start_date'])
            if not is_valid:
                errors.append(msg)
        
        if project_data.get('status'):
            is_valid, msg = Validator.validate_status(project_data['status'])
            if not is_valid:
                errors.append(msg)
        
        # 人名の検証
        for field in ['manager', 'reviewer', 'approver']:
            if project_data.get(field):
                is_valid, msg = Validator.validate_person_name(project_data[field], field)
                if not is_valid:
                    errors.append(msg)
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_project_name(project_name: str) -> Tuple[bool, str]:
        """プロジェクト名の検証"""
        if not project_name or not project_name.strip():
            return False, "プロジェクト名を入力してください"
        
        project_name = project_name.strip()
        
        if len(project_name) > ValidationConstants.MAX_PROJECT_NAME_LENGTH:
            return False, f"プロジェクト名は{ValidationConstants.MAX_PROJECT_NAME_LENGTH}文字以内で入力してください"
        
        if len(project_name) < 3:
            return False, "プロジェクト名は3文字以上で入力してください"
        
        # 使用できない文字のチェック
        invalid_chars = r'[<>:"/\\|?*]'
        if re.search(invalid_chars, project_name):
            return False, "プロジェクト名に使用できない文字が含まれています"
        
        return True, ""
    
    @staticmethod
    def validate_date(date_string: str) -> Tuple[bool, str]:
        """日付形式の検証"""
        if not date_string or not date_string.strip():
            return False, "日付を入力してください"
        
        try:
            datetime.strptime(date_string.strip(), ValidationConstants.DATE_FORMAT)
            return True, ""
        except ValueError:
            return False, f"日付の形式が正しくありません（{ValidationConstants.DATE_FORMAT}形式で入力してください）"
    
    @staticmethod
    def validate_status(status: str) -> Tuple[bool, str]:
        """ステータスの検証"""
        if not status or not status.strip():
            return False, "ステータスを選択してください"
        
        if status not in AppConstants.PROJECT_STATUSES:
            return False, f"無効なステータスです（{', '.join(AppConstants.PROJECT_STATUSES)}から選択してください）"
        
        return True, ""
    
    @staticmethod
    def validate_person_name(name: str, field_type: str = "") -> Tuple[bool, str]:
        """人名の検証"""
        if not name or not name.strip():
            field_name = {
                'manager': '担当者',
                'reviewer': '確認者',
                'approver': '承認者'
            }.get(field_type, '名前')
            return False, f"{field_name}を入力してください"
        
        name = name.strip()
        
        if len(name) > ValidationConstants.MAX_PERSON_NAME_LENGTH:
            return False, f"名前は{ValidationConstants.MAX_PERSON_NAME_LENGTH}文字以内で入力してください"
        
        return True, ""
    
    @staticmethod
    def validate_code(code: str, code_type: str = "") -> Tuple[bool, str]:
        """コードの検証"""
        if not code:
            return True, ""  # コードは任意項目
        
        code = code.strip()
        
        if len(code) > ValidationConstants.MAX_CODE_LENGTH:
            return False, f"{code_type}コードは{ValidationConstants.MAX_CODE_LENGTH}文字以内で入力してください"
        
        # 英数字とアンダースコアのみ許可
        if not re.match(r'^[A-Za-z0-9_]+$', code):
            return False, f"{code_type}コードは英数字とアンダースコアのみ使用できます"
        
        return True, ""
    
    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, str]:
        """ファイルパスの検証"""
        if not file_path or not file_path.strip():
            return False, "ファイルパスを指定してください"
        
        try:
            path = Path(file_path.strip())
            
            # パスが存在するかチェック
            if not path.exists():
                return False, "指定されたパスが存在しません"
            
            # 書き込み権限のチェック
            if path.is_dir():
                test_file = path / '.write_test'
                try:
                    test_file.touch()
                    test_file.unlink()
                except Exception:
                    return False, "指定されたディレクトリに書き込み権限がありません"
            
            return True, ""
            
        except Exception as e:
            return False, f"無効なパスです: {str(e)}"
    
    @staticmethod
    def validate_task_data(task_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """タスクデータの検証"""
        errors = []
        
        # 必須フィールドの検証
        required_fields = ['task_name', 'task_start_date', 'task_finish_date', 'task_status', 'task_milestone']
        for field in required_fields:
            if not task_data.get(field, '').strip():
                errors.append(f"{field}は必須項目です")
        
        # 日付の検証
        for date_field in ['task_start_date', 'task_finish_date']:
            if task_data.get(date_field):
                is_valid, msg = Validator.validate_date(task_data[date_field])
                if not is_valid:
                    errors.append(f"{date_field}: {msg}")
        
        # ステータスの検証
        if task_data.get('task_status') and task_data['task_status'] not in AppConstants.TASK_STATUSES:
            errors.append(f"無効なタスクステータス: {task_data['task_status']}")
        
        # 工数の検証
        if task_data.get('task_work_hours'):
            try:
                hours = float(task_data['task_work_hours'])
                if hours < 0:
                    errors.append("工数は0以上の数値を入力してください")
            except ValueError:
                errors.append("工数は数値で入力してください")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名の無害化"""
        if not filename:
            return "unnamed"
        
        # 使用できない文字を置換
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename.strip())
        
        # 連続するアンダースコアを単一に
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # 前後のアンダースコアを除去
        sanitized = sanitized.strip('_')
        
        # 空になった場合のフォールバック
        if not sanitized:
            sanitized = "unnamed"
        
        return sanitized