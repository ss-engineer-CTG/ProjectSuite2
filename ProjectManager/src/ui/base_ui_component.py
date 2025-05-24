"""UI基底コンポーネントを提供するモジュール"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any, Callable, Tuple, List, Union

from ProjectManager.src.ui.styles.color_scheme import ColorScheme
from ProjectManager.src.core.log_manager import get_logger


class BaseUIComponent:
    """UI基底コンポーネント - 共通のスタイルと機能を提供"""
    
    def __init__(self):
        """初期化"""
        self.logger = get_logger(__name__)
        self.colors = ColorScheme
        
        # フォント設定
        self.default_font = ("Meiryo", 12)
        self.header_font = ("Meiryo", 14, "bold")
        self.title_font = ("Meiryo", 20, "bold")
        self.small_font = ("Meiryo", 10)
        
        # 標準スタイル
        self.styles = {
            'padding': {'padx': 10, 'pady': 5},
            'margin': {'padx': 20, 'pady': 10},
            'button_width': 100,
            'label_width': 120,
            'entry_width': 300
        }
    
    def create_label(self, parent: ctk.CTkFrame, text: str, 
                   font: Optional[Union[tuple, str]] = None,
                   anchor: str = "w", width: Optional[int] = None,
                   text_color: Optional[str] = None,
                   padding: Optional[Dict[str, int]] = None) -> ctk.CTkLabel:
        """
        ラベルの作成
        
        Args:
            parent: 親ウィジェット
            text: ラベルのテキスト
            font: フォント設定
            anchor: テキストの配置 ("w", "e", "center" など)
            width: ラベルの幅
            text_color: テキスト色
            padding: パディング設定
            
        Returns:
            ctk.CTkLabel: 作成されたラベル
        """
        if font is None:
            font = self.default_font
            
        if text_color is None:
            text_color = self.colors.TEXT_PRIMARY
            
        padding = padding or self.styles['padding']
        
        # パラメータの準備（Noneの場合は除外）
        label_kwargs = {
            'master': parent,
            'text': text,
            'font': font,
            'anchor': anchor,
            'text_color': text_color
        }
        
        # widthがNoneでない場合のみ追加
        if width is not None:
            label_kwargs['width'] = width
        
        label = ctk.CTkLabel(**label_kwargs)
        
        return label
    
    def create_button(self, parent: ctk.CTkFrame, text: str, 
                     command: Callable, width: Optional[int] = None,
                     height: Optional[int] = None,
                     fg_color: Optional[str] = None,
                     hover_color: Optional[str] = None,
                     text_color: Optional[str] = None,
                     font: Optional[Union[tuple, str]] = None) -> ctk.CTkButton:
        """
        ボタンの作成
        
        Args:
            parent: 親ウィジェット
            text: ボタンのテキスト
            command: クリック時のコールバック関数
            width: ボタンの幅
            height: ボタンの高さ
            fg_color: 背景色
            hover_color: ホバー時の色
            text_color: テキスト色
            font: フォント設定
            
        Returns:
            ctk.CTkButton: 作成されたボタン
        """
        if width is None:
            width = self.styles['button_width']
            
        if font is None:
            font = self.default_font
            
        if fg_color is None:
            fg_color = self.colors.BUTTON_PRIMARY
            
        if hover_color is None:
            hover_color = self.colors.BUTTON_HOVER
            
        if text_color is None:
            text_color = self.colors.BUTTON_TEXT
        
        # パラメータの準備
        button_kwargs = {
            'master': parent,
            'text': text,
            'command': command,
            'width': width,
            'fg_color': fg_color,
            'hover_color': hover_color,
            'text_color': text_color,
            'font': font
        }
        
        # heightがNoneでない場合のみ追加
        if height is not None:
            button_kwargs['height'] = height
        
        button = ctk.CTkButton(**button_kwargs)
        
        return button
    
    def create_danger_button(self, parent: ctk.CTkFrame, text: str, 
                           command: Callable, width: Optional[int] = None,
                           height: Optional[int] = None,
                           font: Optional[Union[tuple, str]] = None) -> ctk.CTkButton:
        """
        危険なアクションを実行するボタンの作成
        
        Args:
            parent: 親ウィジェット
            text: ボタンのテキスト
            command: クリック時のコールバック関数
            width: ボタンの幅
            height: ボタンの高さ
            font: フォント設定
            
        Returns:
            ctk.CTkButton: 作成されたボタン
        """
        return self.create_button(
            parent,
            text,
            command,
            width,
            height,
            fg_color=self.colors.BUTTON_DANGER,
            hover_color="#CC2F26",  # 少し暗めの赤
            font=font
        )
    
    def create_entry(self, parent: ctk.CTkFrame, width: Optional[int] = None,
                    placeholder: Optional[str] = None,
                    text_var: Optional[tk.StringVar] = None) -> ctk.CTkEntry:
        """
        入力フィールドの作成
        
        Args:
            parent: 親ウィジェット
            width: フィールドの幅
            placeholder: プレースホルダーテキスト
            text_var: テキスト変数
            
        Returns:
            ctk.CTkEntry: 作成された入力フィールド
        """
        if width is None:
            width = self.styles['entry_width']
        
        # パラメータの準備
        entry_kwargs = {
            'master': parent,
            'width': width,
            'font': self.default_font,
            'fg_color': self.colors.INPUT_BG,
            'text_color': self.colors.INPUT_TEXT,
            'border_color': self.colors.INPUT_BORDER
        }
        
        # オプションパラメータの追加
        if placeholder is not None:
            entry_kwargs['placeholder_text'] = placeholder
        if text_var is not None:
            entry_kwargs['textvariable'] = text_var
        
        entry = ctk.CTkEntry(**entry_kwargs)
        
        return entry
    
    def create_combo_box(self, parent: ctk.CTkFrame, values: List[str],
                        width: Optional[int] = None,
                        command: Optional[Callable] = None,
                        state: str = "readonly",
                        variable: Optional[tk.StringVar] = None) -> ctk.CTkComboBox:
        """
        コンボボックスの作成
        
        Args:
            parent: 親ウィジェット
            values: 選択肢のリスト
            width: フィールドの幅
            command: 選択変更時のコールバック関数
            state: 状態（"normal" または "readonly"）
            variable: 変数
            
        Returns:
            ctk.CTkComboBox: 作成されたコンボボックス
        """
        if width is None:
            width = self.styles['entry_width']
        
        # パラメータの準備
        combo_kwargs = {
            'master': parent,
            'values': values,
            'width': width,
            'state': state,
            'font': self.default_font,
            'fg_color': self.colors.INPUT_BG,
            'text_color': self.colors.INPUT_TEXT,
            'border_color': self.colors.INPUT_BORDER,
            'button_color': self.colors.BUTTON_PRIMARY,
            'button_hover_color': self.colors.BUTTON_HOVER,
            'dropdown_fg_color': self.colors.CARD_BG
        }
        
        # オプションパラメータの追加
        if command is not None:
            combo_kwargs['command'] = command
        if variable is not None:
            combo_kwargs['variable'] = variable
        
        combo = ctk.CTkComboBox(**combo_kwargs)
        
        return combo
    
    def create_frame(self, parent: ctk.CTkFrame, fg_color: Optional[str] = None,
                   border_width: int = 0, border_color: Optional[str] = None,
                   corner_radius: int = 10, width: Optional[int] = None,
                   height: Optional[int] = None) -> ctk.CTkFrame:
        """
        フレームの作成
        
        Args:
            parent: 親ウィジェット
            fg_color: 背景色
            border_width: ボーダー幅
            border_color: ボーダー色
            corner_radius: 角の丸み
            width: フレームの幅
            height: フレームの高さ
            
        Returns:
            ctk.CTkFrame: 作成されたフレーム
        """
        if fg_color is None:
            fg_color = self.colors.CARD_BG
            
        if border_color is None and border_width > 0:
            border_color = self.colors.FRAME_BORDER
        
        # パラメータの準備
        frame_kwargs = {
            'master': parent,
            'fg_color': fg_color,
            'border_width': border_width,
            'corner_radius': corner_radius
        }
        
        # border_colorがある場合のみ追加
        if border_color is not None:
            frame_kwargs['border_color'] = border_color
            
        # widthがある場合のみ追加
        if width is not None:
            frame_kwargs['width'] = width
            
        # heightがある場合のみ追加
        if height is not None:
            frame_kwargs['height'] = height
        
        frame = ctk.CTkFrame(**frame_kwargs)
        
        return frame
    
    def create_scrollable_frame(self, parent: ctk.CTkFrame,
                              fg_color: Optional[str] = None,
                              label_text: str = "",
                              label_font: Optional[Union[tuple, str]] = None) -> ctk.CTkScrollableFrame:
        """
        スクロール可能なフレームの作成
        
        Args:
            parent: 親ウィジェット
            fg_color: 背景色
            label_text: ラベルテキスト
            label_font: ラベルフォント
            
        Returns:
            ctk.CTkScrollableFrame: 作成されたスクロール可能フレーム
        """
        if fg_color is None:
            fg_color = self.colors.BACKGROUND
            
        if label_font is None and label_text:
            label_font = self.header_font
        
        # パラメータの準備
        frame_kwargs = {
            'master': parent,
            'fg_color': fg_color,
            'scrollbar_button_color': self.colors.SCROLLBAR_FG,
            'scrollbar_button_hover_color': self.colors.get_hover_color(self.colors.SCROLLBAR_FG)
        }
        
        # label_textがある場合のみ追加
        if label_text:
            frame_kwargs['label_text'] = label_text
        
        frame = ctk.CTkScrollableFrame(**frame_kwargs)
        
        if hasattr(frame, '_scrollbar'):
            frame._scrollbar.configure(
                button_color=self.colors.SCROLLBAR_FG,
                button_hover_color=self.colors.get_hover_color(self.colors.SCROLLBAR_FG)
            )
        
        if hasattr(frame, '_label') and label_text:
            frame._label.configure(
                font=label_font,
                text_color=self.colors.TEXT_PRIMARY
            )
        
        return frame
    
    def create_form_field(self, parent: ctk.CTkFrame, label_text: str,
                        required: bool = False, placeholder: Optional[str] = None,
                        validator: Optional[Callable] = None) -> Tuple[ctk.CTkEntry, ctk.CTkFrame]:
        """
        入力フィールドとラベルを含むフォームフィールドの作成
        
        Args:
            parent: 親ウィジェット
            label_text: ラベルテキスト
            required: 必須フィールドかどうか
            placeholder: プレースホルダーテキスト
            validator: 入力検証関数
            
        Returns:
            Tuple[ctk.CTkEntry, ctk.CTkFrame]: (入力フィールド, フレーム)
        """
        frame = self.create_frame(
            parent,
            border_width=1
        )
        
        # ラベル
        label = self.create_label(
            frame,
            text=f"{label_text}{'*' if required else ''}",
            width=self.styles['label_width']
        )
        label.pack(side="left", padx=(10, 5))
        
        # 入力フィールド
        entry = self.create_entry(
            frame,
            placeholder=placeholder
        )
        entry.pack(side="left", padx=5, expand=True, fill="x")
        
        # バリデーション関数を設定
        if validator:
            entry.validator = validator
        
        return entry, frame
    
    def create_form_combo(self, parent: ctk.CTkFrame, label_text: str,
                        values: List[str], required: bool = False,
                        command: Optional[Callable] = None) -> Tuple[ctk.CTkComboBox, ctk.CTkFrame]:
        """
        コンボボックスとラベルを含むフォームフィールドの作成
        
        Args:
            parent: 親ウィジェット
            label_text: ラベルテキスト
            values: 選択肢のリスト
            required: 必須フィールドかどうか
            command: 選択変更時のコールバック関数
            
        Returns:
            Tuple[ctk.CTkComboBox, ctk.CTkFrame]: (コンボボックス, フレーム)
        """
        frame = self.create_frame(
            parent,
            border_width=1
        )
        
        # ラベル
        label = self.create_label(
            frame,
            text=f"{label_text}{'*' if required else ''}",
            width=self.styles['label_width']
        )
        label.pack(side="left", padx=(10, 5))
        
        # コンボボックス
        combo = self.create_combo_box(
            frame,
            values=values,
            command=command
        )
        combo.pack(side="left", padx=5, expand=True, fill="x")
        
        return combo, frame
    
    def create_section_header(self, parent: ctk.CTkFrame, text: str) -> ctk.CTkFrame:
        """
        セクションヘッダーの作成
        
        Args:
            parent: 親ウィジェット
            text: ヘッダーテキスト
            
        Returns:
            ctk.CTkFrame: 作成されたフレーム
        """
        frame = self.create_frame(parent)
        frame.pack(fill="x", **self.styles['margin'])
        
        label = self.create_label(
            frame,
            text=text,
            font=self.header_font
        )
        label.pack(pady=10, padx=10, anchor="w")
        
        return frame
    
    def create_button_bar(self, parent: ctk.CTkFrame, buttons: List[Dict]) -> ctk.CTkFrame:
        """
        ボタンバーの作成
        
        Args:
            parent: 親ウィジェット
            buttons: ボタン定義のリスト。各辞書には 'text', 'command', 'side' などのキーを含む
            
        Returns:
            ctk.CTkFrame: 作成されたフレーム
        """
        frame = self.create_frame(parent)
        
        for button_def in buttons:
            side = button_def.get('side', 'right')
            is_danger = button_def.get('is_danger', False)
            width = button_def.get('width', self.styles['button_width'])
            
            if is_danger:
                button = self.create_danger_button(
                    frame,
                    text=button_def['text'],
                    command=button_def['command'],
                    width=width
                )
            else:
                button = self.create_button(
                    frame,
                    text=button_def['text'],
                    command=button_def['command'],
                    width=width
                )
            
            button.pack(side=side, padx=5)
        
        return frame
    
    def clear_frame(self, frame: ctk.CTkFrame) -> None:
        """
        フレーム内のすべてのウィジェットを削除
        
        Args:
            frame: クリアするフレーム
        """
        for widget in frame.winfo_children():
            widget.destroy()
    
    def confirm_action(self, title: str, message: str) -> bool:
        """
        確認ダイアログを表示
        
        Args:
            title: ダイアログのタイトル
            message: 確認メッセージ
            
        Returns:
            bool: ユーザーが「はい」を選択した場合はTrue
        """
        return tk.messagebox.askyesno(title, message)
    
    def show_message(self, title: str, message: str, message_type: str = 'info') -> None:
        """
        メッセージダイアログを表示
        
        Args:
            title: ダイアログのタイトル
            message: メッセージ
            message_type: メッセージの種類 ('info', 'warning', 'error')
        """
        if message_type == 'warning':
            tk.messagebox.showwarning(title, message)
        elif message_type == 'error':
            tk.messagebox.showerror(title, message)
        else:
            tk.messagebox.showinfo(title, message)