import sqlite3
import threading
import time
from datetime import datetime, timedelta

DB_PATH = 'bot/botdata.db'

class BotDB:
    _lock = threading.Lock()
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                name TEXT,
                member_count INTEGER,
                invite_link TEXT
            )''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS user_search (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                query TEXT,
                timestamp INTEGER
            )''')

    def upsert_group(self, group_id, name, member_count, invite_link):
        with self._lock, self.conn:
            now = int(time.time())
            # 插入或更新群组信息
            self.conn.execute('''INSERT INTO groups (group_id, name, member_count, invite_link)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(group_id) DO UPDATE SET name=excluded.name, member_count=excluded.member_count, invite_link=excluded.invite_link''',
                (group_id, name, member_count, invite_link))
            # 删除30天前未活跃的群组（可选，若需保留所有群组可不加此逻辑）

    def get_groups(self):
        with self._lock:
            return self.conn.execute('SELECT group_id, name, member_count, invite_link FROM groups').fetchall()

    def log_user_search(self, user_id, username, query):
        with self._lock, self.conn:
            now = int(time.time())
            # 插入新数据
            self.conn.execute('INSERT INTO user_search (user_id, username, query, timestamp) VALUES (?, ?, ?, ?)',
                              (user_id, username, query, now))
            # 删除30天前的数据
            expire = now - 30 * 86400
            self.conn.execute('DELETE FROM user_search WHERE timestamp < ?', (expire,))

    def get_user_stats(self, days=10):
        since = int(time.time()) - days * 86400
        with self._lock:
            return self.conn.execute('''SELECT user_id, username, COUNT(*), GROUP_CONCAT(query, ', ')
                FROM user_search WHERE timestamp > ? GROUP BY user_id, username''', (since,)).fetchall()

    def get_user_searches(self, user_id, days=10):
        since = int(time.time()) - days * 86400
        with self._lock:
            return self.conn.execute('''SELECT query, timestamp FROM user_search WHERE user_id=? AND timestamp > ?''', (user_id, since)).fetchall()

    def get_active_users(self, days=10):
        since = int(time.time()) - days * 86400
        with self._lock:
            return self.conn.execute('''SELECT DISTINCT user_id, username FROM user_search WHERE timestamp > ?''', (since,)).fetchall() 