"""
Build Knowledge Graph (TTL) from CSV Triples
Course: AI3001 - Knowledge Representation & Reasoning
Student: Muhammad Usama Sikandar (23P-0032)
Dataset: kg-23p-0032
"""

import csv
import re
import pathlib
import urllib.parse
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, OWL

KG_NS = Namespace("http://example.org/kg/23p-0032/")

def slugify(text: str) -> str:
    """Create a valid URI safe slug from text."""
    # Remove apostrophes, parens, quotes
    clean = re.sub(r"['\"`\(\)\[\]\{\}]", "", text)
    # Replace spaces and punctuation with underscores
    clean = re.sub(r"[^\w\-]+", "_", clean)
    clean = clean.strip("_")
    if not clean:
        clean = "entity_" + str(abs(hash(text)))
    return clean

def build_knowledge_graph(csv_path: pathlib.Path, ttl_path: pathlib.Path) -> Graph:
    g = Graph()
    g.bind("", KG_NS)
    g.bind("owl", OWL)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj_text = row["subject"].strip()
            pred_text = row["predicate"].strip()
            obj_text = row["object"].strip()
            
            if not subj_text or not pred_text or not obj_text:
                continue
                
            subj_uri = KG_NS[slugify(subj_text)]
            pred_uri = KG_NS[pred_text]
            obj_uri = KG_NS[slugify(obj_text)]
            
            # Add triple
            g.add((subj_uri, pred_uri, obj_uri))
            
            # Add labels
            g.add((subj_uri, RDFS.label, Literal(subj_text, lang="en")))
            g.add((obj_uri, RDFS.label, Literal(obj_text, lang="en")))
            
            # Add types
            g.add((subj_uri, RDF.type, KG_NS.Person))
            
            if pred_text == "bornIn":
                g.add((obj_uri, RDF.type, KG_NS.Place))
            elif pred_text in ("educatedAt", "worksAt"):
                g.add((obj_uri, RDF.type, KG_NS.Organization))
            elif pred_text == "receivedAward":
                g.add((obj_uri, RDF.type, KG_NS.Award))
            elif pred_text == "doctoralAdvisor":
                g.add((obj_uri, RDF.type, KG_NS.Person))
                
    ttl_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(ttl_path), format="turtle")
    print(f"Serialized {len(g)} RDF triples to {ttl_path}")
    return g

if __name__ == "__main__":
    build_knowledge_graph(
        pathlib.Path("out/triples.csv"),
        pathlib.Path("out/kg.ttl")
    )
