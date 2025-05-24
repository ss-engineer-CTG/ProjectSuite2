"""プロジェクトパス設定ダイアログ"""

import os
import logging
from pathlib import Path
from typing import Callable, Optional
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

from ProjectManager.src.ui.base_ui_component import BaseUIComponent
from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.config_manager import ConfigManager
from ProjectManager.src.core.error_handler import ErrorHandler

class PathConfigDialog(BaseUIComponent):
    """プロジェクトパス設定ダイアログ"""
    
    def __init__(self, parent, callback: Optional[Callable] = None):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            callback: 設定変更後のコールバック
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.callback = callback
        self.path_manager = PathManager()
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler()
        
        # ダイアログの作成
        self.window = self.create_dialog(parent)
        
        # 現在の設定を取得
        self.current_path = self.path_manager.get_path("OUTPUT_BASE_DIR")
        
        # UIの構築
        self.setup_ui()
        
        # 閉じるボタンが押された時の処理
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_dialog(self, parent) -> ctk.CTkToplevel:
        """
        ダイアログウィンドウの作成
        
        Args:
            parent: 親ウィンドウ
            
        Returns:
            ctk.CTkToplevel: ダイアログウィンドウ
        """
        window = ctk.CTkToplevel(parent)
        window.title("プロジェクトデータの保存先設定")
        window.transient(parent)
        window.grab_set()
        
        # ウィンドウの位置とサイズの設定
        window_width = 500
        window_height = 280
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        return window
    
    def setup_ui(self) -> None:
        """UIの構築"""
        main_frame = self.create_frame(
            self.window,
            fg_color="transparent"
        )
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ヘッダー
        header_label = self.create_label(
            main_frame,
            text="プロジェクトデータの保存先設定",
            font=self.header_font
        )
        header_label.pack(pady=(0, 20))
        
        # 説明
        description = (
            "プロジェクトのデータが保存されるフォルダを選択してください。\n"
            "既存のプロジェクトは自動的に移行されません。"
        )
        desc_label = self.create_label(
            main_frame,
            text=description
        )
        desc_label.pack(pady=(0, 20))
        
        # パス入力フレーム
        path_frame = self.create_frame(
            main_frame,
            fg_color="transparent"
        )
        path_frame.pack(fill="x", pady=10)
        
        path_label = self.create_label(
            path_frame,
            text="保存先フォルダ:",
            width=140
        )
        path_label.pack(side="left")
        
        self.path_var = tk.StringVar(value=str(self.current_path) or "")
        path_entry = self.create_entry(
            path_frame,
            text_var=self.path_var,
            width=250
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        browse_button = self.create_button(
            path_frame,
            text="参照...",
            width=80,
            command=self.browse_directory
        )
        browse_button.pack(side="left")
        
        # 注意書き
        warning_text = (
            "注意: 変更を適用するにはアプリケーションの再起動が必要です。\n"
            "既存のプロジェクトデータを新しいフォルダに手動で移行してください。"
        )
        warning_label = self.create_label(
            main_frame,
            text=warning_text,
            font=self.small_font,
            text_color="red"
        )
        warning_label.pack(pady=10)
        
        # 現在の設定情報
        current_info = f"現在の設定: {self.current_path}"
        info_label = self.create_label(
            main_frame,
            text=current_info,
            font=self.small_font,
            text_color="gray"
        )
        info_label.pack(pady=(0, 10))
        
        # ボタンフレーム
        button_frame = self.create_frame(
            main_frame,
            fg_color="transparent"
        )
        button_frame.pack(fill="x", pady=10)
        
        cancel_button = self.create_button(
            button_frame,
            text="キャンセル",
            width=100,
            command=self.on_close
        )
        cancel_button.pack(side="right", padx=5)
        
        save_button = self.create_button(
            button_frame,
            text="保存",
            width=100,
            command=self.save_settings
        )
        save_button.pack(side="right", padx=5)
    
    def browse_directory(self) -> None:
        """フォルダ選択ダイアログを表示"""
        initial_dir = self.path_var.get() if Path(self.path_var.get()).exists() else str(Path.home())
        directory = filedialog.askdirectory(initialdir=initial_dir)
        
        if directory:
            self.path_var.set(directory)
    
    def save_settings(self) -> None:
        """設定を保存"""
        new_path = self.path_var.get()
        
        if not new_path:
            self.error_handler.show_warning_dialog(
                "警告",
                "保存先フォルダが指定されていません。",
                self.window
            )
            return
        
        try:
            # パスの存在確認
            path_obj = Path(new_path)
            path_obj = self.path_manager.ensure_directory(path_obj)
            
            # 書き込み権限のチェック
            try:
                test_file = path_obj / '.write_test'
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                self.error_handler.show_error_dialog(
                    "エラー",
                    f"フォルダへの書き込み権限がありません: {e}",
                    self.window
                )
                return
            
            # 設定マネージャーで出力ディレクトリを更新
            self.config_manager.update_output_dir(str(path_obj))
            
            # 画面を閉じる
            self.window.destroy()
            
            # コールバックを呼び出す
            if self.callback:
                self.callback()
                
            self.error_handler.show_info_dialog(
                "保存完了", 
                "保存先フォルダを更新しました。\n設定を完全に適用するには、アプリケーションを再起動してください。"
            )
                
        except Exception as e:
            self.error_handler.handle_error(e, "設定エラー", self.window)
    
    def on_close(self) -> None:
        """ダイアログを閉じる"""
        self.window.destroy()