import re
import json
import base64

from bs4 import BeautifulSoup, PageElement

from telegram_pm.parsers.tag_options import TagOptions


URL_REGEX = re.compile(
    r"https?://(?:www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_+.~#?&/=]*"
)


def content_to_bs(content: str) -> BeautifulSoup:
    return BeautifulSoup(content, "html5lib")


def extract_element(
    bs_content: BeautifulSoup, tag_ops: TagOptions
) -> list[PageElement]:
    elements = bs_content.find_all(tag_ops.tag, attrs=tag_ops.attrs)
    return [elem for elem in elements]


def extract_url_from_style(style_content: str) -> str | None:
    url = URL_REGEX.search(style_content)
    if url:
        return url.group(0)
    return None


def channel_id_clean(id_str: str) -> int:
    """
    Extract id from channel id string
        c2233445566/14992 -> 2233445566
    """
    channel_id = id_str.split("/")[0][1:]
    return int(channel_id)


def decode_channel_id(channel_id_base64: str) -> int:
    if not channel_id_base64.endswith("="):
        channel_id_base64 += "=="
    channel_id = json.loads(base64.b64decode(channel_id_base64))
    return channel_id["c"]
