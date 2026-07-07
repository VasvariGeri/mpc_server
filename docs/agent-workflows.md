# Agent Workflows

This guide describes how an agentic assistant should combine the MEK MCP tools
to answer bibliographic questions against the Magyar Elektronikus Konyvtar.

The server intentionally exposes search primitives, not final research
judgement. Agents should search broadly, inspect records, and explain uncertainty
when MEK metadata is not enough to prove a distinction such as primary vs.
secondary literature.

## Tool Selection

Use `mek_simple_search` for quick bibliographic discovery by title, subject,
creator, or MEK ID. It is a good first pass when the user gives a name, title,
or broad subject.

Use `mek_full_text_search` when the user asks for words or concepts that may
appear inside documents, not only in catalog metadata. This is useful for broad
free-text questions such as Danube references or artificial intelligence.

Use `mek_browse_index` before `mek_advanced_search` when exact controlled forms
matter. Browse with a short prefix, then reuse returned `value` fields in
advanced-search conditions.

Use `mek_advanced_search` for precise bibliographic queries: author vs. subject,
contributor, language, geographic subject, document type, format, and logical
AND/OR/NOT combinations.

Use `mek_get_record` after search results to inspect richer metadata, stable
links, available formats, topics, keywords, descriptions, and related pages.

## General Pattern

1. Start with the least restrictive search that matches the user intent.
2. If the wording may be controlled metadata, call `mek_browse_index`.
3. Run one or more targeted `mek_advanced_search` calls.
4. Fetch promising records with `mek_get_record`.
5. Group, filter, and label results in the agent response.
6. State when a grouping is inferred from title/metadata rather than proven by
   explicit MEK fields.

## Example Workflows

### AI Topics With Exclusions

User request: "Keress magyar nyelvu muveket a mesterseges intelligencia vagy
gepi tanulas temajaban, de zard ki a programozasi tankonyveket."

Suggested flow:

1. Use `mek_full_text_search` for `mesterséges intelligencia` and `gépi tanulás`.
2. Use `mek_advanced_search` with subject conditions if index browsing finds
   useful controlled subject forms.
3. Exclude likely programming textbooks with `operator_after: not` conditions
   against title or subject terms such as `programoz*`, `tankönyv`, or
   `informatika`, but treat this as heuristic filtering.
4. Use `mek_get_record` for shortlisted records and report why each item was
   retained or excluded.

### Orwell: Primary vs. Secondary Literature

User request: "Mutass Orwell-muveket es Orwellrol szolo konyveket magyarul,
kulon csoportositva."

Suggested flow:

1. Run `mek_advanced_search` with `field: dc_creator_o FamilyGivenName`,
   `value: Orwell*`.
2. Run another `mek_advanced_search` with `field: dc_subject keyword` or
   `field: dc_title main`, `value: Orwell*`.
3. Fetch records with `mek_get_record`.
4. Group creator matches as likely primary works and subject/title-only matches
   as likely secondary literature.
5. Mention ambiguous records if Orwell appears both as creator and subject.

### Petofi In Multiple Roles

User request: "Keress Petofihez kapcsolodo rekordokat ugy, hogy Petofi lehet
szerzo, tema vagy kozremukodo is."

Suggested flow:

1. Use `mek_advanced_search` with OR-joined conditions:
   `dc_creator_o FamilyGivenName`, `dc_subject keyword`, and
   `dc_contributor_o FamilyGivenName`.
2. Set `accentless: true` for name variants without accents.
3. Fetch selected records and show the role inferred from the matching field.

### Transylvania By Discipline

User request: "Keress Erdelyhez kapcsolodo muveket, es kulonitsd el a
szepirodalmi, torteneti es neprajzi talalatokat."

Suggested flow:

1. Browse `dc_subject geographic` with prefix `Erd`.
2. Search selected geographic values with `mek_advanced_search`.
3. Run separate subject conditions for `irodalom`, `történelem`, and `néprajz`,
   or inspect topics/keywords from `mek_get_record`.
4. Group by MEK topics and keywords, and label uncertain classifications as
   inferred.

### Controlled Ethnography Terms

User request: "Eloszor nezd meg, milyen relevans targyszoalakok vannak a
neprajz korul, es utana ezekre keress celzottan."

Suggested flow:

1. Call `mek_browse_index` with `field: dc_subject keyword`, `prefix: nep`.
2. Select relevant returned values such as `néprajz`, `magyar néprajz`, or
   `tárgyi néprajz`.
3. Run `mek_advanced_search` once per selected controlled term.
4. Fetch records for the most relevant hits.

### Danube, Not Travel Guides Or Fiction

User request: "Olyan Duna temaju muveket keress, amelyek nem utikonyvek es nem
szepirodalom, inkabb torteneti vagy foldrajzi anyagok."

Suggested flow:

1. Browse `dc_subject geographic` with prefix `Duna`.
2. Run `mek_advanced_search` for selected Danube-related geographic subjects.
3. Add NOT conditions for `útikönyv` and document/topic terms that indicate
   fiction where possible.
4. Use `mek_get_record` to verify topics and keywords before final grouping.

### Hungarian Author, English Language

User request: "Keress angol nyelvu dokumentumokat magyar szerzoktol,
tortenelem vagy kulturtortenet temaban."

Suggested flow:

1. Browse `dc_language m_lang` with prefix `ang`.
2. Search language value plus subject terms such as `történelem` or
   `kultúrtörténet` using `mek_advanced_search`.
3. Fetch records and inspect creators. MEK may not explicitly mark author
   nationality, so "Hungarian author" is often inferred from names or context.

### Accent Handling And Name Variants

User request: "Kezeld automatikusan az ekezetes es ekezet nelkuli nevalakokat,
es mutasd meg, ha emiatt bovult a talalati kor."

Suggested flow:

1. Run a precise `mek_advanced_search` with the accented form.
2. Run the same search with `accentless: true` or an unaccented variant.
3. Compare MEK IDs from both result sets.
4. Report which records appeared only in the broader/accentless search.

## Response Guidance

When answering users, prefer compact grouped lists with title, author, MEK URL,
and a short reason for inclusion. Mention which tool strategy was used only when
it helps the user understand limitations or confidence.

Avoid overclaiming. For example, "probably about Petofi" is better than
"secondary literature" when the distinction is inferred from title or subject
metadata rather than an explicit MEK classification.
