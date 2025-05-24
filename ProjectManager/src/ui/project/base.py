"""プロジェクトフォームの基本クラス"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Dict, Any, Callable

from ProjectManager.src.ui.base_ui_component import BaseUIComponent
from ProjectManager.src.core.config_manager import ConfigManager
from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.error_handler import ErrorHandler

class BaseProjectForm(BaseUIComponent):
    """プロジェクトフォームの基本クラス"""
    
    def __init__(self):
        """初期化"""
        super().__init__()
        self.logger = get_logger(__name__)
        self.config_manager = ConfigManager()
        self.error_handler = ErrorHandler()
        self.fields = {}  # 入力フィールドの参照を保持
    
    def _create_section_label(self, parent, text: str):
        """セクションラベルの作成"""
        frame = self.create_frame(parent)
        frame.pack(fill="x", padx=20, pady=(20, 10))
        
        label = self.create_label(
            frame,
            text=text,
            font=self.header_font
        )
        label.pack(pady=10, padx=10, anchor="w")
        
        return frame

    def _create_input_field(self, parent, label_text, required=False, attr_name=None, 
                         placeholder=None, validator=None):
        """入力フィールドの作成"""
        entry, frame = self.create_form_field(
            parent,
            label_text=label_text,
            required=required,
            placeholder=placeholder
        )
        frame.pack(fill="x", padx=20, pady=5)
        
        if attr_name:
            setattr(self, attr_name, entry)
            self.fields[attr_name] = entry
        
        # バリデータの設定
        if validator:
            entry.validator = validator
            
        return entry, frame

    def _create_combo_field(self, parent, label_text, attr_name, values, required=False, command=None):
        """コンボボックスフィールドの作成"""
        combo, frame = self.create_form_combo(
            parent,
            label_text=label_text,
            values=values,
            required=required,
            command=command
        )
        frame.pack(fill="x", padx=20, pady=5)
        
        if attr_name:
            setattr(self, attr_name, combo)
            self.fields[attr_name] = combo
            
        return combo

    def _validate_date(self, value):
        """日付のバリデーション"""
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True, ""
        except ValueError:
            return False, "日付の形式が正しくありません (YYYY-MM-DD)"

    def _validate_project_name(self, value):
        """プロジェクト名のバリデーション"""
        if len(value) < 3:
            return False, "プロジェクト名は3文字以上で入力してください"
        return True, ""

    def load_default_values(self):
        """デフォルト値の読み込み"""
        try:
            # 設定マネージャーから設定を取得
            default_values = {}
            
            # デフォルト値を取得
            default_keys = [
                'project_name', 'manager', 'reviewer', 'approver',
                'division', 'factory', 'process', 'line'
            ]
            
            for key in default_keys:
                value = self.config_manager.get_setting('defaults', key, '')
                if value:
                    default_values[key] = value
            
            # ウィジェットに値を設定
            for field_name, value in default_values.items():
                if field_name in self.fields and value:
                    widget = self.fields[field_name]
                    if isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, 'end')
                        widget.insert(0, value)
                    elif isinstance(widget, ctk.CTkComboBox):
                        widget.set(value)
                        
        except Exception as e:
            self.logger.warning(f"デフォルト値の読み込みエラー: {e}")