import csv
from pathlib import Path
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, RDFS, SKOS

SCRIPT_DIR = Path(__file__).resolve().parent
CSO_INPUT = SCRIPT_DIR.parent / "1_cso_filtering" / "cso_software_engineering_filtered.ttl"
ESCO_INPUT = SCRIPT_DIR.parent / "2_esco_filtering" / "esco-ict-english.ttl"

CSO_OUTPUT = SCRIPT_DIR / "cso_labels.csv"
ESCO_OCC_OUTPUT = SCRIPT_DIR / "esco_occupation_labels.csv"
ESCO_SKILL_OUTPUT = SCRIPT_DIR / "esco_skill_labels.csv"

ESCO_NS = "http://data.europa.eu/esco/model#"
ESCO_OCCUPATION = URIRef(f"{ESCO_NS}Occupation")
ESCO_SKILL = URIRef(f"{ESCO_NS}Skill")

def extract_cso():
    print(f"[-] Loading CSO data from {CSO_INPUT.name} ...")
    g = Graph()
    g.parse(str(CSO_INPUT), format="turtle")
    
    results = []
    # CSO topics use rdfs:label
    for s, p, o in g.triples((None, RDFS.label, None)):
        if isinstance(s, URIRef) and isinstance(o, Literal):
            results.append({
                "uri": str(s),
                "label": str(o)
            })
            
    print(f"    Found {len(results)} CSO topic labels.")
    
    with open(CSO_OUTPUT, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["uri", "label"])
        writer.writeheader()
        writer.writerows(results)

def extract_esco():
    print(f"[-] Loading ESCO ICT data from {ESCO_INPUT.name} ...")
    g = Graph()
    g.parse(str(ESCO_INPUT), format="turtle")
    
    occ_data = {}
    skill_data = {}
    
    # Process Occupations
    for s, _, _ in g.triples((None, RDF.type, ESCO_OCCUPATION)):
        occ_data[str(s)] = {"prefLabel": "", "altLabels": []}
        
    # Process Skills
    for s, _, _ in g.triples((None, RDF.type, ESCO_SKILL)):
        skill_data[str(s)] = {"prefLabel": "", "altLabels": []}
        
    # Get prefLabels
    for s, p, o in g.triples((None, SKOS.prefLabel, None)):
        s_str = str(s)
        if isinstance(o, Literal):
            if s_str in occ_data:
                occ_data[s_str]["prefLabel"] = str(o)
            elif s_str in skill_data:
                skill_data[s_str]["prefLabel"] = str(o)
                
    # Get altLabels
    for s, p, o in g.triples((None, SKOS.altLabel, None)):
        s_str = str(s)
        if isinstance(o, Literal):
            if s_str in occ_data:
                occ_data[s_str]["altLabels"].append(str(o))
            elif s_str in skill_data:
                skill_data[s_str]["altLabels"].append(str(o))
                
    # Format and save Occupations
    occ_results = []
    for uri, data in occ_data.items():
        occ_results.append({
            "uri": uri,
            "prefLabel": data["prefLabel"],
            "altLabels": "|".join(data["altLabels"])
        })
        
    with open(ESCO_OCC_OUTPUT, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["uri", "prefLabel", "altLabels"])
        writer.writeheader()
        writer.writerows(occ_results)
    print(f"    Saved {len(occ_results)} ESCO occupation labels.")
    
    # Format and save Skills
    skill_results = []
    for uri, data in skill_data.items():
        skill_results.append({
            "uri": uri,
            "prefLabel": data["prefLabel"],
            "altLabels": "|".join(data["altLabels"])
        })
        
    with open(ESCO_SKILL_OUTPUT, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["uri", "prefLabel", "altLabels"])
        writer.writeheader()
        writer.writerows(skill_results)
    print(f"    Saved {len(skill_results)} ESCO skill labels.")

def main():
    print("=== Extracting labels for LLM Semantic Matching ===")
    extract_cso()
    extract_esco()
    print("[+] Extraction complete!")

if __name__ == "__main__":
    main()
