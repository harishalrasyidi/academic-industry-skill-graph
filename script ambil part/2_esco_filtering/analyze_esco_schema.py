"""
Analyze the data model / schema of an ESCO RDF/Turtle file.

Designed for large files (~180 MB+): streams triples via rdflib without
dumping the graph into chat. Uses two passes over the graph iterator.
"""

from __future__ import annotations

import argparse
import time
from collections import Counter, defaultdict
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = SCRIPT_DIR / "esco-v1.2.1-english.ttl"

ESCO_NS = "http://data.europa.eu/esco/model#"
ESCO_OCCUPATION = URIRef(f"{ESCO_NS}Occupation")
ESCO_SKILL = URIRef(f"{ESCO_NS}Skill")

# Predicates commonly used for external concept alignment (incl. Wikidata)
EXTERNAL_LINK_PREDICATES = frozenset(
    {
        OWL.sameAs,
        OWL.equivalentClass,
        SKOS.exactMatch,
        SKOS.closeMatch,
        SKOS.relatedMatch,
        SKOS.broadMatch,
        SKOS.narrowMatch,
        URIRef("http://schema.org/sameAs"),
        URIRef("http://www.w3.org/2002/07/owl#sameAs"),
    }
)

WIKIDATA_MARKERS = ("wikidata.org", "www.wikidata.org")

PROGRESS_EVERY = 500_000


def shorten(uri: URIRef, graph: Graph) -> str:
    try:
        return graph.namespace_manager.normalizeUri(uri)
    except Exception:
        return str(uri)


def is_wikidata_uri(term) -> bool:
    if not isinstance(term, URIRef):
        return False
    text = str(term).lower()
    return any(marker in text for marker in WIKIDATA_MARKERS)


def print_header(title: str) -> None:
    bar = "=" * 72
    print(f"\n{bar}\n{title}\n{bar}")


def pass1_classify_nodes(graph: Graph) -> tuple[Counter, set[URIRef], set[URIRef], int]:
    """Collect rdf:types and index Occupation / Skill instance URIs."""
    class_counts: Counter = Counter()
    occupation_uris: set[URIRef] = set()
    skill_uris: set[URIRef] = set()
    n = 0

    for s, p, o in graph:
        n += 1
        if p != RDF.type:
            continue
        if isinstance(o, URIRef):
            class_counts[o] += 1
            if o == ESCO_OCCUPATION:
                occupation_uris.add(s)
            elif o == ESCO_SKILL:
                skill_uris.add(s)

        if n % PROGRESS_EVERY == 0:
            print(f"  [pass 1] {n:,} triples scanned ...")

    return class_counts, occupation_uris, skill_uris, n


def pass2_analyze(
    graph: Graph,
    occupation_uris: set[URIRef],
    skill_uris: set[URIRef],
    total_triples: int,
) -> tuple[
    Counter,
    Counter,
    list[tuple],
    Counter,
    list[tuple],
]:
    """
    Returns:
      occ_skill_predicates, label_predicates, wikidata_examples,
      external_link_predicates, other_external_examples
    """
    occ_skill_preds: Counter = Counter()
    label_preds: Counter = Counter()
    wikidata_examples: list[tuple] = []
    external_link_preds: Counter = Counter()
    other_external: list[tuple] = []

    seen_wikidata: set[URIRef] = set()
    seen_external: set[URIRef] = set()

    n = 0
    for s, p, o in graph:
        n += 1

        # --- Occupation <-> Skill object properties ---
        if isinstance(o, URIRef):
            if s in occupation_uris and o in skill_uris:
                occ_skill_preds[p] += 1
            elif s in skill_uris and o in occupation_uris:
                occ_skill_preds[p] += 1

            # --- Wikidata / external links ---
            if is_wikidata_uri(o):
                if s not in seen_wikidata and len(wikidata_examples) < 3:
                    wikidata_examples.append((s, p, o))
                    seen_wikidata.add(s)
            elif p in EXTERNAL_LINK_PREDICATES:
                external_link_preds[p] += 1
                if len(other_external) < 3 and s not in seen_external:
                    other_external.append((s, p, o))
                    seen_external.add(s)

        # Also catch Wikidata as subject (rare)
        if is_wikidata_uri(s) and isinstance(o, URIRef) and len(wikidata_examples) < 3:
            if o not in seen_wikidata:
                wikidata_examples.append((s, p, o))
                seen_wikidata.add(o)

        # --- Datatype / textual label properties ---
        if isinstance(o, Literal):
            label_preds[p] += 1

        if n % PROGRESS_EVERY == 0:
            print(f"  [pass 2] {n:,} / {total_triples:,} triples scanned ...")

    return (
        occ_skill_preds,
        label_preds,
        wikidata_examples,
        external_link_preds,
        other_external,
    )


def print_class_report(graph: Graph, class_counts: Counter) -> None:
    print_header("1. DISTINCT CLASSES (objects of rdf:type)")
    print(f"{'Count':>10}  Class")
    print("-" * 72)
    for cls, count in class_counts.most_common():
        print(f"{count:>10,}  {shorten(cls, graph)}")


def print_predicate_report(
    graph: Graph,
    title: str,
    pred_counts: Counter,
    hint: str = "",
) -> None:
    print_header(title)
    if hint:
        print(hint)
        print()
    if not pred_counts:
        print("  (none found)")
        return
    print(f"{'Count':>10}  Predicate")
    print("-" * 72)
    for pred, count in pred_counts.most_common():
        print(f"{count:>10,}  {shorten(pred, graph)}")


def print_wikidata_report(
    graph: Graph,
    wikidata_examples: list[tuple],
    external_link_preds: Counter,
    other_external: list[tuple],
) -> None:
    print_header("4. WIKIDATA & EXTERNAL CONCEPT LINKS")

    print("Predicates checked for external alignment:")
    for pred in sorted(EXTERNAL_LINK_PREDICATES, key=str):
        print(f"  - {shorten(pred, graph)}")
    print()

    if wikidata_examples:
        print(f"Wikidata URIs found: YES ({len(wikidata_examples)} example(s) shown, max 3)")
        for i, (s, p, o) in enumerate(wikidata_examples, 1):
            print(f"\n  Example {i}:")
            print(f"    Subject   : {s}")
            print(f"    Predicate : {shorten(p, graph)}")
            print(f"    Wikidata  : {o}")
            # Show a human-readable label if available
            for label_pred in (SKOS.prefLabel, RDFS.label):
                label = graph.value(s, label_pred)
                if label:
                    print(f"    Label     : {label}")
                    break
    else:
        print("Wikidata URIs found: NO")
        print(
            "  No URI containing 'wikidata.org' appears in any triple "
            "(subject or object)."
        )

    if external_link_preds:
        print("\nOther external-link predicates used (non-Wikidata targets):")
        for pred, count in external_link_preds.most_common(10):
            print(f"  {count:>8,}  {shorten(pred, graph)}")
        if other_external:
            print("\n  Sample triples:")
            for s, p, o in other_external:
                print(f"    ({shorten(s, graph)}) --{shorten(p, graph)}--> {o}")
    else:
        print("\nNo owl:sameAs / skos:exactMatch / skos:closeMatch triples found.")


def print_association_pattern_hint(graph: Graph) -> None:
    """ESCO often links Occupation–Skill via AssociationObject nodes."""
    print_header("NOTE: ESCO AssociationObject pattern (occupation–skill)")
    sample = """
    Many occupation–skill links are not direct. ESCO uses reified relations:

      ?relation a esco:AssociationObject ;
          esco:isAssociationFor ?occupation ;   # the occupation
          esco:target ?skill ;                  # the skill
          dct:type <.../essential-skill> .      # or optional-skill

    Direct edges on skill/occupation nodes also exist, e.g.:
      ?skill esco:isEssentialSkillFor ?occupation .
      ?skill esco:isOptionalSkillFor ?occupation .
    """
    print(sample.strip())

    # Quick counts via SPARQL (fast on loaded graph)
    q = """
    SELECT (COUNT(?r) AS ?n) WHERE { ?r a <http://data.europa.eu/esco/model#AssociationObject> }
    """
    try:
        n = int(list(graph.query(q))[0][0])
        print(f"\n  AssociationObject instances in file: {n:,}")
    except Exception:
        pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize classes, predicates, and external links in an ESCO TTL file."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input Turtle file (default: {DEFAULT_INPUT.name})",
    )
    args = parser.parse_args()
    input_path = args.input.resolve()

    if not input_path.is_file():
        raise FileNotFoundError(f"Input not found: {input_path}")

    print_header("ESCO SCHEMA ANALYSIS")
    print(f"Input : {input_path}")
    print(f"Size  : {input_path.stat().st_size / (1024 * 1024):.1f} MB")

    t0 = time.time()
    print("\nLoading graph (this may take ~1–2 minutes) ...")
    graph = Graph()
    graph.parse(str(input_path), format="turtle")
    load_sec = time.time() - t0
    print(f"Loaded in {load_sec:.1f}s")

    t1 = time.time()
    print("\nPass 1: indexing rdf:types and Occupation/Skill instances ...")
    class_counts, occupation_uris, skill_uris, total = pass1_classify_nodes(graph)
    print(
        f"  Occupation instances: {len(occupation_uris):,}\n"
        f"  Skill instances     : {len(skill_uris):,}"
    )

    print("\nPass 2: predicates, labels, external links ...")
    (
        occ_skill_preds,
        label_preds,
        wikidata_examples,
        external_link_preds,
        other_external,
    ) = pass2_analyze(graph, occupation_uris, skill_uris, total)

    analyze_sec = time.time() - t1
    print(f"\nAnalysis passes finished in {analyze_sec:.1f}s")
    print(f"Total triples: {total:,}")

    print_class_report(graph, class_counts)

    print_predicate_report(
        graph,
        "2. OBJECT PROPERTIES LINKING OCCUPATION <-> SKILL",
        occ_skill_preds,
        hint=(
            "Counts direct URI–URI edges where one endpoint is typed esco:Occupation\n"
            "and the other is typed esco:Skill (either direction)."
        ),
    )
    print_association_pattern_hint(graph)

    print_predicate_report(
        graph,
        "3. DATATYPE / TEXT LABEL PROPERTIES (object is a Literal)",
        label_preds,
        hint=(
            "Includes skos:prefLabel, skos:altLabel, esco:nodeLiteral, skosXl:literalForm, etc.\n"
            "skosXl:prefLabel pointing to skosXl:Label nodes are URI objects and appear in section 2\n"
            "if they connect typed instances; literalForm on Label nodes appears here."
        ),
    )

    print_wikidata_report(
        graph, wikidata_examples, external_link_preds, other_external
    )

    print_header("DONE")
    print(f"Total runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
