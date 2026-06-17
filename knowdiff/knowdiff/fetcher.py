from __future__ import annotations

from urllib.parse import urlparse

import httpx


class KnowDiffError(Exception):
    """Base application error."""


class ValidationError(KnowDiffError):
    """Raised when user input is invalid."""


class FetchError(KnowDiffError):
    """Raised when a page could not be fetched."""


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(f"Invalid URL: {url}. Use a full http:// or https:// address.")
    return url


def fetch_page(url: str, timeout: float = 15.0) -> str:
    validate_url(url)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "knowdiff/0.1"})
    except httpx.TimeoutException as exc:
        raise FetchError(f"Timed out while fetching {url}. Try again later.") from exc
    except httpx.ConnectError as exc:
        raise FetchError(
            f"Could not connect to {url}. Check DNS, network access, or the site URL."
        ) from exc
    except httpx.HTTPError as exc:
        raise FetchError(f"Request failed for {url}: {exc}") from exc

    if response.status_code != 200:
        raise FetchError(f"{url} returned HTTP {response.status_code}.")

    return response.text
