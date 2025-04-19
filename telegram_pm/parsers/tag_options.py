import re
from dataclasses import dataclass


@dataclass
class TagOptions:
    attrs: dict
    tag: str


class PostParseConfig:
    channel_id = TagOptions(
        tag="div",
        attrs={
            "class": "tgme_widget_message text_not_supported_wrap js-widget_message"
        },
    )

    post_block = TagOptions(
        tag="div",
        attrs={"class": re.compile(r"tgme_widget_message_wrap js-widget_message_wrap")},
    )

    post_url = TagOptions(tag="a", attrs={"class": "tgme_widget_message_date"})

    replied_url = TagOptions(tag="a", attrs={"class": "tgme_widget_message_reply"})

    text = TagOptions(
        tag="div",
        attrs={"class": re.compile(r"tgme_widget_message_text js-message_text")},
    )

    date = TagOptions(tag="time", attrs={"class": "time"})

    photo_url = TagOptions(
        tag="a", attrs={"class": re.compile(r"tgme_widget_message_photo_wrap")}
    )

    video_url = TagOptions(
        tag="i", attrs={"class": re.compile(r"tgme_widget_message_video_thumb")}
    )

    round_video_url = TagOptions(
        tag="video",
        attrs={
            "class": re.compile(r"tgme_widget_message_roundvideo js-message_roundvideo")
        },
    )

    url = TagOptions(
        tag="a",
        attrs={
            "target": re.compile(r"_blank"),
            "href": re.compile(r"^https?://"),
        },
    )

    url_preview = TagOptions(
        tag="a", attrs={"class": re.compile(r"tgme_widget_message_link_preview")}
    )

    file = TagOptions(
        tag="div", attrs={"class": re.compile(r"tgme_widget_message_document_title")}
    )

    file_extra = TagOptions(
        tag="div", attrs={"class": re.compile(r"tgme_widget_message_document_extra")}
    )

    tag = TagOptions(tag="a", attrs={"href": re.compile(r"^\?q=%23")})

    forwarded_from_name = TagOptions(
        tag="a", attrs={"class": "tgme_widget_message_forwarded_from_name"}
    )

    forwarded_from_url = TagOptions(
        tag="a", attrs={"class": "tgme_widget_message_forwarded_from_name"}
    )
