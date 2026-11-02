"""
Fetch Ground Truth from Wikidata for Evaluation
Course: AI3001 - Knowledge Representation & Reasoning
Student: Muhammad Usama Sikandar (23P-0032)

Fetches P19 (bornIn), P69 (educatedAt), P166 (receivedAward), P108 (worksAt), P184 (doctoralAdvisor)
for:
- Peter Higgs (Q192112)
- Sheldon Glashow (Q107420)
- Abdus Salam (Q28189)
- Hans Bethe (Q155794)
- Kip Thorne (Q323320)
"""

import csv
import pathlib
import requests

WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "KRR-coursework/1.0 (23p0032@nu.edu.pk)"
}

PERSON_QIDS = {
    "Peter Higgs": "Q192112",
    "Sheldon Glashow": "Q107420",
    "Abdus Salam": "Q28189",
    "Hans Bethe": "Q155794",
    "Kip Thorne": "Q323320"
}

PROP_MAP = {
    "P19": "bornIn",
    "P69": "educatedAt",
    "P166": "receivedAward",
    "P108": "worksAt",
    "P184": "doctoralAdvisor"
}

def fetch_wikidata_facts():
    eval_dir = pathlib.Path("eval")
    eval_dir.mkdir(parents=True, exist_ok=True)
    
    all_facts = []
    
    for person_name, qid in PERSON_QIDS.items():
        print(f"Fetching Wikidata facts for {person_name} ({qid})...")
        query = f"""
        SELECT ?prop ?propLabel ?val ?valLabel WHERE {{
            VALUES ?person {{ wd:{qid} }}
            VALUES (?prop ?propId) {{
                (wdt:P19 "P19")
                (wdt:P69 "P69")
                (wdt:P166 "P166")
                (wdt:P108 "P108")
                (wdt:P184 "P184")
            }}
            ?person ?prop ?val .
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        """
        resp = requests.get(
            WIKIDATA_SPARQL,
            params={"query": query, "format": "json"},
            headers=HEADERS,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        
        person_count = 0
        for item in data["results"]["bindings"]:
            prop_uri = item["prop"]["value"]
            prop_pid = prop_uri.split("/")[-1]
            pred_name = PROP_MAP.get(prop_pid, prop_pid)
            val_label = item["valLabel"]["value"]
            val_uri = item["val"]["value"]
            
            all_facts.append({
                "subject": person_name,
                "predicate": pred_name,
                "wikidata_property": prop_pid,
                "object": val_label,
                "wikidata_uri": val_uri
            })
            person_count += 1
        print(f"  -> Extracted {person_count} facts for {person_name}")
            
    out_csv = eval_dir / "wikidata_eval.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subject", "predicate", "wikidata_property", "object", "wikidata_uri"])
        writer.writeheader()
        writer.writerows(all_facts)
        
    print(f"\nTotal Saved: {len(all_facts)} Wikidata ground-truth facts to {out_csv}")
    return all_facts

if __name__ == "__main__":
    fetch_wikidata_facts()
