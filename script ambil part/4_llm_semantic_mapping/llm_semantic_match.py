import csv
import time
from pathlib import Path

# Try importing required libraries
try:
    import pandas as pd
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim
except ImportError:
    print("Error: Missing required libraries. Please run: pip install sentence-transformers pandas scipy")
    exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
CSO_CSV = SCRIPT_DIR / "cso_labels.csv"
ESCO_OCC_CSV = SCRIPT_DIR / "esco_occupation_labels.csv"
ESCO_SKILL_CSV = SCRIPT_DIR / "esco_skill_labels.csv"
OUTPUT_CSV = SCRIPT_DIR / "cso_esco_similarity_scores.csv"

# Threshold for similarity matching
SIMILARITY_THRESHOLD = 0.70

def format_esco_text(row):
    """Combine prefLabel and altLabels to give the LLM more context"""
    text = str(row['prefLabel'])
    if pd.notna(row['altLabels']) and row['altLabels']:
        alts = str(row['altLabels']).split('|')
        # Limit to first 5 alt labels to avoid diluting the meaning too much
        if alts:
            text += " (" + ", ".join(alts[:5]) + ")"
    return text

def main():
    print("=== Phase 4: LLM Semantic Matching ===")
    
    if not CSO_CSV.exists() or not ESCO_OCC_CSV.exists() or not ESCO_SKILL_CSV.exists():
        print("Error: One or more input CSV files not found. Run prepare_labels_for_matching.py first.")
        return

    print("[-] Loading data...")
    df_cso = pd.read_csv(CSO_CSV)
    df_occ = pd.read_csv(ESCO_OCC_CSV)
    df_skill = pd.read_csv(ESCO_SKILL_CSV)
    
    print(f"    CSO Topics: {len(df_cso)}")
    print(f"    ESCO Occupations: {len(df_occ)}")
    print(f"    ESCO Skills: {len(df_skill)}")

    # Prepare texts for embedding
    cso_texts = df_cso['label'].astype(str).tolist()
    occ_texts = df_occ.apply(format_esco_text, axis=1).tolist()
    skill_texts = df_skill.apply(format_esco_text, axis=1).tolist()

    print("\n[-] Loading LLM Embedding Model ('all-MiniLM-L6-v2')...")
    t0 = time.time()
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f"    Model loaded in {time.time() - t0:.1f}s")

    print("\n[-] Generating Embeddings (this will take a few seconds)...")
    t1 = time.time()
    cso_emb = model.encode(cso_texts, convert_to_tensor=True, show_progress_bar=True)
    occ_emb = model.encode(occ_texts, convert_to_tensor=True, show_progress_bar=True)
    skill_emb = model.encode(skill_texts, convert_to_tensor=True, show_progress_bar=True)
    print(f"    Embeddings generated in {time.time() - t1:.1f}s")

    print("\n[-] Calculating Cosine Similarity Matrix...")
    # Matrix shape: (num_cso, num_occ) and (num_cso, num_skill)
    sim_occ = cos_sim(cso_emb, occ_emb)
    sim_skill = cos_sim(cso_emb, skill_emb)

    results = []
    
    print(f"[-] Finding matches above threshold {SIMILARITY_THRESHOLD}...")
    
    # Process Occupation Matches
    matches_occ = 0
    for i in range(len(cso_texts)):
        scores = sim_occ[i]
        # Get top 3 matches above threshold
        top_indices = scores.topk(k=min(3, len(scores)))
        for score, idx in zip(top_indices[0], top_indices[1]):
            if score.item() >= SIMILARITY_THRESHOLD:
                results.append({
                    "cso_uri": df_cso.iloc[i]['uri'],
                    "cso_label": df_cso.iloc[i]['label'],
                    "esco_uri": df_occ.iloc[idx.item()]['uri'],
                    "esco_label": df_occ.iloc[idx.item()]['prefLabel'],
                    "esco_type": "Occupation",
                    "similarity_score": round(score.item(), 4)
                })
                matches_occ += 1

    # Process Skill Matches
    matches_skill = 0
    for i in range(len(cso_texts)):
        scores = sim_skill[i]
        # Get top 5 matches above threshold
        top_indices = scores.topk(k=min(5, len(scores)))
        for score, idx in zip(top_indices[0], top_indices[1]):
            if score.item() >= SIMILARITY_THRESHOLD:
                results.append({
                    "cso_uri": df_cso.iloc[i]['uri'],
                    "cso_label": df_cso.iloc[i]['label'],
                    "esco_uri": df_skill.iloc[idx.item()]['uri'],
                    "esco_label": df_skill.iloc[idx.item()]['prefLabel'],
                    "esco_type": "Skill",
                    "similarity_score": round(score.item(), 4)
                })
                matches_skill += 1

    print(f"    Found {matches_occ} Occupation matches.")
    print(f"    Found {matches_skill} Skill matches.")
    print(f"    Total matches: {len(results)}")

    print(f"\n[-] Saving results to {OUTPUT_CSV.name}...")
    # Sort by CSO label and then by score descending
    results = sorted(results, key=lambda x: (x['cso_label'], -x['similarity_score']))
    
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cso_uri", "cso_label", "esco_uri", "esco_label", "esco_type", "similarity_score"])
        writer.writeheader()
        writer.writerows(results)
        
    print("[+] Done!")

if __name__ == "__main__":
    main()
