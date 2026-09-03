import argparse
import time
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.namespace import SKOS, RDF

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "esco-v1.2.1-english.ttl"
DEFAULT_OUTPUT = SCRIPT_DIR / "esco-ict-english.ttl"

ESCO_NS = "http://data.europa.eu/esco/model#"
ESCO_OCCUPATION = URIRef(f"{ESCO_NS}Occupation")
ESCO_SKILL = URIRef(f"{ESCO_NS}Skill")
ESCO_ASSOC = URIRef(f"{ESCO_NS}AssociationObject")

ISCO_C25 = URIRef("http://data.europa.eu/esco/isco/C25")
ISCO_C35 = URIRef("http://data.europa.eu/esco/isco/C35")

def main():
    parser = argparse.ArgumentParser(description="Filter ESCO ontology to keep only ICT occupations and skills.")
    parser.add_argument("-i", "--input", type=Path, default=DEFAULT_INPUT, help="Input TTL file")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT, help="Output TTL file")
    args = parser.parse_args()

    input_file = args.input.resolve()
    output_file = args.output.resolve()

    if not input_file.is_file():
        print(f"File not found: {input_file}")
        return

    print(f"[-] Loading {input_file} ... (This takes a moment)")
    t0 = time.time()
    g = Graph()
    g.parse(str(input_file), format="turtle")
    print(f"[+] Loaded {len(g):,} triples in {time.time() - t0:.1f}s")

    print("[-] Identifying ICT occupations ...")
    
    # 1. Find all occupations that have broaderTransitive C25 or C35
    target_occupations = set()
    for s, p, o in g.triples((None, SKOS.broaderTransitive, ISCO_C25)):
        if (s, RDF.type, ESCO_OCCUPATION) in g:
            target_occupations.add(s)
            
    for s, p, o in g.triples((None, SKOS.broaderTransitive, ISCO_C35)):
        if (s, RDF.type, ESCO_OCCUPATION) in g:
            target_occupations.add(s)
            
    print(f"    Found {len(target_occupations):,} ICT occupations.")

    print("[-] Identifying related skills and association objects ...")
    target_skills = set()
    target_assocs = set()

    # Find skills via direct edges
    essential_rel_from_occ = URIRef(f"{ESCO_NS}relatedEssentialSkill")
    optional_rel_from_occ = URIRef(f"{ESCO_NS}relatedOptionalSkill")
    essential_rel_to_occ = URIRef(f"{ESCO_NS}isEssentialSkillFor")
    optional_rel_to_occ = URIRef(f"{ESCO_NS}isOptionalSkillFor")

    for occ in target_occupations:
        for _, _, skill in g.triples((occ, essential_rel_from_occ, None)):
            target_skills.add(skill)
        for _, _, skill in g.triples((occ, optional_rel_from_occ, None)):
            target_skills.add(skill)

    for skill, _, occ in g.triples((None, essential_rel_to_occ, None)):
        if occ in target_occupations:
            target_skills.add(skill)
    for skill, _, occ in g.triples((None, optional_rel_to_occ, None)):
        if occ in target_occupations:
            target_skills.add(skill)

    # Find AssociationObjects
    is_assoc_for = URIRef(f"{ESCO_NS}isAssociationFor")
    assoc_target = URIRef(f"{ESCO_NS}target")

    for assoc, _, occ in g.triples((None, is_assoc_for, None)):
        if occ in target_occupations:
            # The target should be a skill
            for _, _, skill in g.triples((assoc, assoc_target, None)):
                target_skills.add(skill)
                target_assocs.add(assoc)

    for assoc, _, skill in g.triples((None, is_assoc_for, None)):
        if skill in target_skills:
            # We add associations that point to our target skills, if they associate with our target occupations
            for _, _, occ in g.triples((assoc, assoc_target, None)):
                if occ in target_occupations:
                    target_assocs.add(assoc)

    print(f"    Found {len(target_skills):,} related skills.")
    print(f"    Found {len(target_assocs):,} association objects.")

    print("[-] Collecting nodes to keep (including taxonomy concepts) ...")
    nodes_to_keep = set(target_occupations) | set(target_skills) | set(target_assocs)
    
    # We also want to keep ISCO and ISCED-F nodes, and ConceptSchemes, that are relevant.
    # To keep it simple, we will keep any node that is the object of a broader/broaderTransitive/inScheme/topConceptOf 
    # property from any of our kept occupations/skills.
    
    taxonomy_nodes = set()
    hierarchy_props = [
        SKOS.broader, SKOS.broaderTransitive, SKOS.narrower, SKOS.narrowerTransitive,
        SKOS.inScheme, SKOS.topConceptOf,
        URIRef(f"{ESCO_NS}hasNACECode"),
        URIRef(f"{ESCO_NS}regulatedProfessionNote"),
        URIRef(f"{ESCO_NS}skillType"),
        URIRef(f"{ESCO_NS}skillReuseLevel"),
        URIRef(f"{ESCO_NS}targetFramework"),
        URIRef("http://purl.org/dc/terms/type")
    ]
    
    for n in nodes_to_keep:
        for p in hierarchy_props:
            for _, _, obj in g.triples((n, p, None)):
                if isinstance(obj, URIRef):
                    taxonomy_nodes.add(obj)
                    
    print(f"    Found {len(taxonomy_nodes):,} taxonomy/metadata nodes.")
    nodes_to_keep.update(taxonomy_nodes)
    
    # Also we should keep blank nodes and literals connected to our kept nodes,
    # but since we will just iterate through the graph and keep triples where the subject is in nodes_to_keep,
    # we don't need to explicitly track literals.
    # What if a node literal is used? ESCO uses esco:nodeLiteral. 
    # Let's collect URIRefs that are objects of dct:description or skosXl:*Label.
    
    skosxl_pref = URIRef("http://www.w3.org/2008/05/skos-xl#prefLabel")
    skosxl_alt = URIRef("http://www.w3.org/2008/05/skos-xl#altLabel")
    dct_desc = URIRef("http://purl.org/dc/terms/description")
    
    label_nodes = set()
    for n in nodes_to_keep:
        for p in [skosxl_pref, skosxl_alt, dct_desc]:
            for _, _, obj in g.triples((n, p, None)):
                if isinstance(obj, URIRef):
                    label_nodes.add(obj)
                    
    print(f"    Found {len(label_nodes):,} label/description nodes.")
    nodes_to_keep.update(label_nodes)

    print("[-] Building filtered graph ...")
    out_g = Graph()
    for prefix, namespace in g.namespaces():
        out_g.bind(prefix, namespace)
        
    kept_triples = 0
    # Keep triples where subject is in our kept nodes
    for s, p, o in g:
        if s in nodes_to_keep:
            out_g.add((s, p, o))
            kept_triples += 1

    print(f"[+] Filtering complete. Kept {kept_triples:,} triples.")
    
    print(f"[-] Saving to {output_file} ...")
    t1 = time.time()
    out_g.serialize(destination=str(output_file), format="turtle")
    print(f"[+] Saved successfully in {time.time() - t1:.1f}s")
    
if __name__ == "__main__":
    main()
