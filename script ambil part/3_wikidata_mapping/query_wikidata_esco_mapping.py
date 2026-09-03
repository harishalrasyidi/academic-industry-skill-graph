import csv
import time
import requests
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR / "cso_wikidata_ids.csv"
OUTPUT_FILE = SCRIPT_DIR / "wikidata_cso_esco_mapping.csv"

def chunk_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def query_wikidata_batch(qids):
    endpoint = "https://query.wikidata.org/sparql"
    values = " ".join([f"wd:{qid}" for qid in qids])
    
    # P4652 = ESCO occupation URI
    # P4644 = ESCO skill URI
    query = f"""
    SELECT ?wd ?escoURI ?escoType WHERE {{
      VALUES ?wd {{ {values} }}
      {{
        ?wd wdt:P4652 ?escoURI .
        BIND("occupation" AS ?escoType)
      }} UNION {{
        ?wd wdt:P4644 ?escoURI .
        BIND("skill" AS ?escoType)
      }}
    }}
    """
    
    headers = {
        "User-Agent": "AcademicIndustrySkillGraph/1.0 (Contact: harish@polban.ac.id)",
        "Accept": "application/sparql-results+json"
    }
    
    try:
        response = requests.get(endpoint, params={'query': query}, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    [!] Error querying Wikidata: {e}")
        return None

def main():
    if not INPUT_FILE.is_file():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"[-] Loading {INPUT_FILE} ...")
    cso_data = {}
    with open(INPUT_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qid = row["wikidata_id"]
            if qid not in cso_data:
                cso_data[qid] = []
            cso_data[qid].append({
                "cso_uri": row["cso_uri"],
                "cso_label": row["cso_label"]
            })

    qids = list(cso_data.keys())
    print(f"[+] Loaded {len(qids)} unique Wikidata IDs.")

    results = []
    
    # Query in batches to avoid URI too long errors
    batches = list(chunk_list(qids, 50))
    print(f"[-] Querying Wikidata in {len(batches)} batches ...")
    
    for i, batch in enumerate(batches, 1):
        print(f"    Batch {i}/{len(batches)} ({len(batch)} QIDs)...")
        data = query_wikidata_batch(batch)
        if data and 'results' in data and 'bindings' in data['results']:
            for binding in data['results']['bindings']:
                wd_url = binding['wd']['value']
                esco_url = binding['escoURI']['value']
                esco_type = binding.get('escoType', {}).get('value', 'unknown')
                
                # Extract QID
                matched_qid = wd_url.split('/')[-1]
                
                if matched_qid in cso_data:
                    for cso_info in cso_data[matched_qid]:
                        results.append({
                            "cso_uri": cso_info["cso_uri"],
                            "cso_label": cso_info["cso_label"],
                            "wikidata_id": matched_qid,
                            "esco_uri": esco_url,
                            "esco_type": esco_type,
                            "match_type": "exact_via_wikidata"
                        })
        time.sleep(1) # Polite delay
        
    print(f"[-] Found {len(results)} exact matches via Wikidata.")

    print(f"[-] Saving to {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cso_uri", "cso_label", "wikidata_id", "esco_uri", "esco_type", "match_type"])
        writer.writeheader()
        writer.writerows(results)
    
    print("[+] Done!")

if __name__ == "__main__":
    main()
