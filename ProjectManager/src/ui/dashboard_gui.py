"""ダッシュボードGUIクラス"""

import customtkinter as ctk
import tkinter as tk
from typing import Optional, Dict, Any, List
import logging
import traceback

from ProjectManager.src.ui.base_ui_component import BaseUIComponent
from ProjectManager.src.ui.project_list_view import ProjectListView
from ProjectManager.src.ui.project.quick_form import QuickProjectForm
from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.error_handler import ErrorHandler
from ProjectManager.src.services.gantt_chart_manager import GanttChartManager
from ProjectManager.src.integration.document_processor_manager import DocumentProcessorManager


class DashboardGUI(BaseUIComponent):
    """ダッシュボードGUIクラス"""
    
    def __init__(self, db_manager):
        """
        ダッシュボードGUIの初期化
        
        Args:
            db_manager: データベースマネージャーインスタンス
        """
        super().__init__()
        self.logger = get_logger(__name__)
        self.db_manager = db_manager
        self.error_handler = ErrorHandler()
        
        # 選択中のプロジェクト
        self.selected_project = None
        
        # ドキュメント処理マネージャー
        self.doc_processor_manager = None
        
        # 終了フラグ
        self.is_closing = False
        
        # 現在のフィルター設定
        self.current_filter = "進行中"
        
        # ガントチャートマネージャー
        self.gantt_chart_manager = GanttChartManager(db_manager)
        
        # ウィンドウ初期化
        self.window = None
        self.initialize_window()
        
        # プロジェクト作成ダイアログのインスタンス
        self.project_dialog = None
        
        # 初期化
        self.initialize_doc_processor()
        
        # プロジェクトリストの更新
        self.refresh_projects()
        
        self.logger.info("ダッシュボードGUIを初期化しました")
    
    def initialize_window(self) -> None:
        """メインウィンドウの初期化"""
        self.window = ctk.CTk()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.configure(fg_color=self.colors.BACKGROUND)
        self.setup_main_window()
    
    def initialize_doc_processor(self) -> None:
        """ドキュメント処理マネージャーの初期化"""
        try:
            config = {
                'base_dir': str(self.db_manager.path_manager.get_path("DATA_DIR")),
                'db_path': str(self.db_manager.path_manager.get_path("DB_PATH")),
                'master_dir': str(self.db_manager.path_manager.get_path("MASTER_DIR")),
                'output_dir': str(self.db_manager.path_manager.get_path("OUTPUT_BASE_DIR"))
            }
            self.doc_processor_manager = DocumentProcessorManager(config)
            self.logger.info("ドキュメント処理マネージャーを初期化しました")
        except Exception as e:
            self.error_handler.handle_error(e, "初期化エラー", self.window)
    
    def setup_main_window(self) -> None:
        """メインウィンドウ（ダッシュボード）の設定"""
        self.window.title("プロジェクト管理ダッシュボード")
        
        # スクリーンサイズの取得と設定
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        
        # ウィンドウを中央に配置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # メインフレーム
        self.main_frame = self.create_frame(
            self.window,
            fg_color=self.colors.BACKGROUND
        )
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ヘッダーフレーム
        self.header_frame = self.create_frame(self.main_frame)
        self.header_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # タイトル
        title_label = self.create_label(
            self.header_frame,
            text="プロジェクト一覧",
            font=self.title_font
        )
        title_label.pack(side="left", pady=10, padx=10)
        
        # フィルターフレーム
        filter_frame = self.create_frame(self.header_frame)
        filter_frame.pack(side="right", pady=10, padx=10)
        
        # フィルターラベル
        filter_label = self.create_label(
            filter_frame,
            text="表示フィルター:"
        )
        filter_label.pack(side="left", padx=(0, 10))
        
        # フィルターコンボボックス
        self.filter_combo = self.create_combo_box(
            filter_frame,
            values=['進行中', '全て'],
            command=self.on_filter_change,
            width=120
        )
        self.filter_combo.set('進行中')
        self.filter_combo.pack(side="left", padx=(0, 10))
        
        # データベース更新ボタン
        update_button = self.create_button(
            filter_frame,
            text="データベース更新",
            command=self.update_ganttchart_paths,
            width=150
        )
        update_button.pack(side="left", padx=(0, 10))
        
        # 設定ボタン
        settings_button = self.create_button(
            filter_frame,
            text="設定",
            command=self.show_settings_dialog,
            width=80
        )
        settings_button.pack(side="left", padx=(0, 10))
        
        # ドキュメント処理ボタン
        doc_process_button = self.create_button(
            filter_frame,
            text="ドキュメント処理",
            command=self.show_document_processor,
            width=150
        )
        doc_process_button.pack(side="left", padx=(0, 10))
        
        # プロジェクト進捗ダッシュボードボタン
        dashboard_button = self.create_button(
            filter_frame,
            text="進捗ダッシュボード",
            command=self.launch_project_dashboard,
            width=150
        )
        dashboard_button.pack(side="left", padx=(0, 10))
        
        # ボタンフレーム
        button_frame = self.create_frame(self.header_frame)
        button_frame.pack(side="right", pady=10, padx=10)
        
        # 新規プロジェクト作成ボタン
        create_button = self.create_button(
            button_frame,
            text="新規プロジェクト作成",
            command=self.show_create_project_dialog
        )
        create_button.pack(side="right")
        
        # 選択中プロジェクト表示セクション
        self.selected_project_frame = self.create_frame(
            self.main_frame,
            height=100
        )
        self.selected_project_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # タイトル
        selected_title = self.create_label(
            self.selected_project_frame,
            text="選択中のプロジェクト",
            font=self.header_font
        )
        selected_title.pack(side="left", pady=10, padx=10)
        
        # 選択中プロジェクト情報
        self.selected_info = self.create_label(
            self.selected_project_frame,
            text="プロジェクトが選択されていません",
            text_color=self.colors.TEXT_SECONDARY
        )
        self.selected_info.pack(side="left", pady=10, padx=10)
        
        # プロジェクトリストビュー
        self.project_list_view = ProjectListView(
            self.main_frame,
            self.db_manager,
            self.on_project_selected,
            self.edit_project,
            self.delete_project
        )
        self.project_list_view.frame.pack(fill="both", expand=True, padx=20)
    
    def on_filter_change(self, choice) -> None:
        """
        フィルター選択時の処理
        
        Args:
            choice: 選択されたフィルター
        """
        self.current_filter = choice
        self.refresh_projects()
    
    def refresh_projects(self) -> None:
        """プロジェクト一覧の表示を更新"""
        if self.is_closing:
            self.logger.debug("ウィンドウが閉じているため更新をスキップ")
            return
        
        try:
            self.logger.debug("プロジェクト一覧の更新を開始")
            
            # プロジェクト一覧を取得とフィルタリング
            if self.current_filter == '全て':
                projects = self.db_manager.get_all_projects()
            else:
                projects = self.db_manager.get_all_projects(self.current_filter)
            
            # プロジェクトリストビューの更新
            self.project_list_view.update_projects(projects)
            
            # 選択状態の更新
            if self.selected_project:
                project = self.db_manager.get_project(self.selected_project['project_id'])
                if project:
                    self.selected_project = project
                    self.update_selected_info()
                else:
                    self.selected_project = None
                    self.update_selected_info()
            
            self.logger.debug(f"{len(projects)}件のプロジェクトを表示")
                
        except Exception as e:
            self.error_handler.handle_error(e, "データ取得エラー", self.window)
    
    def on_project_selected(self, project: Dict[str, Any]) -> None:
        """
        プロジェクト選択時の処理
        
        Args:
            project: 選択されたプロジェクト
        """
        self.selected_project = project
        self.update_selected_info()
    
    def update_selected_info(self) -> None:
        """選択中プロジェクト情報の更新"""
        if self.selected_project:
            info_text = (
                f"プロジェクト名: {self.selected_project['project_name']} | "
                f"担当者: {self.selected_project['manager']} | "
                f"状態: {self.selected_project['status']}"
            )
            self.selected_info.configure(text=info_text)
        else:
            self.selected_info.configure(text="プロジェクトが選択されていません")
    
    def show_create_project_dialog(self) -> None:
        """新規プロジェクト作成ダイアログを表示"""
        if self.project_dialog is not None:
            self.project_dialog.window.destroy()
        
        self.project_dialog = QuickProjectForm(
            self.window,
            self.db_manager,
            callback=self.on_project_created
        )
    
    def edit_project(self, project_id: int) -> None:
        """
        プロジェクトの編集
        
        Args:
            project_id: 編集対象のプロジェクトID
        """
        try:
            project_data = self.db_manager.get_project(project_id)
            if not project_data:
                self.error_handler.show_error_dialog(
                    "エラー", 
                    "プロジェクトデータの取得に失敗しました。",
                    self.window
                )
                return

            if self.project_dialog is not None:
                self.project_dialog.window.destroy()

            self.project_dialog = QuickProjectForm(
                self.window,
                self.db_manager,
                callback=self.on_project_updated,
                edit_mode=True,
                project_data=project_data
            )

        except Exception as e:
            self.error_handler.handle_error(e, "編集エラー", self.window)
    
    def delete_project(self, project_id: int) -> None:
        """
        プロジェクトの削除
        
        Args:
            project_id: 削除対象のプロジェクトID
        """
        if self.error_handler.confirm_dialog(
            "確認", 
            "このプロジェクトを削除してもよろしいですか？",
            self.window
        ):
            try:
                self.db_manager.delete_project(project_id)
                
                # 削除したプロジェクトが選択中だった場合、選択を解除
                if self.selected_project and self.selected_project['project_id'] == project_id:
                    self.selected_project = None
                    self.update_selected_info()
                
                # プロジェクト一覧を更新
                self.refresh_projects()
                
                self.error_handler.show_info_dialog(
                    "成功", 
                    "プロジェクトを削除しました。",
                    self.window
                )
                
            except Exception as e:
                self.error_handler.handle_error(e, "削除エラー", self.window)
    
    def on_project_created(self) -> None:
        """プロジェクト作成後のコールバック"""
        self.refresh_projects()
            
        if self.project_dialog:
            self.project_dialog.window.destroy()
            self.project_dialog = None
    
    def on_project_updated(self) -> None:
        """プロジェクト更新後のコールバック"""
        self.refresh_projects()
            
        if self.project_dialog:
            self.project_dialog.window.destroy()
            self.project_dialog = None
    
    def show_settings_dialog(self) -> None:
        """設定ダイアログを表示"""
        try:
            from ProjectManager.src.ui.project_path_dialog import ProjectPathDialog
            ProjectPathDialog(self.window, self.on_settings_changed)
        except Exception as e:
            self.error_handler.handle_error(e, "設定エラー", self.window)
    
    def on_settings_changed(self) -> None:
        """設定変更後のコールバック"""
        try:
            # 必要に応じてパスの再読み込みや画面更新を行う
            self.logger.info("設定が変更されました。アプリケーションの再起動が必要です。")
            self.error_handler.show_info_dialog(
                "設定変更",
                "プロジェクトフォルダ設定を変更しました。\n"
                "変更を完全に適用するには、アプリケーションを再起動してください。",
                self.window
            )
        except Exception as e:
            self.error_handler.handle_error(e, "設定エラー", self.window)
    
    def show_document_processor(self) -> None:
        """ドキュメント処理ウィンドウを表示"""
        try:
            if not self.selected_project:
                self.error_handler.show_warning_dialog(
                    "警告",
                    "プロジェクトを選択してください。",
                    self.window
                )
                return

            # 既存のウィンドウがある場合はフォーカス
            if self.doc_processor_manager.is_window_open():
                self.doc_processor_manager.focus_window()
                return

            try:
                # 新しいウィンドウを作成
                processor_window = self.doc_processor_manager.create_window(
                    self.window,
                    self.selected_project
                )

                if processor_window:
                    # プロジェクトデータを設定
                    processor_window.set_project_data(self.selected_project)
                    self.logger.info("ドキュメント処理ウィンドウを表示しました")
                else:
                    raise ValueError("ウィンドウの作成に失敗しました")

            except Exception as e:
                self.logger.error(f"ドキュメント処理ウィンドウの作成エラー: {e}")
                raise

        except Exception as e:
            self.error_handler.handle_error(e, "機能エラー", self.window)
    
    def update_ganttchart_paths(self) -> None:
        """データベースの更新処理"""
        try:
            # 1. データベースマイグレーション
            self.logger.info("データベースマイグレーションを開始します")
            
            # 2. タスクデータの更新
            self.logger.info("タスクデータの更新を開始します")
            task_loader = self.db_manager.db_path
            projects_count, tasks_count, errors_count = task_loader.load_tasks()
            self.logger.info(
                f"タスクデータの更新が完了しました: "
                f"プロジェクト数 {projects_count}, タスク数 {tasks_count}, エラー数 {errors_count}"
            )

            # 3. ガントチャートパスの更新
            self.logger.info("ガントチャートパスの更新を開始します")
            stats = self.gantt_chart_manager.update_ganttchart_paths()
            
            # 結果メッセージの作成
            message = (
                f"データベース更新が完了しました\n\n"
                f"1. タスクデータの更新:\n"
                f"   - 処理対象プロジェクト数: {projects_count}\n"
                f"   - 登録タスク数: {tasks_count}\n"
                f"   - エラー数: {errors_count}\n\n"
                f"2. ガントチャート更新:\n"
                f"   - 処理対象プロジェクト数: {stats['total']}\n"
                f"   - 更新成功: {stats['updated']}\n"
                f"   - 未検出: {stats['not_found']}\n"
                f"   - エラー: {stats['error']}\n"
            )
            
            # 結果表示
            self.error_handler.show_info_dialog("更新完了", message, self.window)
            
            # プロジェクト一覧を更新
            self.refresh_projects()
            
        except Exception as e:
            self.error_handler.handle_error(e, "更新エラー", self.window)
    
    def launch_project_dashboard(self) -> None:
        """
        プロジェクト進捗ダッシュボードアプリを起動
        """
        try:
            import subprocess
            import os
            
            # ダッシュボードの固定パス
            dashboard_path = r"C:\Program Files (x86)\ProjectSuite Complete\ProjectDashboard\Project Dashboard.exe"
            
            # ファイルの存在を確認
            if os.path.exists(dashboard_path):
                # サブプロセスとして起動
                subprocess.Popen([dashboard_path])
                self.logger.info("プロジェクト進捗ダッシュボードを起動しました")
            else:
                # 実行ファイルが見つからない場合の処理
                self.error_handler.show_warning_dialog(
                    "警告", 
                    "プロジェクト進捗ダッシュボードが見つかりません。\n"
                    f"確認パス: {dashboard_path}",
                    self.window
                )
                
        except Exception as e:
            self.error_handler.handle_error(e, "起動エラー", self.window)
    
    def on_closing(self) -> None:
        """アプリケーション終了時の処理"""
        try:
            self.logger.debug("アプリケーション終了処理を開始")
            self.is_closing = True
            
            # ドキュメント処理マネージャーのクリーンアップ
            if self.doc_processor_manager:
                self.doc_processor_manager.cleanup()

            if self.project_dialog:
                try:
                    self.project_dialog.on_closing()
                except:
                    pass
                finally:
                    self.project_dialog = None

            if self.window:
                try:
                    # スケジューリングされたタスクをキャンセル
                    for after_id in self.window.tk.call('after', 'info'):
                        try:
                            self.window.after_cancel(after_id)
                        except:
                            continue

                    # メインウィンドウの破棄
                    self.window.quit()
                    self.window.destroy()
                except Exception as e:
                    self.logger.debug(f"ウィンドウ破棄時のエラー: {e}")
                finally:
                    self.window = None

            self.logger.debug("アプリケーション終了処理を完了")

        except Exception as e:
            self.logger.error(f"アプリケーション終了処理でエラーが発生: {e}")
    
    def run(self) -> None:
        """アプリケーションの実行"""
        try:
            self.window.mainloop()
        except Exception as e:
            self.error_handler.handle_error(e, "実行エラー", self.window)