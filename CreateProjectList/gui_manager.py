"""
統合GUI管理システム
全GUI機能を統合管理
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import threading
import queue
from pathlib import Path
from typing import Optional, Dict, Any, List

class GUIManager:
    """統合GUI管理クラス"""
    
    def __init__(self, root: tk.Tk, core_manager):
        """
        初期化
        
        Args:
            root: tkinterルートウィンドウ
            core_manager: CoreManagerインスタンス
        """
        self.root = root
        self.core_manager = core_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # ドキュメントプロセッサ
        from CreateProjectList.document_processor import DocumentProcessor
        self.processor = DocumentProcessor(core_manager)
        
        # GUI状態変数
        self.project_var = tk.StringVar()
        self.project_info_var = tk.StringVar(value="プロジェクトが選択されていません")
        self.input_folder_var = tk.StringVar(value="未設定")
        self.output_folder_var = tk.StringVar(value="未設定")
        self.db_status_var = tk.StringVar(value="未接続")
        self.status_var = tk.StringVar(value="準備中...")
        
        # 進捗ダイアログ関連
        self.progress_dialog: Optional[tk.Toplevel] = None
        self.progress_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_cancelled = False
        
        # GUI構築
        self._setup_styles()
        self._setup_main_gui()
        self._load_initial_data()
        
        # イベントバインド
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.logger.info("GUI管理システムを初期化しました")
    
    def _setup_styles(self):
        """スタイル設定"""
        style = ttk.Style()
        
        # 基本スタイル
        style.configure('Title.TLabel', font=('Meiryo', 16, 'bold'))
        style.configure('Header.TLabel', font=('Meiryo', 12, 'bold'))
        style.configure('Status.TLabel', font=('Meiryo', 10))
    
    def _setup_main_gui(self):
        """メインGUI構築"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="ドキュメント処理システム", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 左側：プロジェクト・データベース情報
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 右側：実行操作
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 各セクション構築
        self._setup_project_section(left_frame)
        self._setup_database_section(left_frame)
        self._setup_execution_section(right_frame)
        
        # ステータスバー
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel').pack(side=tk.LEFT)
        
        # グリッド設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
    
    def _setup_project_section(self, parent):
        """プロジェクト選択セクション"""
        # プロジェクト選択グループ
        project_group = ttk.LabelFrame(parent, text="プロジェクト選択", padding="10")
        project_group.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # プロジェクト選択
        select_frame = ttk.Frame(project_group)
        select_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        select_frame.columnconfigure(0, weight=1)
        
        self.project_combo = ttk.Combobox(select_frame, textvariable=self.project_var, state='readonly')
        self.project_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(select_frame, text="更新", command=self._update_project_list).grid(row=0, column=1)
        
        # プロジェクト情報表示
        info_frame = ttk.Frame(project_group)
        info_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(info_frame, textvariable=self.project_info_var, wraplength=400).grid(
            row=0, column=0, sticky=(tk.W, tk.E))
        
        # イベントバインド
        self.project_combo.bind('<<ComboboxSelected>>', self._on_project_selected)
        
        project_group.columnconfigure(0, weight=1)
    
    def _setup_database_section(self, parent):
        """データベース状態セクション"""
        # データベース状態グループ
        db_group = ttk.LabelFrame(parent, text="データベース状態", padding="10")
        db_group.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 状態表示
        status_frame = ttk.Frame(db_group)
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(status_frame, text="接続状態:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(status_frame, textvariable=self.db_status_var).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 設定ボタン
        button_frame = ttk.Frame(db_group)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="設定", command=self._open_settings).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="接続テスト", command=self._test_connection).pack(side=tk.LEFT, padx=(5, 0))
        
        db_group.columnconfigure(0, weight=1)
    
    def _setup_execution_section(self, parent):
        """実行操作セクション"""
        # フォルダ設定グループ
        folder_group = ttk.LabelFrame(parent, text="フォルダ設定", padding="10")
        folder_group.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 入力フォルダ
        input_frame = ttk.Frame(folder_group)
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="入力:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(input_frame, textvariable=self.input_folder_var, background='white', relief='sunken').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(input_frame, text="選択", command=self._select_input_folder).grid(row=0, column=2)
        
        # 出力フォルダ
        output_frame = ttk.Frame(folder_group)
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="出力:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(output_frame, textvariable=self.output_folder_var, background='white', relief='sunken').grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(output_frame, text="選択", command=self._select_output_folder).grid(row=0, column=2)
        
        # 実行ボタン
        exec_frame = ttk.Frame(parent)
        exec_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.exec_button = ttk.Button(
            exec_frame, 
            text="処理実行", 
            command=self._execute_processing,
            state='disabled'
        )
        self.exec_button.pack(expand=True, fill='x', pady=(10, 0))
        
        folder_group.columnconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
    
    def _load_initial_data(self):
        """初期データの読み込み"""
        try:
            # データベース接続状態確認
            self._update_database_status()
            
            # フォルダパス表示更新
            self._update_folder_display()
            
            # プロジェクト一覧更新
            if self.processor.is_db_connected:
                self._update_project_list()
            
            # 実行可否チェック
            self._check_execution_ready()
            
        except Exception as e:
            self.logger.error(f"初期データ読み込みエラー: {e}")
    
    def _update_database_status(self):
        """データベース状態更新"""
        try:
            if self.processor.connect_database():
                self.db_status_var.set("接続済み")
                self.status_var.set("データベース接続済み")
            else:
                self.db_status_var.set("未接続")
                self.status_var.set("データベースに接続してください")
        except Exception as e:
            self.db_status_var.set("エラー")
            self.status_var.set("データベース接続エラー")
            self.logger.error(f"データベース状態更新エラー: {e}")
    
    def _update_folder_display(self):
        """フォルダパス表示更新"""
        try:
            # 入力フォルダ
            input_folder = self.core_manager.get_input_folder()
            if input_folder and Path(input_folder).exists():
                self.input_folder_var.set(input_folder)
            else:
                self.input_folder_var.set("未設定")
            
            # 出力フォルダ
            output_folder = self.core_manager.get_output_folder()
            if output_folder:
                self.output_folder_var.set(output_folder)
            else:
                self.output_folder_var.set("未設定")
                
        except Exception as e:
            self.logger.error(f"フォルダ表示更新エラー: {e}")
    
    def _update_project_list(self):
        """プロジェクト一覧更新"""
        try:
            projects = self.processor.get_all_projects()
            project_values = [
                f"{p['project_id']}: {p['project_name']} ({p['start_date']})"
                for p in projects
            ]
            
            self.project_combo['values'] = project_values
            
            # 最新プロジェクトを自動選択
            if projects and not self.project_var.get():
                self.project_combo.set(project_values[0])
                self._on_project_selected(None)
                
        except Exception as e:
            self.logger.error(f"プロジェクト一覧更新エラー: {e}")
            messagebox.showerror("エラー", f"プロジェクト一覧の取得に失敗しました: {e}")
    
    def _on_project_selected(self, event):
        """プロジェクト選択時の処理"""
        if not self.project_var.get():
            return
        
        try:
            project_id = int(self.project_var.get().split(':')[0])
            project_data = self.processor.fetch_project_data(project_id)
            
            if project_data:
                self.processor.set_project_data(project_data)
                
                info_text = (
                    f"プロジェクト名: {project_data['project_name']}\n"
                    f"作成日: {project_data['start_date']}\n"
                    f"工場: {project_data.get('factory', '未設定')}\n"
                    f"工程: {project_data.get('process', '未設定')}\n"
                    f"ライン: {project_data.get('line', '未設定')}\n"
                    f"作成者: {project_data.get('manager', '未設定')}\n"
                    f"確認者: {project_data.get('reviewer', '未設定')}\n"
                    f"承認者: {project_data.get('approver', '未設定')}"
                )
                self.project_info_var.set(info_text)
                
                self._check_execution_ready()
            
        except Exception as e:
            self.logger.error(f"プロジェクト選択エラー: {e}")
            messagebox.showerror("エラー", f"プロジェクトデータの取得に失敗しました: {e}")
    
    def _select_input_folder(self):
        """入力フォルダ選択"""
        folder_path = filedialog.askdirectory(title="入力フォルダを選択")
        if folder_path:
            self.core_manager.set_input_folder(folder_path)
            self.input_folder_var.set(folder_path)
            self._check_execution_ready()
    
    def _select_output_folder(self):
        """出力フォルダ選択"""
        folder_path = filedialog.askdirectory(title="出力フォルダを選択")
        if folder_path:
            self.core_manager.set_output_folder(folder_path)
            self.output_folder_var.set(folder_path)
            self._check_execution_ready()
    
    def _check_execution_ready(self):
        """実行可否チェック"""
        try:
            ready = (
                self.processor.current_project_data is not None and
                self.processor.is_db_connected and
                self.core_manager.get_input_folder() and
                self.core_manager.get_output_folder() and
                Path(self.core_manager.get_input_folder() or "").exists()
            )
            
            if ready:
                self.exec_button.configure(state='normal')
                self.status_var.set("実行可能")
            else:
                self.exec_button.configure(state='disabled')
                self.status_var.set("実行条件が満たされていません")
                
        except Exception as e:
            self.logger.error(f"実行可否チェックエラー: {e}")
            self.exec_button.configure(state='disabled')
    
    def _test_connection(self):
        """データベース接続テスト"""
        try:
            if self.processor.connect_database():
                self.db_status_var.set("接続済み")
                messagebox.showinfo("接続テスト", "データベース接続に成功しました")
                self._update_project_list()
                self._check_execution_ready()
            else:
                self.db_status_var.set("接続失敗")
                messagebox.showerror("接続テスト", "データベース接続に失敗しました")
        except Exception as e:
            self.db_status_var.set("エラー")
            messagebox.showerror("接続テスト", f"接続テスト中にエラーが発生しました: {e}")
    
    def _execute_processing(self):
        """処理実行"""
        try:
            # 確認ダイアログ
            if not messagebox.askyesno(
                "確認",
                f"以下の設定でファイル処理を実行します。\n\n"
                f"プロジェクト: {self.processor.current_project_data.get('project_name', 'Unknown')}\n"
                f"入力フォルダ: {self.core_manager.get_input_folder()}\n"
                f"出力フォルダ: {self.core_manager.get_output_folder()}\n\n"
                "処理を開始しますか？"
            ):
                return
            
            # 進捗ダイアログ表示
            self._show_progress_dialog()
            
            # ワーカースレッド開始
            self.is_cancelled = False
            self.worker_thread = threading.Thread(target=self._worker_process, daemon=True)
            self.worker_thread.start()
            
            # 進捗更新開始
            self._update_progress()
            
        except Exception as e:
            self.logger.error(f"処理実行エラー: {e}")
            messagebox.showerror("エラー", f"処理実行中にエラーが発生しました: {e}")
    
    def _show_progress_dialog(self):
        """進捗ダイアログ表示"""
        self.progress_dialog = tk.Toplevel(self.root)
        self.progress_dialog.title("処理実行中")
        self.progress_dialog.geometry("400x150")
        self.progress_dialog.transient(self.root)
        self.progress_dialog.grab_set()
        
        # 進捗バー
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            self.progress_dialog,
            variable=self.progress_var,
            maximum=100
        )
        progress_bar.pack(pady=20, padx=20, fill='x')
        
        # ステータスラベル
        self.progress_status_var = tk.StringVar(value="処理を開始しています...")
        status_label = ttk.Label(self.progress_dialog, textvariable=self.progress_status_var)
        status_label.pack(pady=10)
        
        # キャンセルボタン
        cancel_button = ttk.Button(
            self.progress_dialog,
            text="キャンセル",
            command=self._cancel_processing
        )
        cancel_button.pack(pady=10)
        
        # ダイアログ中央配置
        self.progress_dialog.update_idletasks()
        x = (self.root.winfo_x() + (self.root.winfo_width() // 2) - 
             (self.progress_dialog.winfo_width() // 2))
        y = (self.root.winfo_y() + (self.root.winfo_height() // 2) - 
             (self.progress_dialog.winfo_height() // 2))
        self.progress_dialog.geometry(f"+{x}+{y}")
    
    def _worker_process(self):
        """ワーカースレッド処理"""
        try:
            def progress_callback(progress: float, status: str, detail: str = ""):
                self.progress_queue.put(("progress", (progress, status, detail)))
            
            def cancel_check() -> bool:
                return self.is_cancelled
            
            result = self.processor.process_documents(
                input_folder_path=self.core_manager.get_input_folder(),
                output_folder_path=self.core_manager.get_output_folder(),
                progress_callback=progress_callback,
                cancel_check=cancel_check
            )
            
            if result.get('cancelled', False):
                self.progress_queue.put(("cancelled", None))
            else:
                self.progress_queue.put(("finished", result))
                
        except Exception as e:
            self.progress_queue.put(("error", str(e)))
    
    def _update_progress(self):
        """進捗更新"""
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == "progress":
                    progress, status, detail = data
                    self.progress_var.set(progress)
                    self.progress_status_var.set(status)
                
                elif msg_type == "error":
                    self._close_progress_dialog()
                    messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{data}")
                    return
                
                elif msg_type == "cancelled":
                    self._close_progress_dialog()
                    messagebox.showinfo("キャンセル", "処理がキャンセルされました")
                    return
                
                elif msg_type == "finished":
                    self._close_progress_dialog()
                    self._show_result(data)
                    return
                
        except queue.Empty:
            pass
        
        if not self.is_cancelled:
            self.root.after(100, self._update_progress)
    
    def _cancel_processing(self):
        """処理キャンセル"""
        self.is_cancelled = True
    
    def _close_progress_dialog(self):
        """進捗ダイアログを閉じる"""
        if self.progress_dialog:
            self.progress_dialog.destroy()
            self.progress_dialog = None
    
    def _show_result(self, result: Dict):
        """処理結果表示"""
        try:
            processed_count = len(result['processed'])
            error_count = len(result['errors'])
            
            message = f"処理が完了しました。\n\n"
            message += f"成功: {processed_count} ファイル\n"
            
            if error_count > 0:
                message += f"エラー: {error_count} ファイル\n\n"
                message += "エラーが発生したファイル:\n"
                for file_path, error in result['errors'][:5]:  # 最初の5件のみ表示
                    message += f"- {file_path.name}: {error}\n"
                if error_count > 5:
                    message += f"...他 {error_count - 5} 件"
                
                messagebox.showwarning("処理結果", message)
            else:
                messagebox.showinfo("処理結果", message)
                
        except Exception as e:
            self.logger.error(f"結果表示エラー: {e}")
            messagebox.showerror("エラー", "処理結果の表示に失敗しました")
    
    def _open_settings(self):
        """設定ダイアログを開く"""
        try:
            SettingsDialog(self.root, self.core_manager, self)
        except Exception as e:
            self.logger.error(f"設定ダイアログエラー: {e}")
            messagebox.showerror("エラー", f"設定ダイアログの表示に失敗しました: {e}")
    
    def refresh_display(self):
        """表示の更新（設定変更後などに呼ばれる）"""
        self._update_database_status()
        self._update_folder_display()
        if self.processor.is_db_connected:
            self._update_project_list()
        self._check_execution_ready()
    
    def _on_closing(self):
        """アプリケーション終了処理"""
        try:
            # 実行中の処理をキャンセル
            if self.worker_thread and self.worker_thread.is_alive():
                self.is_cancelled = True
                self.worker_thread.join(timeout=2)
            
            # 進捗ダイアログを閉じる
            self._close_progress_dialog()
            
            self.logger.info("アプリケーションを終了します")
            self.root.destroy()
            
        except Exception as e:
            self.logger.error(f"終了処理エラー: {e}")
            self.root.destroy()

class SettingsDialog:
    """設定ダイアログ"""
    
    def __init__(self, parent: tk.Tk, core_manager, gui_manager):
        self.parent = parent
        self.core_manager = core_manager
        self.gui_manager = gui_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("設定")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_dialog()
        self._load_settings()
        
        # 中央配置
        self._center_dialog()
    
    def _setup_dialog(self):
        """ダイアログ構築"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # タブ作成
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # データベース設定タブ
        db_frame = ttk.Frame(notebook, padding="10")
        notebook.add(db_frame, text="データベース")
        self._setup_database_tab(db_frame)
        
        # 置換ルール設定タブ
        rules_frame = ttk.Frame(notebook, padding="10")
        notebook.add(rules_frame, text="置換ルール")
        self._setup_rules_tab(rules_frame)
        
        # フォルダ設定タブ
        folder_frame = ttk.Frame(notebook, padding="10")
        notebook.add(folder_frame, text="フォルダ")
        self._setup_folder_tab(folder_frame)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="適用", command=self._apply_settings).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=self._close).pack(side='right')
    
    def _setup_database_tab(self, parent):
        """データベース設定タブ"""
        # データベースパス設定
        path_frame = ttk.LabelFrame(parent, text="データベースファイル", padding="10")
        path_frame.pack(fill='x', pady=(0, 10))
        
        path_input_frame = ttk.Frame(path_frame)
        path_input_frame.pack(fill='x')
        path_input_frame.columnconfigure(0, weight=1)
        
        self.db_path_var = tk.StringVar()
        ttk.Entry(path_input_frame, textvariable=self.db_path_var, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(path_input_frame, text="選択", command=self._select_database).grid(row=0, column=1)
        
        # 接続テスト
        test_frame = ttk.Frame(path_frame)
        test_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(test_frame, text="接続テスト", command=self._test_database).pack(side='left')
        
        self.db_status_label = ttk.Label(test_frame, text="未接続")
        self.db_status_label.pack(side='left', padx=(10, 0))
    
    def _setup_rules_tab(self, parent):
        """置換ルール設定タブ"""
        # ルール一覧
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True)
        
        # リストボックスとスクロールバー
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill='both', expand=True)
        
        self.rules_listbox = tk.Listbox(list_container)
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.rules_listbox.yview)
        self.rules_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.rules_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # ボタンフレーム
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="追加", command=self._add_rule).pack(side='left')
        ttk.Button(button_frame, text="編集", command=self._edit_rule).pack(side='left', padx=(5, 0))
        ttk.Button(button_frame, text="削除", command=self._delete_rule).pack(side='left', padx=(5, 0))
    
    def _setup_folder_tab(self, parent):
        """フォルダ設定タブ"""
        # 入力フォルダ
        input_frame = ttk.LabelFrame(parent, text="入力フォルダ", padding="10")
        input_frame.pack(fill='x', pady=(0, 10))
        
        input_path_frame = ttk.Frame(input_frame)
        input_path_frame.pack(fill='x')
        input_path_frame.columnconfigure(0, weight=1)
        
        self.input_folder_var = tk.StringVar()
        ttk.Entry(input_path_frame, textvariable=self.input_folder_var, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(input_path_frame, text="選択", command=self._select_input_folder).grid(row=0, column=1)
        
        # 出力フォルダ
        output_frame = ttk.LabelFrame(parent, text="出力フォルダ", padding="10")
        output_frame.pack(fill='x')
        
        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill='x')
        output_path_frame.columnconfigure(0, weight=1)
        
        self.output_folder_var = tk.StringVar()
        ttk.Entry(output_path_frame, textvariable=self.output_folder_var, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_path_frame, text="選択", command=self._select_output_folder).grid(row=0, column=1)
    
    def _load_settings(self):
        """設定読み込み"""
        try:
            # データベースパス
            self.db_path_var.set(self.core_manager.get_db_path() or "")
            
            # フォルダパス
            self.input_folder_var.set(self.core_manager.get_input_folder() or "")
            self.output_folder_var.set(self.core_manager.get_output_folder() or "")
            
            # 置換ルール
            self._load_rules()
            
        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
    
    def _load_rules(self):
        """置換ルール読み込み"""
        try:
            self.rules_listbox.delete(0, tk.END)
            rules = self.core_manager.get_replacement_rules()
            
            for rule in rules:
                display_text = f"{rule['search']} → {rule['replace']}"
                self.rules_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            self.logger.error(f"置換ルール読み込みエラー: {e}")
    
    def _select_database(self):
        """データベース選択"""
        file_path = filedialog.askopenfilename(
            title="データベースファイルを選択",
            filetypes=[("SQLite files", "*.db"), ("All files", "*.*")]
        )
        if file_path:
            self.db_path_var.set(file_path)
    
    def _test_database(self):
        """データベーステスト"""
        try:
            db_path = self.db_path_var.get()
            if not db_path:
                messagebox.showwarning("警告", "データベースファイルを選択してください")
                return
            
            # 一時的にパスを設定してテスト
            original_path = self.core_manager.get_db_path()
            self.core_manager.set_db_path(db_path)
            
            if self.core_manager.test_database_connection():
                self.db_status_label.config(text="接続成功")
                messagebox.showinfo("接続テスト", "データベース接続に成功しました")
            else:
                self.db_status_label.config(text="接続失敗")
                messagebox.showerror("接続テスト", "データベース接続に失敗しました")
                self.core_manager.set_db_path(original_path)
                
        except Exception as e:
            self.db_status_label.config(text="エラー")
            messagebox.showerror("接続テスト", f"テスト中にエラーが発生しました: {e}")
    
    def _add_rule(self):
        """置換ルール追加"""
        RuleEditDialog(self.dialog, self.core_manager, self, None)
    
    def _edit_rule(self):
        """置換ルール編集"""
        selection = self.rules_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "編集するルールを選択してください")
            return
        
        index = selection[0]
        rules = self.core_manager.get_replacement_rules()
        if index < len(rules):
            RuleEditDialog(self.dialog, self.core_manager, self, rules[index])
    
    def _delete_rule(self):
        """置換ルール削除"""
        selection = self.rules_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除するルールを選択してください")
            return
        
        if messagebox.askyesno("確認", "選択したルールを削除しますか？"):
            index = selection[0]
            rules = self.core_manager.get_replacement_rules()
            if index < len(rules):
                del rules[index]
                self.core_manager.set_replacement_rules(rules)
                self._load_rules()
    
    def _select_input_folder(self):
        """入力フォルダ選択"""
        folder_path = filedialog.askdirectory(title="入力フォルダを選択")
        if folder_path:
            self.input_folder_var.set(folder_path)
    
    def _select_output_folder(self):
        """出力フォルダ選択"""
        folder_path = filedialog.askdirectory(title="出力フォルダを選択")
        if folder_path:
            self.output_folder_var.set(folder_path)
    
    def _apply_settings(self):
        """設定適用"""
        try:
            # データベースパス
            db_path = self.db_path_var.get()
            if db_path:
                self.core_manager.set_db_path(db_path)
            
            # フォルダパス
            input_folder = self.input_folder_var.get()
            if input_folder:
                self.core_manager.set_input_folder(input_folder)
            
            output_folder = self.output_folder_var.get()
            if output_folder:
                self.core_manager.set_output_folder(output_folder)
            
            messagebox.showinfo("設定", "設定を適用しました")
            
            # GUI表示更新
            self.gui_manager.refresh_display()
            
            self._close()
            
        except Exception as e:
            self.logger.error(f"設定適用エラー: {e}")
            messagebox.showerror("エラー", f"設定の適用に失敗しました: {e}")
    
    def _close(self):
        """ダイアログを閉じる"""
        self.dialog.destroy()
    
    def _center_dialog(self):
        """ダイアログ中央配置"""
        self.dialog.update_idletasks()
        x = (self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 
             (self.dialog.winfo_width() // 2))
        y = (self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 
             (self.dialog.winfo_height() // 2))
        self.dialog.geometry(f"+{x}+{y}")

class RuleEditDialog:
    """置換ルール編集ダイアログ"""
    
    def __init__(self, parent: tk.Toplevel, core_manager, settings_dialog, rule: Optional[Dict] = None):
        self.parent = parent
        self.core_manager = core_manager
        self.settings_dialog = settings_dialog
        self.rule = rule
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # ダイアログ作成
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("置換ルール編集" if rule else "置換ルール追加")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self._setup_dialog()
        self._center_dialog()
    
    def _setup_dialog(self):
        """ダイアログ構築"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # 入力フィールド
        ttk.Label(main_frame, text="検索文字列:").pack(anchor='w')
        self.search_var = tk.StringVar(value=self.rule['search'] if self.rule else "")
        ttk.Entry(main_frame, textvariable=self.search_var, width=50).pack(fill='x', pady=(0, 10))
        
        ttk.Label(main_frame, text="置換後（DB参照キー）:").pack(anchor='w')
        self.replace_var = tk.StringVar(value=self.rule['replace'] if self.rule else "")
        ttk.Entry(main_frame, textvariable=self.replace_var, width=50).pack(fill='x', pady=(0, 10))
        
        # 参照キー一覧
        ttk.Label(main_frame, text="利用可能な参照キー:").pack(anchor='w')
        reference_text = """
project_name: 案件名
start_date: 作成日
factory: 工場
process: 工程
line: ライン
manager: 作成者
reviewer: 確認者
approver: 承認者
division: 事業部
        """.strip()
        
        text_widget = tk.Text(main_frame, height=8, width=50, state='disabled')
        text_widget.pack(fill='both', expand=True, pady=(0, 10))
        text_widget.config(state='normal')
        text_widget.insert('1.0', reference_text)
        text_widget.config(state='disabled')
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x')
        
        ttk.Button(button_frame, text="保存", command=self._save).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=self._close).pack(side='right')
    
    def _save(self):
        """保存"""
        try:
            search = self.search_var.get().strip()
            replace = self.replace_var.get().strip()
            
            if not search or not replace:
                messagebox.showwarning("警告", "検索文字列と置換後文字列を入力してください")
                return
            
            rules = self.core_manager.get_replacement_rules()
            
            # 重複チェック（編集時は自分以外）
            for i, existing_rule in enumerate(rules):
                if existing_rule['search'] == search:
                    if not self.rule or self.rule['search'] != search:
                        messagebox.showwarning("警告", "この検索文字列は既に存在します")
                        return
            
            new_rule = {'search': search, 'replace': replace}
            
            if self.rule:
                # 編集
                for i, existing_rule in enumerate(rules):
                    if existing_rule == self.rule:
                        rules[i] = new_rule
                        break
            else:
                # 追加
                rules.append(new_rule)
            
            self.core_manager.set_replacement_rules(rules)
            self.settings_dialog._load_rules()
            
            self._close()
            
        except Exception as e:
            self.logger.error(f"ルール保存エラー: {e}")
            messagebox.showerror("エラー", f"ルールの保存に失敗しました: {e}")
    
    def _close(self):
        """ダイアログを閉じる"""
        self.dialog.destroy()
    
    def _center_dialog(self):
        """ダイアログ中央配置"""
        self.dialog.update_idletasks()
        x = (self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 
             (self.dialog.winfo_width() // 2))
        y = (self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 
             (self.dialog.winfo_height() // 2))
        self.dialog.geometry(f"+{x}+{y}")