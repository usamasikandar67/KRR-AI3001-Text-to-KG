"""
Validate Knowledge Graph against SHACL Shapes
Course: AI3001 - Knowledge Representation & Reasoning
Student: Muhammad Usama Sikandar (23P-0032)
"""

import pyshacl
from rdflib import Graph

def validate():
    data_graph = Graph().parse("out/kg.ttl", format="turtle")
    shapes_graph = Graph().parse("shapes.ttl", format="turtle")
    ont_graph = Graph().parse("ontology.ttl", format="turtle")
    
    conforms, report_graph, report_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        ont_graph=ont_graph,
        inference='rdfs',
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False
    )
    
    print(f"Validation Conforms: {conforms}")
    print("=" * 60)
    print("SHACL VALIDATION REPORT")
    print("=" * 60)
    print(report_text)
    
    with open("shacl_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print("Saved report to shacl_report.txt")

if __name__ == "__main__":
    validate()
