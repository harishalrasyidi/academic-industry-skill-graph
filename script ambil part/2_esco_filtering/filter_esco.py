"""
Filter ontologi ESCO agar hanya mempertahankan konten berbahasa Inggris.

Menghapus:
- Literal dengan language tag selain 'en' (mis. skos:prefLabel "text"@de)
- Node skosXl:Label yang literalForm-nya bukan @en, beserta referensi skosXl:*Label
- Node esco:NodeLiteral yang esco:language-nya bukan 'en', beserta referensi
  dct:description / skos:scopeNote ke node tersebut
"""

import argparse
import time
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import SKOS, XSD

SCRIPT_DIR = Path(__file__).resolve().parent
ONTOLOGY_DIR = SCRIPT_DIR.parent.parent / "ontology"

ESCO = "http://data.europa.eu/esco/model#"
SKOSXL = "http://www.w3.org/2008/05/skos-xl#"
ESCO_LANGUAGE = URIRef(f"{ESCO}language")
ESCO_NODE_LITERAL = URIRef(f"{ESCO}nodeLiteral")
SKOSXL_LITERAL_FORM = URIRef(f"{SKOSXL}literalForm")

DEFAULT_INPUT = ONTOLOGY_DIR / "esco-v1.2.1.ttl"
DEFAULT_OUTPUT = SCRIPT_DIR / "esco-v1.2.1-english.ttl"
PROGRESS_EVERY = 500_000


def is_english_lang(lang: str | None) -> bool:
    if not lang:
        return False
    return lang.lower().split("-")[0] == "en"


def literal_language_value(literal: Literal) -> str | None:
    if literal.language:
        return literal.language
    if literal.datatype == XSD.language:
        return str(literal)
    return None


def collect_excluded_uris(graph: Graph) -> set[URIRef]:
    """URI skosXl:Label dan esco:NodeLiteral yang bukan bahasa Inggris."""
    excluded: set[URIRef] = set()

    for s, p, o in graph:
        if p == SKOSXL_LITERAL_FORM and isinstance(o, Literal):
            if not is_english_lang(o.language):
                excluded.add(s)
            continue

        if p == ESCO_LANGUAGE:
            lang = literal_language_value(o) if isinstance(o, Literal) else str(o)
            if not is_english_lang(lang):
                excluded.add(s)

    return excluded


def keep_triple(s, p, o, excluded: set[URIRef]) -> bool:
    if s in excluded:
        return False

    if isinstance(o, URIRef) and o in excluded:
        return False

    for term in (s, o):
        if isinstance(term, Literal) and term.language and not is_english_lang(term.language):
            return False

    return True


def filter_english_only(graph: Graph) -> tuple[Graph, int, int]:
    excluded = collect_excluded_uris(graph)
    filtered = Graph()

    for prefix, namespace in graph.namespaces():
        filtered.bind(prefix, namespace)

    total_in = len(graph)
    removed = 0

    for i, (s, p, o) in enumerate(graph, start=1):
        if keep_triple(s, p, o, excluded):
            filtered.add((s, p, o))
        else:
            removed += 1

        if i % PROGRESS_EVERY == 0:
            print(f"    ... diproses {i:,} / {total_in:,} triples")

    return filtered, total_in, removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filter ontologi ESCO (.ttl) agar hanya berisi teks bahasa Inggris."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"File ESCO masukan (default: {DEFAULT_INPUT.name})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"File keluaran (default: {DEFAULT_OUTPUT.name})",
    )
    args = parser.parse_args()

    input_file = args.input.resolve()
    output_file = args.output.resolve()

    if not input_file.is_file():
        raise FileNotFoundError(f"File ontology tidak ditemukan: {input_file}")

    print(f"[-] Memuat {input_file} ...")
    print("    (File ~700 MB; butuh RAM besar dan bisa memakan waktu beberapa menit)")
    start_time = time.time()

    graph = Graph()
    try:
        graph.parse(str(input_file), format="turtle")
    except Exception as exc:
        raise RuntimeError(f"Gagal mem-parse Turtle: {exc}") from exc

    load_seconds = round(time.time() - start_time, 2)
    print(f"[+] Berhasil memuat {len(graph):,} triples ({load_seconds} detik)")

    print("[-] Memfilter bahasa non-Inggris (literal @lang, skosXl:Label, esco:NodeLiteral) ...")
    filtered, total_in, removed = filter_english_only(graph)

    print(f"[+] Filter selesai")
    print(f"    - Triples dihapus : {removed:,}")
    print(f"    - Triples tersisa : {len(filtered):,}")

    print(f"[-] Menyimpan ke {output_file} ...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    filtered.serialize(destination=str(output_file), format="turtle")

    elapsed = round(time.time() - start_time, 2)
    print(f"[+] Selesai ({elapsed} detik). Output: {output_file}")


if __name__ == "__main__":
    main()
