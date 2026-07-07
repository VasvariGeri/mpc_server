"""Shared request and response schemas for MEK searches."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SearchKind(str, Enum):
    SIMPLE = "simple"
    FULL_TEXT = "full_text"
    ADVANCED = "advanced"
    INDEX = "index"
    RECORD = "record"


class SearchSize(int, Enum):
    TEN = 10
    FIFTY = 50
    HUNDRED = 100


class FullTextBroadTopic(str, Enum):
    ALL = ""
    NATURAL_SCIENCES = "természettudományok és matematika"
    TECHNICAL_SCIENCES = "műszaki tudományok, gazdasági ágazatok"
    SOCIAL_SCIENCES = "társadalomtudományok"
    HUMANITIES = "humán területek, kultúra, irodalom"
    REFERENCE = "kézikönyvek és egyéb műfajok"


class AdvancedField(str, Enum):
    TITLE_MAIN = "dc_title main"
    TITLE_SUBTITLE = "dc_title subtitle"
    TITLE_PART_OF = "dc_title PartOf"
    TITLE_PARTS = "dc_title parts"
    TITLE_ALTERNATIVE = "dc_title alternative"
    TITLE_ORIGINAL = "dc_title original"
    TITLE_SERIES = "dc_title series"
    CREATOR = "dc_creator_o FamilyGivenName"
    CREATOR_ROLE = "dc_creator_o role"
    CORPORATE_AUTHOR = "CorporateAuthor Cauth_name"
    CONTRIBUTOR = "dc_contributor_o FamilyGivenName"
    CONTRIBUTOR_ROLE = "dc_contributor_o role"
    PUBLISHER = "dc_publisher pub_name"
    SUBJECT_KEYWORD = "dc_subject keyword"
    SUBJECT_GEOGRAPHIC = "dc_subject geographic"
    SUBJECT_PERIOD = "dc_subject period"
    DOCUMENT_TYPE = "dc_type dc_type"
    FORMAT = "dc_format format_name"
    LANGUAGE = "dc_language m_lang"
    ORIGINAL_LANGUAGE = "dc_language original"
    PRINTED_SOURCE = "PrintedSource PrintedSource"
    RIGHTS_OWNER = "dc_rights owner"
    RIGHTS_OTHER = "dc_rights other"
    CREATIVE_COMMONS = "dc_rights dc_cc"


class AdvancedOperator(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"


class AdvancedSort(str, Enum):
    TITLE = "cimsz"
    CREATOR = "szerzosz"
    CHRONOLOGICAL = "idorend"
    ID = "idsz"


class MekBaseModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, use_enum_values=True)


class SimpleSearchQuery(MekBaseModel):
    title: str | None = Field(default=None, description="Title search term.")
    subject: str | None = Field(default=None, description="Subject search term.")
    creator: str | None = Field(default=None, description="Author/editor/translator.")
    mek_id: str | None = Field(default=None, description="MEK document identifier.")
    limit: SearchSize = SearchSize.TEN
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def require_at_least_one_search_field(self) -> SimpleSearchQuery:
        if not any([self.title, self.subject, self.creator, self.mek_id]):
            raise ValueError("At least one simple search field must be provided.")
        return self


class FullTextSearchQuery(MekBaseModel):
    query: str = Field(min_length=1, description="Full text search query.")
    broadtopic: FullTextBroadTopic = FullTextBroadTopic.ALL
    limit: SearchSize = SearchSize.TEN
    offset: int = Field(default=0, ge=0)


class AdvancedCondition(MekBaseModel):
    field: AdvancedField
    value: str = Field(min_length=1)
    operator_after: AdvancedOperator = AdvancedOperator.AND


class AdvancedSearchQuery(MekBaseModel):
    conditions: list[AdvancedCondition] = Field(min_length=1, max_length=5)
    sort: AdvancedSort = AdvancedSort.CREATOR
    accentless: bool = False
    include_in_progress: bool = False

    @field_validator("conditions")
    @classmethod
    def clear_last_join_operator(
        cls, conditions: list[AdvancedCondition]
    ) -> list[AdvancedCondition]:
        if conditions:
            conditions[-1].operator_after = AdvancedOperator.AND
        return conditions


class IndexBrowseQuery(MekBaseModel):
    field: AdvancedField
    prefix: str = Field(min_length=1)
    limit: int = Field(default=50, ge=1, le=200)


class RecordQuery(MekBaseModel):
    identifier: str = Field(
        min_length=1,
        description="MEK ID such as 05500/05585, or a MEK record URL.",
    )


class SearchResult(MekBaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    url: str | None = None
    mek_id: str | None = None
    snippet: str | None = None
    found_url: str | None = None


class SearchResponse(MekBaseModel):
    kind: SearchKind
    results: list[SearchResult] = Field(default_factory=list)
    total_results: int | None = None
    limit: int
    offset: int
    next_offset: int | None = None
    source_url: str


class IndexEntry(MekBaseModel):
    value: str
    label: str


class IndexBrowseResponse(MekBaseModel):
    kind: SearchKind = SearchKind.INDEX
    field: AdvancedField
    prefix: str
    entries: list[IndexEntry] = Field(default_factory=list)
    total_results: int | None = None
    limit: int
    source_url: str


class RecordFile(MekBaseModel):
    label: str
    url: str
    file_type: str | None = None


class RecordResponse(MekBaseModel):
    kind: SearchKind = SearchKind.RECORD
    title: str | None = None
    authors: list[str] = Field(default_factory=list)
    mek_id: str | None = None
    url: str
    urn: str | None = None
    description: str | None = None
    date: str | None = None
    topics: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    files: list[RecordFile] = Field(default_factory=list)
    related_pages: list[RecordFile] = Field(default_factory=list)
    cover_url: str | None = None
    metadata: dict[str, list[str]] = Field(default_factory=dict)


class MekPage(MekBaseModel):
    url: str
    status_code: int
    html: str
