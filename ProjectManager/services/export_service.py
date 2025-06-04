"""
データエクスポートサービス
KISS原則: シンプルなエクスポート処理
DRY原則: エクスポート処理の統合
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.unified_config import UnifiedConfig
from core.database import DatabaseManager
from core.constants import AppConstants
from utils.file_utils import FileManager
from utils.error_handler import ErrorHandler

class ExportService:
    """データエクスポートの統合サービス"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
    
    def export_dashboard_data(self) -> bool:
        """ダッシュボードデータのエクスポート"""
        try:
            # ダッシュボードテーブルを更新
            self.db_manager.update_dashboard()
            
            # データの取得
            dashboard_data = self._get_dashboard_data()
            if not dashboard_data:
                self.logger.warning("エクスポートするダッシュボードデータがありません")
                return False
            
            # NULL値を "未設定" に変換
            processed_data = self._process_export_data(dashboard_data)
            
            # CSVファイルに出力
            export_path = Path(self.config.get_path('DASHBOARD_EXPORT_PATH'))
            FileManager.write_csv(export_path, processed_data)
            
            self.logger.info(f"ダッシュボードデータをエクスポートしました: {export_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "ダッシュボードデータエクスポート")
            return False
    
    def export_projects_data(self) -> bool:
        """プロジェクトデータのエクスポート"""
        try:
            # プロジェクトデータの取得
            projects_data = self._get_projects_data()
            if not projects_data:
                self.logger.warning("エクスポートするプロジェクトデータがありません")
                return False
            
            # NULL値を "未設定" に変換
            processed_data = self._process_export_data(projects_data)
            
            # CSVファイルに出力
            export_path = Path(self.config.get_path('PROJECTS_EXPORT_PATH'))
            FileManager.write_csv(export_path, processed_data)
            
            self.logger.info(f"プロジェクトデータをエクスポートしました: {export_path}")
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクトデータエクスポート")
            return False
    
    def export_all_data(self) -> bool:
        """全データの一括エクスポート"""
        try:
            success_count = 0
            
            # ダッシュボードデータのエクスポート
            if self.export_dashboard_data():
                success_count += 1
            
            # プロジェクトデータのエクスポート
            if self.export_projects_data():
                success_count += 1
            
            if success_count > 0:
                ErrorHandler.handle_info(f"{success_count}件のデータエクスポートが完了しました", 
                                       "データエクスポート", show_dialog=True)
                return True
            else:
                ErrorHandler.handle_warning("データエクスポートに失敗しました", "データエクスポート")
                return False
                
        except Exception as e:
            ErrorHandler.handle_error(e, "全データエクスポート")
            return False
    
    def export_custom_report(self, filter_conditions: Dict[str, Any], 
                           output_filename: str) -> bool:
        """カスタムレポートのエクスポート"""
        try:
            # フィルター条件に基づいてデータを取得
            custom_data = self._get_filtered_data(filter_conditions)
            if not custom_data:
                ErrorHandler.handle_warning("条件に一致するデータがありません", "カスタムレポートエクスポート")
                return False
            
            # データの加工
            processed_data = self._process_export_data(custom_data)
            
            # ファイル名の処理
            if not output_filename.endswith('.csv'):
                output_filename += '.csv'
            
            # エクスポート先パスの生成
            export_dir = Path(self.config.get_path('EXPORTS_DIR'))
            export_path = export_dir / output_filename
            
            # CSVファイルに出力
            FileManager.write_csv(export_path, processed_data)
            
            ErrorHandler.handle_info(f"カスタムレポートをエクスポートしました: {export_path}", 
                                   "カスタムレポートエクスポート", show_dialog=True)
            return True
            
        except Exception as e:
            ErrorHandler.handle_error(e, "カスタムレポートエクスポート")
            return False
    
    def _get_dashboard_data(self) -> List[Dict[str, Any]]:
        """ダッシュボードデータの取得"""
        try:
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM dashboard ORDER BY project_id, task_id')
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"ダッシュボードデータ取得エラー: {e}")
            return []
    
    def _get_projects_data(self) -> List[Dict[str, Any]]:
        """プロジェクトデータの取得"""
        try:
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT project_id, project_name, start_date, manager, reviewer, approver,
                           division, factory, process, line, status, project_path, 
                           ganttchart_path, created_at, updated_at
                    FROM projects
                    ORDER BY project_id
                ''')
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"プロジェクトデータ取得エラー: {e}")
            return []
    
    def _get_filtered_data(self, filter_conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """フィルター条件に基づくデータ取得"""
        try:
            # 基本クエリ
            base_query = '''
                SELECT d.project_id, d.project_name, d.manager, d.division, d.factory,
                       d.process, d.line, d.status, d.created_at, d.task_id, d.task_name,
                       d.task_start_date, d.task_finish_date, d.task_status, 
                       d.task_milestone, d.task_assignee, d.task_work_hours
                FROM dashboard d
                WHERE 1=1
            '''
            
            conditions = []
            params = []
            
            # フィルター条件の追加
            if filter_conditions.get('status'):
                conditions.append('d.status = ?')
                params.append(filter_conditions['status'])
            
            if filter_conditions.get('division'):
                conditions.append('d.division = ?')
                params.append(filter_conditions['division'])
            
            if filter_conditions.get('date_from'):
                conditions.append('d.task_start_date >= ?')
                params.append(filter_conditions['date_from'])
            
            if filter_conditions.get('date_to'):
                conditions.append('d.task_finish_date <= ?')
                params.append(filter_conditions['date_to'])
            
            # クエリの組み立て
            if conditions:
                query = base_query + ' AND ' + ' AND '.join(conditions)
            else:
                query = base_query
            
            query += ' ORDER BY d.project_id, d.task_id'
            
            with self.db_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"フィルターデータ取得エラー: {e}")
            return []
    
    def _process_export_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """エクスポートデータの加工"""
        processed_data = []
        
        for row in data:
            processed_row = {}
            for key, value in row.items():
                # NULL値や空値を "未設定" に変換
                if value is None or value == "":
                    processed_row[key] = "未設定"
                else:
                    processed_row[key] = str(value)
            
            processed_data.append(processed_row)
        
        return processed_data
    
    def get_export_history(self) -> List[Dict[str, Any]]:
        """エクスポート履歴の取得"""
        try:
            export_dir = Path(self.config.get_path('EXPORTS_DIR'))
            if not export_dir.exists():
                return []
            
            history = []
            for file_path in export_dir.glob('*.csv'):
                try:
                    stat = file_path.stat()
                    history.append({
                        'filename': file_path.name,
                        'file_path': str(file_path),
                        'size': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'created_time': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                    })
                except Exception as e:
                    self.logger.warning(f"ファイル情報取得エラー {file_path}: {e}")
                    continue
            
            # 更新日時で降順ソート
            history.sort(key=lambda x: x['modified_time'], reverse=True)
            return history
            
        except Exception as e:
            self.logger.error(f"エクスポート履歴取得エラー: {e}")
            return []
    
    def cleanup_old_exports(self, days_to_keep: int = 30) -> int:
        """古いエクスポートファイルのクリーンアップ"""
        try:
            export_dir = Path(self.config.get_path('EXPORTS_DIR'))
            if not export_dir.exists():
                return 0
            
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for file_path in export_dir.glob('*.csv'):
                try:
                    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if modified_time < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        self.logger.debug(f"古いエクスポートファイルを削除: {file_path}")
                        
                except Exception as e:
                    self.logger.warning(f"ファイル削除エラー {file_path}: {e}")
                    continue
            
            if deleted_count > 0:
                self.logger.info(f"{deleted_count}個の古いエクスポートファイルを削除しました")
            
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"エクスポートファイルクリーンアップエラー: {e}")
            return 0