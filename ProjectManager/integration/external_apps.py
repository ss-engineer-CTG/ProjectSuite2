"""
外部アプリケーション連携（Windows専用簡素版）
KISS原則: シンプルな外部アプリ起動
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from utils.error_handler import ErrorHandler

class ExternalAppLauncher:
    """外部アプリケーション起動クラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def launch_document_processor(self, project_data: Dict[str, Any]) -> bool:
        """ドキュメント処理アプリの起動"""
        try:
            # CreateProjectListアプリの起動パス
            app_paths = [
                r"C:\Program Files\ProjectSuite Complete\CreateProjectList\CreateProjectList.exe",
                r"C:\Program Files (x86)\ProjectSuite Complete\CreateProjectList\CreateProjectList.exe",
            ]
            
            app_path = None
            for path in app_paths:
                if Path(path).exists():
                    app_path = Path(path)
                    break
            
            if not app_path:
                ErrorHandler.handle_warning(
                    "ドキュメント処理アプリケーションが見つかりません。\n"
                    "CreateProjectListがインストールされているか確認してください。",
                    "外部アプリ起動"
                )
                return False
            
            # プロジェクトデータを環境変数で渡す
            env = os.environ.copy()
            env['PROJECT_NAME'] = project_data.get('project_name', '')
            env['PROJECT_PATH'] = project_data.get('project_path', '')
            env['PROJECT_MANAGER'] = project_data.get('manager', '')
            env['PROJECT_ID'] = str(project_data.get('project_id', ''))
            
            # 実行ファイルとして起動
            subprocess.Popen([str(app_path)], env=env)
            self.logger.info(f"CreateProjectListを起動: {app_path}")
            
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "ドキュメント処理アプリ起動")
            return False
    
    def launch_project_dashboard(self) -> bool:
        """プロジェクトダッシュボードアプリの起動"""
        try:
            # プロジェクトダッシュボードの起動パス
            dashboard_paths = [
                r"C:\Program Files\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe",
                r"C:\Program Files (x86)\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe",
            ]
            
            dashboard_path = None
            for path in dashboard_paths:
                if Path(path).exists():
                    dashboard_path = Path(path)
                    break
            
            if not dashboard_path:
                ErrorHandler.handle_warning(
                    "プロジェクトダッシュボードアプリケーションが見つかりません。\n"
                    "ProjectDashboardがインストールされているか確認してください。",
                    "外部アプリ起動"
                )
                return False
            
            # 実行ファイルとして起動
            subprocess.Popen([str(dashboard_path)])
            
            self.logger.info(f"プロジェクトダッシュボードを起動: {dashboard_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクトダッシュボード起動")
            return False
    
    def launch_excel_app(self, file_path: Optional[Path] = None) -> bool:
        """Excelアプリケーションの起動"""
        try:
            if file_path and Path(file_path).exists():
                # 特定のファイルを開く
                os.startfile(str(file_path))
                self.logger.info(f"Excelファイルを開きました: {file_path}")
            else:
                # Excel アプリケーションを起動
                subprocess.Popen(['excel'])
                self.logger.info("Excelアプリケーションを起動しました")
            
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "Excel起動")
            return False
    
    def open_folder(self, folder_path: Path) -> bool:
        """フォルダをエクスプローラーで開く"""
        try:
            folder_path = Path(folder_path)
            
            if not folder_path.exists():
                ErrorHandler.handle_warning(f"フォルダが存在しません: {folder_path}", "フォルダ表示")
                return False
            
            os.startfile(str(folder_path))
            self.logger.info(f"フォルダを開きました: {folder_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "フォルダ表示")
            return False
    
    def launch_command_prompt(self, working_directory: Optional[Path] = None) -> bool:
        """コマンドプロンプトの起動"""
        try:
            if working_directory and Path(working_directory).exists():
                # 指定ディレクトリでコマンドプロンプトを起動
                subprocess.Popen(['cmd'], cwd=str(working_directory))
                self.logger.info(f"コマンドプロンプトを起動: {working_directory}")
            else:
                # デフォルトディレクトリでコマンドプロンプトを起動
                subprocess.Popen(['cmd'])
                self.logger.info("コマンドプロンプトを起動しました")
            
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "コマンドプロンプト起動")
            return False
    
    def check_app_availability(self, app_name: str) -> bool:
        """アプリケーションの利用可能性チェック"""
        try:
            if app_name == "document_processor":
                app_paths = [
                    r"C:\Program Files\ProjectSuite Complete\CreateProjectList\CreateProjectList.exe",
                    r"C:\Program Files (x86)\ProjectSuite Complete\CreateProjectList\CreateProjectList.exe"
                ]
                return any(Path(path).exists() for path in app_paths)
                
            elif app_name == "project_dashboard":
                app_paths = [
                    r"C:\Program Files\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe",
                    r"C:\Program Files (x86)\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe"
                ]
                return any(Path(path).exists() for path in app_paths)
            else:
                return False
            
        except Exception as e:
            self.logger.error(f"アプリ利用可能性チェックエラー: {e}")
            return False
    
    def get_installed_apps(self) -> Dict[str, bool]:
        """インストール済みアプリの一覧取得"""
        return {
            'document_processor': self.check_app_availability('document_processor'),
            'project_dashboard': self.check_app_availability('project_dashboard'),
            'excel': True,  # Windows環境では通常利用可能
            'explorer': True  # Windows環境では常に利用可能
        }