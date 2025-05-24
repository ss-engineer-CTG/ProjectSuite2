"""クイックプロジェクト作成・編集フォーム"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from pathlib import Path

from ProjectManager.src.ui.project.base import BaseProjectForm
from ProjectManager.src.core.log_manager import get_logger

class QuickProjectForm(BaseProjectForm):
    """クイックプロジェクト作成・編集フォーム"""
    
    def __init__(self, parent: ctk.CTk, 
                 db_manager,
                 callback: Optional[Callable] = None,
                 edit_mode: bool = False,
                 project_data: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            db_manager: データベースマネージャー
            callback: 完了時のコールバック関数
            edit_mode: 編集モードかどうか
            project_data: 編集対象のプロジェクトデータ
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.parent = parent
        self.db_manager = db_manager
        self.callback = callback
        self.edit_mode = edit_mode
        self.project_data = project_data
        
        # ウィンドウの作成
        self.window = ctk.CTkToplevel(parent)
        self.window.title("プロジェクト編集" if edit_mode else "新規プロジェクト作成")
        self.window.transient(parent)
        self.window.grab_set()
        
        # ウィンドウサイズと位置の設定
        window_width = int(parent.winfo_width() * 0.8)
        window_height = int(parent.winfo_height() * 0.8)
        x = parent.winfo_x() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.setup_gui()
        
        # データの設定
        if edit_mode and project_data:
            self.set_project_data(project_data)
        else:
            self.load_default_values()
            # 新規作成時はステータスを「進行中」に設定
            if hasattr(self, 'status'):
                self.status.set("進行中")

    def setup_gui(self):
        """GUIの構築"""
        main_frame = self.create_frame(
            self.window,
            fg_color=self.colors.BACKGROUND
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # スクロール可能なフレーム
        scroll_frame = self.create_scrollable_frame(main_frame)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # プロジェクト基本情報
        self._create_section_label(scroll_frame, "プロジェクト基本情報")
        self._create_input_field(scroll_frame, "プロジェクト名", True, "project_name", 
                               validator=self._validate_project_name)
        self._create_input_field(scroll_frame, "開始日", True, "start_date", 
                               validator=self._validate_date)
        
        # 開始日に今日の日付を設定
        self.start_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        self._create_combo_field(scroll_frame, "ステータス", "status", 
                               ["進行中", "完了", "中止"], True)
        
        # 担当者情報
        self._create_section_label(scroll_frame, "担当者情報")
        self._create_input_field(scroll_frame, "担当者", True, "manager")
        self._create_input_field(scroll_frame, "確認者", True, "reviewer")
        self._create_input_field(scroll_frame, "承認者", True, "approver")
        
        # 製造ライン情報
        self._create_section_label(scroll_frame, "製造ライン情報")
        self._create_input_field(scroll_frame, "事業部", False, "division", "事業部コードを入力")
        self._create_input_field(scroll_frame, "工場", False, "factory", "工場コードを入力")
        self._create_input_field(scroll_frame, "工程", False, "process", "工程コードを入力")
        self._create_input_field(scroll_frame, "line", False, "line", "ラインコードを入力")
        
        # ボタンフレーム
        button_frame = self.create_frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 0))
        
        # デフォルト値として保存するボタンを追加
        save_default_button = self.create_button(
            button_frame,
            text="デフォルトとして保存",
            command=self.save_as_default
        )
        save_default_button.pack(side="left", padx=5)
        
        # 保存ボタン
        save_button = self.create_button(
            button_frame,
            text="保存",
            command=self.save
        )
        save_button.pack(side="right", padx=5)
        
        # キャンセルボタン
        cancel_button = self.create_danger_button(
            button_frame,
            text="キャンセル",
            command=self.cancel
        )
        cancel_button.pack(side="right", padx=5)

    def set_project_data(self, data: Dict[str, Any]):
        """プロジェクトデータを入力フィールドに設定"""
        fields = ['project_name', 'start_date', 'manager', 'reviewer', 'approver', 
                 'status', 'division', 'factory', 'process', 'line']
        for field in fields:
            if hasattr(self, field) and field in data:
                widget = getattr(self, field)
                value = str(data[field]) if data[field] is not None else ""
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(value)
                else:
                    widget.delete(0, 'end')
                    widget.insert(0, value)
    
    def save_as_default(self):
        """現在の値をデフォルトとして保存"""
        try:
            # 現在の入力値を取得
            values = {
                'project_name': self.project_name.get().strip(),
                'manager': self.manager.get().strip(),
                'reviewer': self.reviewer.get().strip(),
                'approver': self.approver.get().strip(),
                'division': self.division.get().strip(),
                'factory': self.factory.get().strip(),
                'process': self.process.get().strip(),
                'line': self.line.get().strip()
            }
            
            # 各設定を更新
            for key, value in values.items():
                if value:  # 空の値は保存しない
                    self.config_manager.set_setting('defaults', key, value)
            
            self.error_handler.show_info_dialog(
                "成功",
                "現在の設定をデフォルト値として保存しました。",
                self.window
            )
            
        except Exception as e:
            self.error_handler.handle_error(e, "設定エラー", self.window)

    def save(self):
        """保存処理"""
        try:
            values = {
                'project_name': self.project_name.get().strip(),
                'start_date': self.start_date.get().strip(),
                'manager': self.manager.get().strip(),
                'reviewer': self.reviewer.get().strip(),
                'approver': self.approver.get().strip(),
                'status': self.status.get().strip(),
                'division': self.division.get().strip(),
                'factory': self.factory.get().strip(),
                'process': self.process.get().strip(),
                'line': self.line.get().strip()
            }
            
            # 必須項目の確認
            required_fields = {
                'project_name': 'プロジェクト名',
                'start_date': '開始日',
                'manager': '担当者',
                'reviewer': '確認者',
                'approver': '承認者'
            }
            
            errors = []
            for field, label in required_fields.items():
                if not values[field]:
                    errors.append(f"{label}を入力してください。")
            
            if errors:
                self.error_handler.show_error_dialog(
                    "入力エラー",
                    "\n".join(errors),
                    self.window
                )
                return
            
            # 日付形式の検証
            try:
                datetime.strptime(values['start_date'], '%Y-%m-%d')
            except ValueError:
                self.error_handler.show_error_dialog(
                    "入力エラー",
                    "開始日の形式が正しくありません。\nYYYY-MM-DD形式で入力してください。",
                    self.window
                )
                return
            
            # 保存処理
            if self.edit_mode:
                self.db_manager.update_project(self.project_data['project_id'], values)
            else:
                self.db_manager.insert_project(values)
            
            # コールバック実行
            if self.callback:
                self.callback()
            
            # 画面を閉じる
            self.window.destroy()
            
        except Exception as e:
            self.error_handler.handle_error(e, "保存エラー", self.window)

    def cancel(self):
        """キャンセル処理"""
        self.window.destroy()
    
    def on_closing(self):
        """閉じる処理"""
        self.window.destroy()