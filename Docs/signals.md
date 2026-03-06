# Initial 30 Signal Definitions

These are **seed heuristics**, not proof of AI authorship. They are adapted from the public patterns cataloged on Wikipedia's *Signs of AI writing* page and translated into implementable detector ideas for HumanText.

Each signal should be configurable by genre and suppressible by a learned voice profile.

## Scoring model

For each signal, store:
- `severity_default`
- `confidence`
- `genre_overrides`
- `profile_softeners`
- `rewrite_strategies`

## Signals

### 1. GENERIC_SIGNIFICANCE
Inflates importance with phrases like “pivotal moment”, “plays a crucial role”, or “marks a shift” without adding concrete information.

### 2. BROADER_TRENDS_PADDING
Claims that a fact “reflects broader trends” or “contributes to the wider landscape” without evidence.

### 3. LEGACY_LANGUAGE
Adds “legacy”, “enduring impact”, or “lasting significance” where no concrete legacy is described.

### 4. NOTABILITY_PADDING
Overstates attention, coverage, or public recognition in a generic way.

### 5. MEDIA_COVERAGE_FILLER
Uses phrases like “covered by major outlets” or “profiled in regional media” without specifics.

### 6. SUPERFICIAL_ANALYSIS_TAG
Appends a shallow interpretive tail, often with `-ing` phrases such as “highlighting”, “underscoring”, or “reflecting”.

### 7. ABSTRACT_IMPACT_CHAIN
Stacks abstract verbs and nouns such as “fostering innovation”, “enhancing engagement”, “contributing to growth”.

### 8. PROMOTIONAL_PUFFERY
Uses ad-like or tourism-like language such as “vibrant”, “renowned”, “rich”, “groundbreaking”, “nestled in the heart of”.

### 9. PEACOCK_ADJECTIVES
Uses ungrounded positive adjectives that make the prose sound like promotion rather than reporting.

### 10. VAGUE_ATTRIBUTION
Attributes claims to unnamed authorities, for example “experts argue”, “observers say”, “industry reports suggest”.

### 11. WEASEL_GENERALIZATION
Uses “many”, “some critics”, “several publications”, or similar wording without enough support.

### 12. OUTLINE_CHALLENGES_SECTION
Ends with formulaic “challenges” language, especially a “despite its strengths, it faces challenges” pattern.

### 13. FUTURE_PROSPECTS_SECTION
Adds a canned “future outlook” or “future prospects” close that reads like a school essay outline.

### 14. CANNED_TRANSITION_ADDITIONALLY
Begins sentences with transition words like “Additionally,” in a repetitive, mechanical way.

### 15. CANNED_TRANSITION_OVERALL
Uses “Overall”, “In summary”, or “In conclusion” to wrap up sections in a generic manner.

### 16. BUZZWORD_VERB_CLUSTER
Overuses verbs such as “underscores”, “highlights”, “showcases”, “delves”, “fosters”, “garnered”.

### 17. ABSTRACT_NOUN_OVERUSE
Leans heavily on nouns like “landscape”, “tapestry”, “interplay”, “significance”, “context”, “framework”.

### 18. COPULA_AVOIDANCE
Avoids simple “is/are/has” constructions in favor of “serves as”, “stands as”, “features”, “offers”.

### 19. MECHANICAL_BOLDFACE
Uses bold emphasis too frequently, especially in a “key takeaways” pattern.

### 20. STRUCTURED_LISTICLE_TONE
Breaks prose into conspicuously tidy headings or list chunks that feel generated rather than authored.

### 21. COLLABORATIVE_CHAT_RESIDUE
Leaves chatbot-style residue such as “I hope this helps”, “Would you like”, “here is a breakdown”.

### 22. KNOWLEDGE_CUTOFF_DISCLAIMER
Includes phrases like “as of my last training update” or “based on available information”.

### 23. SOURCE_SCARCITY_SPECULATION
Speculates about missing sources instead of just stating what is known.

### 24. BROKEN_EXTERNAL_LINK_PATTERN
Contains multiple dead or implausible references, suggesting fabricated citation support.

### 25. UNRELATED_DOI_PATTERN
Uses plausible-looking DOI references that resolve to unrelated material.

### 26. BOOK_CITATION_WEAK_SUPPORT
Uses book citations that are too generic to verify the surrounding claim, often without useful locator detail.

### 27. SEARCH_LINK_LEAKAGE
Leaks search-result style links or malformed references from generated output.

### 28. DIDACTIC_DISCLAIMER
Uses phrases like “it is important to note” or “worth noting” as a prefatory teaching move.

### 29. SECTION_SUMMARY_RESTATEMENT
Restates the obvious at the end of a section instead of advancing the text.

### 30. PROMPT_REFUSAL_RESIDUE
Contains traces such as “as an AI language model” or apology-based refusal language.

## Suggested default categories

- `inflation`
- `genericity`
- `structure`
- `chat_residue`
- `citations`
- `formatting`
- `style`

## Signal to strategy examples

| Signal | Strategy |
|---|---|
| GENERIC_SIGNIFICANCE | replace_with_concrete_fact, delete_if_empty |
| VAGUE_ATTRIBUTION | name_source_or_remove |
| COPULA_AVOIDANCE | simplify_to_plain_statement |
| SECTION_SUMMARY_RESTATEMENT | delete_redundant_summary |
| PROMOTIONAL_PUFFERY | neutralize_promotional_language |
| DIDACTIC_DISCLAIMER | remove_teacherly_preface |

## Important implementation note

A learned profile may soften or suppress some signals. Example:
- a lawyer's trusted corpus may validate high formality
- an academic's corpus may validate longer sentences
- a consultant's corpus may still disallow canned summaries and vague attribution
