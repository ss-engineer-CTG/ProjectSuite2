"""
各種ダイアログ
KISS原則: シンプルなダイアログ実装
DRY原則: ダイアログ共通処理の統合
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any

from core.unified_config import UnifiedConfig
from services.export_service import ExportService
from .styles import ColorScheme, FontScheme, UIConstants
from utils.validators import Validator
from utils.error_handler import ErrorHandler
from utils.file_utils import FileManager

class SettingsDialog:
    """設定ダイアログ"""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        self.parent = parent
        self.callback = callback
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
        
        # ダイアログの作成
        self.window = ctk.CTkToplevel(parent)
        self.window.title("設定")
        self.window.transient(parent)
        self.window.grab_set()
        
        # ウィンドウサイズと位置
        window_width = 500
        window_height = 300
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 現在の設定を取得
        self.current_path = self.config.get_path('OUTPUT_BASE_DIR', '')
        
        self.setup_ui()
        
        # 閉じるボタンの処理
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """UIの構築"""
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, 
                       padx=UIConstants.PADDING_LARGE, pady=UIConstants.PADDING_LARGE)
        
        # ヘッダー
        header_label = ctk.CTkLabel(
            main_frame,
            text="プロジェクトデータ保存先設定",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        header_label.pack(pady=(0, UIConstants.PADDING_LARGE))
        
        # 説明
        description = (
            "プロジェクトのデータが保存されるフォルダを選択してください。\n"
            "既存のプロジェクトは自動的に移行されません。"
        )
        desc_label = ctk.CTkLabel(
            main_frame,
            text=description,
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_SECONDARY,
            wraplength=450
        )
        desc_label.pack(pady=(0, UIConstants.PADDING_LARGE))
        
        # パス入力フレーム
        path_frame = ctk.CTkFrame(main_frame, fg_color=ColorScheme.CARD_BG)
        path_frame.pack(fill="x", pady=UIConstants.PADDING_MEDIUM)
        
        path_label = ctk.CTkLabel(
            path_frame,
            text="保存先フォルダ:",
            font=FontScheme.LABEL_FONT,
            text_color=ColorScheme.TEXT_PRIMARY,
            width=UIConstants.LABEL_WIDTH_WIDE
        )
        path_label.pack(side="left", padx=UIConstants.PADDING_MEDIUM)
        
        self.path_var = ctk.StringVar(value=self.current_path)
        path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.path_var,
            font=FontScheme.ENTRY_FONT,
            fg_color=ColorScheme.INPUT_BG,
            text_color=ColorScheme.INPUT_TEXT,
            border_color=ColorScheme.INPUT_BORDER,
            width=250
        )
        path_entry.pack(side="left", fill="x", expand=True, 
                       padx=UIConstants.PADDING_SMALL)
        
        browse_button = ctk.CTkButton(
            path_frame,
            text="参照...",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_SMALL,
            command=self.browse_directory
        )
        browse_button.pack(side="right", padx=UIConstants.PADDING_MEDIUM)
        
        # 注意書き
        warning_text = (
            "注意: 変更を適用するにはアプリケーションの再起動が必要です。\n"
            "既存のプロジェクトデータを新しいフォルダに手動で移行してください。"
        )
        warning_label = ctk.CTkLabel(
            main_frame,
            text=warning_text,
            font=FontScheme.SMALL_FONT,
            text_color=ColorScheme.ERROR,
            wraplength=450
        )
        warning_label.pack(pady=UIConstants.PADDING_MEDIUM)
        
        # 現在の設定情報
        current_info = f"現在の設定: {self.current_path}"
        info_label = ctk.CTkLabel(
            main_frame,
            text=current_info,
            font=FontScheme.SMALL_FONT,
            text_color=ColorScheme.TEXT_SECONDARY,
            wraplength=450
        )
        info_label.pack(pady=(0, UIConstants.PADDING_MEDIUM))
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=UIConstants.PADDING_MEDIUM)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_DANGER,
            hover_color='#CC2F26',
            width=UIConstants.BUTTON_WIDTH_MEDIUM,
            command=self.on_close
        )
        cancel_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
        
        save_button = ctk.CTkButton(
            button_frame,
            text="保存",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_MEDIUM,
            command=self.save_settings
        )
        save_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
    
    def browse_directory(self):
        """フォルダ選択ダイアログを表示"""
        current_path = self.path_var.get()
        initial_dir = current_path if Path(current_path).exists() else str(Path.home())
        
        directory = filedialog.askdirectory(
            initialdir=initial_dir,
            title="プロジェクトデータ保存先フォルダを選択"
        )
        
        if directory:
            self.path_var.set(directory)
    
    def save_settings(self):
        """設定を保存"""
        new_path = self.path_var.get().strip()
        
        if not new_path:
            ErrorHandler.handle_warning("保存先フォルダが指定されていません。", "設定保存")
            return
        
        # パスの検証
        is_valid, error_msg = Validator.validate_file_path(new_path)
        if not is_valid:
            ErrorHandler.handle_warning(error_msg, "設定保存")
            return
        
        # フォルダの作成（存在しない場合）
        path_obj = Path(new_path)
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"フォルダを作成しました: {path_obj}")
            except Exception as e:
                ErrorHandler.handle_error(e, "フォルダ作成")
                return
        
        # 書き込み権限の確認
        if not FileManager.check_file_permissions(path_obj):
            ErrorHandler.handle_warning("フォルダへの書き込み権限がありません", "設定保存")
            return
        
        try:
            # 設定を保存
            self.config.update_output_directory(new_path)
            
            # ダイアログを閉じる
            self.window.destroy()
            
            # コールバックを呼び出す
            if self.callback:
                self.callback()
            
            ErrorHandler.handle_info(
                "保存先フォルダを更新しました。\n設定を完全に適用するには、アプリケーションを再起動してください。",
                "設定保存", show_dialog=True
            )
            
        except Exception as e:
            ErrorHandler.handle_error(e, "設定保存")
    
    def on_close(self):
        """ダイアログを閉じる"""
        self.window.destroy()

class ExportDialog:
    """エクスポートダイアログ"""
    
    def __init__(self, parent, export_service: ExportService):
        self.parent = parent
        self.export_service = export_service
        self.logger = logging.getLogger(__name__)
        
        # ダイアログの作成
        self.window = ctk.CTkToplevel(parent)
        self.window.title("データエクスポート")
        self.window.transient(parent)
        self.window.grab_set()
        
        # ウィンドウサイズと位置
        window_width = 600
        window_height = 500
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.setup_ui()
        
        # 閉じるボタンの処理
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """UIの構築"""
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, 
                       padx=UIConstants.PADDING_LARGE, pady=UIConstants.PADDING_LARGE)
        
        # ヘッダー
        header_label = ctk.CTkLabel(
            main_frame,
            text="データエクスポート",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        header_label.pack(pady=(0, UIConstants.PADDING_LARGE))
        
        # エクスポートオプション
        options_frame = ctk.CTkFrame(main_frame, fg_color=ColorScheme.CARD_BG)
        options_frame.pack(fill="x", pady=UIConstants.PADDING_MEDIUM)
        
        options_label = ctk.CTkLabel(
            options_frame,
            text="エクスポートオプション",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        options_label.pack(pady=UIConstants.PADDING_MEDIUM)
        
        # エクスポートタイプの選択
        self.export_type = ctk.StringVar(value="all")
        
        all_radio = ctk.CTkRadioButton(
            options_frame,
            text="全データ（ダッシュボード + プロジェクト）",
            variable=self.export_type,
            value="all",
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        all_radio.pack(anchor="w", padx=UIConstants.PADDING_LARGE, 
                      pady=UIConstants.PADDING_SMALL)
        
        dashboard_radio = ctk.CTkRadioButton(
            options_frame,
            text="ダッシュボードデータのみ",
            variable=self.export_type,
            value="dashboard",
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        dashboard_radio.pack(anchor="w", padx=UIConstants.PADDING_LARGE, 
                           pady=UIConstants.PADDING_SMALL)
        
        projects_radio = ctk.CTkRadioButton(
            options_frame,
            text="プロジェクトデータのみ",
            variable=self.export_type,
            value="projects",
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        projects_radio.pack(anchor="w", padx=UIConstants.PADDING_LARGE, 
                          pady=(UIConstants.PADDING_SMALL, UIConstants.PADDING_MEDIUM))
        
        # エクスポート履歴
        history_frame = ctk.CTkFrame(main_frame, fg_color=ColorScheme.CARD_BG)
        history_frame.pack(fill="both", expand=True, pady=UIConstants.PADDING_MEDIUM)
        
        history_label = ctk.CTkLabel(
            history_frame,
            text="エクスポート履歴",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        history_label.pack(pady=UIConstants.PADDING_MEDIUM)
        
        # 履歴リスト
        self.history_listbox = ctk.CTkScrollableFrame(
            history_frame,
            fg_color=ColorScheme.INPUT_BG
        )
        self.history_listbox.pack(fill="both", expand=True, 
                                 padx=UIConstants.PADDING_MEDIUM, 
                                 pady=(0, UIConstants.PADDING_MEDIUM))
        
        # 履歴の読み込み
        self.load_export_history()
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=UIConstants.PADDING_MEDIUM)
        
        # 履歴更新ボタン
        refresh_button = ctk.CTkButton(
            button_frame,
            text="履歴更新",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.INFO,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.get_hover_color(ColorScheme.INFO),
            width=UIConstants.BUTTON_WIDTH_MEDIUM,
            command=self.load_export_history
        )
        refresh_button.pack(side="left", padx=UIConstants.PADDING_SMALL)
        
        # 閉じるボタン
        close_button = ctk.CTkButton(
            button_frame,
            text="閉じる",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_DANGER,
            hover_color='#CC2F26',
            width=UIConstants.BUTTON_WIDTH_MEDIUM,
            command=self.on_close
        )
        close_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
        
        # エクスポート実行ボタン
        export_button = ctk.CTkButton(
            button_frame,
            text="エクスポート実行",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_LARGE,
            command=self.execute_export
        )
        export_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
    
    def load_export_history(self):
        """エクスポート履歴の読み込み"""
        try:
            # 既存の履歴をクリア
            for widget in self.history_listbox.winfo_children():
                widget.destroy()
            
            # 履歴データの取得
            history = self.export_service.get_export_history()
            
            if not history:
                no_history_label = ctk.CTkLabel(
                    self.history_listbox,
                    text="エクスポート履歴がありません",
                    font=FontScheme.DEFAULT_FONT,
                    text_color=ColorScheme.TEXT_SECONDARY
                )
                no_history_label.pack(pady=UIConstants.PADDING_MEDIUM)
                return
            
            # 履歴アイテムの表示
            for item in history[:10]:  # 最新10件を表示
                self.create_history_item(item)
                
        except Exception as e:
            ErrorHandler.handle_error(e, "エクスポート履歴読み込み", show_dialog=False)
    
    def create_history_item(self, item: Dict[str, Any]):
        """履歴アイテムの作成"""
        item_frame = ctk.CTkFrame(self.history_listbox, fg_color=ColorScheme.CARD_BG)
        item_frame.pack(fill="x", padx=UIConstants.PADDING_SMALL, 
                       pady=UIConstants.PADDING_SMALL)
        
        # ファイル名
        filename_label = ctk.CTkLabel(
            item_frame,
            text=item['filename'],
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_PRIMARY,
            anchor="w"
        )
        filename_label.pack(fill="x", padx=UIConstants.PADDING_SMALL)
        
        # 詳細情報
        size_mb = item['size'] / (1024 * 1024)
        details = f"サイズ: {size_mb:.2f}MB | 更新: {item['modified_time']}"
        details_label = ctk.CTkLabel(
            item_frame,
            text=details,
            font=FontScheme.SMALL_FONT,
            text_color=ColorScheme.TEXT_SECONDARY,
            anchor="w"
        )
        details_label.pack(fill="x", padx=UIConstants.PADDING_SMALL)
    
    def execute_export(self):
        """エクスポートの実行"""
        try:
            export_type = self.export_type.get()
            
            if export_type == "all":
                success = self.export_service.export_all_data()
            elif export_type == "dashboard":
                success = self.export_service.export_dashboard_data()
            elif export_type == "projects":
                success = self.export_service.export_projects_data()
            else:
                ErrorHandler.handle_warning("エクスポートタイプが選択されていません", "エクスポート")
                return
            
            if success:
                # 履歴を更新
                self.load_export_history()
            
        except Exception as e:
            ErrorHandler.handle_error(e, "エクスポート実行")
    
    def on_close(self):
        """ダイアログを閉じる"""
        self.window.destroy()

class AboutDialog:
    """アバウトダイアログ"""
    
    def __init__(self, parent):
        self.parent = parent
        
        # ダイアログの作成
        self.window = ctk.CTkToplevel(parent)
        self.window.title("アプリケーション情報")
        self.window.transient(parent)
        self.window.grab_set()
        
        # ウィンドウサイズと位置
        window_width = 400
        window_height = 300
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.setup_ui()
        
        # 閉じるボタンの処理
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """UIの構築"""
        from core.constants import AppConstants
        
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, 
                       padx=UIConstants.PADDING_LARGE, pady=UIConstants.PADDING_LARGE)
        
        # アプリケーション名
        app_name_label = ctk.CTkLabel(
            main_frame,
            text=AppConstants.APP_NAME,
            font=FontScheme.TITLE_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        app_name_label.pack(pady=(UIConstants.PADDING_LARGE, UIConstants.PADDING_MEDIUM))
        
        # バージョン
        version_label = ctk.CTkLabel(
            main_frame,
            text=f"バージョン: {AppConstants.APP_VERSION}",
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_SECONDARY
        )
        version_label.pack(pady=UIConstants.PADDING_SMALL)
        
        # 説明
        description = (
            "プロジェクト管理とタスク追跡のための\n"
            "統合アプリケーションです。\n\n"
            "プロジェクトの作成、編集、削除、\n"
            "タスクの管理、データのエクスポートなど\n"
            "プロジェクト管理に必要な機能を提供します。"
        )
        desc_label = ctk.CTkLabel(
            main_frame,
            text=description,
            font=FontScheme.DEFAULT_FONT,
            text_color=ColorScheme.TEXT_SECONDARY,
            justify="center"
        )
        desc_label.pack(pady=UIConstants.PADDING_LARGE)
        
        # OKボタン
        ok_button = ctk.CTkButton(
            main_frame,
            text="OK",
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_MEDIUM,
            command=self.on_close
        )
        ok_button.pack(pady=UIConstants.PADDING_LARGE)
    
    def on_close(self):
        """ダイアログを閉じる"""
        self.window.destroy()