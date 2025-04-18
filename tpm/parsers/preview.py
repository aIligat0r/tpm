import asyncio

import httpx
from bs4 import BeautifulSoup
from structlog.contextvars import bound_contextvars

from tpm import utils
from tpm.entities import Post
from tpm.utils.logger import logger
from tpm.config import TelegramConfig
from tpm.parsers.base import BaseParser
from tpm.parsers.post import PostsParser
from tpm.http_client.client import HttpClient
from tpm.database.db import DatabaseProcessor


class PreviewParser(BaseParser):
    """
    Telegram preview page parser
    """

    def __init__(
        self,
        channels: list[str],
        db_path: str,
        verbose: bool = False,
    ):
        self.channels: list[str] = channels
        self.http_client = HttpClient()
        self.post_parser = PostsParser(verbose=verbose)
        self.db = DatabaseProcessor(db_path=db_path)
        self._db_initialized = False
        self.verbose = verbose

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

            for parse_repeat in range(TelegramConfig.iteration_in_preview_count):
                if should_break:
                    await logger.ainfo("No new posts yet")
                    break

                try:
                    response = await self._get_preview_page(preview_url=preview_url)
                    if not response:
                        await logger.awarning("Can not get preview page")
                        await asyncio.sleep(TelegramConfig.sleep_after_error_request)
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
                        await asyncio.sleep(TelegramConfig.sleep_after_error_request)
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
                    if before_param_number <= TelegramConfig.before_param_size:
                        before_param_number -= TelegramConfig.before_param_size
                    else:
                        before_param_number = (
                            before_param_number - TelegramConfig.before_param_size
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
