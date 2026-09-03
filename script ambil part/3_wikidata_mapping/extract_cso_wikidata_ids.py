import csv
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import OWL, RDFS

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR.parent / "1_cso_filtering" / "cso_software_engineering_filtered.ttl"
OUTPUT_FILE = SCRIPT_DIR / "cso_wikidata_ids.csv"

def is_wikidata_uri(uri: str) -> bool:
    return "wikidata.org/entity/Q" in uri

def main():
    if not INPUT_FILE.is_file():
        print(f"Error: {INPUT_FILE} not found.")
        return

    print(f"[-] Loading {INPUT_FILE} ...")
    g = Graph()
    g.parse(str(INPUT_FILE), format="turtle")
    print(f"[+] Loaded {len(g)} triples.")

    cso_data = {}

    # Extract labels
    for s, p, o in g.triples((None, RDFS.label, None)):
        if isinstance(s, URIRef) and isinstance(o, Literal):
            cso_data[str(s)] = {"label": str(o), "wikidata_id": None}

    # Extract Wikidata links
    # owl:sameAs is typically used
    for s, p, o in g.triples((None, OWL.sameAs, None)):
        s_str = str(s)
        if isinstance(o, URIRef):
            o_str = str(o)
            if is_wikidata_uri(o_str):
                if s_str not in cso_data:
                    cso_data[s_str] = {"label": "", "wikidata_id": None}
                # Extract the Q-identifier (e.g., Q80993)
                qid = o_str.split("/")[-1]
                cso_data[s_str]["wikidata_id"] = qid

    # Filter to only keep topics that have a Wikidata ID
    results = []
    for uri, data in cso_data.items():
        if data["wikidata_id"]:
            results.append({
                "cso_uri": uri,
                "cso_label": data["label"],
                "wikidata_id": data["wikidata_id"]
            })

    print(f"[-] Found {len(results)} CSO topics with Wikidata IDs.")

    # Save to CSV
    print(f"[-] Saving to {OUTPUT_FILE} ...")
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cso_uri", "cso_label", "wikidata_id"])
        writer.writeheader()
        writer.writerows(results)
    
    print("[+] Done!")

if __name__ == "__main__":
    main()
