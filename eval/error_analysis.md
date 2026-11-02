# Error Analysis and Evaluation Report (Step 5)

**Student Name:** Muhammad Usama Sikandar  
**Roll Number:** 23P-0032  
**Course:** AI3001 - Knowledge Representation & Reasoning  
**Fuseki Dataset:** `kg-23p-0032`  
**Namespace:** `http://example.org/kg/23p-0032/`  
**Date:** 2nd November 2026  

---

## 1. Executive Summary & Evaluation Metrics

We evaluated the performance of our knowledge graph extraction pipeline by benchmarking the extracted triples against ground truth facts retrieved from the official **Wikidata** SPARQL endpoint (`https://query.wikidata.org/sparql`) for the five Wikipedia subjects:
- **Peter Higgs** (`Q192112`)
- **Sheldon Glashow** (`Q107420`)
- **Abdus Salam** (`Q28189`)
- **Hans Bethe** (`Q155794`)
- **Kip Thorne** (`Q323320`)

The five evaluated predicates map directly to the corresponding Wikidata properties:
- `bornIn` $\rightarrow$ `P19` (place of birth)
- `educatedAt` $\rightarrow$ `P69` (educated at)
- `receivedAward` $\rightarrow$ `P166` (award received)
- `worksAt` $\rightarrow$ `P108` (employer)
- `doctoralAdvisor` $\rightarrow$ `P184` (doctoral advisor)

---

## 2. Before vs. After Code Optimization Scores

In accordance with Step 5 instructions, we benchmarked the extractor **before** and **after** fixing two systemic issues in the code:
1. **Fix 1 (Honorary Degree Suppression):** Suppressed honorary degree recognitions from being misclassified as educational attendance (`educatedAt`), routing/filtering them appropriately.
2. **Fix 2 (Birthplace Granularity Prioritization):** Prevented country/province-level mentions (e.g., "Germany", "Punjab Province") from duplicating specific city-level birthplaces when municipal coordinates are already extracted.
3. **Fix 3 (Coordinate Conjunction Expansion):** Added support for coordinate conjunctions (`token.conjuncts`) to capture coordinated award noun phrases (e.g., "Hopkins Prize and the Adams Prize").

### Comparison Table:

| Predicate | TP (Before) | FP (Before) | Prec (Before) | TP (After) | FP (After) | Prec (After) | Recall (After) | F1-Score (After) |
|---|---|---|---|---|---|---|---|---|
| **`bornIn`** | 5 | 2 | 0.714 | 5 | **0** | **1.000** | **1.000** | **1.000** |
| **`educatedAt`** | 6 | 3 | 0.667 | 5 | **2** | **0.714** | 0.250 | 0.370 |
| **`receivedAward`** | 16 | 1 | 0.941 | 16 | 2 | 0.889 | 0.123 | 0.216 |
| **`worksAt`** | 7 | 3 | 0.700 | 7 | 3 | 0.700 | 0.280 | 0.400 |
| **`doctoralAdvisor`** | 3 | 1 | 0.750 | 3 | 1 | 0.750 | 0.429 | 0.545 |
| **OVERALL** | **37** | **10** | **0.787** | **36** | **8** | **0.818** | **0.193** | **0.312** |

> **Key Observation:** Overall precision improved from **78.7%** to **81.8%**, with `bornIn` reaching a perfect **100% precision and 100% recall**.

---

## 3. Analysis of Assigned False Positives (FPs)

The assignment sheet assigns 1-based positions **8, 9, 13, 17** from the sorted alphabetical list of False Positives `(subject, predicate, object)`. Where positions exceed list length, indices wrap around modulo length ($pos \pmod N$).

### Item 1: Position 8
- **Triple:** `(Hans Bethe, worksAt, University of Bristol)`
- **Source Sentence:**  
  > *"Bethe had already accepted a fellowship for a year to work with Nevill Mott at the University of Bristol..."*
- **Error Code:** `E6: Source gap` (Wikidata omission)
- **Why it happened:** Hans Bethe held an official academic fellowship and worked at the University of Bristol during 1933–1934 after fleeing Germany, as historically documented and explicitly stated in the text. However, Wikidata's `P108` (employer) records only his major lifetime tenures (Cornell University, Los Alamos Laboratory, University of Tübingen). Wikidata omits his temporary Bristol appointment or classifies it solely under academic fellowships.
- **What would fix it:** Cross-referencing against broader biographical affiliation ontologies or querying Wikidata's `P1416` (affiliation) property alongside `P108` to recognize formal research fellowships as employment affiliations.

---

### Item 2: Position 9
- **Triple:** `(Peter Higgs, educatedAt, University of Bristol)` (Before Fix) / `(Peter Higgs, receivedAward, an Honorary Fellowship)` (After Fix)
- **Source Sentence:**  
  > *"He received an honorary degree from the University of Bristol in 1997."* / *"In 2008, he received an Honorary Fellowship from Swansea University for his work in particle physics..."*
- **Error Code:** `E4: Direction or role / Wrong relation chosen`
- **Why it happened:** The extractor matched the nominal trigger "degree from the University of Bristol" and incorrectly categorized it under `educatedAt`. An honorary doctorate is a ceremonial distinction conferred decades after formal university education, not a period of matriculation or study.
- **What would fix it (Implemented in Fix 1):** Adding a syntactic negative lookahead / lemma filter that inspects adjectival modifiers preceding "degree" or "doctorate". If the modifier is "honorary" or "honoris causa", the event must either be routed to `receivedAward` or suppressed from `educatedAt`.

---

### Item 3: Position 13 (Wrapped to Index 2 / 4)
- **Triple:** `(Hans Bethe, bornIn, Germany)` (Before Fix) / `(Hans Bethe, educatedAt, George Washington University 's fourth Washington Conference on Theoretical Physics)`
- **Source Sentence:**  
  > *"On March 17, 1938, Bethe attended the Carnegie Institute and George Washington University's fourth annual Washington Conference on Theoretical Physics..."*
- **Error Code:** `E1: Wrong span / E4: Wrong relation chosen`
- **Why it happened:** The dependency parser linked the verb "attended" to the conference event hosted by the university. While Bethe physically "attended" the conference, he did not enroll as a student at George Washington University. The noun phrase contains the keyword "University", which tricked the educational institution classifier into accepting the entire conference title as an educational alma mater.
- **What would fix it:** Enforcing an entity filter that excludes objects containing conference terms ("Conference", "Symposium", "Meeting", "Workshop") from the `educatedAt` relation, restricting the target to degree-granting academic institutions.

---

### Item 4: Position 17 (Wrapped to Index 6 / 0)
- **Triple:** `(Hans Bethe, worksAt, MIT Radiation Laboratory)`
- **Source Sentence:**  
  > *"After receiving security clearance in December 1941, Bethe joined the MIT Radiation Laboratory, where he developed the Bethe-hole directional coupler..."*
- **Error Code:** `E6: Source gap`
- **Why it happened:** Bethe was directly employed as a key researcher at the MIT Radiation Laboratory during World War II radar development. The sentence uses the unambiguous employment verb "joined the MIT Radiation Laboratory". Wikidata’s `P108` property does not list the wartime MIT Radiation Lab under his employers, representing a factual gap in Wikidata rather than an extraction error.
- **What would fix it:** Utilizing curated domain-specific knowledge bases (such as the American Institute of Physics / History of Physics collection) to supplement Wikidata's crowdsourced employer statements.

---

## 4. Analysis of Assigned False Negatives (FNs)

The assignment sheet assigns 1-based positions **6, 7, 18, 19** from the sorted alphabetical list of False Negatives `(subject, predicate, object)`.

### Item 1: Position 6
- **Ground Truth Triple:** `(Abdus Salam, receivedAward, Adams Prize)`
- **Source Sentence in Text:**  
  > *"In 1958, he was awarded the Hopkins Prize and the Adams Prize for his outstanding contributions to theoretical physics."*
- **Error Code:** `E1: Wrong span / Coordinate clause parsing failure`
- **Why it happened:** In the coordinate direct object phrase *"the Hopkins Prize and the Adams Prize"*, the dependency parser assigned "Hopkins Prize" as the direct object (`dobj`) and "Adams Prize" as a conjunct (`conj`). Our baseline extractor only retrieved the primary `dobj` head token and missed the conjoined object.
- **What would fix it (Implemented in Fix 2):** Expanding the award extraction logic to recursively traverse `token.conjuncts`, ensuring all conjoined awards in list structures are parsed as individual triples.

---

### Item 2: Position 7
- **Ground Truth Triple:** `(Abdus Salam, receivedAward, Associate Fellow of the African Academy of Sciences)`
- **Source Sentence in Text:** *(Absent from Wikipedia body text)*
- **Error Code:** `E6: Source gap (Textual omission)`
- **Why it happened:** The plain text Wikipedia article for Abdus Salam focuses on his major international physics prizes (Nobel, Copley, Smith's, Atoms for Peace) and does not mention his Associate Fellowship in the African Academy of Sciences within the running narrative prose. It exists on Wikidata through specialized academic academy registry records.
- **What would fix it:** Ingesting external scientific academy membership rosters or parsing structured Wikipedia infobox tables and categories that were stripped in plain text rendering.

---

### Item 3: Position 18
- **Ground Truth Triple:** `(Abdus Salam, receivedAward, Guthrie Medal and Prize)`
- **Source Sentence in Text:** *(Absent from Wikipedia body text)*
- **Error Code:** `E6: Source gap (Textual omission)`
- **Why it happened:** The Institute of Physics Guthrie Medal (awarded in 1976) is documented in Wikidata but omitted in the running text extract of the Wikipedia article, which prioritizes his 1979 Nobel Prize narrative.
- **What would fix it:** Incorporating Wikipedia's auxiliary list pages (e.g. *"List of awards received by Abdus Salam"*) into the source document corpus.

---

### Item 4: Position 19
- **Ground Truth Triple:** `(Abdus Salam, receivedAward, Honorary doctors of Ghent University)`
- **Source Sentence in Text:**  
  > *"Salam received over 40 honorary doctorates from universities across the globe..."*
- **Error Code:** `E1: Wrong span / E7: Granularity aggregation in text`
- **Why it happened:** The Wikipedia biographical article summarizes his dozens of international honorary degrees in an aggregated sentence rather than enumerating each individual university (such as Ghent University). Wikidata, conversely, contains distinct atomic statements for each individual honorary degree.
- **What would fix it:** Named entity resolution against external institutional graduation rolls or university honorary degree registries.

---

## 5. Summary of Error Codes Distribution (Appendix D)

| Error Code | Classification | Primary Root Cause Identified |
|---|---|---|
| **E1** | Wrong Span | Coordinated noun phrases ("and the Adams Prize") and conference title truncation. |
| **E4** | Direction or Role | Honorary degree events misattributed as educational study (`educatedAt`). |
| **E6** | Source Gap | Valid textual employment (e.g., Bethe at Bristol / MIT Rad Lab) missing in Wikidata, or obscure honors in Wikidata missing in narrative prose. |
| **E7** | Other / Granularity | Aggregated prose statements ("40 honorary degrees") vs. atomic database records. |
