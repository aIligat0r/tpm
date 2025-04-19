import httpx
from retry import retry

from telegram_pm.utils.logger import logger
from telegram_pm.config import HttpClientConfig


class HttpClient:
    def __init__(
        self,
        retries: int = HttpClientConfig.retries,
        timeout: int = HttpClientConfig.timeout,
        backoff: int = HttpClientConfig.backoff,
        headers: dict[str, str] = HttpClientConfig.headers,
    ):
        self._headers = headers
        self._backoff = backoff
        self._retries = retries
        self.client = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(
                verify=False,
                retries=retries,
            ),
            timeout=timeout,
            verify=False,
        )

    async def request(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        @retry(backoff=self._backoff, logger=logger)  # type: ignore[arg-type]
        async def nested_request() -> httpx.Response:
            response = await self.client.request(
                method=method, url=url, headers=self._headers, **kwargs
            )
            return response

        return await nested_request()
