from dataclasses import dataclass, field


@dataclass
class Post:
    username: str
    url: str
    date: str
    id: int | None
    text: str | None = None
    replied_post_url: str | None = None
    urls: list[str] = field(default_factory=list)
    url_preview: str | None = None
    photo_urls: list[str] = field(default_factory=list[str])
    video_urls: list[str] = field(default_factory=list[str])
    round_video_url: str | None = None
    files: list[dict[str, str]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list[str])
    forwarded_from_url: str | None = None
    forwarded_from_name: str | None = None
