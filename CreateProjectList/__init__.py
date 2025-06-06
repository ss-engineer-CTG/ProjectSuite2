"""
CreateProjectList Package - 最適化版
ドキュメント処理アプリケーション
"""
from pathlib import Path
import sys
import logging

# パッケージのルートディレクトリを取得
package_root = Path(__file__).parent.absolute()

# パッケージのルートをsys.pathに追加（存在しない場合のみ）
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

# バージョン情報
__version__ = '2.0.0'

# メインコンポーネントの遅延インポート
def get_document_processor():
    """DocumentProcessor の遅延インポート"""
    from CreateProjectList.document_processor import DocumentProcessor
    return DocumentProcessor

def get_gui_manager():
    """GUIManager の遅延インポート"""
    from CreateProjectList.gui_manager import GUIManager
    return GUIManager

def get_core_manager():
    """CoreManager の遅延インポート"""
    from CreateProjectList.core_manager import CoreManager
    return CoreManager

def main():
    """メイン実行関数の遅延インポート"""
    from CreateProjectList.main import main as main_func
    return main_func()

# 公開API
__all__ = [
    'get_document_processor',
    'get_gui_manager', 
    'get_core_manager',
    'main'
]

# ログ設定の基本初期化
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)