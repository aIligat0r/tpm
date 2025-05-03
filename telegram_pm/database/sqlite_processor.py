import json
from typing import List
from dataclasses import asdict
from contextlib import asynccontextmanager

import aiosqlite

from telegram_pm.entities import Post


class DatabaseProcessor:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._pool = None

    async def initialize(self):
        async with self._get_connection() as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA cache_size=-10000")  # 10MB кэша
            await conn.execute("PRAGMA temp_store=MEMORY")
            await conn.commit()

    @asynccontextmanager
    async def _get_connection(self):
        conn = await aiosqlite.connect(self.db_path, timeout=30, isolation_level=None)
        conn.row_factory = aiosqlite.Row
        try:
            yield conn
        finally:
            await conn.close()

    @asynccontextmanager
    async def _get_cursor(self):
        async with self._get_connection() as conn:
            cursor = await conn.cursor()
            try:
                yield cursor
                await conn.commit()
            except Exception as e:
                await conn.rollback()
                raise e

    async def table_exists(self, table_name: str) -> bool:
        async with self._get_cursor() as cursor:
            await cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            return await cursor.fetchone() is not None

    async def create_table_from_post(self, table_name: str):
        columns = [
            "url TEXT PRIMARY KEY",
            "username TEXT",
            "id INTEGER",
            "date TEXT NOT NULL",
            "text TEXT",
            "replied_post_url TEXT",
            "urls TEXT",  # JSON
            "url_preview TEXT",
            "photo_urls TEXT",  # JSON
            "video_urls TEXT",  # JSON
            "round_video_url TEXT",
            "files TEXT",  # JSON
            "tags TEXT",  # JSON
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "forwarded_from_url TEXT",
            "forwarded_from_name TEXT",
        ]

        async with self._get_cursor() as cursor:
            await cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {", ".join(columns)}
                )
                """
            )
            await cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date ON {table_name}(date)"
            )

    async def insert_posts_batch(self, table_name: str, posts: List[Post]):
        if not posts:
            return

        columns = [
            "url",
            "username",
            "id",
            "date",
            "text",
            "replied_post_url",
            "urls",
            "url_preview",
            "photo_urls",
            "video_urls",
            "round_video_url",
            "files",
            "tags",
            "forwarded_from_url",
            "forwarded_from_name",
        ]

        placeholders = ", ".join(["?"] * len(columns))
        query = f"""
            INSERT OR IGNORE INTO {table_name}
            ({", ".join(columns)})
            VALUES ({placeholders})
        """

        async with self._get_cursor() as cursor:
            data = []
            for post in posts:
                post_dict = asdict(post)
                for field in ["urls", "photo_urls", "video_urls", "files", "tags"]:
                    post_dict[field] = json.dumps(post_dict[field])
                data.append(tuple(post_dict[col] for col in columns))
            await cursor.executemany(query, data)

    async def is_table_empty(self, table_name: str) -> bool:
        async with self._get_cursor() as cursor:
            await cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
            return await cursor.fetchone() is None

    async def drop_table_if_empty(self, table_name: str):
        if await self.table_exists(table_name) and await self.is_table_empty(
            table_name
        ):
            async with self._get_cursor() as cursor:
                await cursor.execute(f"DROP TABLE {table_name}")

    async def post_exists(self, table_name: str, url: str) -> bool:
        query = f"SELECT 1 FROM {table_name} WHERE url = ? LIMIT 1"

        async with self._get_cursor() as cursor:
            await cursor.execute(query, (url,))
            return await cursor.fetchone() is not None

    async def close(self):
        if hasattr(self, "conn") and self.conn:
            await self.conn.close()
