"""プロジェクトパス設定ダイアログ"""

import logging
from pathlib import Path
from typing import Callable, Optional
import tkinter as tk
from tkinter import filedialog

from ProjectManager.src.ui.base_ui_component import BaseUIComponent
from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.config_manager import ConfigManager
from ProjectManager.src.core.error_handler import ErrorHandler

class ProjectPathDialog(BaseUIComponent):
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
        self.window = ctk.CTkToplevel(parent)
        self.window.title("プロジェクトフォルダ設定")
        self.window.transient(parent)
        self.window.grab_set()
        
        # ウィンドウの位置とサイズの設定
        window_width = 500
        window_height = 250
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 現在の設定を取得
        self.current_path = self.path_manager.get_path("OUTPUT_BASE_DIR")
        
        # UIの構築
        self.setup_ui()
        
        # 閉じるボタンが押された時の処理
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
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
            text="プロジェクトフォルダの設定",
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
            text=description,
            wraplength=450
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
            text="プロジェクトフォルダ:",
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
            text_color="red",
            wraplength=450
        )
        warning_label.pack(pady=10)
        
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
                "プロジェクトフォルダが指定されていません。",
                self.window
            )
            return
        
        try:
            # パスを確保
            path_obj = self.path_manager.ensure_directory(new_path)
            
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
            
            # デフォルト設定ファイルにも保存
            self.save_to_defaults_txt(str(path_obj))
            
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
    
    def save_to_defaults_txt(self, projects_path: str) -> None:
        """
        defaults.txtに設定を保存
        
        Args:
            projects_path: プロジェクトフォルダのパス
        """
        try:
            # 設定を更新
            self.config_manager.set_setting('defaults', 'output_dir', projects_path)
            
            self.logger.info(f"デフォルト設定を更新しました: output_dir={projects_path}")
            
        except Exception as e:
            self.logger.error(f"defaults.txtへの保存に失敗: {e}")
            raise
    
    def on_close(self) -> None:
        """ダイアログを閉じる"""
        self.window.destroy()