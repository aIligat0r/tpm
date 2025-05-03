import csv
from typing import List
from dataclasses import asdict
from pathlib import Path
import json
from datetime import datetime

from telegram_pm.entities import Post


class CSVProcessor:
    def __init__(self, csv_dir: str):
        self.csv_dir = Path(csv_dir)
        self.csv_dir.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, table_name: str) -> Path:
        return self.csv_dir / f"{table_name}.csv"

    async def table_exists(self, table_name: str) -> bool:
        return self._get_filename(table_name).exists()

    async def create_table_from_post(self, table_name: str):
        filename = self._get_filename(table_name)
        if not filename.exists():
            filename.touch()

    async def insert_posts_batch(self, table_name: str, posts: List[Post]):
        if not posts:
            return

        filename = self._get_filename(table_name)
        file_exists = filename.exists()

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
            "created_at",
            "forwarded_from_url",
            "forwarded_from_name",
        ]

        with open(filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)

            if not file_exists or filename.stat().st_size == 0:
                writer.writeheader()

            for post in posts:
                post_dict = asdict(post)
                for field in ["urls", "photo_urls", "video_urls", "files", "tags"]:
                    post_dict[field] = json.dumps(post_dict[field])
                if "created_at" not in post_dict or not post_dict["created_at"]:
                    post_dict["created_at"] = datetime.now().isoformat()
                writer.writerow(post_dict)

    async def is_table_empty(self, table_name: str) -> bool:
        filename = self._get_filename(table_name)
        if not filename.exists():
            return True
        return filename.stat().st_size == 0

    async def drop_table_if_empty(self, table_name: str):
        filename = self._get_filename(table_name)
        if await self.is_table_empty(table_name) and filename.exists():
            filename.unlink()

    async def post_exists(self, table_name: str, url: str) -> bool:
        filename = self._get_filename(table_name)
        if not filename.exists():
            return False

        with open(filename, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["url"] == url:
                    return True
        return False

    async def close(self):
        pass

    async def initialize(self):
        pass
