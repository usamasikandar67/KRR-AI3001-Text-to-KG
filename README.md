# Knowledge Representation & Reasoning (AI3001) - Assignment 1
## From Text to Knowledge Graph

**Student Name:** Muhammad Usama Sikandar  
**Roll Number:** 23P-0032  
**Dataset Name (Fuseki):** `kg-23p-0032`  
**Data Namespace:** `http://example.org/kg/23p-0032/`  
**Submission Date:** 3rd November 2026  
**Assigned Wikipedia Subjects:**  
1. Peter Higgs  
2. Sheldon Glashow  
3. Abdus Salam  
4. Hans Bethe  
5. Kip Thorne  

---

## 1. Project Directory Structure

```text
.
├── ASSIGNMENT_SHEET.md          # Personal parameters and assigned error positions
├── README.md                    # System documentation and execution guide
├── predictions.md               # Prior extraction volume & precision predictions
├── reflection.md                # Post-evaluation reflection on OWA and results (<= 400 words)
├── ontology.ttl                 # RDFS/OWL ontology with classes, domains/ranges, disjointness
├── shapes.ttl                   # SHACL shapes enforcing maxCount, types, and constraints
├── shacl_report.txt             # pySHACL validation report and half-page analysis note
├── private_document.txt         # Synthetic tricky biography (Zainab Chishti)
├── data/
│   └── raw/                     # Raw text corpus (5 Wikipedia articles + private_document.txt)
│       ├── Abdus_Salam.txt
│       ├── Hans_Bethe.txt
│       ├── Kip_Thorne.txt
│       ├── Peter_Higgs.txt
│       ├── Sheldon_Glashow.txt
│       └── private_document.txt
├── src/
│   ├── fetch_data.py            # Automated fetcher for Wikipedia extracts
│   ├── extract.py               # Core extractor implementing all 6 required criteria
│   ├── build_kg.py              # RDF graph builder converting CSV triples to Turtle
│   ├── validate_shacl.py        # pySHACL graph validator
│   ├── run_queries.py           # Automated SPARQL query runner querying Fuseki
│   └── fetch_wikidata.py        # SPARQL ground truth collector from Wikidata endpoint
├── out/
│   ├── triples.csv              # Extracted triples with full provenance
│   └── kg.ttl                   # RDF Knowledge Graph serialized in Turtle
├── queries/
│   ├── q1.rq                    # Q1: Person and birthplace (OPTIONAL)
│   ├── q2.rq                    # Q2: Predicate count aggregation (GROUP BY, COUNT)
│   ├── q3.rq                    # Q3: Pairs of people sharing a birthplace
│   ├── q4.rq                    # Q4: People with >= 2 birthplaces (HAVING COUNT >= 2)
│   ├── q5.rq                    # Q5: People with no education record (FILTER NOT EXISTS)
│   └── q6.rq                    # Q6: Transitive doctoral ancestry path (doctoralAdvisor+)
├── results/
│   ├── q1.csv ... q6.csv        # Execution outputs for all six SPARQL queries
├── eval/
│   ├── metrics.csv              # Precision, Recall, F1 scores across predicates
│   ├── wikidata_eval.csv        # Extracted Wikidata ground truth facts
│   └── error_analysis.md        # In-depth analysis of assigned positions (8,9,13,17 / 6,7,18,19)
└── screenshots/
    ├── fuseki_dataset.png       # Screenshot of dataset kg-23p-0032 in Fuseki UI
    └── fuseki_query.png         # Screenshot of SPARQL query execution in Fuseki UI
```

---

## 2. Setup and Execution Instructions

### Prerequisites
- Python 3.10+
- Java 17+ (Java 25 LTS used: `/Library/Java/JavaVirtualMachines/temurin-25.jdk`)
- Apache Jena Fuseki

### Installation
```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies and download spaCy language model
pip install spacy rdflib pyshacl requests
python -m spacy download en_core_web_sm
```

### Reproducing the Pipeline Step by Step

1. **Step 1 – Download Corpus:**
   ```bash
   python src/fetch_data.py
   ```
2. **Step 2 – Extract Triples:**
   ```bash
   python src/extract.py
   # Generates out/triples.csv
   ```
3. **Step 3 – Build Graph & Run SHACL Validation:**
   ```bash
   python src/build_kg.py
   python src/validate_shacl.py
   # Generates out/kg.ttl and shacl_report.txt
   ```
4. **Step 4 – Start Fuseki Server & Run Queries:**
   ```bash
   # In terminal 1: start Fuseki
   cd fuseki && java -jar fuseki-server.jar --port=3030
   
   # In terminal 2: run queries
   python src/run_queries.py
   # Results saved to results/q1.csv ... results/q6.csv
   ```
5. **Step 5 – Benchmark against Wikidata:**
   ```bash
   python src/fetch_wikidata.py
   python src/evaluate.py
   # Updates eval/metrics.csv and displays error analysis positions
   ```

---

## 3. How Each Extraction Rule Works (`src/extract.py`)

Our extractor uses `spaCy` linguistic features and satisfies the 6 criteria specified in Step 2:

### Rule 1: `bornIn` (Dependency Parse Rule #1)
- **Mechanism:** Searches for verbal/adjectival heads matching lemma `"born"` or `"bear"`.
- **Subject Extraction:** Navigates the dependency tree via `nsubjpass` or `nsubj` child tokens. If a pronoun (`"he"`, `"she"`) is encountered, it resolves to the active gender buffer.
- **Location Extraction:** Follows prepositional children (`dep_ == "prep"`, `lower_ == "in"`), extracting the prepositional object (`pobj`). It truncates relative clauses, dates, and leading articles, capturing clean locations (e.g. `"Strasbourg"`, `"Gujranwala"`, `"Newcastle upon Tyne"`).
- **Negation Check:** Skips the token if `is_negated(token)` returns `True`.

### Rule 2: `doctoralAdvisor` (Dependency Parse Rule #2)
- **Pattern A (Nominal head with copula):** Identifies nouns `"advisor"`, `"supervisor"`, `"promoter"`, or `"mentor"`. Identifies the student via the possessive modifier (`poss` / `nmod`, e.g., *"Zainab Chishti's doctoral advisor"*). Identifies the advisor through the copula verb's attribute (`attr` / `dobj`, e.g., *"was Salman Siddiqui"*).
- **Pattern B (Passive voice & prepositional agent):** Detects verbs `"supervise"` or `"advise"` with agent preposition `"by"` (e.g., *"supervised by John Wheeler"*).
- **Pattern C (Prepositional supervision):** Detects nouns `"supervision"` or `"guidance"` followed by preposition `"of"`.
- **Coreference Update:** When an advisor is identified, their name updates the `last_male_person` buffer, enabling seamless resolution of subsequent pronouns.

### Rule 3: `educatedAt`
- **Mechanism:** Detects study verbs (`"study"`, `"attend"`, `"matriculate"`, `"graduate"`) or degree acquisition events (`"received his doctorate from"`, `"bachelor from"`).
- **Object Resolution:** Captures prepositional objects attached via `"at"` or `"from"` that contain institutional indicators (`"University"`, `"College"`, `"School"`, `"Institute"`).
- **Negation Handling:** Evaluates `is_negated(token)`. A negative child (e.g. *"never studied at Northgate Institute of Physics"*) immediately halts extraction, preventing false positives.
- **Honorary Degree Filter:** Specifically excludes ceremonial distinctions (e.g. *"honorary degree from University of Bristol"*) from being marked as formal enrollment.

### Rule 4: `worksAt`
- **Mechanism:** Detects employment verbs (`"join"`, `"work"`, `"serve"`, `"move"`, `"teach"`, `"appoint"`).
- **Prepositional Parsing:** Direct objects (`"joined Ashdown Institute of Physics"`) or prepositional phrases (`"moved to Calder College of Science"`, `"worked at Cornell University"`) are extracted.
- **Role Stripping:** Strips job title prefixes (such as *"appointed professor at"*, *"senior research fellow at"*) to extract clean institutional names.

### Rule 5: `receivedAward`
- **Mechanism:** Detects recognition verbs (`"receive"`, `"win"`, `"award"`, `"confer"`, `"honor"`).
- **Target Filtering:** Inspects direct objects (`dobj`) and prepositional targets (`"with"`, `"for"`), filtering for award keywords (`"Prize"`, `"Medal"`, `"Award"`, `"Nobel"`, `"Copley"`, `"Fellowship"`).
- **Coordinate Conjunctions:** Uses `token.conjuncts` to split coordinated award expressions (e.g., *"the Hopkins Prize and the Adams Prize"*) into discrete triples.

### Cross-Cutting Features:
1. **Pronoun & Coreference Resolution:** Maintains gendered recency buffers (`last_male_person`, `last_female_person`). In `private_document.txt`, when Sentence 6 identifies Salman Siddiqui as the doctoral advisor, `last_male_person` switches to Salman Siddiqui. Sentence 7 (*"He later moved to Calder College of Science"*) correctly attributes the move to Salman Siddiqui rather than Zainab Chishti.
2. **Entity Canonicalization & Alias Merging:** Normalizes honorific variants (`"Dr. Chishti"` $\rightarrow$ `"Zainab Chishti"`, `"Bethe"` $\rightarrow$ `"Hans Bethe"`). The system logs every alias merge and reports a total of **236 alias merges**.
3. **Provenance:** Every row in `out/triples.csv` records the exact originating `source_doc` and verbatim `sentence`.

---

## 4. SPARQL Queries Summary (Step 4)

| Query File | Purpose | Key SPARQL Construct | Key Finding |
|---|---|---|---|
| `queries/q1.rq` | Person & birthplace | `OPTIONAL { ?person :bornIn ?bp }` | Lists all people, showing birthplaces where known and nulls where unstated. |
| `queries/q2.rq` | Predicate frequency counts | `GROUP BY ?predicate`, `COUNT(*)` | `receivedAward`: 23, `educatedAt`: 13, `worksAt`: 13, `bornIn`: 8, `doctoralAdvisor`: 5. |
| `queries/q3.rq` | Shared birthplaces | `FILTER (STR(?p1) < STR(?p2))` | Identifies distinct individuals born in the same city. |
| `queries/q4.rq` | Multiple birthplaces | `HAVING (COUNT(DISTINCT ?bp) >= 2)` | Identifies entities with multiple birthplace extractions (`Abdus Salam`, `Hans Bethe`). |
| `queries/q5.rq` | People without education | `FILTER NOT EXISTS { ?p :educatedAt ?o }` | Flags secondary entities lacking education data (demonstrates OWA incompleteness). |
| `queries/q6.rq` | Transitive doctoral ancestors | `:doctoralAdvisor+` | Traverses arbitrary-depth mentorship chains (e.g. `Thorne -> Wheeler`, `Higgs -> Coulson`). |

---

## 5. Evaluation & Error Analysis Highlights (Step 5)

- **Overall Precision:** **81.8%** (36 TP / 44 extracted Wikipedia triples).
- **`bornIn` Precision:** **100.0%** (5 TP / 5 extracted).
- **Error Analysis Positions:**
  - **False Positives (8, 9, 13, 17):**
    - Pos 8: `Hans Bethe -> worksAt -> University of Bristol` (`E6: Source gap`, valid fellowship omitted in Wikidata `P108`).
    - Pos 9: `Peter Higgs -> educatedAt -> University of Bristol` (`E4: Role mismatch`, honorary degree misidentified as study; resolved via Fix 1).
    - Pos 13: `Hans Bethe -> bornIn -> Germany` (`E1/E7: Multi-tier granularity`, city vs country; resolved via Fix 2).
    - Pos 17: `Hans Bethe -> worksAt -> MIT Radiation Laboratory` (`E6: Source gap`, historical wartime laboratory omitted in Wikidata).
  - **False Negatives (6, 7, 18, 19):**
    - Pos 6: `Abdus Salam -> receivedAward -> Adams Prize` (`E1: Coordinate clause`, missed second conjunct; resolved via Fix 3).
    - Pos 7: `Abdus Salam -> Associate Fellow African Academy of Sciences` (`E6: Textual omission`, absent from body text).
    - Pos 18: `Abdus Salam -> Guthrie Medal and Prize` (`E6: Textual omission`, absent from summary text).
    - Pos 19: `Abdus Salam -> Honorary doctors of Ghent University` (`E1/E7: Aggregation in text`, aggregated as "over 40 honorary doctorates").

---

## 6. Viva Checklist

- [x] Repository initialized with clean Git commit history showing incremental progress.
- [x] `predictions.md` committed prior to full corpus extraction.
- [x] `src/extract.py` implements all 6 requirements (dependency parse, pronouns, negation, aliases, provenance).
- [x] `private_document.txt` correctly resolves "Dr. Chishti" alias, Salman Siddiqui coreference, and "never studied at" negation.
- [x] `ontology.ttl` defines classes, properties, domains/ranges, disjointness, and functional property.
- [x] `shapes.ttl` defines SHACL shapes and triggers expected violations on multi-tier birthplaces.
- [x] `shacl_report.txt` includes pySHACL output and complete half-page analytical note comparing OWL vs SHACL.
- [x] Six SPARQL queries executed in Fuseki, outputs saved in `results/`, and UI screenshots stored in `screenshots/`.
- [x] `eval/metrics.csv`, `eval/wikidata_eval.csv`, and `eval/error_analysis.md` complete with before/after scores.
- [x] `reflection.md` under 400 words explaining predictions vs reality and OWA implications.
