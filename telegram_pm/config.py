from os import environ

from dotenv import load_dotenv

load_dotenv()


class BaseConfig: ...


class HttpClientConfig(BaseConfig):
    retries: int = int(environ.get("HTTP_RETRIES", 3))
    backoff: int = int(environ.get("HTTP_BACKOFF", 3))
    timeout: int = int(environ.get("HTTP_TIMEOUT", 30))


class TelegramConfig(BaseConfig):
    base_url: str = environ.get("TELEGRAM_BASE_URL", "https://t.me")

    before_param_size: int = int(environ.get("TELEGRAM_BEFORE_PARAM_SIZE", 20))
    iteration_in_preview_count: int = int(environ.get("TELEGRAM_PARSE_REPEAT_COUNT", 5))
    sleep_time_seconds: int = int(environ.get("TELEGRAM_SLEEP_TIME_SECONDS", 60))
    sleep_after_error_request: int = int(
        environ.get("TELEGRAM_SLEEP_AFTER_ERROR_REQUEST", 30)
    )
