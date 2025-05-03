import asyncio

import httpx
from bs4 import BeautifulSoup
from structlog.contextvars import bound_contextvars

from telegram_pm import utils, config
from telegram_pm.entities import Post
from telegram_pm.utils.logger import logger
from telegram_pm.parsers.base import BaseParser
from telegram_pm.parsers.post import PostsParser
from telegram_pm.http_client.client import HttpClient
from telegram_pm.database.sqlite_processor import DatabaseProcessor
from telegram_pm.database.csv_processor import CSVProcessor


class PreviewParser(BaseParser):
    """
    Telegram preview page parser
    """

    def __init__(
        self,
        channels: list[str],
        db_path: str,
        format: str = "sqlite",
        verbose: bool = False,
        tg_before_param_size: int = config.TelegramConfig.before_param_size,
        tg_iteration_in_preview_count: int = config.TelegramConfig.iteration_in_preview_count,
        tg_sleep_time_seconds: int = config.TelegramConfig.sleep_time_seconds,
        tg_sleep_after_error_request: int = config.TelegramConfig.sleep_after_error_request,
        http_retries: int = config.HttpClientConfig.retries,
        http_backoff: int = config.HttpClientConfig.backoff,
        http_timeout: int = config.HttpClientConfig.timeout,
        http_headers: dict[str, str] = config.HttpClientConfig.headers,
    ):
        """
        :param db_path: Path to sqlite database
        :param channels: Channels list
        :param verbose: Verbose mode
        :param tg_before_param_size: 20 messages per request. (1 iter - last 20 messages)
        :param tg_iteration_in_preview_count: Number of requests (default 5). 20 messages per request. (1 iter - last 20 messages)
        :param tg_sleep_time_seconds:  Number of seconds after which the next process of receiving data from channels will begin (default 60 seconds)
        :param tg_sleep_after_error_request: Waiting after a failed requests (default 30)
        :param http_retries: Number of repeated request attempts (default 3)
        :param http_backoff: Delay between attempts for failed requests (default 3 seconds)
        :param http_timeout: Waiting for a response (default 30 seconds)
        :param http_headers: HTTP headers
        """
        self._tg_sleep_after_error_request = tg_sleep_after_error_request
        self._tg_sleep_time_seconds = tg_sleep_time_seconds
        self._tg_iteration_in_preview_count = tg_iteration_in_preview_count
        self._tg_before_param_size = tg_before_param_size

        self.channels: list[str] = channels
        self.http_client = HttpClient(
            retries=http_retries,
            backoff=http_backoff,
            timeout=http_timeout,
            headers=http_headers,
        )
        self.post_parser = PostsParser(verbose=verbose)
        self.db = self.__initial_db(format=format, db_path=db_path)
        self._db_initialized = False
        self.verbose = verbose

    @staticmethod
    def __initial_db(format: str, db_path: str):
        if format == "sqlite":
            return DatabaseProcessor(db_path=db_path)
        else:
            return CSVProcessor(csv_dir=db_path)

    @staticmethod
    def __forbidden_parse_preview(response: httpx.Response) -> bool:
        """
        Check parsing availability
        :param response: httpx.Response
        :return: bool. If True, then you can't parse preview page
        """
        if response.status_code in (302,):
            return True
        return False

    @staticmethod
    def __parse_before_param_value(post_url: str) -> int:
        before_value = post_url.split("/")[-1]
        return int(before_value)

    async def _get_preview_page(self, preview_url: str) -> httpx.Response:
        """
        Get preview page
        :param preview_url: str. Full preview URL
        :return: httpx.Response
        """
        response_preview_url = await self.http_client.request(
            url=preview_url,
        )
        return response_preview_url

    def _parse_posts_in_preview(
        self, username: str, response: httpx.Response
    ) -> list[Post]:
        bs_content = BeautifulSoup(response.text, "html5lib")
        posts = self.post_parser.parse(username=username, bs_preview_content=bs_content)
        return posts

    async def initialize(self):
        """Initialize database"""
        if not self._db_initialized:
            await self.db.initialize()
            self._db_initialized = True

    async def close(self):
        """Clean up resources"""
        if hasattr(self.db, "close"):
            await self.db.close()

    async def parse_channel(self, channel_username: str):
        """Parse single channel"""
        channel_username = utils.url.get_username_from_tg_url(channel_username)
        with bound_contextvars(username=channel_username):
            if not await self.db.table_exists(channel_username):
                await self.db.create_table_from_post(channel_username)
                await logger.ainfo("Created new table for channel")

            preview_url = utils.url.build_preview_url(username=channel_username)
            posts_result = []
            should_break = False

            for parse_repeat in range(self._tg_iteration_in_preview_count):
                if should_break:
                    await logger.ainfo("No new posts yet")
                    break

                try:
                    response = await self._get_preview_page(preview_url=preview_url)
                    if not response:
                        await logger.awarning("Can not get preview page")
                        await asyncio.sleep(self._tg_sleep_after_error_request)
                        continue

                    if self.__forbidden_parse_preview(response=response):
                        await logger.awarning("Forbidden parsing preview")
                        break

                    parsed_posts = self._parse_posts_in_preview(
                        username=channel_username, response=response
                    )
                    if not parsed_posts:
                        await logger.awarning("No posts parsed from preview page")  # type: ignore
                        await self.db.drop_table_if_empty(channel_username)
                        await asyncio.sleep(self._tg_sleep_after_error_request)
                        break

                    first_post_exists = await self.db.post_exists(
                        channel_username, parsed_posts[0].url
                    )
                    if first_post_exists:
                        should_break = True
                        continue

                    await self.db.insert_posts_batch(channel_username, parsed_posts)
                    posts_result.extend(parsed_posts)

                    before_param_number = self.__parse_before_param_value(
                        post_url=parsed_posts[-1].url
                    )
                    if before_param_number <= self._tg_before_param_size:
                        before_param_number -= self._tg_before_param_size
                    else:
                        before_param_number = (
                            before_param_number - self._tg_before_param_size
                        )
                        if before_param_number <= 0:
                            break

                    preview_url = utils.url.build_param_before_url(
                        url=preview_url, before=before_param_number
                    )

                except Exception as e:
                    await logger.aerror(
                        f"Error parsing channel {channel_username}: {e}"
                    )
                    break

            return posts_result

    async def parse(self):
        """Main parsing method"""
        await self.initialize()

        try:
            for channel_username in self.channels:
                try:
                    await self.parse_channel(channel_username)
                except Exception as e:
                    await logger.aerror(
                        f"Failed to parse channel {channel_username}: {e}"
                    )
                    continue
        finally:
            await self.close()
