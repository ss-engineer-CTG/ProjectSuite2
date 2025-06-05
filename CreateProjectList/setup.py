"""
CreateProjectList セットアップファイル
パッケージ化対応の最小限設定
KISS原則: 必要最小限の設定のみ
"""
from setuptools import setup, find_packages
from pathlib import Path

# README読み込み
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ""

# 最小限の必須依存関係
REQUIRED_PACKAGES = [
    # Office操作（条件付き）
    "pywin32>=227; platform_system=='Windows'",  # Windows環境でのみ
    
    # ファイル処理（軽量な代替）
    "python-docx>=0.8.11",  # DOCX処理用
    "openpyxl>=3.0.9",      # XLSX処理用
]

# 開発・テスト用依存関係（オプション）
DEVELOPMENT_PACKAGES = [
    "pytest>=6.0.0",
    "pytest-cov>=2.10.0",
    "black>=21.0.0",
    "flake8>=3.8.0",
]

# エクストラ依存関係（機能拡張用）
EXTRA_PACKAGES = {
    'dev': DEVELOPMENT_PACKAGES,
    'full': [
        # フル機能版の追加パッケージ（必要時のみ）
        "xlrd>=2.0.1",      # 古いExcel形式サポート
        "xlwt>=1.3.0",      # Excel書き込み拡張
    ]
}

setup(
    # === 基本情報 ===
    name="CreateProjectList",
    version="2.0.0",
    description="軽量化されたドキュメント処理アプリケーション",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # === 作成者情報 ===
    author="CreateProjectList Development Team",
    author_email="dev@createprojectlist.com",
    url="https://github.com/createprojectlist/CreateProjectList",
    
    # === パッケージ設定 ===
    packages=find_packages(exclude=['tests', 'docs', 'examples']),
    package_data={
        'CreateProjectList': [
            'config/*.json',
            'config/*.yaml',
            'config/*.ini',
        ],
    },
    include_package_data=True,
    
    # === 依存関係 ===
    install_requires=REQUIRED_PACKAGES,
    extras_require=EXTRA_PACKAGES,
    
    # === Python要件 ===
    python_requires=">=3.8",
    
    # === エントリーポイント（パッケージ化対応） ===
    entry_points={
        'console_scripts': [
            # メインアプリケーション
            'CreateProjectList=CreateProjectList.__main__:main',
            'cpl=CreateProjectList.__main__:main',  # 短縮コマンド
        ],
        'gui_scripts': [
            # GUIアプリケーション（Windowsで専用）
            'CreateProjectList-gui=CreateProjectList.__main__:main',
        ],
    },
    
    # === 分類・メタデータ ===
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications :: Qt",
        "Natural Language :: Japanese",
    ],
    
    # === キーワード ===
    keywords=[
        "document", "processing", "office", "automation", 
        "word", "excel", "template", "replacement",
        "japanese", "gui", "tkinter"
    ],
    
    # === ライセンス ===
    license="MIT",
    
    # === プロジェクト情報 ===
    project_urls={
        "Bug Reports": "https://github.com/createprojectlist/CreateProjectList/issues",
        "Source": "https://github.com/createprojectlist/CreateProjectList",
        "Documentation": "https://createprojectlist.readthedocs.io/",
    },
    
    # === ZIP安全性 ===
    zip_safe=False,
    
    # === PyInstaller対応設定 ===
    options={
        'build_exe': {
            # PyInstallerでのビルド設定
            'excludes': [
                # 不要なモジュールを除外（サイズ削減）
                'tkinter.test',
                'test',
                'tests',
                'unittest',
                'pdb',
                'doctest',
                'difflib',
                'inspect',
                'pydoc',
                'tkinter.dnd',
                'tkinter.colorchooser',
                'tkinter.commondialog',
                'tkinter.simpledialog',
                'email',
                'html',
                'http',
                'urllib',
                'xml',
                'xmlrpc',
                'multiprocessing',
                'concurrent',
                'asyncio',
            ],
            'include_files': [
                # 必要なファイルを含める
                ('CreateProjectList/config/', 'config/'),
            ],
            'packages': [
                # 必要なパッケージを明示的に含める
                'CreateProjectList',
            ],
        },
    },
)

# === 追加のセットアップ処理 ===
def post_install():
    """インストール後の初期化処理"""
    try:
        from CreateProjectList.core_manager import CoreManager
        
        # CoreManagerの初期化（設定ファイル作成）
        core_manager = CoreManager.get_instance()
        
        # 標準ディレクトリ構造の作成
        from CreateProjectList.path_constants import create_standard_directory_structure
        from pathlib import Path
        
        user_data_dir = Path.home() / "Documents" / "ProjectSuite"
        create_standard_directory_structure(str(user_data_dir))
        
        print("CreateProjectList のセットアップが完了しました。")
        print(f"設定ディレクトリ: {user_data_dir}")
        
    except Exception as e:
        print(f"初期化処理でエラーが発生しました: {e}")
        print("手動でアプリケーションを起動して初期化を行ってください。")

# インストール時の自動実行（開発環境では無効化）
import sys
if 'install' in sys.argv and '--development' not in sys.argv:
    # リリース環境でのみ実行
    import atexit
    atexit.register(post_install)