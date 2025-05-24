"""プロジェクト一覧表示コンポーネント"""

import customtkinter as ctk
from typing import List, Dict, Any, Callable, Optional

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.ui.base_ui_component import BaseUIComponent
from ProjectManager.src.ui.project_card import ProjectCard


class ProjectListView(BaseUIComponent):
    """プロジェクト一覧表示コンポーネント"""
    
    def __init__(self, parent: ctk.CTkFrame, db_manager, 
                 on_select: Callable[[Dict[str, Any]], None],
                 on_edit: Callable[[int], None],
                 on_delete: Callable[[int], None]):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            db_manager: データベースマネージャー
            on_select: プロジェクト選択時のコールバック
            on_edit: プロジェクト編集時のコールバック
            on_delete: プロジェクト削除時のコールバック
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.parent = parent
        self.db_manager = db_manager
        self.on_select = on_select
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        # 現在のプロジェクトリスト
        self.projects = []
        
        # 選択中のプロジェクト
        self.selected_project = None
        
        # プロジェクトカードのリスト
        self.project_cards = []
        
        # フレームの初期化
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """UIのセットアップ"""
        # スクロール可能なフレーム
        self.frame = self.create_scrollable_frame(
            self.parent,
            fg_color=self.colors.BACKGROUND
        )
    
    def update_projects(self, projects: List[Dict[str, Any]]) -> None:
        """
        プロジェクト一覧の更新
        
        Args:
            projects: プロジェクトリスト
        """
        # プロジェクトリストを更新
        self.projects = projects
        
        # 既存のカードをクリア
        self.clear_frame(self.frame)
        self.project_cards = []
        
        # プロジェクトがない場合のメッセージ
        if not self.projects:
            self._show_no_projects_message()
            return
        
        # 各プロジェクトのカードを作成
        for project in self.projects:
            self._create_project_card(project)
    
    def _show_no_projects_message(self) -> None:
        """プロジェクトがない場合のメッセージを表示"""
        message_frame = self.create_frame(self.frame)
        message_frame.pack(fill="x", padx=10, pady=10)
        
        message = self.create_label(
            message_frame,
            text="プロジェクトが存在しません。\n新規プロジェクト作成ボタンからプロジェクトを作成してください。",
            text_color=self.colors.TEXT_SECONDARY
        )
        message.pack(pady=20)
    
    def _create_project_card(self, project: Dict[str, Any]) -> None:
        """
        プロジェクトカードの作成
        
        Args:
            project: プロジェクトデータ
        """
        # プロジェクトカードを作成
        card = ProjectCard(
            self.frame, 
            project, 
            self._on_card_select,
            self.on_edit,
            self.on_delete,
            is_selected=self.selected_project and self.selected_project['project_id'] == project['project_id']
        )
        
        # カードを追加
        self.project_cards.append(card)
    
    def _on_card_select(self, project: Dict[str, Any]) -> None:
        """
        カード選択時の処理
        
        Args:
            project: 選択されたプロジェクト
        """
        # 選択状態を更新
        self.selected_project = project
        
        # カードの選択状態を更新
        for card in self.project_cards:
            card.set_selected(card.project['project_id'] == project['project_id'])
        
        # 親コンポーネントに通知
        if self.on_select:
            self.on_select(project)
    
    def get_selected_project(self) -> Optional[Dict[str, Any]]:
        """
        選択中のプロジェクトを取得
        
        Returns:
            Optional[Dict[str, Any]]: 選択中のプロジェクト
        """
        return self.selected_project