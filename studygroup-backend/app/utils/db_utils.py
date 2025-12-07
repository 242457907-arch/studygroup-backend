import pymysql
from pymysql.cursors import DictCursor
from app.config import MYSQL_CONFIG
from typing import Tuple, Dict, Any, Optional

def get_db_connection() -> Tuple[pymysql.connections.Connection, pymysql.cursors.Cursor]:
    """获取数据库连接与DictCursor（返回字典格式结果）"""
    try:
        # 创建配置副本，过滤掉 pymysql.connect 不支持的参数
        conn_config = MYSQL_CONFIG.copy()
        
        # pymysql.connect 支持的参数列表
        allowed_keys = ['host', 'port', 'user', 'password', 'database', 
                       'db', 'charset', 'cursorclass', 'autocommit']
        
        # 过滤掉不支持的参数
        filtered_config = {k: v for k, v in conn_config.items() 
                          if k in allowed_keys and v is not None}
        
        # 如果 db 和 database 同时存在，优先使用 database
        if 'db' in filtered_config and 'database' not in filtered_config:
            filtered_config['database'] = filtered_config.pop('db')
        
        conn = pymysql.connect(**filtered_config)
        cursor = conn.cursor(DictCursor)  # 使用 DictCursor 返回字典
        return conn, cursor
    except pymysql.MySQLError as e:
        raise pymysql.MySQLError(f"数据库连接失败：{str(e)}") from e

def commit_transaction(conn: pymysql.connections.Connection) -> None:
    """提交事务"""
    try:
        conn.commit()
    except pymysql.MySQLError as e:
        raise pymysql.MySQLError(f"事务提交失败：{str(e)}") from e

def rollback_transaction(conn: pymysql.connections.Connection) -> None:
    """回滚事务"""
    try:
        if conn.open:
            conn.rollback()
    except pymysql.MySQLError as e:
        print(f"事务回滚警告：{str(e)}")

def close_db_resource(conn: pymysql.connections.Connection, cursor: pymysql.cursors.Cursor) -> None:
    """关闭游标与连接"""
    try:
        if cursor:
            cursor.close()
    except pymysql.MySQLError as e:
        print(f"游标关闭警告：{str(e)}")
    finally:
        try:
            if conn and conn.open:
                conn.close()
        except pymysql.MySQLError as e:
            print(f"连接关闭警告：{str(e)}")

def query_one(sql: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
    """查询单条结果"""
    conn, cursor = None, None
    try:
        conn, cursor = get_db_connection()
        cursor.execute(sql, params)
        return cursor.fetchone()
    except pymysql.MySQLError as e:
        print(f"查询异常：SQL={sql}, Params={params}, Error={str(e)}")
        return None
    finally:
        close_db_resource(conn, cursor)

def query_all(sql: str, params: Tuple[Any, ...] = ()) -> Optional[list[Dict[str, Any]]]:
    """查询多条结果"""
    conn, cursor = None, None
    try:
        conn, cursor = get_db_connection()
        cursor.execute(sql, params)
        return cursor.fetchall() or []
    except pymysql.MySQLError as e:
        print(f"查询异常：SQL={sql}, Params={params}, Error={str(e)}")
        return None
    finally:
        close_db_resource(conn, cursor)

def execute_sql(sql: str, params: Tuple[Any, ...] = ()) -> Tuple[bool, Optional[int]]:
    """执行增删改SQL"""
    conn, cursor = None, None
    try:
        conn, cursor = get_db_connection()
        affected_rows = cursor.execute(sql, params)
        commit_transaction(conn)
        if sql.strip().upper().startswith("INSERT"):
            return True, cursor.lastrowid
        return True, affected_rows
    except pymysql.MySQLError as e:
        if conn:
            rollback_transaction(conn)
        print(f"执行异常：SQL={sql}, Params={params}, Error={str(e)}")
        return False, None
    finally:
        close_db_resource(conn, cursor)