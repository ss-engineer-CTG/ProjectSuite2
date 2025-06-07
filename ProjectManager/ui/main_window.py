"""
メインウィンドウ（ダッシュボード統合）
"""

import customtkinter as ctk
import logging
from typing import Dict, Any, Optional

from config import Config
from services import ProjectService, TaskService, ExportService
from models import Project
from .styles import Colors, Fonts, Sizes
from .forms import ProjectFormDialog, SettingsDialog, ExportDialog
from utils import ErrorHandler, ExternalApp

class MainWindow:
    """メインウィンドウクラス"""
    
    def __init__(self, config: Config, project_service: ProjectService, 
                 task_service: TaskService, export_service: ExportService):
        self.config = config
        self.project_service = project_service
        self.task_service = task_service
        self.export_service = export_service
        self.logger = logging.getLogger(__name__)
        
        # 状態管理
        self.selected_project = None
        self.current_filter = "進行中"
        self.project_list = []
        
        # CustomTkinterの設定
        ctk.set_appearance_mode("dark")
        
        # ウィンドウの初期化
        self.window = ctk.CTk()
        self._setup_window()
        self._setup_gui()
        
        # 初期データの読み込み
        self.refresh_projects()
    
    def _setup_window(self):
        """ウィンドウの設定"""
        self.window.title("プロジェクト管理ダッシュボード")
        self.window.configure(fg_color=Colors.BACKGROUND)
        
        # ウィンドウサイズの設定
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = max(int(screen_width * 0.8), Sizes.MIN_WINDOW_WIDTH)
        window_height = max(int(screen_height * 0.8), Sizes.MIN_WINDOW_HEIGHT)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _setup_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ctk.CTkFrame(self.window, fg_color=Colors.BACKGROUND)
        main_frame.pack(fill="both", expand=True, 
                       padx=Sizes.PADDING_LARGE, pady=Sizes.PADDING_LARGE)
        
        # ヘッダー部分
        self._create_header(main_frame)
        
        # 選択中プロジェクト表示
        self._create_selection_display(main_frame)
        
        # プロジェクト一覧
        self._create_project_list(main_frame)
    
    def _create_header(self, parent):
        """ヘッダー部分の作成"""
        header_frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG)
        header_frame.pack(fill="x", pady=(0, Sizes.PADDING_LARGE))
        
        # タイトル
        title_label = ctk.CTkLabel(
            header_frame,
            text="プロジェクト一覧",
            font=Fonts.TITLE,
            text_color=Colors.TEXT_PRIMARY
        )
        title_label.pack(side="left", pady=Sizes.PADDING_MEDIUM, 
                        padx=Sizes.PADDING_MEDIUM)
        
        # 右側のコントロール
        right_frame = ctk.CTkFrame(header_frame, fg_color=Colors.CARD_BG)
        right_frame.pack(side="right", pady=Sizes.PADDING_MEDIUM, 
                        padx=Sizes.PADDING_MEDIUM)
        
        # 新規プロジェクト作成ボタン
        create_button = ctk.CTkButton(
            right_frame,
            text="新規プロジェクト作成",
            command=self.show_create_project_dialog,
            font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_PRIMARY,
            text_color=Colors.BUTTON_TEXT,
            hover_color=Colors.BUTTON_HOVER,
            width=Sizes.BUTTON_WIDTH_LARGE
        )
        create_button.pack(side="right", padx=Sizes.PADDING_SMALL)
        
        # 機能ボタン群
        self._create_control_buttons(right_frame)
    
    def _create_control_buttons(self, parent):
        """コントロールボタンの作成"""
        control_frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG)
        control_frame.pack(side="right", pady=Sizes.PADDING_MEDIUM, 
                          padx=Sizes.PADDING_MEDIUM)
        
        # フィルター
        filter_label = ctk.CTkLabel(
            control_frame,
            text="フィルター:",
            font=Fonts.DEFAULT,
            text_color=Colors.TEXT_PRIMARY
        )
        filter_label.pack(side="left", padx=(0, Sizes.PADDING_SMALL))
        
        self.filter_combo = ctk.CTkComboBox(
            control_frame,
            values=["進行中", "全て"],
            command=self.on_filter_change,
            state="readonly",
            font=Fonts.DEFAULT,
            fg_color=Colors.INPUT_BG,
            text_color=Colors.INPUT_TEXT,
            border_color=Colors.INPUT_BORDER,
            width=120
        )
        self.filter_combo.set('進行中')
        self.filter_combo.pack(side="left", padx=Sizes.PADDING_SMALL)
        
        # 機能ボタン
        buttons = [
            ("データ更新", self.update_data),
            ("エクスポート", self.show_export_dialog),
            ("設定", self.show_settings_dialog),
            ("ダッシュボード", self.launch_dashboard),
        ]
        
        for text, command in buttons:
            button = ctk.CTkButton(
                control_frame,
                text=text,
                command=command,
                font=Fonts.BUTTON,
                fg_color=Colors.BUTTON_PRIMARY,
                text_color=Colors.BUTTON_TEXT,
                hover_color=Colors.BUTTON_HOVER,
                width=Sizes.BUTTON_WIDTH_MEDIUM
            )
            button.pack(side="left", padx=Sizes.PADDING_SMALL)
    
    def _create_selection_display(self, parent):
        """選択中プロジェクト表示の作成"""
        self.selection_frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG, height=80)
        self.selection_frame.pack(fill="x", pady=(0, Sizes.PADDING_LARGE))
        self.selection_frame.pack_propagate(False)
        
        # タイトル
        title_label = ctk.CTkLabel(
            self.selection_frame,
            text="選択中のプロジェクト",
            font=Fonts.HEADER,
            text_color=Colors.TEXT_PRIMARY
        )
        title_label.pack(side="left", pady=Sizes.PADDING_MEDIUM, 
                        padx=Sizes.PADDING_MEDIUM)
        
        # 選択中プロジェクト情報
        self.selection_info = ctk.CTkLabel(
            self.selection_frame,
            text="プロジェクトが選択されていません",
            font=Fonts.DEFAULT,
            text_color=Colors.TEXT_SECONDARY
        )
        self.selection_info.pack(side="left", pady=Sizes.PADDING_MEDIUM, 
                                padx=Sizes.PADDING_MEDIUM)
        
        # アクションボタン
        self.action_frame = ctk.CTkFrame(self.selection_frame, fg_color=Colors.CARD_BG)
        self.action_frame.pack(side="right", pady=Sizes.PADDING_MEDIUM, 
                              padx=Sizes.PADDING_MEDIUM)
        
        self.doc_process_button = ctk.CTkButton(
            self.action_frame,
            text="ドキュメント処理",
            command=self.show_document_processor,
            font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_PRIMARY,
            text_color=Colors.BUTTON_TEXT,
            hover_color=Colors.BUTTON_HOVER,
            width=Sizes.BUTTON_WIDTH_LARGE,
            state="disabled"
        )
        self.doc_process_button.pack(side="right", padx=Sizes.PADDING_SMALL)
    
    def _create_project_list(self, parent):
        """プロジェクト一覧の作成"""
        self.projects_frame = ctk.CTkScrollableFrame(
            parent,
            label_text="",
            fg_color=Colors.BACKGROUND
        )
        self.projects_frame.pack(fill="both", expand=True)
    
    def _create_project_card(self, project: Dict[str, Any]):
        """プロジェクトカードの作成"""
        is_selected = (self.selected_project and 
                      self.selected_project['project_id'] == project['project_id'])
        
        card = ctk.CTkFrame(
            self.projects_frame,
            fg_color=Colors.CARD_BG,
            border_color=Colors.BUTTON_PRIMARY if is_selected else Colors.FRAME_BORDER,
            border_width=2 if is_selected else 1
        )
        card.pack(fill="x", padx=Sizes.PADDING_MEDIUM, pady=Sizes.PADDING_SMALL)
        
        # カードクリックイベント
        card.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # 左側情報エリア
        info_frame = ctk.CTkFrame(card, fg_color=Colors.CARD_BG)
        info_frame.pack(side="left", fill="both", expand=True, 
                       padx=Sizes.PADDING_MEDIUM, pady=Sizes.PADDING_MEDIUM)
        info_frame.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # プロジェクト名
        name_label = ctk.CTkLabel(
            info_frame,
            text=f"プロジェクト名: {project['project_name']}",
            font=Fonts.HEADER,
            text_color=Colors.TEXT_PRIMARY,
            anchor="w"
        )
        name_label.pack(fill="x")
        name_label.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # 詳細情報
        info_parts = [
            f"開始日: {project['start_date']}",
            f"担当者: {project['manager']}",
            f"確認者: {project['reviewer']}",
            f"承認者: {project['approver']}"
        ]
        
        # 製造ライン情報
        line_parts = []
        for field, label in [('division', '事業部'), ('factory', '工場'), 
                           ('process', '工程'), ('line', 'ライン')]:
            value = project.get(field)
            line_parts.append(f"{label}: {value or '未設定'}")
        
        all_info = " | ".join(info_parts + line_parts)
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=all_info,
            font=Fonts.DEFAULT,
            text_color=Colors.TEXT_SECONDARY,
            anchor="w"
        )
        details_label.pack(fill="x", pady=(Sizes.PADDING_SMALL, 0))
        details_label.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # 右側ステータス・ボタンエリア
        self._create_card_actions(card, project)
    
    def _create_card_actions(self, card, project):
        """カードアクション部分の作成"""
        right_frame = ctk.CTkFrame(card, fg_color=Colors.CARD_BG)
        right_frame.pack(side="right", padx=Sizes.PADDING_MEDIUM, 
                        pady=Sizes.PADDING_MEDIUM)
        
        # ステータスバッジ
        status = project.get('status', '進行中')
        status_frame = ctk.CTkFrame(right_frame, fg_color=Colors.get_status_color(status))
        status_frame.pack(pady=(0, Sizes.PADDING_SMALL))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text=status,
            text_color=Colors.BUTTON_TEXT,
            font=Fonts.SMALL
        )
        status_label.pack(padx=8, pady=4)
        
        # アクションボタン
        button_frame = ctk.CTkFrame(right_frame, fg_color=Colors.CARD_BG)
        button_frame.pack()
        
        edit_button = ctk.CTkButton(
            button_frame,
            text="編集",
            command=lambda: self.edit_project(project['project_id']),
            font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_PRIMARY,
            text_color=Colors.BUTTON_TEXT,
            hover_color=Colors.BUTTON_HOVER,
            width=Sizes.BUTTON_WIDTH_SMALL
        )
        edit_button.pack(pady=(0, Sizes.PADDING_SMALL))
        
        delete_button = ctk.CTkButton(
            button_frame,
            text="削除",
            command=lambda: self.delete_project(project['project_id']),
            font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_DANGER,
            hover_color='#CC2F26',
            width=Sizes.BUTTON_WIDTH_SMALL
        )
        delete_button.pack()
    
    def select_project(self, project: Dict[str, Any]):
        """プロジェクトの選択"""
        self.selected_project = project
        
        if project:
            info_text = (
                f"プロジェクト名: {project['project_name']} | "
                f"担当者: {project['manager']} | "
                f"状態: {project['status']}"
            )
            self.selection_info.configure(text=info_text)
            self.doc_process_button.configure(state="normal")
        else:
            self.selection_info.configure(text="プロジェクトが選択されていません")
            self.doc_process_button.configure(state="disabled")
        
        self.refresh_projects()
    
    def refresh_projects(self):
        """プロジェクト一覧の更新"""
        try:
            # 既存の内容をクリア
            for widget in self.projects_frame.winfo_children():
                widget.destroy()
            
            # プロジェクト一覧を取得
            self.project_list = self.project_service.get_all_projects(self.current_filter)
            
            if not self.project_list:
                no_projects_label = ctk.CTkLabel(
                    self.projects_frame,
                    text="該当するプロジェクトが存在しません。\n新規プロジェクト作成ボタンからプロジェクトを作成してください。",
                    font=Fonts.DEFAULT,
                    text_color=Colors.TEXT_SECONDARY
                )
                no_projects_label.pack(pady=Sizes.PADDING_LARGE)
                return
            
            # 各プロジェクトのカードを作成
            for project in self.project_list:
                self._create_project_card(project)
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト一覧更新")
    
    def on_filter_change(self, choice: str):
        """フィルター変更時の処理"""
        self.current_filter = choice
        self.refresh_projects()
    
    def show_create_project_dialog(self):
        """新規プロジェクト作成ダイアログの表示"""
        dialog = ProjectFormDialog(
            self.window, self.config, self.project_service, 
            callback=self.on_project_updated
        )
    
    def edit_project(self, project_id: int):
        """プロジェクト編集ダイアログの表示"""
        project_data = self.project_service.get_project(project_id)
        if not project_data:
            ErrorHandler.show_warning("プロジェクトデータの取得に失敗しました")
            return
        
        dialog = ProjectFormDialog(
            self.window, self.config, self.project_service,
            edit_mode=True, project_data=project_data,
            callback=self.on_project_updated
        )
    
    def delete_project(self, project_id: int):
        """プロジェクトの削除"""
        if self.project_service.delete_project(project_id):
            if (self.selected_project and 
                self.selected_project['project_id'] == project_id):
                self.select_project(None)
            self.refresh_projects()
    
    def on_project_updated(self):
        """プロジェクト更新後のコールバック"""
        self.refresh_projects()
    
    def update_data(self):
        """データの更新"""
        try:
            if self.task_service.load_all_tasks():
                ErrorHandler.show_info("データ更新が完了しました")
                self.refresh_projects()
            else:
                ErrorHandler.show_warning("データ更新に失敗しました")
        except Exception as e:
            ErrorHandler.handle_error(e, "データ更新")
    
    def show_export_dialog(self):
        """エクスポートダイアログの表示"""
        dialog = ExportDialog(self.window, self.export_service)
    
    def show_settings_dialog(self):
        """設定ダイアログの表示"""
        dialog = SettingsDialog(self.window, self.config, self.on_settings_changed)
    
    def on_settings_changed(self):
        """設定変更後のコールバック"""
        ErrorHandler.show_info("設定を変更しました。変更を完全に適用するには、アプリケーションを再起動してください。")
    
    def show_document_processor(self):
        """ドキュメント処理ウィンドウの表示"""
        if not self.selected_project:
            ErrorHandler.show_warning("プロジェクトを選択してください")
            return
        
        ExternalApp.launch_document_processor(self.selected_project)
    
    def launch_dashboard(self):
        """外部ダッシュボードの起動"""
        ExternalApp.launch_project_dashboard()
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        try:
            self.logger.info("アプリケーションを終了します")
            self.window.quit()
            self.window.destroy()
        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")
    
    def run(self):
        """アプリケーションの実行"""
        try:
            self.window.mainloop()
        except Exception as e:
            ErrorHandler.handle_error(e, "アプリケーション実行")