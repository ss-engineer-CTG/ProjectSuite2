"""
統合ユーティリティ
"""

import re
import csv
import shutil
import logging
import traceback
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from tkinter import messagebox
from datetime import datetime

from constants import *

class ErrorHandler:
    """エラーハンドリング"""
    
    @staticmethod
    def handle_error(error: Exception, context: str = ""):
        """一般的なエラーハンドリング"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        messagebox.showerror("エラー", error_msg)
    
    @staticmethod
    def handle_critical_error(error: Exception, context: str = ""):
        """致命的エラーのハンドリング"""
        error_msg = f"致命的エラー - {context}: {str(error)}" if context else f"致命的エラー: {str(error)}"
        logging.critical(f"{error_msg}\n{traceback.format_exc()}")
        messagebox.showerror("致命的エラー", f"{error_msg}\n\nアプリケーションを終了します。")
        sys.exit(1)
    
    @staticmethod
    def show_warning(message: str, title: str = "警告"):
        """警告表示"""
        logging.warning(message)
        messagebox.showwarning(title, message)
    
    @staticmethod
    def show_info(message: str, title: str = "情報"):
        """情報表示"""
        logging.info(message)
        messagebox.showinfo(title, message)
    
    @staticmethod
    def confirm_dialog(message: str, title: str = "確認") -> bool:
        """確認ダイアログ"""
        return messagebox.askyesno(title, message)

class Validator:
    """入力検証"""
    
    @staticmethod
    def validate_project_data(project_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """プロジェクトデータの総合検証"""
        errors = []
        
        # 必須フィールドの検証
        for field in REQUIRED_PROJECT_FIELDS:
            if not project_data.get(field, '').strip():
                field_name = {
                    'project_name': 'プロジェクト名',
                    'start_date': '開始日',
                    'manager': '担当者',
                    'reviewer': '確認者',
                    'approver': '承認者'
                }.get(field, field)
                errors.append(f"{field_name}は必須項目です")
        
        # プロジェクト名の検証
        if project_data.get('project_name'):
            project_name = project_data['project_name'].strip()
            if len(project_name) > MAX_PROJECT_NAME_LENGTH:
                errors.append(f"プロジェクト名は{MAX_PROJECT_NAME_LENGTH}文字以内で入力してください")
            elif len(project_name) < 3:
                errors.append("プロジェクト名は3文字以上で入力してください")
        
        # 日付の検証
        if project_data.get('start_date'):
            if not Validator._validate_date(project_data['start_date']):
                errors.append(f"日付の形式が正しくありません（{DATE_FORMAT}形式で入力してください）")
        
        # ステータスの検証
        if project_data.get('status') and project_data['status'] not in PROJECT_STATUSES:
            errors.append(f"無効なステータスです")
        
        return len(errors) == 0, errors
    
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
            if task_data.get(date_field) and not Validator._validate_date(task_data[date_field]):
                errors.append(f"{date_field}: 日付形式が正しくありません")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_date(date_string: str) -> bool:
        """日付形式の検証"""
        try:
            datetime.strptime(date_string.strip(), DATE_FORMAT)
            return True
        except ValueError:
            return False

class FileUtils:
    """ファイル操作ユーティリティ"""
    
    @staticmethod
    def read_csv_with_encoding(file_path: Path) -> List[Dict[str, Any]]:
        """エンコーディング自動判定でCSV読み込み"""
        file_path = Path(file_path)
        
        for encoding in ENCODING_OPTIONS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    return list(reader)
            except UnicodeDecodeError:
                continue
            except Exception:
                break
        
        raise ValueError(f"CSV読み込み失敗: {file_path}")
    
    @staticmethod
    def write_csv(file_path: Path, data: List[Dict[str, Any]], encoding: str = 'utf-8-sig'):
        """CSV書き込み"""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not data:
            return
        
        with open(file_path, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def copy_directory(source: Path, destination: Path):
        """ディレクトリのコピー"""
        source = Path(source)
        destination = Path(destination)
        
        if source.exists() and source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)

class PathUtils:
    """パス操作ユーティリティ"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """ファイル名の無害化"""
        if not filename:
            return "unnamed"
        
        # 使用できない文字を置換
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '_', filename.strip())
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        
        return sanitized if sanitized else "unnamed"
    
    @staticmethod
    def create_project_folder_name(project_data: dict) -> str:
        """プロジェクトフォルダ名の生成"""
        components = []
        
        # 製造ライン情報
        for field in ['division', 'factory', 'process', 'line']:
            value = project_data.get(field, '').strip()
            if value:
                components.append(PathUtils.sanitize_filename(value))
        
        # プロジェクト基本情報
        for field in ['project_name', 'start_date', 'manager']:
            value = project_data.get(field, '').strip()
            if value:
                components.append(PathUtils.sanitize_filename(value))
        
        folder_name = '_'.join(filter(None, components))
        
        # 長すぎる場合は切り詰め
        if len(folder_name) > 200:
            folder_name = folder_name[:200].rstrip('_')
        
        return folder_name or "unnamed_project"
    
    @staticmethod
    def ensure_unique_path(base_path: Path, desired_name: str) -> Path:
        """一意なパスの確保"""
        base_path = Path(base_path)
        target_path = base_path / desired_name
        
        if not target_path.exists():
            return target_path
        
        # 重複する場合は番号を付与
        counter = 1
        while target_path.exists():
            new_name = f"{desired_name}_{counter}"
            target_path = base_path / new_name
            counter += 1
            
            if counter > 1000:  # 無限ループ防止
                import time
                timestamp = int(time.time())
                new_name = f"{desired_name}_{timestamp}"
                target_path = base_path / new_name
                break
        
        return target_path

class ExternalApp:
    """外部アプリケーション起動"""
    
    @staticmethod
    def launch_document_processor(project_data: Dict[str, Any]) -> bool:
        """ドキュメント処理アプリの起動"""
        try:
            import subprocess
            import os
            
            app_paths = [
                r"C:\Program Files\ProjectSuite Complete\CreateProjectList\CreateProjectList.exe",
                r"C:\Program Files (x86)\ProjectSuite Complete\CreateProjectList\CreateProjectList.exe",
            ]
            
            app_path = None
            for path in app_paths:
                if Path(path).exists():
                    app_path = path
                    break
            
            if not app_path:
                ErrorHandler.show_warning("ドキュメント処理アプリケーションが見つかりません")
                return False
            
            # 環境変数でプロジェクトデータを渡す
            env = os.environ.copy()
            env['PROJECT_NAME'] = project_data.get('project_name', '')
            env['PROJECT_PATH'] = project_data.get('project_path', '')
            env['PROJECT_MANAGER'] = project_data.get('manager', '')
            
            subprocess.Popen([app_path], env=env)
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "外部アプリ起動")
            return False
    
    @staticmethod
    def launch_project_dashboard() -> bool:
        """プロジェクトダッシュボードの起動"""
        try:
            import subprocess
            
            app_paths = [
                r"C:\Program Files\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe",
                r"C:\Program Files (x86)\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe",
            ]
            
            app_path = None
            for path in app_paths:
                if Path(path).exists():
                    app_path = path
                    break
            
            if not app_path:
                ErrorHandler.show_warning("プロジェクトダッシュボードが見つかりません")
                return False
            
            subprocess.Popen([app_path])
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "ダッシュボード起動")
            return False
    
    @staticmethod
    def open_folder(folder_path: Path) -> bool:
        """フォルダをエクスプローラーで開く"""
        try:
            import os
            folder_path = Path(folder_path)
            
            if not folder_path.exists():
                ErrorHandler.show_warning(f"フォルダが存在しません: {folder_path}")
                return False
            
            os.startfile(str(folder_path))
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "フォルダ表示")
            return False