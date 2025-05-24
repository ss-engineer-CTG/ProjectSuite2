"""ガントチャートファイルの検出と管理を行うモジュール"""

import logging
import traceback
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Any

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.file_utils import FileUtils
from ProjectManager.src.core.error_handler import FileError


class GanttChartManager:
    """ガントチャートファイル管理サービス"""
    
    def __init__(self, db_manager):
        """
        初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        self.db_manager = db_manager
        self.logger = get_logger(__name__)
        self.path_manager = PathManager()
        self.file_utils = FileUtils()
    
    def update_ganttchart_paths(self) -> Dict[str, int]:
        """
        全プロジェクトのガントチャートパスを更新
        
        Returns:
            Dict[str, int]: 処理結果の統計情報
        """
        stats = {
            'total': 0,        # 処理対象の総プロジェクト数
            'updated': 0,      # パス更新に成功したプロジェクト数
            'not_found': 0,    # ガントチャートが見つからなかったプロジェクト数
            'error': 0         # エラーが発生したプロジェクト数
        }
        
        try:
            # 全プロジェクトのパスを取得
            all_projects = self.db_manager.get_all_projects()
            stats['total'] = len(all_projects)
            
            for project in all_projects:
                try:
                    project_path = project.get('project_path')
                    if not project_path or not Path(project_path).exists():
                        self.logger.warning(f"プロジェクトパスが無効です: {project['project_name']}")
                        stats['not_found'] += 1
                        continue
                    
                    # ガントチャートファイルを検索
                    gantt_path = self._find_ganttchart(Path(project_path))
                    
                    if gantt_path:
                        # パスをデータベースに保存
                        self._update_ganttchart_path(
                            project['project_id'],
                            str(gantt_path)
                        )
                        stats['updated'] += 1
                        self.logger.info(
                            f"ガントチャートパスを更新しました: {project['project_name']}"
                        )
                    else:
                        stats['not_found'] += 1
                        self.logger.warning(
                            f"ガントチャートが見つかりません: {project['project_name']}"
                        )
                
                except Exception as e:
                    stats['error'] += 1
                    self.logger.error(
                        f"プロジェクト '{project['project_name']}' の処理中にエラー: {e}\n"
                        f"{traceback.format_exc()}"
                    )
            
            return stats
            
        except Exception as e:
            self.logger.error(f"ガントチャートパス更新処理でエラー: {e}\n{traceback.format_exc()}")
            raise
    
    def _find_ganttchart(self, project_path: Path) -> Optional[Path]:
        """
        プロジェクトフォルダ内のガントチャートファイルを検索
        
        Args:
            project_path: プロジェクトフォルダのパス
            
        Returns:
            Optional[Path]: ガントチャートファイルのパス。見つからない場合はNone
        """
        try:
            # 「工程表」を含むフォルダを検索
            process_folders = []
            for folder in project_path.rglob('*'):
                if folder.is_dir() and '工程表' in folder.name:
                    process_folders.append(folder)
            
            # 各フォルダ内でガントチャートファイルを検索
            for folder in process_folders:
                for file in folder.glob('*.xlsm'):
                    if '工程表作成補助アプリ' in file.name:
                        return file
                        
            return None
            
        except Exception as e:
            self.logger.error(f"ガントチャートファイルの検索でエラー: {e}")
            return None
    
    def _update_ganttchart_path(self, project_id: int, gantt_path: str) -> None:
        """
        プロジェクトのガントチャートパスを更新
        
        Args:
            project_id: プロジェクトID
            gantt_path: ガントチャートファイルのパス
        """
        query = 'UPDATE projects SET ganttchart_path = ? WHERE project_id = ?'
        self.db_manager.execute_update(query, (gantt_path, project_id))
    
    def get_ganttchart_path(self, project_id: int) -> Optional[str]:
        """
        プロジェクトのガントチャートパスを取得
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            Optional[str]: ガントチャートファイルのパス。存在しない場合はNone
        """
        project = self.db_manager.get_project(project_id)
        if not project or not project.get('ganttchart_path'):
            return None
        
        gantt_path = project['ganttchart_path']
        if not Path(gantt_path).exists():
            self.logger.warning(f"ガントチャートファイルが存在しません: {gantt_path}")
            return None
        
        return gantt_path
    
    def open_ganttchart(self, project_id: int) -> bool:
        """
        ガントチャートファイルを開く
        
        Args:
            project_id: プロジェクトID
            
        Returns:
            bool: 成功した場合はTrue
        """
        gantt_path = self.get_ganttchart_path(project_id)
        if not gantt_path:
            self.logger.warning(f"開けるガントチャートファイルがありません: プロジェクトID {project_id}")
            return False
        
        try:
            # OSに依存しない方法でファイルを開く
            if os.name == 'nt':  # Windows
                os.startfile(gantt_path)
            else:  # macOS, Linux
                subprocess.run(['open' if os.name == 'posix' else 'xdg-open', gantt_path])
            
            self.logger.info(f"ガントチャートファイルを開きました: {gantt_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"ガントチャートファイルを開けません: {gantt_path}, {e}")
            return False