"""
CreateProjectList パッケージ実行エントリーポイント
`python -m CreateProjectList` 実行時に呼び出される

KISS原則: 最もシンプルなエントリーポイント実装
目的: 外部からのモジュール実行を可能にし、相対インポートエラーを解決
"""

from .main import main

if __name__ == '__main__':
    main()