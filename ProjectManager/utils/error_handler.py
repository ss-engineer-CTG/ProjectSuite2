"""
統一エラーハンドリング
KISS原則: シンプルなエラー処理
DRY原則: 重複するエラー処理の統合
"""

import logging
import traceback
import sys
from typing import Optional, Callable
from tkinter import messagebox

class ErrorHandler:
    """統一エラーハンドリングクラス"""
    
    logger = logging.getLogger(__name__)
    
    @staticmethod
    def handle_error(error: Exception, context: str = "", show_dialog: bool = True, 
                    parent=None) -> None:
        """一般的なエラーハンドリング"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        
        # ログに記録
        ErrorHandler.logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        # ユーザーにダイアログ表示
        if show_dialog:
            try:
                messagebox.showerror("エラー", error_msg, parent=parent)
            except Exception:
                # ダイアログ表示に失敗した場合はログのみ
                ErrorHandler.logger.error("エラーダイアログの表示に失敗しました")
    
    @staticmethod
    def handle_critical_error(error: Exception, context: str = "") -> None:
        """致命的エラーのハンドリング"""
        error_msg = f"致命的エラー - {context}: {str(error)}" if context else f"致命的エラー: {str(error)}"
        
        # ログに記録
        ErrorHandler.logger.critical(f"{error_msg}\n{traceback.format_exc()}")
        
        # ユーザーに通知
        try:
            messagebox.showerror("致命的エラー", 
                               f"{error_msg}\n\nアプリケーションを終了します。")
        except Exception:
            print(f"致命的エラー: {error_msg}")
        
        # アプリケーション終了
        sys.exit(1)
    
    @staticmethod
    def handle_warning(message: str, context: str = "", show_dialog: bool = True,
                      parent=None) -> None:
        """警告のハンドリング"""
        warning_msg = f"{context}: {message}" if context else message
        
        # ログに記録
        ErrorHandler.logger.warning(warning_msg)
        
        # ユーザーにダイアログ表示
        if show_dialog:
            try:
                messagebox.showwarning("警告", warning_msg, parent=parent)
            except Exception:
                ErrorHandler.logger.error("警告ダイアログの表示に失敗しました")
    
    @staticmethod
    def handle_info(message: str, context: str = "", show_dialog: bool = False,
                   parent=None) -> None:
        """情報メッセージのハンドリング"""
        info_msg = f"{context}: {message}" if context else message
        
        # ログに記録
        ErrorHandler.logger.info(info_msg)
        
        # ユーザーにダイアログ表示
        if show_dialog:
            try:
                messagebox.showinfo("情報", info_msg, parent=parent)
            except Exception:
                ErrorHandler.logger.error("情報ダイアログの表示に失敗しました")
    
    @staticmethod
    def safe_execute(func: Callable, context: str = "", show_dialog: bool = True,
                    parent=None, default_return=None):
        """安全な関数実行（例外をキャッチ）"""
        try:
            return func()
        except Exception as e:
            ErrorHandler.handle_error(e, context, show_dialog, parent)
            return default_return
    
    @staticmethod
    def validate_and_execute(validation_func: Callable, execute_func: Callable,
                           context: str = "", parent=None):
        """検証付き実行"""
        try:
            # 検証実行
            is_valid, errors = validation_func()
            if not is_valid:
                error_msg = "\n".join(errors) if isinstance(errors, list) else str(errors)
                ErrorHandler.handle_warning(error_msg, context, True, parent)
                return False
            
            # メイン処理実行
            result = execute_func()
            return result
            
        except Exception as e:
            ErrorHandler.handle_error(e, context, True, parent)
            return False
    
    @staticmethod
    def confirmation_dialog(message: str, title: str = "確認", parent=None) -> bool:
        """確認ダイアログの表示"""
        try:
            return messagebox.askyesno(title, message, parent=parent)
        except Exception as e:
            ErrorHandler.logger.error(f"確認ダイアログの表示に失敗: {e}")
            return False
    
    @staticmethod
    def choice_dialog(message: str, title: str = "選択", parent=None) -> Optional[str]:
        """選択ダイアログの表示"""
        try:
            return messagebox.askyesnocancel(title, message, parent=parent)
        except Exception as e:
            ErrorHandler.logger.error(f"選択ダイアログの表示に失敗: {e}")
            return None

class DatabaseErrorHandler:
    """データベース専用エラーハンドリング"""
    
    @staticmethod
    def handle_db_error(error: Exception, operation: str = "", 
                       show_dialog: bool = True, parent=None) -> None:
        """データベースエラーの特別処理"""
        import sqlite3
        
        if isinstance(error, sqlite3.IntegrityError):
            if "UNIQUE constraint failed" in str(error):
                ErrorHandler.handle_warning("同名のデータが既に存在します", 
                                          f"データベース操作({operation})", 
                                          show_dialog, parent)
            elif "FOREIGN KEY constraint failed" in str(error):
                ErrorHandler.handle_warning("関連するデータが見つかりません", 
                                          f"データベース操作({operation})", 
                                          show_dialog, parent)
            else:
                ErrorHandler.handle_error(error, f"データベース整合性エラー({operation})", 
                                        show_dialog, parent)
        elif isinstance(error, sqlite3.OperationalError):
            ErrorHandler.handle_error(error, f"データベース操作エラー({operation})", 
                                    show_dialog, parent)
        else:
            ErrorHandler.handle_error(error, f"データベースエラー({operation})", 
                                    show_dialog, parent)

class FileErrorHandler:
    """ファイル操作専用エラーハンドリング"""
    
    @staticmethod
    def handle_file_error(error: Exception, file_path: str = "", 
                         operation: str = "", show_dialog: bool = True, parent=None) -> None:
        """ファイル操作エラーの特別処理"""
        
        if isinstance(error, FileNotFoundError):
            ErrorHandler.handle_warning(f"ファイルが見つかりません: {file_path}", 
                                      f"ファイル操作({operation})", 
                                      show_dialog, parent)
        elif isinstance(error, PermissionError):
            ErrorHandler.handle_warning(f"ファイルへのアクセス権限がありません: {file_path}", 
                                      f"ファイル操作({operation})", 
                                      show_dialog, parent)
        elif isinstance(error, UnicodeDecodeError):
            ErrorHandler.handle_warning(f"ファイルのエンコーディングが正しくありません: {file_path}", 
                                      f"ファイル操作({operation})", 
                                      show_dialog, parent)
        else:
            ErrorHandler.handle_error(error, f"ファイル操作エラー({operation}): {file_path}", 
                                    show_dialog, parent)