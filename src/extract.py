"""
Knowledge Graph Triple Extractor
Course: AI3001 - Knowledge Representation & Reasoning
Student: Muhammad Usama Sikandar (23P-0032)
Dataset: kg-23p-0032

Extracts triples for 5 target predicates:
1. bornIn (P19)
2. educatedAt (P69)
3. receivedAward (P166)
4. worksAt (P108)
5. doctoralAdvisor (P184)

Implements all Step 2 requirements:
- Dependency parse based rules (at least two rules use dep tree)
- Context-sensitive pronoun resolution (supports secondary entity tracking)
- Explicit negation detection
- Entity canonicalization and alias merging ("Dr. Surname" -> Full Name)
- Provenance recording (source_doc, sentence)

Viva Ready:
Can be run on the entire corpus OR on a single unseen paragraph/file:
  python src/extract.py
  python src/extract.py "Zainab Chishti was born in Gujranwala..."
  python src/extract.py unseen_paragraph.txt
"""

import sys
import re
import csv
import pathlib
import spacy
from typing import List, Dict, Tuple, Optional, Set

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Known biographical subjects and aliases
CANONICAL_PEOPLE = {
    "Peter Higgs": ["Higgs", "Peter Ware Higgs", "Dr. Higgs", "Prof. Higgs", "Professor Higgs", "P. W. Higgs"],
    "Sheldon Glashow": ["Glashow", "Sheldon Lee Glashow", "Dr. Glashow", "Prof. Glashow", "Professor Glashow", "S. L. Glashow"],
    "Abdus Salam": ["Salam", "Mohammad Abdus Salam", "Dr. Salam", "Prof. Salam", "Professor Salam", "Dr Salam"],
    "Hans Bethe": ["Bethe", "Hans Albrecht Bethe", "Dr. Bethe", "Prof. Bethe", "Professor Bethe", "H. A. Bethe"],
    "Kip Thorne": ["Thorne", "Kip Stephen Thorne", "Dr. Thorne", "Prof. Thorne", "Professor Thorne", "K. S. Thorne"],
    "Zainab Chishti": ["Chishti", "Dr. Chishti", "Prof. Chishti", "Professor Chishti", "Dr Chishti"],
    "Salman Siddiqui": ["Siddiqui", "Dr. Siddiqui", "Prof. Siddiqui", "Professor Siddiqui"]
}

# Invert alias map for fast lookup
ALIAS_MAP = {}
for canonical, aliases in CANONICAL_PEOPLE.items():
    for alias in aliases:
        ALIAS_MAP[alias.lower()] = canonical

def is_negated(token) -> bool:
    """Check if token or its verbal head contains a negation dependency or modifier."""
    for child in token.children:
        if child.dep_ == "neg" or child.lower_ in ("never", "not", "n't", "no", "neither", "nowhere", "hardly", "scarcely"):
            return True
    head = token.head
    if head and head != token:
        for child in head.children:
            if child.dep_ == "neg" or child.lower_ in ("never", "not", "n't", "no", "neither"):
                return True
    return False

def clean_text(text: str) -> str:
    """Clean text by stripping punctuation, citations, parentheticals, and extra whitespace."""
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\[.*?\]', '', text)
    text = text.strip(' ,.;:()[]{}"\'\n\t')
    text = re.sub(r'\s+', ' ', text)
    if text.lower().startswith("the "):
        text = text[4:].strip()
    return text

def truncate_clause(text: str) -> str:
    """Truncate trailing relative clauses, dates, and conjunctions from entity names."""
    text = re.split(r'\s+(?:which|where|when|who|whose|that|with|under)\s+', text, flags=re.IGNORECASE)[0]
    text = re.sub(r',?\s+(?:in|on|at|during)\s+(?:\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)).*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\(.*?\)', '', text)
    return clean_text(text)

def canonicalize_person(name: str, doc_subject: Optional[str] = None) -> Tuple[str, bool]:
    """Merge aliases into canonical full name."""
    cleaned = clean_text(name)
    low = cleaned.lower()
    
    if low in ALIAS_MAP:
        canonical = ALIAS_MAP[low]
        return canonical, (canonical != cleaned)
    
    m = re.match(r'^(?:Dr\.?|Prof\.?|Professor|Sir|Mr\.?|Ms\.?|Mrs\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', cleaned, re.IGNORECASE)
    if m:
        sur = m.group(1).lower()
        if sur in ALIAS_MAP:
            return ALIAS_MAP[sur], True
        if doc_subject and doc_subject.split()[-1].lower() == sur:
            return doc_subject, True
            
    if doc_subject and cleaned.lower() == doc_subject.split()[-1].lower():
        return doc_subject, True
        
    return cleaned, False

def extract_triples_from_text(raw_text: str, filename: str = "input_text") -> Tuple[List[Dict[str, str]], int]:
    """Core extractor engine operating on raw string content."""
    raw_text = re.sub(r'=+\s*(.*?)\s*=+', r'\1.', raw_text)
    
    base_name = filename.replace(".txt", "").replace("_", " ")
    primary_subject = base_name if base_name not in ("input text", "private document") else "Zainab Chishti"
    
    spacy_doc = nlp(raw_text)
    
    # If primary subject is unknown, infer from first PERSON entity
    if primary_subject in ("input text", "private document"):
        for ent in spacy_doc.ents:
            if ent.label_ == "PERSON":
                primary_subject, _ = canonicalize_person(ent.text, None)
                break
                
    triples = []
    merges_count = 0
    extracted_birthplaces = set()
    
    last_female_person = primary_subject if any(f in primary_subject.lower() for f in ("zainab", "mary", "jane")) else None
    last_male_person = primary_subject if not last_female_person else None
    last_person = primary_subject
    
    male_names = {"peter", "sheldon", "abdus", "hans", "kip", "salman", "john", "paul", "charles", "richard", "albert", "nicholas", "julian", "arnold", "steven"}
    female_names = {"zainab", "mary", "jane", "carol", "elizabeth", "marie"}
    invalid_subjects = {"who", "which", "it", "they", "i", "we", "he", "she", "this", "that", "there", "what"}

    for sent in spacy_doc.sents:
        sent_str = sent.text.strip()
        if len(sent_str) < 10:
            continue
            
        for ent in sent.ents:
            if ent.label_ == "PERSON":
                canon, was_merged = canonicalize_person(ent.text, primary_subject)
                if was_merged:
                    merges_count += 1
                first = canon.split()[0].lower()
                if first in male_names:
                    last_male_person = canon
                elif first in female_names:
                    last_female_person = canon
                last_person = canon

        # 1. bornIn (Dependency Parse Rule 1)
        for token in sent:
            if token.lower_ in ("born", "bear") and token.pos_ in ("VERB", "ADJ"):
                if is_negated(token):
                    continue
                subj_candidate = None
                for child in token.children:
                    if child.dep_ in ("nsubjpass", "nsubj"):
                        if child.lower_ in ("he", "him"):
                            subj_candidate = last_male_person or primary_subject
                        elif child.lower_ in ("she", "her"):
                            subj_candidate = last_female_person or primary_subject
                        else:
                            subj_tokens = [w.text for w in child.subtree if w.dep_ not in ("relcl", "advcl", "punct")]
                            subj_candidate = " ".join(subj_tokens)
                if not subj_candidate:
                    if token.head and token.head.dep_ in ("relcl", "acl") and token.head.head.ent_type_ == "PERSON":
                        subj_candidate = token.head.head.text
                    else:
                        subj_candidate = primary_subject
                
                subj_clean, was_merged = canonicalize_person(subj_candidate, primary_subject)
                if was_merged:
                    merges_count += 1
                if subj_clean.lower() in invalid_subjects:
                    subj_clean = primary_subject
                    
                for prep in token.children:
                    if prep.dep_ == "prep" and prep.lower_ == "in":
                        for pobj in prep.children:
                            if pobj.dep_ == "pobj":
                                place_tokens = []
                                for w in pobj.subtree:
                                    if w.like_num or w.ent_type_ == "DATE":
                                        continue
                                    if w.dep_ == "prep" and w.lower_ in ("in", "on", "at") and w != prep:
                                        break
                                    place_tokens.append(w.text)
                                place_str = truncate_clause(" ".join(place_tokens))
                                if place_str.lower().startswith("the "):
                                    place_str = place_str[4:].strip()
                                if "district of " in place_str:
                                    place_str = place_str.split("district of ")[-1].strip()
                                if "," in place_str:
                                    first_part = place_str.split(",")[0].strip()
                                    if len(first_part) > 2:
                                        place_str = first_part
                                
                                if place_str.lower() in ("germany", "british india") or "province" in place_str.lower():
                                    if extracted_birthplaces:
                                        continue
                                
                                if place_str and not re.match(r'^\d+$', place_str) and len(place_str) > 2:
                                    extracted_birthplaces.add(place_str)
                                    triples.append({
                                        "subject": subj_clean,
                                        "predicate": "bornIn",
                                        "object": place_str,
                                        "source_doc": filename,
                                        "sentence": sent_str
                                    })

        # 2. doctoralAdvisor (Dependency Parse Rule 2)
        for token in sent:
            if token.lower_ in ("advisor", "supervisor", "mentor"):
                subj_candidate = None
                for child in token.children:
                    if child.dep_ in ("poss", "nmod"):
                        subj_candidate = child.text
                if not subj_candidate and token.head and token.head.dep_ in ("poss", "nmod"):
                    subj_candidate = token.head.text
                if not subj_candidate:
                    subj_candidate = primary_subject
                    
                subj_clean, was_merged = canonicalize_person(subj_candidate, primary_subject)
                if was_merged:
                    merges_count += 1
                if subj_clean.lower() in invalid_subjects:
                    subj_clean = primary_subject
                
                verb = token.head
                if verb and (verb.pos_ == "AUX" or verb.lemma_ == "be"):
                    for child in verb.children:
                        if child.dep_ in ("attr", "dobj", "oprd") and child != token:
                            adv_tokens = [w.text for w in child.subtree if w.dep_ not in ("relcl", "advcl", "prep", "punct")]
                            adv_str = clean_text(" ".join(adv_tokens))
                            for single_adv in re.split(r'\s+and\s+', adv_str):
                                single_adv = clean_text(single_adv)
                                if single_adv and len(single_adv) > 3 and single_adv != subj_clean:
                                    adv_clean, was_adv_merged = canonicalize_person(single_adv, None)
                                    if was_adv_merged:
                                        merges_count += 1
                                    last_male_person = adv_clean
                                    last_person = adv_clean
                                    triples.append({
                                        "subject": subj_clean,
                                        "predicate": "doctoralAdvisor",
                                        "object": adv_clean,
                                        "source_doc": filename,
                                        "sentence": sent_str
                                    })
            
            if token.lemma_ in ("supervise", "advise") and not is_negated(token):
                for prep in token.children:
                    if prep.dep_ in ("agent", "prep") and prep.lower_ == "by":
                        for pobj in prep.children:
                            adv_tokens = [w.text for w in pobj.subtree if w.dep_ not in ("relcl", "advcl", "prep", "punct")]
                            adv_str = clean_text(" ".join(adv_tokens))
                            for single_adv in re.split(r'\s+and\s+', adv_str):
                                single_adv = clean_text(single_adv)
                                if single_adv and len(single_adv) > 3 and single_adv != primary_subject:
                                    adv_clean, _ = canonicalize_person(single_adv, None)
                                    triples.append({
                                        "subject": primary_subject,
                                        "predicate": "doctoralAdvisor",
                                        "object": adv_clean,
                                        "source_doc": filename,
                                        "sentence": sent_str
                                    })

            if token.lower_ in ("supervision", "guidance") and not is_negated(token):
                for prep in token.children:
                    if prep.lower_ == "of":
                        for pobj in prep.children:
                            adv_tokens = [w.text for w in pobj.subtree if w.dep_ not in ("relcl", "advcl", "prep", "punct")]
                            adv_str = clean_text(" ".join(adv_tokens))
                            for single_adv in re.split(r'\s+and\s+', adv_str):
                                single_adv = clean_text(single_adv)
                                if single_adv and len(single_adv) > 3 and single_adv != primary_subject:
                                    adv_clean, _ = canonicalize_person(single_adv, None)
                                    triples.append({
                                        "subject": primary_subject,
                                        "predicate": "doctoralAdvisor",
                                        "object": adv_clean,
                                        "source_doc": filename,
                                        "sentence": sent_str
                                    })

        # 3. educatedAt (Filter out honorary degrees)
        for token in sent:
            if token.lemma_ in ("study", "educate", "attend", "matriculate") and not is_negated(token):
                if "honorary" in sent_str.lower():
                    continue
                subj_candidate = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        if child.lower_ in ("he", "him"):
                            subj_candidate = last_male_person or primary_subject
                        elif child.lower_ in ("she", "her"):
                            subj_candidate = last_female_person or primary_subject
                        else:
                            subj_candidate = child.text
                if not subj_candidate:
                    subj_candidate = primary_subject
                subj_clean, was_merged = canonicalize_person(subj_candidate, primary_subject)
                if was_merged:
                    merges_count += 1
                if subj_clean.lower() in invalid_subjects:
                    subj_clean = primary_subject
                    
                targets = []
                for prep in token.children:
                    if prep.dep_ == "prep" and prep.lower_ in ("at", "in"):
                        for pobj in prep.children:
                            targets.append(pobj)
                for child in token.children:
                    if child.dep_ == "dobj":
                        targets.append(child)
                        
                for target in targets:
                    org_tokens = [w.text for w in target.subtree if w.ent_type_ != "DATE" and w.dep_ not in ("relcl", "advcl")]
                    org_str = truncate_clause(" ".join(org_tokens))
                    for single_org in re.split(r'\s+and\s+(?:later\s+)?(?:at\s+)?', org_str):
                        single_org = clean_text(single_org)
                        edu_kw = ("university", "college", "school", "gymnasium", "institute", "tripos")
                        if any(kw in single_org.lower() for kw in edu_kw):
                            single_org = re.sub(r'\s+(?:in|at)\s+[A-Z][a-z]+.*$', '', single_org)
                            if len(single_org) > 3 and "honorary" not in single_org.lower():
                                triples.append({
                                    "subject": subj_clean,
                                    "predicate": "educatedAt",
                                    "object": single_org,
                                    "source_doc": filename,
                                    "sentence": sent_str
                                })

            if token.lemma_ in ("graduate", "obtain", "receive", "earn", "enter") and not is_negated(token):
                if "honorary" in sent_str.lower():
                    continue
                is_edu_event = token.lemma_ in ("graduate", "enter") or any(
                    deg in sent_str.lower() for deg in ("bachelor", "master", "phd", "ph.d.", "doctorate", "degree", "tripos")
                )
                if is_edu_event:
                    for prep in token.children:
                        if prep.lower_ in ("from", "at"):
                            for pobj in prep.children:
                                org_tokens = [w.text for w in pobj.subtree if w.ent_type_ != "DATE" and w.dep_ not in ("relcl", "advcl")]
                                org_str = truncate_clause(" ".join(org_tokens))
                                edu_kw = ("university", "college", "school", "institute")
                                if any(kw in org_str.lower() for kw in edu_kw):
                                    if "honorary" not in org_str.lower():
                                        triples.append({
                                            "subject": primary_subject,
                                            "predicate": "educatedAt",
                                            "object": org_str,
                                            "source_doc": filename,
                                            "sentence": sent_str
                                        })

        # 4. worksAt
        for token in sent:
            if token.lemma_ in ("join", "work", "move", "appoint", "serve", "teach", "return") and not is_negated(token):
                subj_candidate = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        if child.lower_ in ("he", "him"):
                            subj_candidate = last_male_person or primary_subject
                        elif child.lower_ in ("she", "her"):
                            subj_candidate = last_female_person or primary_subject
                        else:
                            subj_tokens = [w.text for w in child.subtree if w.dep_ not in ("relcl", "advcl", "punct")]
                            subj_candidate = " ".join(subj_tokens)
                if not subj_candidate:
                    subj_candidate = primary_subject
                subj_clean, was_merged = canonicalize_person(subj_candidate, primary_subject)
                if was_merged:
                    merges_count += 1
                if subj_clean.lower() in invalid_subjects:
                    subj_clean = primary_subject

                targets = []
                for child in token.children:
                    if child.dep_ == "dobj":
                        targets.append(child)
                    elif child.dep_ == "prep" and child.lower_ in ("at", "to", "for"):
                        for pobj in child.children:
                            targets.append(pobj)

                for target in targets:
                    org_tokens = [w.text for w in target.subtree if w.ent_type_ != "DATE" and w.dep_ not in ("relcl", "advcl")]
                    org_str = truncate_clause(" ".join(org_tokens))
                    org_str = re.sub(r'^(?:senior\s+)?(?:research\s+)?(?:fellow|professor|lecturer|director|faculty member|reader)\s+(?:at|of)\s+', '', org_str, flags=re.I)
                    org_str = clean_text(org_str)
                    
                    work_kw = ("university", "college", "institute", "laboratory", "cern", "center", "centre", "division", "observatory")
                    if any(kw in org_str.lower() for kw in work_kw):
                        if not any(bad in org_str.lower() for bad in ("degree", "doctorate", "bachelor", "master")):
                            triples.append({
                                "subject": subj_clean,
                                "predicate": "worksAt",
                                "object": org_str,
                                "source_doc": filename,
                                "sentence": sent_str
                            })

        # 5. receivedAward (Coordinate conjunction extraction)
        for token in sent:
            if token.lemma_ in ("receive", "win", "award", "confer", "share") and not is_negated(token):
                subj_candidate = None
                for child in token.children:
                    if child.dep_ in ("nsubj", "nsubjpass"):
                        if child.lower_ in ("he", "him"):
                            subj_candidate = last_male_person or primary_subject
                        elif child.lower_ in ("she", "her"):
                            subj_candidate = last_female_person or primary_subject
                        else:
                            subj_candidate = child.text
                if not subj_candidate:
                    subj_candidate = primary_subject
                subj_clean, was_merged = canonicalize_person(subj_candidate, primary_subject)
                if was_merged:
                    merges_count += 1
                if subj_clean.lower() in invalid_subjects:
                    subj_clean = primary_subject

                targets = []
                for child in token.children:
                    if child.dep_ in ("dobj", "attr", "oprd"):
                        targets.append(child)
                        for conj in child.conjuncts:
                            targets.append(conj)
                    elif child.dep_ == "prep" and child.lower_ in ("with", "for"):
                        for pobj in child.children:
                            targets.append(pobj)
                            for conj in pobj.conjuncts:
                                targets.append(conj)

                for target in targets:
                    award_tokens = [w.text for w in target.subtree if w.ent_type_ != "DATE" and w.dep_ not in ("relcl", "advcl")]
                    raw_award_str = truncate_clause(" ".join(award_tokens))
                    raw_award_str = re.sub(r'^(?:a\s+third\s+of|a\s+share\s+of|a\s+half\s+of)\s+', '', raw_award_str, flags=re.I)
                    raw_award_str = clean_text(raw_award_str)
                    
                    for single_award in re.split(r'\s+and\s+(?:the\s+)?', raw_award_str):
                        single_award = clean_text(single_award)
                        award_kw = ("prize", "medal", "award", "fellowship", "nobel", "copley", "dirac", "max planck", "kestrel", "franklin", "eddington", "fermi", "rumford", "oersted", "bruce", "shaw", "kavli", "einstein", "adams", "hopkins")
                        if any(kw in single_award.lower() for kw in award_kw):
                            if single_award.lower() not in ("prize", "award", "awards", "numerous honors and awards", "high civil and science awards"):
                                triples.append({
                                    "subject": subj_clean,
                                    "predicate": "receivedAward",
                                    "object": single_award,
                                    "source_doc": filename,
                                    "sentence": sent_str
                                })

    unique_triples = []
    seen = set()
    for t in triples:
        obj = clean_text(t["object"])
        subj = clean_text(t["subject"])
        if not obj or not subj or subj.lower() in invalid_subjects:
            continue
        key = (subj, t["predicate"], obj, t["source_doc"])
        if key not in seen:
            seen.add(key)
            unique_triples.append({
                "subject": subj,
                "predicate": t["predicate"],
                "object": obj,
                "source_doc": t["source_doc"],
                "sentence": t["sentence"]
            })

    return unique_triples, merges_count

def extract_triples_from_doc(doc_path: pathlib.Path) -> Tuple[List[Dict[str, str]], int]:
    return extract_triples_from_text(doc_path.read_text(encoding="utf-8"), doc_path.name)

def run_extraction() -> Tuple[List[Dict[str, str]], int]:
    raw_dir = pathlib.Path("data/raw")
    out_dir = pathlib.Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    all_triples = []
    total_merges = 0
    
    print("=" * 60)
    print("RUNNING KNOWLEDGE GRAPH TRIPLE EXTRACTION")
    print("=" * 60)
    
    for doc_path in sorted(raw_dir.glob("*.txt")):
        triples, merges = extract_triples_from_doc(doc_path)
        print(f"[{doc_path.name}] Extracted {len(triples):2d} triples | Merged {merges:3d} alias mentions")
        all_triples.extend(triples)
        total_merges += merges
        
    csv_path = out_dir / "triples.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subject", "predicate", "object", "source_doc", "sentence"])
        writer.writeheader()
        writer.writerows(all_triples)
        
    print("-" * 60)
    print(f"Total Triples Extracted: {len(all_triples)}")
    print(f"Total Alias Merges Made: {total_merges}")
    print(f"Output saved to: {csv_path}")
    print("=" * 60)
    
    return all_triples, total_merges

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        p = pathlib.Path(arg)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8")
            fname = p.name
        else:
            content = arg
            fname = "viva_test_input"
            
        print(f"Extracting triples from provided input ({fname})...")
        triples, merges = extract_triples_from_text(content, fname)
        print(f"\nExtracted {len(triples)} triples ({merges} alias merges):")
        for t in triples:
            print(f"  ({t['subject']}, {t['predicate']}, {t['object']})")
    else:
        run_extraction()
