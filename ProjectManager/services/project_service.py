"""
プロジェクトビジネスロジック
KISS原則: シンプルなプロジェクト操作
DRY原則: プロジェクト関連処理の統合
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from core.unified_config import UnifiedConfig
from core.database import DatabaseManager
from utils.path_utils import PathManager
from utils.validators import Validator
from utils.error_handler import ErrorHandler, DatabaseErrorHandler

class ProjectService:
    """プロジェクト操作の統合サービス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
    
    def create_project(self, project_data: Dict[str, Any]) -> Optional[int]:
        """プロジェクトの作成"""
        try:
            # データ検証
            is_valid, errors = Validator.validate_project_data(project_data)
            if not is_valid:
                error_msg = "\n".join(errors)
                ErrorHandler.handle_warning(error_msg, "プロジェクト作成")
                return None
            
            # データベースにプロジェクトを作成
            project_id = self.db_manager.create_project(project_data)
            
            # プロジェクトフォルダを作成
            project_folder = self._create_project_folder(project_data)
            if project_folder:
                # プロジェクトパスをデータベースに保存
                self.db_manager.update_project_path(project_id, str(project_folder))
            
            self.logger.info(f"プロジェクトを作成しました: {project_data['project_name']}")
            return project_id
            
        except Exception as e:
            DatabaseErrorHandler.handle_db_error(e, "プロジェクト作成")
            return None
    
    def update_project(self, project_id: int, project_data: Dict[str, Any]) -> bool:
        """プロジェクトの更新"""
        try:
            # データ検証
            is_valid, errors = Validator.validate_project_data(project_data)
            if not is_valid:
                error_msg = "\n".join(errors)
                ErrorHandler.handle_warning(error_msg, "プロジェクト更新")
                return False
            
            # 現在のプロジェクト情報を取得
            current_project = self.db_manager.get_project(project_id)
            if not current_project:
                ErrorHandler.handle_warning("プロジェクトが見つかりません", "プロジェクト更新")
                return False
            
            # データベースを更新
            self.db_manager.update_project(project_id, project_data)
            
            # フォルダ名が変更される可能性がある場合はフォルダを再作成
            if self._should_recreate_folder(current_project, project_data):
                self._recreate_project_folder(current_project, project_data, project_id)
            
            self.logger.info(f"プロジェクトを更新しました: ID {project_id}")
            return True
            
        except Exception as e:
            DatabaseErrorHandler.handle_db_error(e, "プロジェクト更新")
            return False
    
    def delete_project(self, project_id: int) -> bool:
        """プロジェクトの削除"""
        try:
            # プロジェクト情報の取得
            project = self.db_manager.get_project(project_id)
            if not project:
                ErrorHandler.handle_warning("プロジェクトが見つかりません", "プロジェクト削除")
                return False
            
            # 確認ダイアログ
            if not ErrorHandler.confirmation_dialog(
                f"プロジェクト '{project['project_name']}' を削除してもよろしいですか？\n"
                "関連するフォルダとファイルも削除されます。",
                "プロジェクト削除の確認"
            ):
                return False
            
            # プロジェクトフォルダの削除
            if project.get('project_path'):
                self._delete_project_folder(Path(project['project_path']))
            
            # データベースから削除
            self.db_manager.delete_project(project_id)
            
            self.logger.info(f"プロジェクトを削除しました: {project['project_name']}")
            return True
            
        except Exception as e:
            DatabaseErrorHandler.handle_db_error(e, "プロジェクト削除")
            return False
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """プロジェクトの取得"""
        try:
            return self.db_manager.get_project(project_id)
        except Exception as e:
            DatabaseErrorHandler.handle_db_error(e, "プロジェクト取得", show_dialog=False)
            return None
    
    def get_all_projects(self, status_filter: str = "全て") -> List[Dict[str, Any]]:
        """プロジェクト一覧の取得"""
        try:
            all_projects = self.db_manager.get_all_projects()
            
            if status_filter == "全て":
                return all_projects
            else:
                return [p for p in all_projects if p.get('status') == status_filter]
                
        except Exception as e:
            DatabaseErrorHandler.handle_db_error(e, "プロジェクト一覧取得", show_dialog=False)
            return []
    
    def _create_project_folder(self, project_data: Dict[str, Any]) -> Optional[Path]:
        """プロジェクトフォルダの作成"""
        try:
            # 出力ベースディレクトリの取得
            output_base_dir = Path(self.config.get_path('OUTPUT_BASE_DIR'))
            
            # フォルダ名の生成
            folder_name = PathManager.create_project_folder_name(project_data)
            
            # 一意なパスの確保
            project_folder = PathManager.ensure_unique_path(output_base_dir, folder_name)
            
            # フォルダの作成
            project_folder.mkdir(parents=True, exist_ok=True)
            
            # テンプレートフォルダがあればコピー
            self._copy_template_structure(project_folder)
            
            self.logger.info(f"プロジェクトフォルダを作成: {project_folder}")
            return project_folder
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクトフォルダ作成")
            return None
    
    def _copy_template_structure(self, project_folder: Path) -> None:
        """テンプレート構造のコピー"""
        try:
            template_dir = Path(self.config.get_path('TEMPLATES_DIR'))
            if template_dir.exists():
                PathManager.copy_directory_structure(
                    template_dir, project_folder, copy_files=True
                )
                self.logger.debug(f"テンプレート構造をコピー: {template_dir} -> {project_folder}")
        except Exception as e:
            self.logger.warning(f"テンプレート構造のコピーに失敗: {e}")
    
    def _should_recreate_folder(self, current_project: Dict[str, Any], 
                              new_project_data: Dict[str, Any]) -> bool:
        """フォルダ再作成が必要かの判定"""
        # フォルダ名に影響する項目の変更をチェック
        affecting_fields = ['project_name', 'division', 'factory', 'process', 'line', 'manager']
        
        for field in affecting_fields:
            if current_project.get(field) != new_project_data.get(field):
                return True
        
        return False
    
    def _recreate_project_folder(self, current_project: Dict[str, Any], 
                                new_project_data: Dict[str, Any], project_id: int) -> None:
        """プロジェクトフォルダの再作成"""
        try:
            old_path = current_project.get('project_path')
            
            # 新しいフォルダを作成
            new_folder = self._create_project_folder(new_project_data)
            if not new_folder:
                return
            
            # 既存フォルダの内容を新しいフォルダにコピー
            if old_path and Path(old_path).exists():
                self._copy_folder_contents(Path(old_path), new_folder)
                
                # 古いフォルダを削除
                self._delete_project_folder(Path(old_path))
            
            # データベースのパスを更新
            self.db_manager.update_project_path(project_id, str(new_folder))
            
            self.logger.info(f"プロジェクトフォルダを再作成: {old_path} -> {new_folder}")
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクトフォルダ再作成")
    
    def _copy_folder_contents(self, src_folder: Path, dst_folder: Path) -> None:
        """フォルダ内容のコピー"""
        try:
            if not src_folder.exists():
                return
            
            for item in src_folder.iterdir():
                if item.is_file():
                    shutil.copy2(item, dst_folder / item.name)
                elif item.is_dir():
                    dst_subdir = dst_folder / item.name
                    dst_subdir.mkdir(exist_ok=True)
                    self._copy_folder_contents(item, dst_subdir)
                    
        except Exception as e:
            self.logger.warning(f"フォルダ内容コピーエラー: {e}")
    
    def _delete_project_folder(self, folder_path: Path) -> None:
        """プロジェクトフォルダの削除"""
        try:
            if folder_path.exists():
                shutil.rmtree(folder_path)
                self.logger.info(f"プロジェクトフォルダを削除: {folder_path}")
        except Exception as e:
            self.logger.warning(f"プロジェクトフォルダ削除エラー: {e}")
    
    def find_ganttchart_files(self, project_id: int) -> List[Path]:
        """ガントチャートファイルの検索"""
        try:
            project = self.db_manager.get_project(project_id)
            if not project or not project.get('project_path'):
                return []
            
            project_path = Path(project['project_path'])
            if not project_path.exists():
                return []
            
            # ガントチャートファイルを検索
            gantt_files = []
            
            # 工程表フォルダを検索
            for folder in project_path.rglob('*'):
                if folder.is_dir() and '工程表' in folder.name:
                    # xlsmファイルを検索
                    for file in folder.glob('*.xlsm'):
                        if '工程表' in file.name or 'ガント' in file.name:
                            gantt_files.append(file)
            
            return gantt_files
            
        except Exception as e:
            ErrorHandler.handle_error(e, "ガントチャートファイル検索", show_dialog=False)
            return []
    
    def update_ganttchart_path(self, project_id: int, gantt_path: str) -> bool:
        """ガントチャートパスの更新"""
        try:
            # プロジェクトの存在確認
            project = self.db_manager.get_project(project_id)
            if not project:
                return False
            
            # ガントチャートパスをデータベースに保存
            self.db_manager.update_project_path(project_id, gantt_path)
            
            self.logger.info(f"ガントチャートパスを更新: プロジェクトID {project_id}")
            return True
            
        except Exception as e:
            DatabaseErrorHandler.handle_db_error(e, "ガントチャートパス更新", show_dialog=False)
            return False
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """プロジェクト統計情報の取得"""
        try:
            all_projects = self.get_all_projects()
            
            stats = {
                'total': len(all_projects),
                'by_status': {},
                'recent_projects': []
            }
            
            # ステータス別集計
            for project in all_projects:
                status = project.get('status', '不明')
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # 最近のプロジェクト（最新5件）
            stats['recent_projects'] = all_projects[:5]
            
            return stats
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト統計取得", show_dialog=False)
            return {'total': 0, 'by_status': {}, 'recent_projects': []}