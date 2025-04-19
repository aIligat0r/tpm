import sys
import signal
import asyncio

from telegram_pm.parsers.preview import PreviewParser
from telegram_pm.utils.logger import logger
from telegram_pm.config import TelegramConfig


class ParserRunner:
    def __init__(self, db_path: str, channels: list[str], verbose: bool = False):
        self.db_path = db_path
        self.channels = channels
        self.verbose = verbose

        self._shutdown = False

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self._shutdown = True
        sys.exit(0)

    async def run(self):
        parser = PreviewParser(
            channels=self.channels, verbose=self.verbose, db_path=self.db_path
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


def run_parser(db_path: str, channels: list[str], verbose: bool = False):
    runner = ParserRunner(channels=channels, verbose=verbose, db_path=db_path)
    asyncio.run(runner.run())
