"""プロジェクトカードコンポーネント"""

import customtkinter as ctk
from typing import Dict, Any, Callable, Optional

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.ui.base_ui_component import BaseUIComponent


class ProjectCard(BaseUIComponent):
    """プロジェクトカードコンポーネント"""
    
    def __init__(self, parent: ctk.CTkFrame, project: Dict[str, Any],
                 on_select: Callable[[Dict[str, Any]], None],
                 on_edit: Callable[[int], None],
                 on_delete: Callable[[int], None],
                 is_selected: bool = False):
        """
        初期化
        
        Args:
            parent: 親ウィジェット
            project: プロジェクトデータ
            on_select: 選択時のコールバック
            on_edit: 編集ボタンクリック時のコールバック
            on_delete: 削除ボタンクリック時のコールバック
            is_selected: 選択状態フラグ
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.parent = parent
        self.project = project
        self.on_select = on_select
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.is_selected = is_selected
        
        # カードのセットアップ
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """UIのセットアップ"""
        # カードフレーム
        self.card = self.create_frame(
            self.parent,
            border_width=1 if not self.is_selected else 2,
            border_color=self.colors.FRAME_BORDER if not self.is_selected else self.colors.BUTTON_PRIMARY
        )
        self.card.pack(fill="x", padx=10, pady=5)
        
        # イベントバインド
        self.card.bind('<Button-1>', self._on_click)
        
        # 左側の情報フレーム
        info_frame = self.create_frame(self.card)
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        info_frame.bind('<Button-1>', self._on_click)
        
        # 現在のステータスを取得
        current_status = self.project.get('status', '進行中')
        
        # ステータスバッジ
        status_frame = ctk.CTkFrame(
            info_frame,
            fg_color=self.colors.STATUS[current_status]
        )
        status_frame.pack(side="right", padx=5)
        status_frame.bind('<Button-1>', self._on_click)
        
        status_label = self.create_label(
            status_frame,
            text=current_status,
            text_color=self.colors.BUTTON_TEXT,
            font=('Meiryo', 10, 'bold')
        )
        status_label.pack(padx=8, pady=4)
        status_label.bind('<Button-1>', self._on_click)
        
        # プロジェクト名
        name_label = self.create_label(
            info_frame,
            text=f"プロジェクト名: {self.project['project_name']}",
            font=self.header_font
        )
        name_label.pack(fill="x")
        name_label.bind('<Button-1>', self._on_click)
        
        # NULL値の場合は "未設定" と表示する関数
        def get_display_value(value):
            return value if value is not None else "未設定"
        
        # 基本情報テキスト
        info_text = (
            f"開始日: {self.project['start_date']} | "
            f"担当者: {self.project['manager']} | "
            f"確認者: {self.project['reviewer']} | "
            f"承認者: {self.project['approver']} | "
            f"事業部: {get_display_value(self.project['division'])} | "
            f"工場: {get_display_value(self.project['factory'])} | "
            f"工程: {get_display_value(self.project['process'])} | "
            f"ライン: {get_display_value(self.project['line'])}"
        )
        
        details_label = self.create_label(
            info_frame,
            text=info_text,
            text_color=self.colors.TEXT_SECONDARY
        )
        details_label.pack(fill="x", pady=(5, 0))
        details_label.bind('<Button-1>', self._on_click)
        
        # 右側のボタンフレーム
        button_frame = self.create_frame(self.card)
        button_frame.pack(side="right", padx=10, pady=10)
        
        # 編集ボタン
        edit_button = self.create_button(
            button_frame,
            text="編集",
            command=self._on_edit
        )
        edit_button.pack(pady=(0, 5))
        
        # 削除ボタン
        delete_button = self.create_danger_button(
            button_frame,
            text="削除",
            command=self._on_delete
        )
        delete_button.pack()
    
    def _on_click(self, event) -> None:
        """
        カードクリック時の処理
        
        Args:
            event: イベントオブジェクト
        """
        if self.on_select:
            self.on_select(self.project)
    
    def _on_edit(self) -> None:
        """編集ボタンクリック時の処理"""
        if self.on_edit:
            self.on_edit(self.project['project_id'])
    
    def _on_delete(self) -> None:
        """削除ボタンクリック時の処理"""
        if self.on_delete:
            self.on_delete(self.project['project_id'])
    
    def set_selected(self, selected: bool) -> None:
        """
        選択状態の設定
        
        Args:
            selected: 選択状態
        """
        self.is_selected = selected
        
        # ボーダー設定を更新
        if selected:
            self.card.configure(
                border_width=2,
                border_color=self.colors.BUTTON_PRIMARY
            )
        else:
            self.card.configure(
                border_width=1,
                border_color=self.colors.FRAME_BORDER
            )