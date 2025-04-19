import httpx
from retry import retry

from telegram_pm.utils.logger import logger
from telegram_pm.config import HttpClientConfig


class HttpClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(
                verify=False,
                retries=HttpClientConfig.retries,
            ),
            timeout=HttpClientConfig.timeout,
            verify=False,
        )

    @retry(backoff=HttpClientConfig.backoff, logger=logger)  # type: ignore[arg-type]
    async def request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        response = await self.client.request(method=method, url=url, **kwargs)
        return response
