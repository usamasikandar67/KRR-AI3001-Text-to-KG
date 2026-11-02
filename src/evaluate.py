"""
Evaluate Extracted Triples against Wikidata Ground Truth
Course: AI3001 - Knowledge Representation & Reasoning
Student: Muhammad Usama Sikandar (23P-0032)
Dataset: kg-23p-0032

Calculates TP, FP, FN, Precision, and Recall for each predicate.
Identifies false positives and false negatives for error analysis at assigned positions:
- FP positions: 8, 9, 13, 17
- FN positions: 6, 7, 18, 19
"""

import csv
import re
import pathlib
from collections import defaultdict
from typing import Dict, List, Tuple, Set

WIKIPEDIA_PEOPLE = {
    "Peter Higgs",
    "Sheldon Glashow",
    "Abdus Salam",
    "Hans Bethe",
    "Kip Thorne"
}

def normalize_string(s: str) -> str:
    """Normalize strings for fuzzy/token-overlap matching."""
    s = s.lower()
    s = re.sub(r'[\(\)\[\]\{\}\'"\.,;:–\-_]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def matches_entity(extracted: str, truth: str) -> bool:
    """Check if extracted entity string matches ground truth entity label."""
    norm_ext = normalize_string(extracted)
    norm_tru = normalize_string(truth)
    
    if norm_ext == norm_tru:
        return True
    # Substring / containment
    if norm_tru in norm_ext or norm_ext in norm_tru:
        return True
        
    # Word set overlap (Jaccard)
    words_ext = set(norm_ext.split())
    words_tru = set(norm_tru.split())
    # Remove stop words
    stop = {"the", "of", "in", "at", "for", "and", "a", "an", "on", "to"}
    words_ext -= stop
    words_tru -= stop
    
    if words_ext and words_tru:
        intersection = words_ext & words_tru
        if len(intersection) >= min(len(words_ext), len(words_tru)):
            return True
        if len(intersection) / len(words_tru) >= 0.6:
            return True
            
    return False

def evaluate():
    triples_path = pathlib.Path("out/triples.csv")
    wikidata_path = pathlib.Path("eval/wikidata_eval.csv")
    
    # 1. Load extracted triples for the 5 Wikipedia subjects
    extracted_triples = []
    with open(triples_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["subject"] in WIKIPEDIA_PEOPLE:
                extracted_triples.append(row)
                
    # 2. Load Wikidata ground truth
    ground_truth = []
    with open(wikidata_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["subject"] in WIKIPEDIA_PEOPLE:
                ground_truth.append(row)
                
    predicates = ["bornIn", "educatedAt", "receivedAward", "worksAt", "doctoralAdvisor"]
    
    # Track matches
    tp_map = defaultdict(list)
    fp_map = defaultdict(list)
    fn_map = defaultdict(list)
    
    for pred in predicates:
        pred_ext = [t for t in extracted_triples if t["predicate"] == pred]
        pred_gt = [t for t in ground_truth if t["predicate"] == pred]
        
        matched_gt_indices = set()
        
        for ext in pred_ext:
            subj = ext["subject"]
            obj = ext["object"]
            
            # Find matching ground truth
            match_found = False
            for idx, gt in enumerate(pred_gt):
                if gt["subject"] == subj and matches_entity(obj, gt["object"]):
                    match_found = True
                    matched_gt_indices.add(idx)
                    tp_map[pred].append({
                        "extracted": ext,
                        "matched_truth": gt
                    })
                    break
                    
            if not match_found:
                fp_map[pred].append(ext)
                
        # False negatives are ground truth facts that were not matched
        for idx, gt in enumerate(pred_gt):
            if idx not in matched_gt_indices:
                fn_map[pred].append(gt)

    # Calculate metrics table
    metrics_rows = []
    total_tp = 0
    total_fp = 0
    total_fn = 0
    
    for pred in predicates:
        tp = len(tp_map[pred])
        fp = len(fp_map[pred])
        fn = len(fn_map[pred])
        
        total_tp += tp
        total_fp += fp
        total_fn += fn
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        
        metrics_rows.append({
            "Predicate": pred,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "Precision": f"{prec:.3f}",
            "Recall": f"{rec:.3f}",
            "F1-Score": f"{f1:.3f}"
        })
        
    overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0
    
    metrics_rows.append({
        "Predicate": "OVERALL",
        "TP": total_tp,
        "FP": total_fp,
        "FN": total_fn,
        "Precision": f"{overall_prec:.3f}",
        "Recall": f"{overall_rec:.3f}",
        "F1-Score": f"{overall_f1:.3f}"
    })
    
    # Save metrics.csv
    metrics_csv = pathlib.Path("eval/metrics.csv")
    with open(metrics_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Predicate", "TP", "FP", "FN", "Precision", "Recall", "F1-Score"])
        writer.writeheader()
        writer.writerows(metrics_rows)
        
    print("=" * 70)
    print("EVALUATION METRICS TABLE")
    print("=" * 70)
    for r in metrics_rows:
        print(f"{r['Predicate']:16s} | TP: {r['TP']:2d} | FP: {r['FP']:2d} | FN: {r['FN']:2d} | Prec: {r['Precision']:5s} | Rec: {r['Recall']:5s} | F1: {r['F1-Score']:5s}")
    print("=" * 70)
    
    # Collect all False Positives sorted alphabetically by (subject, predicate, object)
    all_fps = []
    for pred in predicates:
        all_fps.extend(fp_map[pred])
    all_fps.sort(key=lambda x: (x["subject"], x["predicate"], x["object"]))
    
    # Collect all False Negatives sorted alphabetically by (subject, predicate, object)
    all_fns = []
    for pred in predicates:
        all_fns.extend(fn_map[pred])
    all_fns.sort(key=lambda x: (x["subject"], x["predicate"], x["object"]))
    
    print(f"\nTotal False Positives: {len(all_fps)}")
    print(f"Total False Negatives: {len(all_fns)}")
    
    # Extract positions:
    # FP positions: 8, 9, 13, 17
    fp_positions = [8, 9, 13, 17]
    fn_positions = [6, 7, 18, 19]
    
    print("\n--- ASSIGNED FALSE POSITIVES ---")
    for pos in fp_positions:
        idx = (pos - 1) % len(all_fps) if all_fps else 0
        item = all_fps[idx] if all_fps else None
        print(f"Position {pos} (index {idx}): {item['subject']} | {item['predicate']} | {item['object']}")
        print(f"   Source sentence: {item.get('sentence', '')[:100]}...")
        
    print("\n--- ASSIGNED FALSE NEGATIVES ---")
    for pos in fn_positions:
        idx = (pos - 1) % len(all_fns) if all_fns else 0
        item = all_fns[idx] if all_fns else None
        print(f"Position {pos} (index {idx}): {item['subject']} | {item['predicate']} | {item['object']}")

if __name__ == "__main__":
    evaluate()
