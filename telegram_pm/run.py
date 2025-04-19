import sys
import signal
import asyncio

from telegram_pm import config
from telegram_pm.utils.logger import logger
from telegram_pm.config import TelegramConfig
from telegram_pm.parsers.preview import PreviewParser


class ParserRunner:
    def __init__(
        self,
    ):
        self._shutdown = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown = True
        sys.exit(0)

    async def run(
        self,
        db_path: str,
        channels: list[str],
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
        parser = PreviewParser(
            channels=channels,
            verbose=verbose,
            db_path=db_path,
            tg_before_param_size=tg_before_param_size,
            tg_iteration_in_preview_count=tg_iteration_in_preview_count,
            tg_sleep_time_seconds=tg_sleep_time_seconds,
            tg_sleep_after_error_request=tg_sleep_after_error_request,
            http_retries=http_retries,
            http_backoff=http_backoff,
            http_timeout=http_timeout,
            http_headers=http_headers,
        )
        try:
            while not self._shutdown:
                try:
                    await parser.parse()
                    logger.info(
                        f"💤 Sleep {TelegramConfig.sleep_time_seconds} seconds ... 💤"
                    )
                    await asyncio.sleep(TelegramConfig.sleep_time_seconds)
                except Exception as e:
                    logger.error(f"Error during parsing: {e}")
                    await asyncio.sleep(TelegramConfig.sleep_after_error_request)
        finally:
            if parser:
                await parser.close()


def run_tpm(
    db_path: str,
    channels: list[str],
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
    runner = ParserRunner()
    asyncio.run(
        runner.run(
            channels=channels,
            verbose=verbose,
            db_path=db_path,
            tg_before_param_size=tg_before_param_size,
            tg_iteration_in_preview_count=tg_iteration_in_preview_count,
            tg_sleep_time_seconds=tg_sleep_time_seconds,
            tg_sleep_after_error_request=tg_sleep_after_error_request,
            http_retries=http_retries,
            http_backoff=http_backoff,
            http_timeout=http_timeout,
            http_headers=http_headers,
        )
    )
