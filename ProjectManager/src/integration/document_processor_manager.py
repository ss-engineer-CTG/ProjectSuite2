"""ドキュメント処理機能の統合管理クラス"""

import customtkinter as ctk
import tkinter as tk
from pathlib import Path
from typing import Optional, Dict, Any

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.path_manager import PathManager
from ProjectManager.src.core.error_handler import ErrorHandler

class DocumentProcessorManager:
    """ドキュメント処理機能の統合管理クラス"""
    
    def __init__(self, main_config: dict):
        """
        初期化
        
        Args:
            main_config: メインアプリケーションの設定
        """
        self.main_config = main_config
        self.doc_processor_window = None
        self.doc_processor_gui = None
        self.logger = get_logger(__name__)
        self.path_manager = PathManager()
        self.error_handler = ErrorHandler()
        
        # 設定の初期化
        self.initialize()

    def initialize(self) -> None:
        """初期化処理"""
        try:
            # パスの解決
            integration_paths = self._resolve_integration_paths()
            
            # CreateProjectListが利用可能か確認
            try:
                # インポートをここで試みる
                from CreateProjectList.gui.main_window.document_processor_gui import DocumentProcessorGUI
                from CreateProjectList.utils.config_manager import ConfigManager
                from CreateProjectList.utils.log_manager import LogManager
                
                # ConfigManagerの初期化
                self.config_manager = ConfigManager()
                self.config_manager.initialize_with_parent_config({
                    'paths': integration_paths,
                    'main_config': self.main_config
                })
                
                self.logger.info("DocumentProcessorManager initialized successfully")
                
            except ImportError as e:
                self.logger.warning(f"CreateProjectList モジュールが見つかりません: {e}")
                
        except Exception as e:
            self.error_handler.handle_error(e, "初期化エラー")
    
    def _resolve_integration_paths(self) -> Dict[str, str]:
        """
        統合機能用のパス解決
        
        Returns:
            Dict[str, str]: 解決されたパス情報
        """
        # 基本パスを取得
        template_dir = self.path_manager.get_path("TEMPLATES_DIR")
        output_dir = self.path_manager.get_path("OUTPUT_BASE_DIR")
        temp_dir = self.path_manager.get_path("TEMP_DIR")
        master_dir = self.path_manager.get_path("MASTER_DIR")
        export_dir = self.path_manager.get_path("EXPORTS_DIR")
        
        # パスの設定
        paths = {
            'template_dir': str(template_dir),
            'output_dir': str(output_dir),
            'temp_dir': str(temp_dir),
            'master_dir': str(master_dir),
            'export_dir': str(export_dir)
        }
        
        # 各ディレクトリを確保
        for path_name, path_str in paths.items():
            self.path_manager.ensure_directory(path_str)
        
        self.logger.info(f"パス解決完了: {paths}")
        return paths

    def create_window(self, parent: tk.Widget, project_data: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """
        ドキュメント処理ウィンドウの作成
        
        Args:
            parent: 親ウィンドウ
            project_data: プロジェクトデータ（オプション）
            
        Returns:
            Optional[Any]: 作成されたGUIインスタンス
        """
        try:
            try:
                # CreateProjectListモジュールをインポート
                from CreateProjectList.gui.main_window.document_processor_gui import DocumentProcessorGUI
            except ImportError:
                self.error_handler.show_error_dialog(
                    "機能エラー",
                    "ドキュメント処理機能が利用できません。\n"
                    "CreateProjectListモジュールがインストールされていることを確認してください。",
                    parent
                )
                return None
            
            # 既存のウィンドウがある場合はクリーンアップ
            if hasattr(self, 'doc_processor_window') and self.doc_processor_window:
                self.cleanup()

            # プロジェクトデータの確認
            if not project_data:
                self.error_handler.show_warning_dialog(
                    "警告",
                    "プロジェクトを選択してください。",
                    parent
                )
                return None

            # プロジェクトパスの確認
            if not project_data.get('project_path'):
                self.error_handler.show_error_dialog(
                    "エラー",
                    "プロジェクトフォルダが設定されていません。",
                    parent
                )
                return None

            project_path = Path(project_data['project_path'])
            if not project_path.exists():
                try:
                    # 出力フォルダがない場合は作成
                    project_path.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"プロジェクトフォルダを作成しました: {project_path}")
                except Exception as e:
                    self.error_handler.show_error_dialog(
                        "エラー",
                        f"プロジェクトフォルダが存在せず、作成に失敗しました: {e}",
                        parent
                    )
                    return None

            # 新しいウィンドウの作成
            self.doc_processor_window = ctk.CTkToplevel(parent)
            self.doc_processor_window.title("ドキュメント処理")
            
            # ウィンドウの位置とサイズの設定
            window_width = 800
            window_height = 600
            x = parent.winfo_x() + (parent.winfo_width() - window_width) // 2
            y = parent.winfo_y() + (parent.winfo_height() - window_height) // 2
            self.doc_processor_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # メインフレームの作成
            main_frame = ctk.CTkFrame(self.doc_processor_window)
            main_frame.pack(fill="both", expand=True)
            
            # 内部のパディングを持つコンテナフレームを作成
            container_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            container_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # GUIの初期化
            self.doc_processor_gui = DocumentProcessorGUI(container_frame)
            
            # プロジェクトデータとパスの設定
            self.doc_processor_gui.processor.current_project_data = project_data
            self.doc_processor_gui.processor.last_output_folder = str(project_path)
            
            # モーダル設定
            self.doc_processor_window.transient(parent)
            self.doc_processor_window.grab_set()
            
            # クローズ時の処理設定
            self.doc_processor_window.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            return self.doc_processor_gui
                
        except Exception as e:
            self.error_handler.handle_error(e, "機能エラー", parent)
            return None

    def set_project_data(self, project_data: Dict[str, Any]) -> None:
        """
        プロジェクトデータの設定
        
        Args:
            project_data: 設定するプロジェクトデータ
        """
        try:
            if self.doc_processor_gui:
                self.doc_processor_gui.set_project_data(project_data)
            else:
                self.logger.warning("GUIが初期化されていません")
                
        except Exception as e:
            self.error_handler.handle_error(e, "設定エラー", self.doc_processor_window)

    def on_closing(self) -> None:
        """ウィンドウが閉じられる時の処理"""
        try:
            self.cleanup()
            if self.doc_processor_window:
                self.doc_processor_window.grab_release()
                self.doc_processor_window.destroy()
                self.doc_processor_window = None
                
        except Exception as e:
            self.logger.error(f"クローズ処理エラー: {e}")

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self.doc_processor_gui:
                try:
                    self.doc_processor_gui.cleanup()
                except:
                    pass
                self.doc_processor_gui = None
                
            self.logger.info("DocumentProcessorManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"クリーンアップエラー: {e}")

    def is_window_open(self) -> bool:
        """
        ウィンドウが開いているか確認
        
        Returns:
            bool: ウィンドウが開いている場合True
        """
        return bool(self.doc_processor_window and self.doc_processor_window.winfo_exists())

    def focus_window(self) -> None:
        """ウィンドウにフォーカスを設定"""
        if self.is_window_open():
            self.doc_processor_window.lift()
            self.doc_processor_window.focus_force()