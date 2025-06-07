"""
フォーム関連（統合）
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from config import Config
from services import ProjectService, ExportService
from .styles import Colors, Fonts, Sizes
from utils import ErrorHandler, Validator
from constants import PROJECT_STATUSES

class ProjectFormDialog:
    """プロジェクトフォームダイアログ"""
    
    def __init__(self, parent, config: Config, project_service: ProjectService,
                 edit_mode: bool = False, project_data: Optional[Dict[str, Any]] = None,
                 callback: Optional[Callable] = None):
        self.parent = parent
        self.config = config
        self.project_service = project_service
        self.edit_mode = edit_mode
        self.project_data = project_data
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # 入力フィールドの保持
        self.fields = {}
        
        # ウィンドウの作成
        self.window = ctk.CTkToplevel(parent)
        self._setup_window()
        self._setup_gui()
        
        # データの設定
        if edit_mode and project_data:
            self._set_project_data(project_data)
        else:
            self._load_default_values()
    
    def _setup_window(self):
        """ウィンドウの設定"""
        mode_text = "編集" if self.edit_mode else "作成"
        self.window.title(f"プロジェクト{mode_text}")
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # ウィンドウサイズと位置
        window_width = 600
        window_height = 700
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() - window_width) // 2
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(fg_color=Colors.BACKGROUND)
    
    def _setup_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ctk.CTkFrame(self.window, fg_color=Colors.BACKGROUND)
        main_frame.pack(fill="both", expand=True, 
                       padx=Sizes.PADDING_LARGE, pady=Sizes.PADDING_LARGE)
        
        # スクロール可能なフレーム
        self.scroll_frame = ctk.CTkScrollableFrame(
            main_frame, fg_color=Colors.BACKGROUND
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, Sizes.PADDING_LARGE))
        
        # セクション作成
        self._create_basic_info_section()
        self._create_personnel_section()
        self._create_manufacturing_section()
        
        # ボタンフレーム
        self._create_button_frame(main_frame)
    
    def _create_section_label(self, parent, text: str):
        """セクションラベルの作成"""
        frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG)
        frame.pack(fill="x", padx=Sizes.PADDING_LARGE, 
                  pady=(Sizes.PADDING_LARGE, Sizes.PADDING_MEDIUM))
        
        label = ctk.CTkLabel(
            frame, text=text, font=Fonts.HEADER,
            text_color=Colors.TEXT_PRIMARY, anchor="w"
        )
        label.pack(pady=Sizes.PADDING_MEDIUM, 
                  padx=Sizes.PADDING_MEDIUM, anchor="w")
        
        return frame
    
    def _create_input_field(self, parent, label_text: str, required: bool = False, 
                          field_name: str = None, placeholder: str = None):
        """入力フィールドの作成"""
        frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG, 
                           border_color=Colors.FRAME_BORDER, border_width=1)
        frame.pack(fill="x", padx=Sizes.PADDING_LARGE, pady=Sizes.PADDING_SMALL)
        
        # ラベル
        label = ctk.CTkLabel(
            frame, text=f"{label_text}{'*' if required else ''}",
            anchor="w", width=Sizes.LABEL_WIDTH, font=Fonts.DEFAULT,
            text_color=Colors.TEXT_PRIMARY
        )
        label.pack(side="left", padx=(Sizes.PADDING_MEDIUM, Sizes.PADDING_SMALL))
        
        # 入力フィールド
        entry = ctk.CTkEntry(
            frame, width=Sizes.ENTRY_WIDTH, placeholder_text=placeholder,
            font=Fonts.DEFAULT, fg_color=Colors.INPUT_BG,
            text_color=Colors.INPUT_TEXT, border_color=Colors.INPUT_BORDER
        )
        entry.pack(side="left", padx=Sizes.PADDING_SMALL, expand=True, fill="x")
        
        if field_name:
            self.fields[field_name] = entry
            
        return entry
    
    def _create_combo_field(self, parent, label_text: str, field_name: str, 
                          values: list, required: bool = False):
        """コンボボックスフィールドの作成"""
        frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG,
                           border_color=Colors.FRAME_BORDER, border_width=1)
        frame.pack(fill="x", padx=Sizes.PADDING_LARGE, pady=Sizes.PADDING_SMALL)
        
        # ラベル
        label = ctk.CTkLabel(
            frame, text=f"{label_text}{'*' if required else ''}",
            anchor="w", width=Sizes.LABEL_WIDTH, font=Fonts.DEFAULT,
            text_color=Colors.TEXT_PRIMARY
        )
        label.pack(side="left", padx=(Sizes.PADDING_MEDIUM, Sizes.PADDING_SMALL))
        
        # コンボボックス
        combo = ctk.CTkComboBox(
            frame, width=Sizes.ENTRY_WIDTH, values=values, state="readonly",
            font=Fonts.DEFAULT, fg_color=Colors.INPUT_BG,
            text_color=Colors.INPUT_TEXT, border_color=Colors.INPUT_BORDER
        )
        combo.pack(side="left", padx=Sizes.PADDING_SMALL, expand=True, fill="x")
        
        if field_name:
            self.fields[field_name] = combo
            
        return combo
    
    def _create_basic_info_section(self):
        """基本情報セクションの作成"""
        self._create_section_label(self.scroll_frame, "基本情報")
        
        self._create_input_field(self.scroll_frame, "プロジェクト名", True, "project_name")
        
        # 開始日入力
        self._create_input_field(self.scroll_frame, "開始日", True, "start_date", "YYYY-MM-DD")
        
        # 編集モードでない場合は今日の日付を設定
        if not self.edit_mode:
            self.fields['start_date'].insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        self._create_combo_field(self.scroll_frame, "ステータス", "status", 
                               PROJECT_STATUSES, True)
        
        # 新規作成時はデフォルトで「進行中」を設定
        if not self.edit_mode:
            self.fields['status'].set("進行中")
    
    def _create_personnel_section(self):
        """担当者情報セクションの作成"""
        self._create_section_label(self.scroll_frame, "担当者情報")
        
        self._create_input_field(self.scroll_frame, "担当者", True, "manager")
        self._create_input_field(self.scroll_frame, "確認者", True, "reviewer")
        self._create_input_field(self.scroll_frame, "承認者", True, "approver")
    
    def _create_manufacturing_section(self):
        """製造ライン情報セクションの作成"""
        self._create_section_label(self.scroll_frame, "製造ライン情報")
        
        self._create_input_field(self.scroll_frame, "事業部", False, "division", "事業部コードを入力")
        self._create_input_field(self.scroll_frame, "工場", False, "factory", "工場コードを入力")
        self._create_input_field(self.scroll_frame, "工程", False, "process", "工程コードを入力")
        self._create_input_field(self.scroll_frame, "ライン", False, "line", "ラインコードを入力")
    
    def _create_button_frame(self, parent):
        """ボタンフレームの作成"""
        button_frame = ctk.CTkFrame(parent, fg_color=Colors.CARD_BG)
        button_frame.pack(fill="x", pady=(Sizes.PADDING_LARGE, 0))
        
        # 保存ボタン
        save_button = ctk.CTkButton(
            button_frame, text="保存", command=self._save,
            font=Fonts.BUTTON, fg_color=Colors.BUTTON_PRIMARY,
            text_color=Colors.BUTTON_TEXT, hover_color=Colors.BUTTON_HOVER,
            width=Sizes.BUTTON_WIDTH_MEDIUM
        )
        save_button.pack(side="right", padx=Sizes.PADDING_SMALL)
        
        # キャンセルボタン
        cancel_button = ctk.CTkButton(
            button_frame, text="キャンセル", command=self._cancel,
            font=Fonts.BUTTON, fg_color=Colors.BUTTON_DANGER,
            hover_color="#CC2F26", width=Sizes.BUTTON_WIDTH_MEDIUM
        )
        cancel_button.pack(side="right", padx=Sizes.PADDING_SMALL)
    
    def _set_project_data(self, data: Dict[str, Any]):
        """プロジェクトデータを入力フィールドに設定"""
        field_mappings = {
            'project_name': 'project_name',
            'start_date': 'start_date',
            'manager': 'manager',
            'reviewer': 'reviewer',
            'approver': 'approver',
            'status': 'status',
            'division': 'division',
            'factory': 'factory',
            'process': 'process',
            'line': 'line'
        }
        
        for field_name, data_key in field_mappings.items():
            if field_name in self.fields and data_key in data:
                widget = self.fields[field_name]
                value = str(data[data_key]) if data[data_key] is not None else ""
                
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(value)
                else:
                    widget.delete(0, 'end')
                    widget.insert(0, value)
    
    def _load_default_values(self):
        """デフォルト値の読み込み"""
        try:
            defaults = {
                'project_name': self.config.get_setting('default_project_name', ''),
                'manager': self.config.get_setting('default_manager', ''),
                'reviewer': self.config.get_setting('default_reviewer', ''),
                'approver': self.config.get_setting('default_approver', ''),
                'division': self.config.get_setting('default_division', ''),
                'factory': self.config.get_setting('default_factory', ''),
                'process': self.config.get_setting('default_process', ''),
                'line': self.config.get_setting('default_line', '')
            }
            
            for field_name, value in defaults.items():
                if field_name in self.fields and value:
                    widget = self.fields[field_name]
                    if isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, 'end')
                        widget.insert(0, value)
                        
        except Exception as e:
            self.logger.warning(f"デフォルト値の読み込みエラー: {e}")
    
    def _save(self):
        """保存処理"""
        try:
            # 入力値の取得
            values = self._get_form_values()
            
            # データ検証
            is_valid, errors = Validator.validate_project_data(values)
            if not is_valid:
                ErrorHandler.show_warning("\n".join(errors))
                return
            
            # 保存処理
            if self.edit_mode:
                success = self.project_service.update_project(
                    self.project_data['project_id'], values
                )
            else:
                project_id = self.project_service.create_project(values)
                success = project_id is not None
            
            if success:
                if self.callback:
                    self.callback()
                self.window.destroy()
            
        except Exception as e:
            ErrorHandler.handle_error(e, "プロジェクト保存")
    
    def _get_form_values(self) -> Dict[str, Any]:
        """フォームから値を取得"""
        values = {}
        
        for field_name, widget in self.fields.items():
            if isinstance(widget, ctk.CTkEntry):
                values[field_name] = widget.get().strip()
            elif isinstance(widget, ctk.CTkComboBox):
                values[field_name] = widget.get().strip()
        
        # 空文字をNoneに変換（オプショナルフィールド）
        optional_fields = ['division', 'factory', 'process', 'line']
        for field in optional_fields:
            if field in values and not values[field]:
                values[field] = None
        
        return values
    
    def _cancel(self):
        """キャンセル処理"""
        self.window.destroy()

class SettingsDialog:
    """設定ダイアログ"""
    
    def __init__(self, parent, config: Config, callback: Optional[Callable] = None):
        self.parent = parent
        self.config = config
        self.callback = callback
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
        self.window.configure(fg_color=Colors.BACKGROUND)
        
        # 現在の設定を取得
        self.current_path = self.config.get_path('output_base')
        
        self.setup_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """UIの構築"""
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, 
                       padx=Sizes.PADDING_LARGE, pady=Sizes.PADDING_LARGE)
        
        # ヘッダー
        header_label = ctk.CTkLabel(
            main_frame, text="プロジェクトデータ保存先設定",
            font=Fonts.HEADER, text_color=Colors.TEXT_PRIMARY
        )
        header_label.pack(pady=(0, Sizes.PADDING_LARGE))
        
        # 説明
        description = (
            "プロジェクトのデータが保存されるフォルダを選択してください。\n"
            "既存のプロジェクトは自動的に移行されません。"
        )
        desc_label = ctk.CTkLabel(
            main_frame, text=description, font=Fonts.DEFAULT,
            text_color=Colors.TEXT_SECONDARY, wraplength=450
        )
        desc_label.pack(pady=(0, Sizes.PADDING_LARGE))
        
        # パス入力フレーム
        path_frame = ctk.CTkFrame(main_frame, fg_color=Colors.CARD_BG)
        path_frame.pack(fill="x", pady=Sizes.PADDING_MEDIUM)
        
        path_label = ctk.CTkLabel(
            path_frame, text="保存先フォルダ:", font=Fonts.DEFAULT,
            text_color=Colors.TEXT_PRIMARY, width=140
        )
        path_label.pack(side="left", padx=Sizes.PADDING_MEDIUM)
        
        self.path_var = ctk.StringVar(value=self.current_path)
        path_entry = ctk.CTkEntry(
            path_frame, textvariable=self.path_var, font=Fonts.DEFAULT,
            fg_color=Colors.INPUT_BG, text_color=Colors.INPUT_TEXT,
            border_color=Colors.INPUT_BORDER, width=250
        )
        path_entry.pack(side="left", fill="x", expand=True, 
                       padx=Sizes.PADDING_SMALL)
        
        browse_button = ctk.CTkButton(
            path_frame, text="参照...", font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_PRIMARY, text_color=Colors.BUTTON_TEXT,
            hover_color=Colors.BUTTON_HOVER, width=Sizes.BUTTON_WIDTH_SMALL,
            command=self.browse_directory
        )
        browse_button.pack(side="right", padx=Sizes.PADDING_MEDIUM)
        
        # 注意書き
        warning_text = (
            "注意: 変更を適用するにはアプリケーションの再起動が必要です。\n"
            "既存のプロジェクトデータを新しいフォルダに手動で移行してください。"
        )
        warning_label = ctk.CTkLabel(
            main_frame, text=warning_text, font=Fonts.SMALL,
            text_color=Colors.BUTTON_DANGER, wraplength=450
        )
        warning_label.pack(pady=Sizes.PADDING_MEDIUM)
        
        # 現在の設定情報
        current_info = f"現在の設定: {self.current_path}"
        info_label = ctk.CTkLabel(
            main_frame, text=current_info, font=Fonts.SMALL,
            text_color=Colors.TEXT_SECONDARY, wraplength=450
        )
        info_label.pack(pady=(0, Sizes.PADDING_MEDIUM))
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=Sizes.PADDING_MEDIUM)
        
        cancel_button = ctk.CTkButton(
            button_frame, text="キャンセル", font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_DANGER, hover_color='#CC2F26',
            width=Sizes.BUTTON_WIDTH_MEDIUM, command=self.on_close
        )
        cancel_button.pack(side="right", padx=Sizes.PADDING_SMALL)
        
        save_button = ctk.CTkButton(
            button_frame, text="保存", font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_PRIMARY, text_color=Colors.BUTTON_TEXT,
            hover_color=Colors.BUTTON_HOVER, width=Sizes.BUTTON_WIDTH_MEDIUM,
            command=self.save_settings
        )
        save_button.pack(side="right", padx=Sizes.PADDING_SMALL)
    
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
            ErrorHandler.show_warning("保存先フォルダが指定されていません。")
            return
        
        # パスの存在確認
        path_obj = Path(new_path)
        if not path_obj.exists():
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"フォルダを作成しました: {path_obj}")
            except Exception as e:
                ErrorHandler.handle_error(e, "フォルダ作成")
                return
        
        try:
            # 設定を保存
            self.config.update_output_directory(new_path)
            
            # ダイアログを閉じる
            self.window.destroy()
            
            # コールバックを呼び出す
            if self.callback:
                self.callback()
            
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
        window_width = 400
        window_height = 300
        x = parent.winfo_rootx() + (parent.winfo_width() - window_width) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.configure(fg_color=Colors.BACKGROUND)
        
        self.setup_ui()
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_ui(self):
        """UIの構築"""
        main_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, 
                       padx=Sizes.PADDING_LARGE, pady=Sizes.PADDING_LARGE)
        
        # ヘッダー
        header_label = ctk.CTkLabel(
            main_frame, text="データエクスポート",
            font=Fonts.HEADER, text_color=Colors.TEXT_PRIMARY
        )
        header_label.pack(pady=(0, Sizes.PADDING_LARGE))
        
        # エクスポートオプション
        options_frame = ctk.CTkFrame(main_frame, fg_color=Colors.CARD_BG)
        options_frame.pack(fill="x", pady=Sizes.PADDING_MEDIUM)
        
        options_label = ctk.CTkLabel(
            options_frame, text="エクスポートオプション",
            font=Fonts.HEADER, text_color=Colors.TEXT_PRIMARY
        )
        options_label.pack(pady=Sizes.PADDING_MEDIUM)
        
        # エクスポートタイプの選択
        self.export_type = ctk.StringVar(value="all")
        
        all_radio = ctk.CTkRadioButton(
            options_frame, text="全データ（ダッシュボード + プロジェクト）",
            variable=self.export_type, value="all",
            font=Fonts.DEFAULT, text_color=Colors.TEXT_PRIMARY
        )
        all_radio.pack(anchor="w", padx=Sizes.PADDING_LARGE, 
                      pady=Sizes.PADDING_SMALL)
        
        dashboard_radio = ctk.CTkRadioButton(
            options_frame, text="ダッシュボードデータのみ",
            variable=self.export_type, value="dashboard",
            font=Fonts.DEFAULT, text_color=Colors.TEXT_PRIMARY
        )
        dashboard_radio.pack(anchor="w", padx=Sizes.PADDING_LARGE, 
                           pady=Sizes.PADDING_SMALL)
        
        projects_radio = ctk.CTkRadioButton(
            options_frame, text="プロジェクトデータのみ",
            variable=self.export_type, value="projects",
            font=Fonts.DEFAULT, text_color=Colors.TEXT_PRIMARY
        )
        projects_radio.pack(anchor="w", padx=Sizes.PADDING_LARGE, 
                          pady=(Sizes.PADDING_SMALL, Sizes.PADDING_MEDIUM))
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=Sizes.PADDING_LARGE)
        
        # 閉じるボタン
        close_button = ctk.CTkButton(
            button_frame, text="閉じる", font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_DANGER, hover_color='#CC2F26',
            width=Sizes.BUTTON_WIDTH_MEDIUM, command=self.on_close
        )
        close_button.pack(side="right", padx=Sizes.PADDING_SMALL)
        
        # エクスポート実行ボタン
        export_button = ctk.CTkButton(
            button_frame, text="エクスポート実行", font=Fonts.BUTTON,
            fg_color=Colors.BUTTON_PRIMARY, text_color=Colors.BUTTON_TEXT,
            hover_color=Colors.BUTTON_HOVER, width=Sizes.BUTTON_WIDTH_LARGE,
            command=self.execute_export
        )
        export_button.pack(side="right", padx=Sizes.PADDING_SMALL)
    
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
                ErrorHandler.show_warning("エクスポートタイプが選択されていません")
                return
            
            if success:
                self.window.destroy()
            
        except Exception as e:
            ErrorHandler.handle_error(e, "エクスポート実行")
    
    def on_close(self):
        """ダイアログを閉じる"""
        self.window.destroy()