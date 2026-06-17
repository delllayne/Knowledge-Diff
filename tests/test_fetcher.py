from __future__ import annotations

import httpx
import pytest
from knowdiff.fetcher import FetchError, ValidationError, fetch_page, validate_url


class FakeClient:
    def __init__(
        self,
        response: httpx.Response | None = None,
        error: Exception | None = None,
    ) -> None:
        self._response = response
        self._error = error

    def __enter__(self) -> FakeClient:
        return self

    def __exit__(self, _exc_type: object, exc: object, _tb: object) -> None:
        return None

    def get(self, url: str, headers: dict[str, str]) -> httpx.Response:
        del url, headers
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


def test_validate_url_rejects_invalid_input() -> None:
    with pytest.raises(ValidationError):
        validate_url("example.com")


def test_fetch_page_returns_html(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "knowdiff.fetcher.httpx.Client",
        lambda **_: FakeClient(response=httpx.Response(200, text="<html></html>")),
    )
    assert fetch_page("https://example.com") == "<html></html>"


def test_fetch_page_raises_on_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "knowdiff.fetcher.httpx.Client",
        lambda **_: FakeClient(response=httpx.Response(500, text="boom")),
    )
    with pytest.raises(FetchError):
        fetch_page("https://example.com")


def test_fetch_page_maps_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("GET", "https://example.com")
    monkeypatch.setattr(
        "knowdiff.fetcher.httpx.Client",
        lambda **_: FakeClient(error=httpx.ReadTimeout("timeout", request=request)),
    )
    with pytest.raises(FetchError):
        fetch_page("https://example.com")
