"""統一的なエラー処理メカニズムを提供するモジュール"""

import logging
import traceback
from typing import Optional, Callable, Dict, Any, Type, List
import tkinter as tk
from tkinter import messagebox

class ApplicationError(Exception):
    """アプリケーション固有のエラー基底クラス"""
    
    def __init__(self, title: str, message: str):
        """
        初期化
        
        Args:
            title: エラーのタイトル
            message: 詳細なエラーメッセージ
        """
        self.title = title
        self.message = message
        super().__init__(message)

class ConfigurationError(ApplicationError):
    """設定関連のエラー"""
    pass

class DatabaseError(ApplicationError):
    """データベース関連のエラー"""
    pass

class FileError(ApplicationError):
    """ファイル操作関連のエラー"""
    pass

class ValidationError(ApplicationError):
    """データ検証関連のエラー"""
    pass

class ErrorHandler:
    """統一的なエラー処理を提供するクラス"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self._error_registry = self._setup_error_registry()
    
    def _setup_error_registry(self) -> Dict[Type[Exception], Callable]:
        """
        エラータイプごとのハンドラー登録
        
        Returns:
            Dict[Type[Exception], Callable]: エラータイプとハンドラーの対応辞書
        """
        return {
            ConfigurationError: self._handle_configuration_error,
            DatabaseError: self._handle_database_error,
            FileError: self._handle_file_error,
            ValidationError: self._handle_validation_error,
            ApplicationError: self._handle_application_error,
            Exception: self._handle_general_error
        }
    
    def handle_error(self, error: Exception, title: Optional[str] = None, 
                   parent: Optional[tk.Widget] = None,
                   cleanup_func: Optional[Callable] = None) -> None:
        """
        エラーの処理
        
        Args:
            error: 発生したエラー
            title: エラーダイアログのタイトル（オプション）
            parent: エラーダイアログの親ウィンドウ（オプション）
            cleanup_func: クリーンアップ関数（オプション）
        """
        try:
            # エラータイプに応じたハンドラーの取得
            handler = self._get_error_handler(type(error))
            
            # クリーンアップ処理の実行
            if cleanup_func:
                try:
                    cleanup_func()
                except Exception as cleanup_error:
                    self.logger.error(f"クリーンアップエラー: {cleanup_error}")
            
            # エラー処理の実行
            handler(error, title, parent)
            
        except Exception as e:
            self.logger.error(f"エラーハンドリング中の例外: {e}\n{traceback.format_exc()}")
            self.show_error_dialog(
                "致命的なエラー",
                f"エラー処理中に問題が発生しました:\n{str(e)}",
                parent
            )
    
    def _get_error_handler(self, error_type: Type[Exception]) -> Callable:
        """
        エラータイプに応じたハンドラーを取得
        
        Args:
            error_type: エラーの型
            
        Returns:
            Callable: エラーハンドラー関数
        """
        for error_class, handler in self._error_registry.items():
            if issubclass(error_type, error_class):
                return handler
        return self._handle_general_error
    
    def _handle_configuration_error(self, error: ConfigurationError, title: Optional[str], parent: Optional[tk.Widget]) -> None:
        """
        設定エラーの処理
        
        Args:
            error: 設定エラー
            title: エラータイトル
            parent: 親ウィンドウ
        """
        self.logger.error(f"設定エラー: {error}\n{traceback.format_exc()}")
        self.show_error_dialog(
            title or "設定エラー",
            f"設定の読み込みまたは検証中にエラーが発生しました:\n{str(error)}",
            parent
        )
    
    def _handle_database_error(self, error: DatabaseError, title: Optional[str], parent: Optional[tk.Widget]) -> None:
        """
        データベースエラーの処理
        
        Args:
            error: データベースエラー
            title: エラータイトル
            parent: 親ウィンドウ
        """
        self.logger.error(f"データベースエラー: {error}\n{traceback.format_exc()}")
        self.show_error_dialog(
            title or "データベースエラー",
            f"データベース操作中にエラーが発生しました:\n{str(error)}",
            parent
        )
    
    def _handle_file_error(self, error: FileError, title: Optional[str], parent: Optional[tk.Widget]) -> None:
        """
        ファイルエラーの処理
        
        Args:
            error: ファイルエラー
            title: エラータイトル
            parent: 親ウィンドウ
        """
        self.logger.error(f"ファイルエラー: {error}\n{traceback.format_exc()}")
        self.show_error_dialog(
            title or "ファイルエラー",
            f"ファイル操作中にエラーが発生しました:\n{str(error)}",
            parent
        )
    
    def _handle_validation_error(self, error: ValidationError, title: Optional[str], parent: Optional[tk.Widget]) -> None:
        """
        検証エラーの処理
        
        Args:
            error: 検証エラー
            title: エラータイトル
            parent: 親ウィンドウ
        """
        self.logger.error(f"検証エラー: {error}")
        self.show_error_dialog(
            title or "検証エラー",
            f"データ検証中にエラーが発生しました:\n{str(error)}",
            parent
        )
    
    def _handle_application_error(self, error: ApplicationError, title: Optional[str], parent: Optional[tk.Widget]) -> None:
        """
        アプリケーションエラーの処理
        
        Args:
            error: アプリケーションエラー
            title: エラータイトル
            parent: 親ウィンドウ
        """
        self.logger.error(f"アプリケーションエラー: {error.title} - {error.message}\n{traceback.format_exc()}")
        self.show_error_dialog(
            title or error.title,
            error.message,
            parent
        )
    
    def _handle_general_error(self, error: Exception, title: Optional[str], parent: Optional[tk.Widget]) -> None:
        """
        一般エラーの処理
        
        Args:
            error: 一般エラー
            title: エラータイトル
            parent: 親ウィンドウ
        """
        self.logger.error(f"一般エラー: {error}\n{traceback.format_exc()}")
        self.show_error_dialog(
            title or "エラー",
            f"予期せぬエラーが発生しました:\n{str(error)}",
            parent
        )
    
    def show_error_dialog(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        エラーダイアログの表示
        
        Args:
            title: ダイアログのタイトル
            message: エラーメッセージ
            parent: 親ウィンドウ
        """
        try:
            messagebox.showerror(title, message, parent=parent)
        except Exception as e:
            self.logger.error(f"エラーダイアログ表示エラー: {e}")
    
    def show_warning_dialog(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        警告ダイアログの表示
        
        Args:
            title: ダイアログのタイトル
            message: 警告メッセージ
            parent: 親ウィンドウ
        """
        try:
            messagebox.showwarning(title, message, parent=parent)
        except Exception as e:
            self.logger.error(f"警告ダイアログ表示エラー: {e}")
    
    def show_info_dialog(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> None:
        """
        情報ダイアログの表示
        
        Args:
            title: ダイアログのタイトル
            message: 情報メッセージ
            parent: 親ウィンドウ
        """
        try:
            messagebox.showinfo(title, message, parent=parent)
        except Exception as e:
            self.logger.error(f"情報ダイアログ表示エラー: {e}")
    
    def confirm_dialog(self, title: str, message: str, parent: Optional[tk.Widget] = None) -> bool:
        """
        確認ダイアログの表示
        
        Args:
            title: ダイアログのタイトル
            message: 確認メッセージ
            parent: 親ウィンドウ
            
        Returns:
            bool: ユーザーが「はい」を選択した場合はTrue
        """
        try:
            return messagebox.askyesno(title, message, parent=parent)
        except Exception as e:
            self.logger.error(f"確認ダイアログ表示エラー: {e}")
            return False
    
    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        入力データの検証
        
        Args:
            data: 検証するデータ辞書
            required_fields: 必須フィールドのリスト
            
        Returns:
            List[str]: エラーメッセージのリスト（空なら問題なし）
        """
        errors = []
        
        # 必須フィールドの存在確認
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} は必須項目です")
        
        return errors
    
    def format_validation_errors(self, errors: List[str]) -> str:
        """
        検証エラーのフォーマット
        
        Args:
            errors: エラーメッセージのリスト
            
        Returns:
            str: フォーマットされたエラーメッセージ
        """
        return "以下の問題を解決してください:\n" + "\n".join(f"- {error}" for error in errors)