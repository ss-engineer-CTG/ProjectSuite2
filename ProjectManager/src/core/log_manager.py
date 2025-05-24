"""ログ管理と設定を提供するモジュール"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime

from ProjectManager.src.core.path_manager import PathManager

# シングルトンロガーの辞書
_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """
    指定した名前のロガーを取得
    
    Args:
        name: ロガー名（通常は __name__ を使用）
        
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        
        # すでに初期化されている場合は何もしない
        if logger.handlers:
            _loggers[name] = logger
            return logger
        
        # LogManagerのインスタンスを取得し、デフォルト設定を適用
        log_manager = LogManager()
        logger.setLevel(log_manager.log_level)
        
        # ストリームハンドラの追加（コンソール出力）
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(log_manager.log_format))
        logger.addHandler(stream_handler)
        
        _loggers[name] = logger
    
    return _loggers[name]

class LogManager:
    """ログ管理を一元化するシングルトンクラス"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        
        # ログフォーマット
        self.log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
        
        # デフォルトのログレベル（環境変数から取得または INFO）
        log_level_name = os.environ.get('PMSUITE_LOG_LEVEL', 'INFO')
        self.log_level = getattr(logging, log_level_name, logging.INFO)
        
        # パスマネージャーの取得
        self.path_manager = PathManager()
        
        # ログファイルのパス
        today = datetime.now().strftime('%Y%m%d')
        self.log_file = self.path_manager.get_path("LOGS_DIR") / f"app_{today}.log"
    
    def setup(self) -> None:
        """ロギング設定のセットアップ"""
        try:
            # ルートロガーの設定
            root_logger = logging.getLogger()
            root_logger.setLevel(self.log_level)
            
            # 既存のハンドラをクリア
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # ログディレクトリを確保
            logs_dir = self.path_manager.ensure_directory("LOGS_DIR")
            
            # ファイルハンドラの設定（ローテーション付き）
            file_handler = RotatingFileHandler(
                self.log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=10,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(self.log_format))
            root_logger.addHandler(file_handler)
            
            # コンソールハンドラの設定
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(self.log_format))
            root_logger.addHandler(console_handler)
            
            # インフォメーションログ
            logger = get_logger(__name__)
            logger.info(f"ログ設定を初期化しました: {self.log_file}")
            logger.info(f"ログレベル: {logging.getLevelName(self.log_level)}")
            
        except Exception as e:
            print(f"ログ設定の初期化に失敗しました: {e}")
            raise
    
    def set_log_level(self, level_name: str) -> None:
        """
        ログレベルの設定
        
        Args:
            level_name: ログレベル名 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        try:
            # level_nameが有効なログレベル名であることを確認
            level = getattr(logging, level_name, None)
            if level is None:
                raise ValueError(f"無効なログレベル名: {level_name}")
            
            # ログレベルを更新
            self.log_level = level
            logging.getLogger().setLevel(level)
            
            # 環境変数にも設定
            os.environ['PMSUITE_LOG_LEVEL'] = level_name
            
            # 変更を記録
            logger = get_logger(__name__)
            logger.info(f"ログレベルを変更しました: {level_name}")
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"ログレベル設定エラー: {e}")
            raise
    
    def get_log_file_path(self) -> Path:
        """
        現在のログファイルのパスを取得
        
        Returns:
            Path: ログファイルのパス
        """
        return self.log_file