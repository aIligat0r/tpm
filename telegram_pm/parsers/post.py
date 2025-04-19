import typer
from bs4 import BeautifulSoup, PageElement

from telegram_pm import utils
from telegram_pm.entities import Post
from telegram_pm.utils.logger import logger
from telegram_pm.parsers.base import BaseParser
from telegram_pm.config import TelegramConfig
from telegram_pm.parsers.tag_options import PostParseConfig, TagOptions


class PostsParser(BaseParser):
    """
    Posts parsers from preview page
    """

    def __init__(self, verbose: bool = False):
        self.__verbose: bool = verbose
        self._tag_ops = PostParseConfig

    @staticmethod
    def get_post_attribute(
        post: PageElement,
        tab_ops: TagOptions,
        extract_field: str,
        _warn_log_enable: bool = True,
    ) -> str | None:
        post_attribute = post.find(name=tab_ops.tag, attrs=tab_ops.attrs)  # type: ignore[attr-defined]
        if post_attribute:
            if extract_field == "text":
                return post_attribute.text
            return post_attribute.get(extract_field)
        if _warn_log_enable:
            logger.warning(f"Not found. '{tab_ops.tag}': '{tab_ops.attrs}'")
        return None

    def get_channel_id(self, post: PageElement) -> int | None:
        channel_base64 = self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.channel_id,
            extract_field="data-view",
            _warn_log_enable=False,
        )
        if not channel_base64:
            return None
        channel_id = utils.parse.decode_channel_id(channel_base64)
        return channel_id

    @staticmethod
    def get_urls_from_styles(post: PageElement, tag_pos: TagOptions) -> list[str]:
        urls = []
        styles_list = post.find_all(name=tag_pos.tag, attrs=tag_pos.attrs)  # type: ignore[attr-defined]
        for style in styles_list:
            urls.append(
                utils.parse.extract_url_from_style(style_content=style.get("style", ""))
            )
        return urls  # type: ignore[return-value]

    def get_posts(self, bs_preview_content: BeautifulSoup) -> list[PageElement]:
        posts_list = utils.parse.extract_element(
            bs_content=bs_preview_content,
            tag_ops=self._tag_ops.post_block,
        )
        return posts_list

    def get_post_url(self, username: str, post: PageElement) -> str:
        post_url = self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.post_url,
            extract_field="href",
        )
        if post_url.startswith(f"{TelegramConfig.base_url}/"):  # type: ignore[union-attr]
            post_url = post_url.split("/")[-1]  # type: ignore[union-attr]
            post_url = f"{TelegramConfig.base_url}/{username}/{post_url}"
        return post_url  # type: ignore[return-value]

    def get_post_date(self, post: PageElement) -> str:
        return self.get_post_attribute(  # type: ignore[return-value]
            post=post,
            tab_ops=self._tag_ops.date,
            extract_field="datetime",
        )

    def get_replied_url(self, post: PageElement) -> str | None:
        return self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.replied_url,
            extract_field="href",
            _warn_log_enable=False,
        )

    def get_forwarded_from_url(self, post: PageElement) -> str | None:
        return self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.forwarded_from_url,
            extract_field="href",
            _warn_log_enable=False,
        )

    def get_forwarded_from_name(self, post: PageElement) -> str | None:
        return self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.forwarded_from_name,
            extract_field="text",
            _warn_log_enable=False,
        )

    def get_text(self, post: PageElement) -> str | None:
        return self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.text,
            extract_field="text",
            _warn_log_enable=False,
        )

    def get_photo_urls(self, post: PageElement) -> list[str]:
        return self.get_urls_from_styles(
            post=post,
            tag_pos=self._tag_ops.photo_url,
        )

    def get_video_urls(self, post: PageElement) -> list[str]:
        return self.get_urls_from_styles(
            post=post,
            tag_pos=self._tag_ops.video_url,
        )

    def get_round_video(self, post: PageElement) -> str | None:
        return self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.round_video_url,
            extract_field="src",
            _warn_log_enable=False,
        )

    def get_urls(self, post: PageElement) -> list[str]:
        urls = set()
        url_elements = post.find_all(  # type: ignore[attr-defined]
            name=self._tag_ops.url.tag,
            attrs=self._tag_ops.url.attrs,
        )
        for url in url_elements:
            urls.add(url.get("href"))
        return list(urls)

    def get_url_preview(self, post: PageElement) -> str | None:
        return self.get_post_attribute(
            post=post,
            tab_ops=self._tag_ops.url_preview,
            extract_field="text",
            _warn_log_enable=False,
        )

    def get_files(self, post: PageElement) -> list[dict[str, str]]:
        files: list = []
        files_elements = post.find_all(  # type: ignore[attr-defined]
            name=self._tag_ops.file.tag,
            attrs=self._tag_ops.file.attrs,
        )
        file: PageElement
        for file in files_elements:
            title = file.text
            extra = file.find_next_sibling(  # type: ignore[union-attr]
                name=self._tag_ops.file_extra.tag,
                attrs=self._tag_ops.file_extra.attrs,
            ).text
            files.append({"title": title, "extra": extra})
        return files

    def get_tags(self, post: PageElement) -> list[str]:
        tags_elements = post.find_all(  # type: ignore[attr-defined]
            name=self._tag_ops.tag.tag,
            attrs=self._tag_ops.tag.attrs,
        )
        return [tag.text for tag in tags_elements]

    def parse(self, username: str, bs_preview_content: BeautifulSoup) -> list[Post]:
        parse_results = []
        posts_list = self.get_posts(bs_preview_content=bs_preview_content)
        for post_element in posts_list:
            post = Post(
                username=username,
                id=self.get_channel_id(post_element),
                url=self.get_post_url(username, post_element),
                date=self.get_post_date(post_element),
                replied_post_url=self.get_replied_url(post_element),
                text=self.get_text(post_element),
                photo_urls=self.get_photo_urls(post_element),
                video_urls=self.get_video_urls(post_element),
                round_video_url=self.get_round_video(post_element),
                urls=self.get_urls(post_element),
                url_preview=self.get_url_preview(post_element),
                files=self.get_files(post_element),
                tags=self.get_tags(post_element),
                forwarded_from_url=self.get_forwarded_from_url(post_element),
                forwarded_from_name=self.get_forwarded_from_name(post_element),
            )
            parse_results.append(post)
            if self.__verbose:
                self._print_post(post=post)
        return parse_results

    @staticmethod
    def _print_post(post: Post):
        typer.echo("\n" + typer.style("═" * 50, fg=typer.colors.BRIGHT_MAGENTA))
        typer.echo(
            typer.style("🎯 Username: ", fg=typer.colors.BRIGHT_RED)
            + typer.style(post.username, fg=typer.colors.RED)
        )
        typer.echo(
            typer.style("📅 Date: ", fg=typer.colors.BRIGHT_CYAN)
            + typer.style(post.date, fg=typer.colors.WHITE)
        )

        typer.echo(
            typer.style("🔗 URL: ", fg=typer.colors.BRIGHT_CYAN)
            + typer.style(post.url, fg=typer.colors.BRIGHT_BLUE, underline=True)
        )

        if post.replied_post_url:
            typer.echo(
                typer.style("↩️ Replied: ", fg=typer.colors.BRIGHT_YELLOW)
                + typer.style(post.replied_post_url, fg=typer.colors.BLUE)
            )

        if post.text:
            typer.echo("\n💬💬💬")
            typer.echo(typer.style(post.text[:50], fg=typer.colors.GREEN))
            typer.echo("💬💬💬")

        if post.photo_urls:
            typer.echo("\n" + typer.style("📷 Photo: ", fg=typer.colors.BRIGHT_RED))
            for photo in post.photo_urls:
                typer.echo(typer.style(f"  → {photo}", fg=typer.colors.RED))

        if post.video_urls:
            typer.echo("\n" + typer.style("🎥 Video: ", fg=typer.colors.BRIGHT_RED))
            for video in post.video_urls:
                typer.echo(typer.style(f"  → {video}", fg=typer.colors.RED))

        if post.urls:
            typer.echo("\n" + typer.style("🌐 URLs: ", fg=typer.colors.BRIGHT_MAGENTA))
            for url in post.urls:
                typer.echo(typer.style(f"  → {url}", fg=typer.colors.MAGENTA))

        if post.url_preview:
            typer.echo("\n👀👀👀")
            typer.echo(
                typer.style(
                    f"🔍 URL preview: {post.url_preview[:50]}", fg=typer.colors.GREEN
                )
            )
            typer.echo("👀👀👀")

        if post.round_video_url:
            typer.echo(
                "\n"
                + typer.style(
                    f"🔍 Round video: {post.round_video_url}", fg=typer.colors.BLUE
                )
            )

        if post.tags:
            typer.echo(
                "\n"
                + typer.style("⌗ Tags: ", fg=typer.colors.BRIGHT_GREEN)
                + typer.style(", ".join(post.tags), fg=typer.colors.GREEN)
            )

        if post.files:
            typer.echo("\n" + typer.style("📂 Files: ", fg=typer.colors.BRIGHT_YELLOW))
            for file in post.files:
                print_file = file.get("title")
                if print_file:
                    extra = file.get("extra")
                    if extra:
                        print_file = f"{print_file} ({extra})"
                typer.echo(typer.style(f"  → {print_file}", fg=typer.colors.YELLOW))

        typer.echo(typer.style("═" * 50, fg=typer.colors.BRIGHT_MAGENTA) + "\n")
