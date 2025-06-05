"""
CreateProjectList メイン実行モジュール
アプリケーション起動・終了制御を統合管理
"""
import sys
import logging
import traceback
from pathlib import Path
from typing import Optional

def initialize_application():
    """アプリケーション初期化"""
    try:
        # コア管理システムの初期化
        from .core_manager import CoreManager
        core_manager = CoreManager.get_instance()
        
        # 設定アダプターの適用
        try:
            from .config_adapters_cp import adapt_create_project_list_config
            adapt_create_project_list_config()
            logging.info("設定アダプターを適用しました")
        except Exception as e:
            logging.warning(f"設定アダプター適用に失敗: {e}")
        
        return core_manager
        
    except Exception as e:
        logging.error(f"アプリケーション初期化エラー: {e}")
        raise

def process_with_project_id(project_id: int) -> bool:
    """
    指定されたプロジェクトIDに対してドキュメント処理を実行
    
    Args:
        project_id: 処理対象のプロジェクトID
    Returns:
        bool: 処理成功時True
    """
    try:
        # 初期化
        core_manager = initialize_application()
        
        from .document_processor import DocumentProcessor
        processor = DocumentProcessor(core_manager)
        
        # データベース接続とプロジェクトデータ取得
        if not processor.connect_database():
            raise ValueError("データベースに接続できません")
            
        project_data = processor.fetch_project_data(project_id)
        if not project_data:
            raise ValueError(f"プロジェクトID {project_id} が見つかりません")
            
        processor.set_project_data(project_data)
        
        # 入力・出力フォルダの確認
        input_folder = core_manager.get_input_folder()
        output_folder = core_manager.get_output_folder()
        
        if not input_folder or not Path(input_folder).exists():
            raise ValueError("入力フォルダが設定されていないか存在しません")
        if not output_folder:
            raise ValueError("出力フォルダが設定されていません")
            
        # 進捗・キャンセルコールバック
        def progress_callback(progress: float, status: str, detail: str = ""):
            logging.info(f"進捗: {progress:.1f}% - {status}")
            if detail:
                logging.debug(f"詳細: {detail}")
        
        def cancel_check() -> bool:
            return False  # CLIモードではキャンセルなし
            
        # ドキュメント処理実行
        result = processor.process_documents(
            input_folder_path=input_folder,
            output_folder_path=output_folder,
            progress_callback=progress_callback,
            cancel_check=cancel_check
        )
        
        # 結果の出力
        logging.info(f"プロジェクト {project_id} の処理が完了しました")
        logging.info(f"処理成功: {len(result['processed'])} ファイル")
        
        if result.get('cancelled', False):
            logging.info("処理はキャンセルされました")
            
        if result['errors']:
            logging.warning(f"処理エラー: {len(result['errors'])} ファイル")
            for file_path, error in result['errors']:
                logging.error(f"  {file_path}: {error}")
        
        return len(result['errors']) == 0
        
    except Exception as e:
        logging.error(f"処理エラー: {e}")
        logging.debug(traceback.format_exc())
        return False

def run_gui_mode():
    """GUIモードでアプリケーションを起動"""
    try:
        # 初期化
        core_manager = initialize_application()
        
        # tkinterのインポートと初期化
        import tkinter as tk
        from .gui_manager import GUIManager
        
        # メインウィンドウの作成
        root = tk.Tk()
        root.title("ドキュメント処理アプリケーション")
        root.geometry("900x700")
        
        # GUIマネージャーの初期化
        gui_manager = GUIManager(root, core_manager)
        
        # アプリケーション実行
        logging.info("GUIモードでアプリケーションを起動しました")
        root.mainloop()
        
    except Exception as e:
        logging.error(f"GUIモード実行エラー: {e}")
        logging.debug(traceback.format_exc())
        raise

def main():
    """メイン実行関数"""
    try:
        # コマンドライン引数の処理
        if len(sys.argv) > 1:
            try:
                project_id = int(sys.argv[1])
                logging.info(f"コマンドラインモード: プロジェクト {project_id} の処理を開始します")
                
                success = process_with_project_id(project_id)
                if success:
                    logging.info("処理が正常に完了しました")
                    return 0
                else:
                    logging.error("処理中にエラーが発生しました")
                    return 1
                    
            except ValueError:
                error_msg = "プロジェクトIDは数値で指定してください"
                logging.error(error_msg)
                print(f"エラー: {error_msg}")
                print("使用方法: CreateProjectList [project_id]")
                return 1
                
        else:
            # GUIモード
            run_gui_mode()
            return 0
            
    except KeyboardInterrupt:
        logging.info("ユーザーによって中断されました")
        return 0
    except Exception as e:
        logging.error(f"アプリケーション実行エラー: {e}")
        logging.debug(traceback.format_exc())
        print(f"エラー: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())