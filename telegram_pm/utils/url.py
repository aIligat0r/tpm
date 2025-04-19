from urllib.parse import urljoin

from telegram_pm.config import TelegramConfig


def build_preview_url(username: str) -> str:
    """
    Build preview URL.
        username -> https://t.me/s/username
    :param username: Telegram username
    :return: str
    """
    return urljoin(TelegramConfig.base_url, urljoin("/s/", username))


def build_param_before_url(url: str, before: int | str) -> str:
    """
    Build preview URL with before parameter.
        - https://t.me/s/username -> https://t.me/s/username?before
        - https://t.me/s/username -> https://t.me/s/username?before=123
    :param url: str - Preview URL
    :param before: - Before parameter value
    :return: str
    """
    return urljoin(url, f"?before={before}")


def get_username_from_tg_url(url: str) -> str:
    """
    Get username from Telegram URL.
    """
    if url.startswith(TelegramConfig.base_url):
        return url.split("/")[-1]
    return url
