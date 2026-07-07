"""HTTP client for the Magyar Elektronikus Konyvtar web search forms."""

from __future__ import annotations

from collections.abc import Mapping
from types import TracebackType
from typing import Any

import httpx

from .schemas import (
    AdvancedField,
    AdvancedOperator,
    AdvancedSearchQuery,
    FullTextSearchQuery,
    IndexBrowseQuery,
    MekPage,
    RecordQuery,
    SimpleSearchQuery,
)

MEK_BASE_URL = "https://mek.oszk.hu"
DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_USER_AGENT = "mek-mcp/0.1.0 (+https://mek.oszk.hu/)"
ADVANCED_FIELD_VALUES = tuple(field.value for field in AdvancedField)
ADVANCED_OPERATOR_VALUES = tuple(operator.value for operator in AdvancedOperator)
DEFAULT_ADVANCED_FIELD_INDEXES = (0, 7, 16, 13, 18)


class MekClientError(RuntimeError):
    """Raised when MEK cannot be reached or returns an unusable response."""


class MekClient:
    """Small HTTP wrapper around MEK search endpoints."""

    def __init__(
        self,
        *,
        base_url: str = MEK_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> MekClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def fetch_simple_search(self, query: SimpleSearchQuery) -> MekPage:
        data = {
            "dc_title": query.title or "",
            "dc_subject": query.subject or "",
            "dc_creator": query.creator or "",
            "id": query.mek_id or "",
            "size": str(query.limit),
            "sort": "",
            "from": str(query.offset) if query.offset else "",
        }
        return self.post("/hu/search/elfull/", data=data)

    def fetch_full_text_search(self, query: FullTextSearchQuery) -> MekPage:
        data = {
            "body": query.query,
            "broadtopic": query.broadtopic,
            "size": str(query.limit),
            "sort": "",
            "from": str(query.offset) if query.offset else "",
        }
        return self.post("/hu/search/elfulltext/", data=data)

    def fetch_advanced_search(self, query: AdvancedSearchQuery) -> MekPage:
        data: dict[str, str] = {"szerint": query.sort}
        params = _advanced_index_params(query)

        for index, condition in enumerate(query.conditions, start=1):
            data[f"s{index}"] = condition.field
            data[f"m{index}"] = condition.value
            if index < 5:
                data[f"muv{index}"] = condition.operator_after

        for index in range(len(query.conditions) + 1, 6):
            data[f"s{index}"] = ""
            data[f"m{index}"] = ""
            if index < 5:
                data[f"muv{index}"] = "and"

        if query.accentless:
            data["ekezet"] = "ektelen"
        if query.include_in_progress:
            data["subid"] = "on"

        return self._request("POST", "/katalog/kataluj.php3", params=params, data=data)

    def fetch_index_browse(self, query: IndexBrowseQuery) -> MekPage:
        field_index = ADVANCED_FIELD_VALUES.index(query.field)
        params = {
            "tablefield": query.field,
            "par": "0",
            "indindex": str(field_index),
            "muv1index": "0",
            "muv2index": "0",
            "muv3index": "0",
            "muv4index": "0",
        }
        data = {
            "szerint": "",
            "s1": query.field,
            "s2": "",
            "s3": "",
            "s4": "",
            "s5": "",
            "m1": query.prefix,
            "m2": "",
            "m3": "",
            "m4": "",
            "m5": "",
            "muv1": "",
            "muv2": "",
            "muv3": "",
            "muv4": "",
        }
        return self.post("/katalog/browsuj.php3", params=params, data=data)

    def fetch_record(self, query: RecordQuery) -> MekPage:
        return self.get(_record_path(query.identifier))

    def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> MekPage:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> MekPage:
        return self._request("POST", path, params=params, data=data)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> MekPage:
        try:
            response = self._client.request(method, path, params=params, data=data)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MekClientError(f"MEK request failed: {exc}") from exc

        return MekPage(
            url=str(response.url),
            status_code=response.status_code,
            html=_decode_response_text(response),
        )


def _decode_response_text(response: httpx.Response) -> str:
    content_type = response.headers.get("content-type", "").lower()
    sample = response.content[:2048].lower()

    if "iso-8859-2" in content_type or b"iso-8859-2" in sample:
        return response.content.decode("iso-8859-2", errors="replace")
    if "utf-8" in content_type or b"utf-8" in sample:
        return response.content.decode("utf-8", errors="replace")

    return response.text


def _advanced_index_params(query: AdvancedSearchQuery) -> dict[str, str]:
    params: dict[str, str] = {}

    for index in range(1, 6):
        field_index = DEFAULT_ADVANCED_FIELD_INDEXES[index - 1]
        if index <= len(query.conditions):
            field = query.conditions[index - 1].field
            field_index = ADVANCED_FIELD_VALUES.index(field)
        params[f"sind{index}"] = str(field_index)

    for index in range(1, 5):
        operator_index = 0
        if index <= len(query.conditions):
            operator = query.conditions[index - 1].operator_after
            operator_index = ADVANCED_OPERATOR_VALUES.index(operator)
        params[f"muv{index}index"] = str(operator_index)

    return params


def _record_path(identifier: str) -> str:
    clean_identifier = identifier.strip()
    if clean_identifier.startswith(MEK_BASE_URL):
        clean_identifier = clean_identifier.removeprefix(MEK_BASE_URL)
    if clean_identifier.startswith("http://mek.oszk.hu"):
        clean_identifier = clean_identifier.removeprefix("http://mek.oszk.hu")
    if not clean_identifier.startswith("/"):
        clean_identifier = f"/{clean_identifier}"
    return clean_identifier
