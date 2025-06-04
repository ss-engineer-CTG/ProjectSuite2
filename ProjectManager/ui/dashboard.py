"""
ダッシュボードGUI
KISS原則: シンプルなダッシュボード画面
DRY原則: UI共通処理の統合
"""

import customtkinter as ctk
import logging
from typing import Optional, Dict, Any, List

from core.unified_config import UnifiedConfig
from core.constants import AppConstants
from services.project_service import ProjectService
from services.task_service import TaskService
from services.export_service import ExportService
from .styles import ColorScheme, FontScheme, UIConstants
from .project_forms import ProjectFormDialog
from .dialogs import SettingsDialog, ExportDialog
from utils.error_handler import ErrorHandler
from integration.external_apps import ExternalAppLauncher

class DashboardGUI:
    """ダッシュボードメイン画面"""
    
    def __init__(self, db_manager, project_service: ProjectService):
        self.db_manager = db_manager
        self.project_service = project_service
        self.task_service = TaskService(db_manager)
        self.export_service = ExportService(db_manager)
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
        
        # 状態管理
        self.is_closing = False
        self.current_filter = "進行中"
        self.selected_project = None
        self.project_list = []
        
        # CustomTkinterの設定
        ctk.set_appearance_mode("dark")
        
        # メインウィンドウの初期化
        self.window = None
        self.initialize_window()
        
        # 子ダイアログの管理
        self.active_dialogs = []
        
        # 初期データの読み込み
        self.refresh_projects()
        
        self.logger.info("ダッシュボードGUIを初期化しました")
    
    def initialize_window(self):
        """メインウィンドウの初期化"""
        self.window = ctk.CTk()
        self.window.title(AppConstants.WINDOW_TITLE)
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.configure(fg_color=ColorScheme.BACKGROUND)
        
        # ウィンドウサイズの設定
        geometry = UIConstants.get_window_geometry(self.window)
        self.window.geometry(geometry)
        
        self.setup_gui()
    
    def setup_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ctk.CTkFrame(self.window, fg_color=ColorScheme.BACKGROUND)
        main_frame.pack(fill="both", expand=True, padx=UIConstants.PADDING_LARGE, 
                       pady=UIConstants.PADDING_LARGE)
        
        # ヘッダー部分
        self.create_header(main_frame)
        
        # 選択中プロジェクト表示
        self.create_selection_display(main_frame)
        
        # プロジェクト一覧
        self.create_project_list(main_frame)
    
    def create_header(self, parent):
        """ヘッダー部分の作成"""
        header_frame = ctk.CTkFrame(parent, fg_color=ColorScheme.CARD_BG)
        header_frame.pack(fill="x", pady=(0, UIConstants.PADDING_LARGE))
        
        # タイトル
        title_label = ctk.CTkLabel(
            header_frame,
            text="プロジェクト一覧",
            font=FontScheme.TITLE_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        title_label.pack(side="left", pady=UIConstants.PADDING_MEDIUM, 
                        padx=UIConstants.PADDING_MEDIUM)
        
        # 右側のコントロール
        right_frame = ctk.CTkFrame(header_frame, fg_color=ColorScheme.CARD_BG)
        right_frame.pack(side="right", pady=UIConstants.PADDING_MEDIUM, 
                        padx=UIConstants.PADDING_MEDIUM)
        
        # 新規プロジェクト作成ボタン
        create_button = ctk.CTkButton(
            right_frame,
            text="新規プロジェクト作成",
            command=self.show_create_project_dialog,
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_LARGE
        )
        create_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
        
        # フィルター・機能ボタンフレーム
        control_frame = ctk.CTkFrame(header_frame, fg_color=ColorScheme.CARD_BG)
        control_frame.pack(side="right", pady=UIConstants.PADDING_MEDIUM, 
                          padx=UIConstants.PADDING_MEDIUM)
        
        # フィルター
        filter_label = ctk.CTkLabel(
            control_frame,
            text="フィルター:",
            font=FontScheme.LABEL_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        filter_label.pack(side="left", padx=(0, UIConstants.PADDING_SMALL))
        
        self.filter_combo = ctk.CTkComboBox(
            control_frame,
            values=AppConstants.FILTER_OPTIONS,
            command=self.on_filter_change,
            state="readonly",
            font=FontScheme.DEFAULT_FONT,
            fg_color=ColorScheme.INPUT_BG,
            text_color=ColorScheme.INPUT_TEXT,
            border_color=ColorScheme.INPUT_BORDER,
            button_color=ColorScheme.BUTTON_PRIMARY,
            button_hover_color=ColorScheme.BUTTON_HOVER,
            dropdown_fg_color=ColorScheme.CARD_BG,
            width=120
        )
        self.filter_combo.set('進行中')
        self.filter_combo.pack(side="left", padx=UIConstants.PADDING_SMALL)
        
        # 機能ボタン群
        buttons = [
            ("データ更新", self.update_data),
            ("データエクスポート", self.show_export_dialog),
            ("設定", self.show_settings_dialog),
            ("ダッシュボード", self.launch_dashboard),
        ]
        
        for text, command in buttons:
            button = ctk.CTkButton(
                control_frame,
                text=text,
                command=command,
                font=FontScheme.BUTTON_FONT,
                fg_color=ColorScheme.BUTTON_PRIMARY,
                text_color=ColorScheme.BUTTON_TEXT,
                hover_color=ColorScheme.BUTTON_HOVER,
                width=UIConstants.BUTTON_WIDTH_MEDIUM
            )
            button.pack(side="left", padx=UIConstants.PADDING_SMALL)
    
    def create_selection_display(self, parent):
        """選択中プロジェクト表示の作成"""
        self.selection_frame = ctk.CTkFrame(parent, fg_color=ColorScheme.CARD_BG, height=80)
        self.selection_frame.pack(fill="x", pady=(0, UIConstants.PADDING_LARGE))
        self.selection_frame.pack_propagate(False)
        
        # タイトル
        title_label = ctk.CTkLabel(
            self.selection_frame,
            text="選択中のプロジェクト",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        title_label.pack(side="left", pady=UIConstants.PADDING_MEDIUM, 
                        padx=UIConstants.PADDING_MEDIUM)
        
        # 選択中プロジェクト情報
        self.selection_info = ctk.CTkLabel(
            self.selection_frame,
            text="プロジェクトが選択されていません",
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_SECONDARY
        )
        self.selection_info.pack(side="left", pady=UIConstants.PADDING_MEDIUM, 
                                padx=UIConstants.PADDING_MEDIUM)
        
        # 選択中プロジェクトのアクションボタン
        self.action_frame = ctk.CTkFrame(self.selection_frame, fg_color=ColorScheme.CARD_BG)
        self.action_frame.pack(side="right", pady=UIConstants.PADDING_MEDIUM, 
                              padx=UIConstants.PADDING_MEDIUM)
        
        self.doc_process_button = ctk.CTkButton(
            self.action_frame,
            text="ドキュメント処理",
            command=self.show_document_processor,
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_LARGE,
            state="disabled"
        )
        self.doc_process_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
    
    def create_project_list(self, parent):
        """プロジェクト一覧の作成"""
        self.projects_frame = ctk.CTkScrollableFrame(
            parent,
            label_text="",
            fg_color=ColorScheme.BACKGROUND,
            scrollbar_button_color=ColorScheme.SCROLLBAR_FG,
            scrollbar_button_hover_color=ColorScheme.get_hover_color(ColorScheme.SCROLLBAR_FG)
        )
        self.projects_frame.pack(fill="both", expand=True)
    
    def create_project_card(self, project: Dict[str, Any]):
        """プロジェクトカードの作成"""
        # カードフレーム
        is_selected = (self.selected_project and 
                      self.selected_project['project_id'] == project['project_id'])
        
        card = ctk.CTkFrame(
            self.projects_frame,
            fg_color=ColorScheme.CARD_BG,
            border_color=ColorScheme.BUTTON_PRIMARY if is_selected else ColorScheme.FRAME_BORDER,
            border_width=2 if is_selected else 1
        )
        card.pack(fill="x", padx=UIConstants.PADDING_MEDIUM, pady=UIConstants.PADDING_SMALL)
        
        # カードクリックイベント
        card.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # 左側情報エリア
        info_frame = ctk.CTkFrame(card, fg_color=ColorScheme.CARD_BG)
        info_frame.pack(side="left", fill="both", expand=True, 
                       padx=UIConstants.PADDING_MEDIUM, pady=UIConstants.PADDING_MEDIUM)
        info_frame.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # プロジェクト名
        name_label = ctk.CTkLabel(
            info_frame,
            text=f"プロジェクト名: {project['project_name']}",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY,
            anchor="w"
        )
        name_label.pack(fill="x")
        name_label.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # 基本情報
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
            if value:
                line_parts.append(f"{label}: {value}")
            else:
                line_parts.append(f"{label}: 未設定")
        
        all_info = " | ".join(info_parts + line_parts)
        
        details_label = ctk.CTkLabel(
            info_frame,
            text=all_info,
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_SECONDARY,
            anchor="w"
        )
        details_label.pack(fill="x", pady=(UIConstants.PADDING_SMALL, 0))
        details_label.bind('<Button-1>', lambda e, p=project: self.select_project(p))
        
        # 右側ステータス・ボタンエリア
        right_frame = ctk.CTkFrame(card, fg_color=ColorScheme.CARD_BG)
        right_frame.pack(side="right", padx=UIConstants.PADDING_MEDIUM, 
                        pady=UIConstants.PADDING_MEDIUM)
        
        # ステータスバッジ
        status = project.get('status', '進行中')
        status_frame = ctk.CTkFrame(right_frame, fg_color=ColorScheme.get_status_color(status))
        status_frame.pack(pady=(0, UIConstants.PADDING_SMALL))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text=status,
            text_color=ColorScheme.BUTTON_TEXT,
            font=FontScheme.get_font('small')
        )
        status_label.pack(padx=8, pady=4)
        
        # アクションボタン
        button_frame = ctk.CTkFrame(right_frame, fg_color=ColorScheme.CARD_BG)
        button_frame.pack()
        
        edit_button = ctk.CTkButton(
            button_frame,
            text="編集",
            command=lambda: self.edit_project(project['project_id']),
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_SMALL
        )
        edit_button.pack(pady=(0, UIConstants.PADDING_SMALL))
        
        delete_button = ctk.CTkButton(
            button_frame,
            text="削除",
            command=lambda: self.delete_project(project['project_id']),
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_DANGER,
            hover_color='#CC2F26',
            width=UIConstants.BUTTON_WIDTH_SMALL
        )
        delete_button.pack()
    
    def select_project(self, project: Dict[str, Any]):
        """プロジェクトの選択"""
        self.selected_project = project
        
        # 選択情報の更新
        if project:
            info_text = (
                f"プロジェクト名: {project['project_name']} | "
                f"担当者: {project['manager']} | "
                f"状態: {project['status']}"
            )
            self.selection_info.configure(text=info_text)
            
            # ドキュメント処理ボタンを有効化
            self.doc_process_button.configure(state="normal")
        else:
            self.selection_info.configure(text="プロジェクトが選択されていません")
            self.doc_process_button.configure(state="disabled")
        
        # プロジェクトカードの表示を更新
        self.refresh_projects()
    
    def refresh_projects(self):
        """プロジェクト一覧の更新"""
        if self.is_closing:
            return
        
        try:
            # 既存の内容をクリア
            for widget in self.projects_frame.winfo_children():
                widget.destroy()
            
            # プロジェクト一覧を取得
            self.project_list = self.project_service.get_all_projects(self.current_filter)
            
            if not self.project_list:
                # プロジェクトが存在しない場合
                message = ("該当するプロジェクトが存在しません。" if self.current_filter == "進行中" 
                          else "プロジェクトが存在しません。")
                
                no_projects_label = ctk.CTkLabel(
                    self.projects_frame,
                    text=f"{message}\n新規プロジェクト作成ボタンからプロジェクトを作成してください。",
                    font=FontScheme.DEFAULT_FONT,
                    text_color=ColorScheme.TEXT_SECONDARY
                )
                no_projects_label.pack(pady=UIConstants.PADDING_LARGE)
                return
            
            # 各プロジェクトのカードを作成
            for project in self.project_list:
                self.create_project_card(project)
            
            self.logger.debug(f"{len(self.project_list)}件のプロジェクトを表示")
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト一覧更新", show_dialog=False)
    
    def on_filter_change(self, choice: str):
        """フィルター変更時の処理"""
        self.current_filter = choice
        self.refresh_projects()
    
    def show_create_project_dialog(self):
        """新規プロジェクト作成ダイアログの表示"""
        dialog = ProjectFormDialog(self.window, self.project_service, 
                                 callback=self.on_project_updated)
        self.active_dialogs.append(dialog)
    
    def edit_project(self, project_id: int):
        """プロジェクト編集ダイアログの表示"""
        project_data = self.project_service.get_project(project_id)
        if not project_data:
            ErrorHandler.handle_warning("プロジェクトデータの取得に失敗しました", "プロジェクト編集")
            return
        
        dialog = ProjectFormDialog(self.window, self.project_service, 
                                 edit_mode=True, project_data=project_data,
                                 callback=self.on_project_updated)
        self.active_dialogs.append(dialog)
    
    def delete_project(self, project_id: int):
        """プロジェクトの削除"""
        if self.project_service.delete_project(project_id):
            # 削除したプロジェクトが選択中だった場合、選択を解除
            if (self.selected_project and 
                self.selected_project['project_id'] == project_id):
                self.select_project(None)
            
            self.refresh_projects()
    
    def on_project_updated(self):
        """プロジェクト更新後のコールバック"""
        self.refresh_projects()
        # アクティブなダイアログを除去
        self.active_dialogs = [d for d in self.active_dialogs if d.window.winfo_exists()]
    
    def update_data(self):
        """データの更新"""
        try:
            # タスクデータの更新
            if self.task_service.load_all_tasks():
                ErrorHandler.handle_info("データ更新が完了しました", "データ更新", show_dialog=True)
                self.refresh_projects()
            else:
                ErrorHandler.handle_warning("データ更新に失敗しました", "データ更新")
        except Exception as e:
            ErrorHandler.handle_error(e, "データ更新")
    
    def show_export_dialog(self):
        """エクスポートダイアログの表示"""
        dialog = ExportDialog(self.window, self.export_service)
        self.active_dialogs.append(dialog)
    
    def show_settings_dialog(self):
        """設定ダイアログの表示"""
        dialog = SettingsDialog(self.window, callback=self.on_settings_changed)
        self.active_dialogs.append(dialog)
    
    def on_settings_changed(self):
        """設定変更後のコールバック"""
        ErrorHandler.handle_info(
            "設定を変更しました。変更を完全に適用するには、アプリケーションを再起動してください。",
            "設定変更", show_dialog=True
        )
    
    def show_document_processor(self):
        """ドキュメント処理ウィンドウの表示"""
        if not self.selected_project:
            ErrorHandler.handle_warning("プロジェクトを選択してください", "ドキュメント処理")
            return
        
        try:
            # 外部アプリの起動
            launcher = ExternalAppLauncher()
            launcher.launch_document_processor(self.selected_project)
        except Exception as e:
            ErrorHandler.handle_error(e, "ドキュメント処理")
    
    def launch_dashboard(self):
        """外部ダッシュボードの起動"""
        try:
            launcher = ExternalAppLauncher()
            launcher.launch_project_dashboard()
        except Exception as e:
            ErrorHandler.handle_error(e, "ダッシュボード起動")
    
    def on_closing(self):
        """アプリケーション終了時の処理"""
        try:
            self.logger.debug("アプリケーション終了処理を開始")
            self.is_closing = True
            
            # アクティブなダイアログを閉じる
            for dialog in self.active_dialogs:
                try:
                    if dialog.window.winfo_exists():
                        dialog.window.destroy()
                except:
                    pass
            
            if self.window:
                try:
                    self.window.quit()
                    self.window.destroy()
                except Exception as e:
                    self.logger.debug(f"ウィンドウ破棄時のエラー: {e}")
                finally:
                    self.window = None
            
            self.logger.debug("アプリケーション終了処理を完了")
            
        except Exception as e:
            self.logger.error(f"アプリケーション終了処理でエラーが発生: {e}")
    
    def run(self):
        """アプリケーションの実行"""
        try:
            self.window.mainloop()
        except Exception as e:
            ErrorHandler.handle_error(e, "アプリケーション実行")