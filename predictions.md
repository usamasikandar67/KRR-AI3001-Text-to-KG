# Extraction Predictions (Step 6)

**Student Name:** Muhammad Usama Sikandar  
**Roll Number:** 23P-0032  
**Dataset:** `kg-23p-0032`  
**Date:** 28th October 2026  

---

## 1. Expected Number of Triples per Predicate

Based on our survey of the five Nobel-laureate physicist biographies (Peter Higgs, Sheldon Glashow, Abdus Salam, Hans Bethe, Kip Thorne) and the single synthetic biographical note (`private_document.txt`), we anticipate the following volume of extracted triples:

| Predicate | Expected Triples | Rationale |
|---|---|---|
| `bornIn` | **7 – 10** | Each of the 6 core subjects has an explicit birthplace in their opening paragraph. In addition, mentions of spouses, parents, or mentors may trigger an additional 1–3 birthplace extractions. |
| `educatedAt` | **18 – 25** | High-profile theoretical physicists typically attend 2 to 4 academic institutions throughout their undergraduate and graduate training (e.g., Cambridge, Caltech, Cornell, Harvard, Princeton, etc.). |
| `receivedAward` | **30 – 50** | All five historical subjects are Nobel laureates with extensive records of prestigious international medals, prizes, and honors (Nobel Prize, Copley Medal, Dirac Medal, Lorentz Medal, Planck Medal, etc.). Award paragraphs in their Wikipedia articles are dense. |
| `worksAt` | **20 – 35** | The subjects held tenured appointments, professorships, laboratory directorships, and visiting chairs across several universities and research institutes (e.g., CERN, Imperial College London, Cornell University, Caltech, Harvard University). |
| `doctoralAdvisor` | **7 – 12** | Each subject has 1 or 2 documented PhD supervisors (e.g., Charles Coulson and Christopher Longuet-Higgins for Higgs; Julian Schwinger for Glashow; Nicholas Kemmer and Paul Dirac for Salam; Arnold Sommerfeld for Bethe; John Wheeler for Thorne; Salman Siddiqui for Zainab Chishti). |
| **Total** | **82 – 132** | Overall graph size across the 6 text documents. |

---

## 2. Predicate Predicted to Have Lowest Precision

We predict that **`worksAt`** will achieve the lowest precision, for the following reasons:
1. **Semantic Ambiguity of Institutional Affiliations:** Verbs indicating employment ("joined", "worked at", "moved to", "served as", "was appointed") frequently link persons to entities that are not formal legal employers—such as temporary research committees, governmental advisory boards (e.g., Manhattan Project, President's Science Advisory Committee), academic divisions, or municipal locations.
2. **Prepositional Attachment and Complex Dependencies:** In sentences describing academic careers, prepositional phrases like "worked at the lab in Princeton under X" often lead dependency parsers to attach location nouns or project titles as the object of employment.
3. **Contrast with Wikidata Ground Truth:** Wikidata’s `P108` (employer) strictly records formal organizational employers. Many historical appointments or research postings described in running prose will count as False Positives against Wikidata if Wikidata lacks the specific temporary post or labels it as a membership/position rather than direct employment.

---

## 3. Anticipated Failure Point in Private Document

In `private_document.txt`, the most challenging difficulty is the **pronoun switch to a secondary entity**:
> *"Zainab Chishti's doctoral advisor was Salman Siddiqui. He later moved to Calder College of Science."*

- **The Challenge:** In single-subject biographical texts, conventional rule-based coreference heuristics default to resolving masculine/feminine third-person pronouns to the primary biographical subject (or the latest subject of the current gender). Here, the pronoun `"He"` refers to the secondary person introduced in the predicate position of the preceding clause (`"Salman Siddiqui"`), NOT the document subject (`"Zainab Chishti"`).
- **Failure Mode:** If an extractor naively resolves `"He"` to the document subject or ignores the immediate grammatical antecedent, it will either misattribute `"Calder College of Science"` to Zainab Chishti as a `worksAt` / `educatedAt` fact, or fail to resolve the subject entirely.

