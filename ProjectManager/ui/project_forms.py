"""
統合プロジェクトフォーム
KISS原則: シンプルなフォーム統合
DRY原則: BaseForm + QuickForm + DetailForm の統合
"""

import customtkinter as ctk
from tkinter import messagebox
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable

from core.unified_config import UnifiedConfig
from core.master_data import MasterDataManager
from core.constants import AppConstants, PathConstants
from services.project_service import ProjectService
from .styles import ColorScheme, FontScheme, UIConstants
from utils.validators import Validator
from utils.error_handler import ErrorHandler

class ProjectFormDialog:
    """統合プロジェクトフォームダイアログ"""
    
    def __init__(self, parent: ctk.CTk, 
                 project_service: ProjectService,
                 edit_mode: bool = False,
                 project_data: Optional[Dict[str, Any]] = None,
                 callback: Optional[Callable] = None,
                 form_mode: str = "quick"):
        """
        初期化
        
        Args:
            parent: 親ウィンドウ
            project_service: プロジェクトサービス
            edit_mode: 編集モードかどうか
            project_data: 編集対象のプロジェクトデータ
            callback: 完了時のコールバック関数
            form_mode: フォームモード ("quick", "detail")
        """
        self.parent = parent
        self.project_service = project_service
        self.edit_mode = edit_mode
        self.project_data = project_data
        self.callback = callback
        self.form_mode = form_mode
        self.config = UnifiedConfig()
        self.logger = logging.getLogger(__name__)
        
        # 入力フィールドの保持
        self.fields = {}
        
        # マスターデータマネージャーの初期化
        self.master_data = None
        self.current_selection = {
            'division': None,
            'factory': None,
            'process': None,
            'line': None
        }
        
        if form_mode == "detail":
            self._initialize_master_data()
        
        # ウィンドウの作成
        self.window = ctk.CTkToplevel(parent)
        self._setup_window()
        self._setup_gui()
        
        # データの設定
        if edit_mode and project_data:
            self._set_project_data(project_data)
        else:
            self._load_default_values()
    
    def _initialize_master_data(self):
        """マスターデータの初期化"""
        try:
            master_data_path = PathConstants.MASTER_DATA_PATH
            self.master_data = MasterDataManager(master_data_path)
        except Exception as e:
            self.logger.error(f"マスターデータ初期化エラー: {e}")
            ErrorHandler.handle_warning("マスターデータの読み込みに失敗しました。詳細モードは利用できません。")
            self.form_mode = "quick"
    
    def _setup_window(self):
        """ウィンドウの設定"""
        mode_text = "編集" if self.edit_mode else "作成"
        form_text = "詳細" if self.form_mode == "detail" else "クイック"
        self.window.title(f"プロジェクト{mode_text} ({form_text})")
        
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # ウィンドウサイズの設定
        if self.form_mode == "detail":
            geometry = UIConstants.get_window_geometry(self.parent, 0.7, 0.8)
        else:
            geometry = UIConstants.get_window_geometry(self.parent, 0.6, 0.7)
        
        self.window.geometry(geometry)
        self.window.configure(fg_color=ColorScheme.BACKGROUND)
    
    def _setup_gui(self):
        """GUI構築"""
        # メインフレーム
        main_frame = ctk.CTkFrame(self.window, fg_color=ColorScheme.BACKGROUND)
        main_frame.pack(fill="both", expand=True, 
                       padx=UIConstants.PADDING_LARGE, pady=UIConstants.PADDING_LARGE)
        
        # スクロール可能なフレーム
        self.scroll_frame = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=ColorScheme.BACKGROUND
        )
        self.scroll_frame.pack(fill="both", expand=True, pady=(0, UIConstants.PADDING_LARGE))
        
        # セクション作成
        self._create_basic_info_section()
        self._create_personnel_section()
        
        if self.form_mode == "detail":
            self._create_manufacturing_section()
        else:
            self._create_simple_manufacturing_section()
        
        # ボタンフレーム
        self._create_button_frame(main_frame)
    
    def _create_section_label(self, parent, text: str):
        """セクションラベルの作成"""
        frame = ctk.CTkFrame(parent, fg_color=ColorScheme.CARD_BG)
        frame.pack(fill="x", padx=UIConstants.PADDING_LARGE, 
                  pady=(UIConstants.PADDING_LARGE, UIConstants.PADDING_MEDIUM))
        
        label = ctk.CTkLabel(
            frame,
            text=text,
            font=FontScheme.HEADER_FONT,
            text_color=ColorScheme.TEXT_PRIMARY,
            anchor="w"
        )
        label.pack(pady=UIConstants.PADDING_MEDIUM, 
                  padx=UIConstants.PADDING_MEDIUM, anchor="w")
        
        return frame
    
    def _create_input_field(self, parent, label_text: str, required: bool = False, 
                          field_name: str = None, placeholder: str = None):
        """入力フィールドの作成"""
        frame = ctk.CTkFrame(
            parent,
            fg_color=ColorScheme.CARD_BG,
            border_color=ColorScheme.FRAME_BORDER,
            border_width=1
        )
        frame.pack(fill="x", padx=UIConstants.PADDING_LARGE, pady=UIConstants.PADDING_SMALL)
        
        # ラベル
        label = ctk.CTkLabel(
            frame,
            text=f"{label_text}{'*' if required else ''}",
            anchor="w",
            width=UIConstants.LABEL_WIDTH_STANDARD,
            font=FontScheme.LABEL_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        label.pack(side="left", padx=(UIConstants.PADDING_MEDIUM, UIConstants.PADDING_SMALL))
        
        # 入力フィールド
        entry = ctk.CTkEntry(
            frame,
            width=UIConstants.ENTRY_WIDTH_LARGE,
            placeholder_text=placeholder,
            font=FontScheme.ENTRY_FONT,
            fg_color=ColorScheme.INPUT_BG,
            text_color=ColorScheme.INPUT_TEXT,
            border_color=ColorScheme.INPUT_BORDER
        )
        entry.pack(side="left", padx=UIConstants.PADDING_SMALL, expand=True, fill="x")
        
        if field_name:
            self.fields[field_name] = entry
            
        return entry
    
    def _create_combo_field(self, parent, label_text: str, field_name: str, 
                          values: list, required: bool = False, command=None):
        """コンボボックスフィールドの作成"""
        frame = ctk.CTkFrame(
            parent,
            fg_color=ColorScheme.CARD_BG,
            border_color=ColorScheme.FRAME_BORDER,
            border_width=1
        )
        frame.pack(fill="x", padx=UIConstants.PADDING_LARGE, pady=UIConstants.PADDING_SMALL)
        
        # ラベル
        label = ctk.CTkLabel(
            frame,
            text=f"{label_text}{'*' if required else ''}",
            anchor="w",
            width=UIConstants.LABEL_WIDTH_STANDARD,
            font=FontScheme.LABEL_FONT,
            text_color=ColorScheme.TEXT_PRIMARY
        )
        label.pack(side="left", padx=(UIConstants.PADDING_MEDIUM, UIConstants.PADDING_SMALL))
        
        # コンボボックス
        combo = ctk.CTkComboBox(
            frame,
            width=UIConstants.ENTRY_WIDTH_LARGE,
            values=values,
            state="readonly",
            command=command,
            font=FontScheme.ENTRY_FONT,
            fg_color=ColorScheme.INPUT_BG,
            text_color=ColorScheme.INPUT_TEXT,
            border_color=ColorScheme.INPUT_BORDER,
            button_color=ColorScheme.BUTTON_PRIMARY
        )
        combo.pack(side="left", padx=UIConstants.PADDING_SMALL, expand=True, fill="x")
        
        if field_name:
            self.fields[field_name] = combo
            
        return combo
    
    def _create_basic_info_section(self):
        """基本情報セクションの作成"""
        self._create_section_label(self.scroll_frame, "基本情報")
        
        self._create_input_field(self.scroll_frame, "プロジェクト名", True, "project_name")
        
        # 開始日入力
        self._create_input_field(self.scroll_frame, "開始日", True, "start_date", 
                               "YYYY-MM-DD")
        
        # 編集モードでない場合は今日の日付を設定
        if not self.edit_mode:
            self.fields['start_date'].insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        self._create_combo_field(self.scroll_frame, "ステータス", "status", 
                               AppConstants.PROJECT_STATUSES, True)
        
        # 新規作成時はデフォルトで「進行中」を設定
        if not self.edit_mode:
            self.fields['status'].set("進行中")
    
    def _create_personnel_section(self):
        """担当者情報セクションの作成"""
        self._create_section_label(self.scroll_frame, "担当者情報")
        
        self._create_input_field(self.scroll_frame, "担当者", True, "manager")
        self._create_input_field(self.scroll_frame, "確認者", True, "reviewer")
        self._create_input_field(self.scroll_frame, "承認者", True, "approver")
    
    def _create_simple_manufacturing_section(self):
        """簡易製造ライン情報セクションの作成"""
        self._create_section_label(self.scroll_frame, "製造ライン情報")
        
        self._create_input_field(self.scroll_frame, "事業部", False, "division", 
                               "事業部コードを入力")
        self._create_input_field(self.scroll_frame, "工場", False, "factory", 
                               "工場コードを入力")
        self._create_input_field(self.scroll_frame, "工程", False, "process", 
                               "工程コードを入力")
        self._create_input_field(self.scroll_frame, "ライン", False, "line", 
                               "ラインコードを入力")
    
    def _create_manufacturing_section(self):
        """詳細製造ライン情報セクションの作成"""
        if not self.master_data:
            self._create_simple_manufacturing_section()
            return
        
        self._create_section_label(self.scroll_frame, "製造ライン情報")
        
        # 事業部選択
        divisions = self.master_data.get_divisions()
        division_values = ['未選択'] + [f"{d['name']} ({d['code']})" for d in divisions]
        self._create_combo_field(
            self.scroll_frame, "事業部", "division", 
            division_values, False, self._on_division_change
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
        button_frame = ctk.CTkFrame(parent, fg_color=ColorScheme.CARD_BG)
        button_frame.pack(fill="x", pady=(UIConstants.PADDING_LARGE, 0))
        
        # 保存ボタン
        save_button = ctk.CTkButton(
            button_frame,
            text="保存",
            command=self._save,
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_PRIMARY,
            text_color=ColorScheme.BUTTON_TEXT,
            hover_color=ColorScheme.BUTTON_HOVER,
            width=UIConstants.BUTTON_WIDTH_MEDIUM
        )
        save_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
        
        # キャンセルボタン
        cancel_button = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            command=self._cancel,
            font=FontScheme.BUTTON_FONT,
            fg_color=ColorScheme.BUTTON_DANGER,
            hover_color="#CC2F26",
            width=UIConstants.BUTTON_WIDTH_MEDIUM
        )
        cancel_button.pack(side="right", padx=UIConstants.PADDING_SMALL)
        
        # フォームモード切り替えボタン（新規作成時のみ）
        if not self.edit_mode:
            mode_text = "詳細モード" if self.form_mode == "quick" else "クイックモード"
            switch_button = ctk.CTkButton(
                button_frame,
                text=mode_text,
                command=self._switch_form_mode,
                font=FontScheme.BUTTON_FONT,
                fg_color=ColorScheme.INFO,
                text_color=ColorScheme.BUTTON_TEXT,
                hover_color=ColorScheme.get_hover_color(ColorScheme.INFO),
                width=UIConstants.BUTTON_WIDTH_LARGE
            )
            switch_button.pack(side="left", padx=UIConstants.PADDING_SMALL)
    
    # マスターデータ連動処理
    def _on_division_change(self, event=None):
        """事業部選択時の処理"""
        selected = self.fields['division'].get()
        if selected == '未選択':
            self.current_selection['division'] = None
        else:
            self.current_selection['division'] = selected.split('(')[1].rstrip(')')
        
        self._update_factory_options()
        self._update_process_options()
        self._update_line_options()
    
    def _on_factory_change(self, event=None):
        """工場選択時の処理"""
        selected = self.fields['factory'].get()
        if selected == '未選択':
            self.current_selection['factory'] = None
        else:
            self.current_selection['factory'] = selected.split('(')[1].rstrip(')')
        
        self._update_process_options()
        self._update_line_options()
    
    def _on_process_change(self, event=None):
        """工程選択時の処理"""
        selected = self.fields['process'].get()
        if selected == '未選択':
            self.current_selection['process'] = None
        else:
            self.current_selection['process'] = selected.split('(')[1].rstrip(')')
        
        self._update_line_options()
    
    def _on_line_change(self, event=None):
        """ライン選択時の処理"""
        selected = self.fields['line'].get()
        if selected == '未選択':
            self.current_selection['line'] = None
        else:
            self.current_selection['line'] = selected.split('(')[1].rstrip(')')
    
    def _update_factory_options(self):
        """工場の選択肢を更新"""
        if not self.master_data:
            return
            
        factories = self.master_data.get_factories(self.current_selection['division'])
        values = ['未選択'] + [f"{f['name']} ({f['code']})" for f in factories]
        self.fields['factory'].configure(values=values)
        self.fields['factory'].set('未選択')
    
    def _update_process_options(self):
        """工程の選択肢を更新"""
        if not self.master_data:
            return
            
        processes = self.master_data.get_processes(
            self.current_selection['division'],
            self.current_selection['factory']
        )
        values = ['未選択'] + [f"{p['name']} ({p['code']})" for p in processes]
        self.fields['process'].configure(values=values)
        self.fields['process'].set('未選択')
    
    def _update_line_options(self):
        """ラインの選択肢を更新"""
        if not self.master_data:
            return
            
        lines = self.master_data.get_lines(
            self.current_selection['division'],
            self.current_selection['factory'],
            self.current_selection['process']
        )
        values = ['未選択'] + [f"{l['name']} ({l['code']})" for l in lines]
        self.fields['line'].configure(values=values)
        self.fields['line'].set('未選択')
    
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
                    # 詳細モードでマスターデータが利用可能な場合
                    if (self.form_mode == "detail" and self.master_data and 
                        field_name in ['division', 'factory', 'process', 'line']):
                        # マスターデータから名前を取得して設定
                        if value:
                            name = self.master_data.get_name_by_code(value, field_name)
                            if name:
                                display_value = f"{name} ({value})"
                                widget.set(display_value)
                                self.current_selection[field_name] = value
                            else:
                                widget.set('未選択')
                        else:
                            widget.set('未選択')
                    else:
                        widget.set(value)
                else:
                    widget.delete(0, 'end')
                    widget.insert(0, value)
        
        # 詳細モードでマスターデータの連動更新
        if self.form_mode == "detail" and self.master_data:
            self._update_factory_options()
            self._update_process_options()
            self._update_line_options()
    
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
                    elif isinstance(widget, ctk.CTkComboBox):
                        # 簡易モードでは直接設定
                        if self.form_mode == "quick":
                            widget.set(value)
                        
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
                error_msg = "\n".join(errors)
                ErrorHandler.handle_warning(error_msg, "入力検証")
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
        
        # 基本フィールド
        basic_fields = ['project_name', 'start_date', 'manager', 'reviewer', 'approver', 'status']
        for field in basic_fields:
            if field in self.fields:
                values[field] = self.fields[field].get().strip()
        
        # 製造ライン情報
        if self.form_mode == "detail" and self.master_data:
            # 詳細モードではcurrent_selectionから取得
            values['division'] = self.current_selection.get('division')
            values['factory'] = self.current_selection.get('factory')
            values['process'] = self.current_selection.get('process')
            values['line'] = self.current_selection.get('line')
        else:
            # 簡易モードでは直接入力値を取得
            manufacturing_fields = ['division', 'factory', 'process', 'line']
            for field in manufacturing_fields:
                if field in self.fields:
                    value = self.fields[field].get().strip()
                    values[field] = value if value else None
        
        return values
    
    def _cancel(self):
        """キャンセル処理"""
        self.window.destroy()
    
    def _switch_form_mode(self):
        """フォームモードの切り替え"""
        try:
            # 現在の値を保持
            current_values = self._get_form_values()
            
            # モードを切り替え
            new_mode = "detail" if self.form_mode == "quick" else "quick"
            
            # 新しいフォームを作成
            new_dialog = ProjectFormDialog(
                self.parent, self.project_service,
                edit_mode=False, callback=self.callback,
                form_mode=new_mode
            )
            
            # 値を新しいフォームに設定
            new_dialog._set_form_values(current_values)
            
            # 現在のフォームを閉じる
            self.window.destroy()
            
        except Exception as e:
            ErrorHandler.handle_error(e, "フォームモード切り替え")
    
    def _set_form_values(self, values: Dict[str, Any]):
        """フォームに値を設定"""
        for field_name, value in values.items():
            if field_name in self.fields and value:
                widget = self.fields[field_name]
                if isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, 'end')
                    widget.insert(0, str(value))
                elif isinstance(widget, ctk.CTkComboBox):
                    widget.set(str(value))