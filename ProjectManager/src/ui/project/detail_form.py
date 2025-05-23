"""詳細プロジェクト作成フォーム"""

import customtkinter as ctk 
from typing import Dict, Any
from datetime import datetime

from ProjectManager.src.ui.project.base import BaseProjectForm
from ProjectManager.src.core.master_data import MasterDataManager
from ProjectManager.src.core.log_manager import get_logger

class DetailProjectForm(BaseProjectForm):
    """詳細プロジェクト作成フォーム"""
    
    def __init__(self, db_manager):
        """
        初期化
        
        Args:
            db_manager: データベースマネージャー
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.db_manager = db_manager
        
        # マスターデータマネージャーの初期化
        try:
            self.master_data = MasterDataManager()
        except Exception as e:
            self.error_handler.handle_error(e, "初期化エラー")
            raise
        
        # 現在の選択値を保持
        self.current_selection = {
            'division': None,
            'factory': None,
            'process': None,
            'line': None
        }
        
        # ウィンドウの作成
        self.window = ctk.CTk()
        self.window.title("プロジェクト詳細情報入力")
        self.setup_window()
        self.setup_gui()
        self.load_default_values()

    def setup_window(self):
        """ウィンドウの設定"""
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = int(screen_width * 0.5)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(fg_color=self.colors.BACKGROUND)

    def setup_gui(self):
        """GUIの構築"""
        main_frame = self.create_frame(
            self.window,
            fg_color=self.colors.BACKGROUND
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # スクロール可能なフレーム
        self.scroll_frame = self.create_scrollable_frame(
            main_frame,
            label_text="プロジェクト詳細情報"
        )
        self.scroll_frame.pack(fill="both", expand=True)
        
        # 基本情報セクション
        self._create_section_label(self.scroll_frame, "基本情報")
        self._create_input_field(self.scroll_frame, "プロジェクト名", True, "project_name", 
                               validator=self._validate_project_name)
        self._create_input_field(self.scroll_frame, "開始日", True, "start_date", 
                               validator=self._validate_date)
        self._create_combo_field(
            self.scroll_frame, "ステータス", "status", 
            ["進行中", "完了", "中止"], True
        )
        
        # 担当者情報セクション
        self._create_section_label(self.scroll_frame, "担当者情報")
        self._create_input_field(self.scroll_frame, "担当者", True, "manager")
        self._create_input_field(self.scroll_frame, "確認者", True, "reviewer")
        self._create_input_field(self.scroll_frame, "承認者", True, "approver")
        
        # 製造ライン情報セクション
        self._create_section_label(self.scroll_frame, "製造ライン情報")
        self._create_manufacturing_fields()
        
        # ボタンフレーム
        self._create_button_frame(main_frame)

    def _create_manufacturing_fields(self):
        """製造ライン関連フィールドの作成"""
        # 事業部選択
        divisions = self.master_data.get_divisions()
        values = ['未選択'] + [f"{d['name']} ({d['code']})" for d in divisions]
        self._create_combo_field(
            self.scroll_frame, "事業部", "division", 
            values, False, self._on_division_change
        )
        
        # 工場選択
        self._create_combo_field(
            self.scroll_frame, "工場", "factory", 
            ['未選択'], False, self._on_factory_change
        )
        
        # 工程選択
        self._create_combo_field(
            self.scroll_frame, "工程", "process", 
            ['未選択'], False, self._on_process_change
        )
        
        # ライン選択
        self._create_combo_field(
            self.scroll_frame, "ライン", "line", 
            ['未選択'], False, self._on_line_change
        )

    def _create_button_frame(self, parent):
        """ボタンフレームの作成"""
        button_frame = self.create_frame(parent)
        button_frame.pack(fill="x", pady=(20, 0))
        
        save_button = self.create_button(
            button_frame,
            text="保存",
            command=self.save
        )
        save_button.pack(side="right", padx=5)
        
        cancel_button = self.create_danger_button(
            button_frame,
            text="キャンセル",
            command=self.window.destroy
        )
        cancel_button.pack(side="right", padx=5)
        
        # デフォルト値として保存するボタンを追加
        save_default_button = self.create_button(
            button_frame,
            text="デフォルトとして保存",
            command=self.save_as_default
        )
        save_default_button.pack(side="left", padx=5)

    def _on_division_change(self, event=None):
        """事業部選択時の処理"""
        selected = self.division.get()
        if selected == '未選択':
            self.current_selection['division'] = None
        else:
            self.current_selection['division'] = selected.split('(')[1].rstrip(')')
        self._update_factory_options()
        self._update_process_options()
        self._update_line_options()

    def _on_factory_change(self, event=None):
        """工場選択時の処理"""
        selected = self.factory.get()
        if selected == '未選択':
            self.current_selection['factory'] = None
        else:
            self.current_selection['factory'] = selected.split('(')[1].rstrip(')')
        self._update_process_options()
        self._update_line_options()

    def _on_process_change(self, event=None):
        """工程選択時の処理"""
        selected = self.process.get()
        if selected == '未選択':
            self.current_selection['process'] = None
        else:
            self.current_selection['process'] = selected.split('(')[1].rstrip(')')
        self._update_line_options()

    def _on_line_change(self, event=None):
        """ライン選択時の処理"""
        selected = self.line.get()
        if selected == '未選択':
            self.current_selection['line'] = None
        else:
            self.current_selection['line'] = selected.split('(')[1].rstrip(')')

    def _update_factory_options(self):
        """工場の選択肢を更新"""
        factories = self.master_data.get_factories(self.current_selection['division'])
        values = ['未選択'] + [f"{f['name']} ({f['code']})" for f in factories]
        self.factory.configure(values=values)
        self.factory.set('未選択')

    def _update_process_options(self):
        """工程の選択肢を更新"""
        processes = self.master_data.get_processes(
            self.current_selection['division'],
            self.current_selection['factory']
        )
        values = ['未選択'] + [f"{p['name']} ({p['code']})" for p in processes]
        self.process.configure(values=values)
        self.process.set('未選択')

    def _update_line_options(self):
        """ラインの選択肢を更新"""
        lines = self.master_data.get_lines(
            self.current_selection['division'],
            self.current_selection['factory'],
            self.current_selection['process']
        )
        values = ['未選択'] + [f"{l['name']} ({l['code']})" for l in lines]
        self.line.configure(values=values)
        self.line.set('未選択')
    
    def save_as_default(self):
        """現在の値をデフォルトとして保存"""
        try:
            # 現在の入力値を取得
            values = {
                'project_name': self.project_name.get().strip(),
                'start_date': self.start_date.get().strip(),
                'status': self.status.get().strip(),
                'manager': self.manager.get().strip(),
                'reviewer': self.reviewer.get().strip(),
                'approver': self.approver.get().strip(),
                'division': self.current_selection['division'],
                'factory': self.current_selection['factory'],
                'process': self.current_selection['process'],
                'line': self.current_selection['line']
            }
            
            # 各設定を更新
            for key, value in values.items():
                if value is not None:  # None値は保存しない
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
                'status': self.status.get().strip(),
                'manager': self.manager.get().strip(),
                'reviewer': self.reviewer.get().strip(),
                'approver': self.approver.get().strip(),
                'division': self.current_selection['division'],
                'factory': self.current_selection['factory'],
                'process': self.current_selection['process'],
                'line': self.current_selection['line']
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
                    errors.append(f"{label}を入力してください")
            
            if errors:
                self.error_handler.show_error_dialog(
                    "入力エラー",
                    "\n".join(errors),
                    self.window
                )
                return
            
            # 保存処理
            self.db_manager.insert_project(values)
            
            self.error_handler.show_info_dialog(
                "成功",
                "プロジェクトを保存しました。",
                self.window
            )
            
            self.window.destroy()
            
        except Exception as e:
            self.error_handler.handle_error(e, "保存エラー", self.window)

    def run(self):
        """アプリケーションの実行"""
        self.window.mainloop()