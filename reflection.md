# Reflection on Knowledge Graph Engineering (Step 6)

**Student Name:** Muhammad Usama Sikandar  
**Roll Number:** 23P-0032  
**Dataset:** `kg-23p-0032`  
**Date:** 3rd November 2026  

---

### Comparison: Predictions vs. Actual Extraction Results

In `predictions.md`, we anticipated extracting between 82 and 132 triples across our six documents. Our pipeline extracted **62 canonical triples**, which proved slightly more conservative but substantially cleaner. As predicted, `bornIn` yielded high precision (reaching **100%** after resolving multi-tier geographic mentions), while `worksAt` was among the most prone to apparent false positives (**70.0% precision**). 

The underlying cause of false positives in `worksAt` aligned closely with our prior hypothesis: textual narratives freely document temporary appointments, wartime laboratories, and visiting research fellowships (such as Hans Bethe at the University of Bristol and the MIT Radiation Laboratory). While these statements are factually accurate in prose, Wikidata’s `P108` (employer) strictly curates permanent tenured chairs, classifying temporary research postings under different properties or omitting them entirely.

In `private_document.txt`, our predicted pitfall—the pronoun switch from the main biographical subject (Zainab Chishti) to her doctoral advisor (Salman Siddiqui)—was successfully resolved. By maintaining recency-aware coreference buffers keyed to entity gender, `"He later moved to Calder College of Science"` was correctly attributed to Salman Siddiqui, avoiding the trap of misattributing the move to Zainab Chishti while cleanly merging her `"Dr. Chishti"` alias and suppressing the negated `"never studied at"` assertion.

---

### The Open-World Assumption in Graph Evaluation

The Open World Assumption (OWA) fundamentally reshaped how we interpret query results and error metrics. A vivid example occurred in **SPARQL Query 5**, which searched for individuals with no `:educatedAt` relation (`FILTER NOT EXISTS`). The query returned secondary scholars such as Charles Coulson and John Wheeler. Under a Closed World database mindset, one might naively deduce that these world-renowned scientists were uneducated. Under OWA, however, *"not asserted in the graph"* simply means unknown rather than false. 

Similarly, our evaluation revealed that out of 151 apparent "False Negatives" against Wikidata, the vast majority represented awards (e.g., Abdus Salam's Guthrie Medal or Associate Fellowship in the African Academy of Sciences) that were simply absent from Wikipedia's narrative summary. Recognizing that knowledge graphs are inherently incomplete, open-world representations altered our goal from striving for artificial 100% recall to ensuring high-fidelity provenance and semantic consistency.
