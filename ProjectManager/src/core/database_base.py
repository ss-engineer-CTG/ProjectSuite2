"""データベース操作の基本機能を提供するモジュール"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Iterator, Union
from contextlib import contextmanager

from ProjectManager.src.core.log_manager import get_logger
from ProjectManager.src.core.error_handler import DatabaseError

class DatabaseBaseManager:
    """データベース操作の基本機能を提供するクラス"""
    
    def __init__(self, db_path: Path):
        """
        データベースマネージャーの初期化
        
        Args:
            db_path (Path): データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.logger = get_logger(__name__)
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """データベースファイルの親ディレクトリが存在することを確認"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            error_msg = f"データベースディレクトリの作成に失敗しました: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
    
    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """
        データベース接続のコンテキストマネージャー
        
        Yields:
            sqlite3.Connection: データベース接続オブジェクト
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            error_msg = f"データベース接続エラー: {e}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", error_msg)
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        SELECT クエリを実行
        
        Args:
            query: SQLクエリ文字列
            params: クエリパラメータ
            
        Returns:
            List[Dict[str, Any]]: クエリ結果の行のリスト
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
            except sqlite3.Error as e:
                error_msg = f"クエリ実行エラー: {e}, クエリ: {query}, パラメータ: {params}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"クエリ実行中にエラーが発生しました: {e}")
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        UPDATE/INSERT/DELETE クエリを実行
        
        Args:
            query: SQLクエリ文字列
            params: クエリパラメータ
            
        Returns:
            int: 影響を受けた行数
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
            except sqlite3.Error as e:
                error_msg = f"更新クエリ実行エラー: {e}, クエリ: {query}, パラメータ: {params}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"データベース更新中にエラーが発生しました: {e}")
    
    def execute_insert(self, query: str, params: Tuple = ()) -> int:
        """
        INSERT クエリを実行し、生成されたIDを返す
        
        Args:
            query: SQLクエリ文字列
            params: クエリパラメータ
            
        Returns:
            int: 生成された行のID
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.lastrowid
            except sqlite3.Error as e:
                error_msg = f"挿入クエリ実行エラー: {e}, クエリ: {query}, パラメータ: {params}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"データベース挿入中にエラーが発生しました: {e}")
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> int:
        """
        複数の行に対して一括でクエリを実行
        
        Args:
            query: SQLクエリ文字列
            params_list: クエリパラメータのリスト
            
        Returns:
            int: 影響を受けた行数
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
            except sqlite3.Error as e:
                error_msg = f"一括クエリ実行エラー: {e}, クエリ: {query}, パラメータ数: {len(params_list)}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"一括データベース操作中にエラーが発生しました: {e}")
    
    def table_exists(self, table_name: str) -> bool:
        """
        テーブルが存在するか確認
        
        Args:
            table_name: テーブル名
            
        Returns:
            bool: テーブルが存在する場合はTrue
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, (table_name,))
                return cursor.fetchone() is not None
            except sqlite3.Error as e:
                error_msg = f"テーブル存在確認エラー: {e}, テーブル名: {table_name}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"テーブル確認中にエラーが発生しました: {e}")
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """
        カラムが存在するか確認
        
        Args:
            table_name: テーブル名
            column_name: カラム名
            
        Returns:
            bool: カラムが存在する場合はTrue
        """
        query = f"PRAGMA table_info({table_name})"
        with self.connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query)
                columns = [row['name'] for row in cursor.fetchall()]
                return column_name in columns
            except sqlite3.Error as e:
                error_msg = f"カラム存在確認エラー: {e}, テーブル: {table_name}, カラム: {column_name}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"カラム確認中にエラーが発生しました: {e}")
    
    def add_column(self, table_name: str, column_name: str, column_type: str) -> None:
        """
        既存のテーブルに新しいカラムを追加
        
        Args:
            table_name: テーブル名
            column_name: 新しいカラム名
            column_type: カラムのデータ型と制約
        """
        if not self.column_exists(table_name, column_name):
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            try:
                self.execute_update(query)
                self.logger.info(f"{table_name}テーブルに{column_name}列を追加しました")
            except DatabaseError as e:
                error_msg = f"カラム追加エラー: {e}, テーブル: {table_name}, カラム: {column_name}, 型: {column_type}"
                self.logger.error(error_msg)
                raise DatabaseError("データベースエラー", f"カラム追加中にエラーが発生しました: {e}")
    
    def get_by_id(self, table_name: str, id_column: str, id_value: int) -> Optional[Dict[str, Any]]:
        """
        IDによるレコード取得
        
        Args:
            table_name: テーブル名
            id_column: ID列名
            id_value: 検索するID値
            
        Returns:
            Optional[Dict[str, Any]]: 取得したレコード。見つからない場合はNone
        """
        query = f"SELECT * FROM {table_name} WHERE {id_column} = ?"
        results = self.execute_query(query, (id_value,))
        return results[0] if results else None
    
    def get_all(self, table_name: str, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        テーブルの全レコード取得
        
        Args:
            table_name: テーブル名
            order_by: ソート条件（オプション）
            limit: 取得件数の上限（オプション）
            
        Returns:
            List[Dict[str, Any]]: 取得したレコードのリスト
        """
        query = f"SELECT * FROM {table_name}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query)
    
    def delete_by_id(self, table_name: str, id_column: str, id_value: int) -> bool:
        """
        IDによるレコード削除
        
        Args:
            table_name: テーブル名
            id_column: ID列名
            id_value: 削除するレコードのID
            
        Returns:
            bool: 削除に成功した場合はTrue
        """
        query = f"DELETE FROM {table_name} WHERE {id_column} = ?"
        rows_affected = self.execute_update(query, (id_value,))
        return rows_affected > 0
    
    def clear_table(self, table_name: str) -> None:
        """
        テーブルの全レコードを削除
        
        Args:
            table_name: クリアするテーブル名
        """
        query = f"DELETE FROM {table_name}"
        try:
            self.execute_update(query)
            self.logger.info(f"{table_name}テーブルのデータを全て削除しました")
        except DatabaseError as e:
            error_msg = f"テーブルクリアエラー: {e}, テーブル: {table_name}"
            self.logger.error(error_msg)
            raise DatabaseError("データベースエラー", f"テーブルクリア中にエラーが発生しました: {e}")