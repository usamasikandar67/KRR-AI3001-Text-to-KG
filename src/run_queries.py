"""
Execute SPARQL queries against Apache Jena Fuseki
Course: AI3001 - Knowledge Representation & Reasoning
Student: Muhammad Usama Sikandar (23P-0032)
Dataset: kg-23p-0032
"""

import csv
import pathlib
import requests

FUSEKI_ENDPOINT = "http://localhost:3030/kg-23p-0032/sparql"

def run_query(rq_file: pathlib.Path, csv_out: pathlib.Path):
    query_str = rq_file.read_text(encoding="utf-8")
    
    headers = {
        "Accept": "text/csv"
    }
    params = {
        "query": query_str
    }
    
    resp = requests.get(FUSEKI_ENDPOINT, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    csv_out.write_text(resp.text, encoding="utf-8")
    
    print(f"[{rq_file.name}] Output written to {csv_out}:")
    lines = resp.text.strip().splitlines()
    for l in lines[:10]:
        print("  ", l)
    if len(lines) > 10:
        print(f"   ... ({len(lines) - 10} more rows)")
    print()

def main():
    queries_dir = pathlib.Path("queries")
    results_dir = pathlib.Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(1, 7):
        rq = queries_dir / f"q{i}.rq"
        csv_out = results_dir / f"q{i}.csv"
        run_query(rq, csv_out)

if __name__ == "__main__":
    main()
