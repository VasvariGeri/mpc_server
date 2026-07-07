"""HTML parsers for MEK search result pages."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from .client import MEK_BASE_URL
from .schemas import (
    AdvancedField,
    IndexBrowseResponse,
    IndexEntry,
    MekPage,
    RecordFile,
    RecordResponse,
    SearchKind,
    SearchResponse,
    SearchResult,
)

MEK_ID_PATTERN = re.compile(r"/(\d{5}/\d{5})(?:[/#?]|$)")
TOTAL_RESULTS_PATTERN = re.compile(r"(?:A\s+)?találatok száma:?\s*(\d+)", re.I)
NEXT_OFFSET_PATTERN = re.compile(r"pageNextPrev\('(\d+)'")
OLD_NEXT_OFFSET_PATTERN = re.compile(
    r"name=[\"']offset[\"']\s+value=[\"'](\d+)[\"']",
    re.I,
)
WHITESPACE_PATTERN = re.compile(r"\s+")
VOID_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


def parse_simple_results(
    page: MekPage, *, limit: int, offset: int = 0
) -> SearchResponse:
    return _parse_search_results(
        page,
        kind=SearchKind.SIMPLE,
        limit=limit,
        offset=offset,
    )


def parse_full_text_results(
    page: MekPage, *, limit: int, offset: int = 0
) -> SearchResponse:
    return _parse_search_results(
        page,
        kind=SearchKind.FULL_TEXT,
        limit=limit,
        offset=offset,
    )


def parse_advanced_results(page: MekPage, *, limit: int = 100) -> SearchResponse:
    return _parse_search_results(
        page,
        kind=SearchKind.ADVANCED,
        limit=limit,
        offset=0,
    )


def parse_index_browse_results(
    page: MekPage,
    *,
    field: AdvancedField,
    prefix: str,
    limit: int,
) -> IndexBrowseResponse:
    root = _parse_html(page.html)
    entries: list[IndexEntry] = []

    for option in root.find_all("option"):
        value = _clean_text(option.attr("value") or "")
        label = _node_text(option)
        if not value or label == "ÜRES LISTA":
            continue
        entries.append(IndexEntry(value=value, label=label or value))
        if len(entries) >= limit:
            break

    return IndexBrowseResponse(
        field=field,
        prefix=prefix,
        entries=entries,
        total_results=_parse_total_results(root.text()),
        limit=limit,
        source_url=page.url,
    )


def parse_record(page: MekPage) -> RecordResponse:
    root = _parse_html(page.html)
    metadata = _parse_meta_metadata(root)
    title = _node_text(root.find_first("h3", "title")) or _first_meta(
        metadata, "dc.title"
    )
    authors = _record_authors(root, metadata)
    topics = _record_topics(root)
    url = _record_url(root, page.url)

    return RecordResponse(
        title=title or None,
        authors=authors,
        mek_id=_parse_mek_id(url),
        url=url,
        urn=_record_urn(root, metadata),
        description=_node_text(root.find_first("div", "itemlead")) or None,
        date=_node_text(root.find_first("div", "reldate"))
        or _last_meta(metadata, "dc.date"),
        topics=topics,
        keywords=_record_keywords(root, metadata),
        files=_record_files(root),
        related_pages=_record_related_pages(root),
        cover_url=_record_cover_url(root, metadata),
        metadata=metadata,
    )


def _parse_search_results(
    page: MekPage,
    *,
    kind: SearchKind,
    limit: int,
    offset: int,
) -> SearchResponse:
    root = _parse_html(page.html)
    return SearchResponse(
        kind=kind,
        results=[_parse_hit(hit) for hit in root.find_all("div", "hit")],
        total_results=_parse_total_results(root.text()),
        limit=limit,
        offset=offset,
        next_offset=_parse_next_offset(page.html),
        source_url=page.url,
    )


def _parse_hit(hit: _Node) -> SearchResult:
    item = hit.find_first("a", "etitem")
    if item is None:
        return _parse_old_hit(hit)

    title = _node_text(item.find_first("div", "dctitle"))
    authors = _split_authors(_node_text(item.find_first("div", "dcauthor")))
    snippet = _node_text(item.find_first("div", "foundtext")) or None
    record_url = _absolute_url(item.attr("href"))
    found_link = hit.find_first("a", "mekfound")
    found_url = _absolute_url(found_link.attr("href")) if found_link else None

    return SearchResult(
        title=title or _clean_text(item.text()),
        authors=authors,
        url=record_url,
        mek_id=_parse_mek_id(record_url),
        snippet=snippet,
        found_url=found_url,
    )


def _parse_old_hit(hit: _Node) -> SearchResult:
    url = _old_hit_url(hit)
    raw_title = _node_text(hit.find_first("b")) or _old_hit_title_from_link(hit)
    title, authors = _split_old_title_and_authors(raw_title)
    snippet = _old_hit_subtitle(hit, raw_title)

    return SearchResult(
        title=title or _clean_text(hit.text()),
        authors=authors,
        url=url,
        mek_id=_parse_mek_id(url),
        snippet=snippet,
    )


def _parse_meta_metadata(root: _Node) -> dict[str, list[str]]:
    metadata: dict[str, list[str]] = {}
    for node in root.find_all("meta"):
        name = node.attr("name") or node.attr("property")
        content = node.attr("content")
        if name and content:
            metadata.setdefault(name, []).append(_clean_text(content))
    return metadata


def _record_authors(root: _Node, metadata: dict[str, list[str]]) -> list[str]:
    author_text = _node_text(root.find_first("h4", "author"))
    authors = _split_authors(author_text)
    if authors:
        return authors
    return metadata.get("dc.creator", [])


def _record_topics(root: _Node) -> list[str]:
    topics: list[str] = []
    for class_name in ("topic", "subtopic"):
        text = _node_text(root.find_first("div", class_name))
        if text:
            topics.append(text)
    return topics


def _record_keywords(root: _Node, metadata: dict[str, list[str]]) -> list[str]:
    keywords: list[str] = []
    keyword_node = root.find_first("div", "keywords")
    if keyword_node:
        for link in keyword_node.find_all("a"):
            keyword = _node_text(link)
            if keyword:
                keywords.append(keyword)
    if keywords:
        return keywords
    return metadata.get("dc.subject", [])


def _record_files(root: _Node) -> list[RecordFile]:
    files: list[RecordFile] = []
    for link in root.find_all("a", "cssfile"):
        url = _absolute_url(link.attr("href"))
        if url is None:
            continue
        files.append(
            RecordFile(
                label=_node_text(link) or link.attr("title") or "file",
                url=url,
                file_type=_record_file_type(link),
            )
        )
    return files


def _record_file_type(link: _Node) -> str | None:
    class_names = (link.attr("class") or "").split()
    for class_name in class_names:
        if class_name != "cssfile":
            return class_name
    title = link.attr("title")
    if title and "." in title:
        return title.rsplit(".", 1)[-1].lower()
    return None


def _record_related_pages(root: _Node) -> list[RecordFile]:
    pages: list[RecordFile] = []
    container = root.find_first("div", "contpages")
    if container is None:
        return pages
    for link in container.find_all("a"):
        url = _absolute_url(link.attr("href"))
        if url is None:
            continue
        pages.append(RecordFile(label=_node_text(link), url=url, file_type="html"))
    return pages


def _record_url(root: _Node, fallback_url: str) -> str:
    item_url = root.find_first("a", "itemurl")
    text = _node_text(item_url)
    if text.startswith("URL:"):
        return text.removeprefix("URL:").strip()
    href = item_url.attr("href") if item_url else None
    return _absolute_url(href) or fallback_url


def _record_urn(root: _Node, metadata: dict[str, list[str]]) -> str | None:
    item_urn = root.find_first("a", "itemurn")
    text = _node_text(item_urn)
    if text.startswith("URN:"):
        return text.removeprefix("URN:").strip()
    for identifier in metadata.get("dc.identifier", []):
        if identifier.startswith("urn:"):
            return identifier
    return None


def _record_cover_url(root: _Node, metadata: dict[str, list[str]]) -> str | None:
    image = root.find_first("img")
    image_url = _absolute_url(image.attr("src")) if image else None
    if image_url:
        return image_url
    return _first_meta(metadata, "og:image")


def _first_meta(metadata: dict[str, list[str]], key: str) -> str:
    values = metadata.get(key, [])
    return values[0] if values else ""


def _last_meta(metadata: dict[str, list[str]], key: str) -> str | None:
    values = metadata.get(key, [])
    return values[-1] if values else None


def _old_hit_url(hit: _Node) -> str | None:
    for link in hit.find_all("a"):
        href = link.attr("href") or ""
        text = _node_text(link)
        if href.startswith(("http://", "https://")):
            return _absolute_url(href)
        if text.startswith(("http://", "https://")):
            return _absolute_url(text)

    form = hit.find_first("form")
    action = form.attr("action") if form else None
    if action:
        return _absolute_url(action.replace("/index.phtml", ""))
    return None


def _old_hit_title_from_link(hit: _Node) -> str:
    for link in hit.find_all("a"):
        href = link.attr("href") or ""
        if href.lower().startswith("javascript:"):
            return _node_text(link)
    return ""


def _old_hit_subtitle(hit: _Node, raw_title: str) -> str | None:
    for link in hit.find_all("a"):
        href = link.attr("href") or ""
        if href.lower().startswith("javascript:"):
            text = _node_text(link)
            subtitle = text.replace(raw_title, "", 1).strip()
            return subtitle or None
    return None


def _split_old_title_and_authors(raw_title: str) -> tuple[str, list[str]]:
    normalized = raw_title.replace("\xa0", " ").strip()
    if ": " not in normalized:
        return normalized, []

    author_text, title = normalized.split(": ", 1)
    authors = [
        author.strip()
        for author in re.split(r"\s*(?:;|-)\s*", author_text)
        if author.strip()
    ]
    return title.strip(), authors


def _parse_total_results(text: str) -> int | None:
    match = TOTAL_RESULTS_PATTERN.search(text)
    if match is None:
        return None
    return int(match.group(1))


def _parse_next_offset(html: str) -> int | None:
    match = NEXT_OFFSET_PATTERN.search(html) or OLD_NEXT_OFFSET_PATTERN.search(html)
    if match is None:
        return None
    return int(match.group(1))


def _parse_mek_id(url: str | None) -> str | None:
    if url is None:
        return None
    match = MEK_ID_PATTERN.search(url)
    if match is None:
        return None
    return match.group(1)


def _absolute_url(url: str | None) -> str | None:
    if not url:
        return None
    return urljoin(MEK_BASE_URL, url)


def _node_text(node: _Node | None) -> str:
    if node is None:
        return ""
    return _clean_text(node.text())


def _split_authors(text: str) -> list[str]:
    if not text:
        return []
    return [author.strip() for author in re.split(r"\s*;\s*", text) if author.strip()]


def _clean_text(text: str) -> str:
    return WHITESPACE_PATTERN.sub(" ", text).strip()


def _parse_html(html: str) -> _Node:
    parser = _TreeBuilder()
    parser.feed(html)
    parser.close()
    return parser.root


class _Node:
    def __init__(self, tag: str, attrs: dict[str, str] | None = None) -> None:
        self.tag = tag
        self.attrs = attrs or {}
        self.children: list[_Node | str] = []

    def attr(self, name: str) -> str | None:
        return self.attrs.get(name)

    def text(self) -> str:
        parts: list[str] = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            else:
                parts.append(child.text())
        return "".join(parts)

    def find_first(
        self, tag: str | None = None, class_name: str | None = None
    ) -> _Node | None:
        matches = self.find_all(tag, class_name)
        return matches[0] if matches else None

    def find_all(
        self, tag: str | None = None, class_name: str | None = None
    ) -> list[_Node]:
        matches: list[_Node] = []
        if self._matches(tag, class_name):
            matches.append(self)

        for child in self.children:
            if isinstance(child, _Node):
                matches.extend(child.find_all(tag, class_name))
        return matches

    def _matches(self, tag: str | None, class_name: str | None) -> bool:
        if tag is not None and self.tag != tag:
            return False
        if class_name is None:
            return True
        return class_name in self.attrs.get("class", "").split()


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document")
        self._stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag, {key: value or "" for key, value in attrs})
        self._stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self._stack) - 1, 0, -1):
            if self._stack[index].tag == tag:
                del self._stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self._stack[-1].children.append(data)
