import time
from pathlib import Path

from rdflib import Graph, Namespace

SCRIPT_DIR = Path(__file__).resolve().parent
ONTOLOGY_DIR = SCRIPT_DIR.parent.parent / "ontology"

# 1. Definisi Namespace yang dipakai di CSO
CSO = Namespace("http://cso.kmi.open.ac.uk/schema/cso#")
# Topik di CSO 3.5 memakai https (bukan http) — URI harus persis sama dengan file .ttl
CSO_TOPIC = Namespace("https://cso.kmi.open.ac.uk/topics/")

def main():
    # Path absolut agar aman di Windows (RDFLib salah resolve path relatif jika ada spasi)
    INPUT_FILE = ONTOLOGY_DIR / "CSO.3.5.ttl"
    OUTPUT_FILE = SCRIPT_DIR / "cso_software_engineering_filtered.ttl"
    
    # Topik akar yang ingin kita ambil beserta semua turunannya
    TARGET_TOPIC_URI = CSO_TOPIC["software_engineering"]

    print(f"Mulai memuat file {INPUT_FILE} ke memori...")
    start_time = time.time()
    
    # 2. Load graph asli (Proses ini mungkin butuh 1-3 menit karena ukurannya besar)
    g_original = Graph()
    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"File ontology tidak ditemukan: {INPUT_FILE}")
    g_original.parse(str(INPUT_FILE), format="turtle")
    
    print(f"Selesai memuat! Waktu: {time.time() - start_time:.2f} detik")
    print(f"Total triples di graph asli: {len(g_original)}")

    # 3. Fungsi rekursif untuk mencari semua sub-topik (anak, cucu, cicit)
    def get_all_subtopics(graph, start_uri):
        topics_found = set([start_uri])
        topics_to_process = [start_uri]
        
        while topics_to_process:
            current_topic = topics_to_process.pop(0)
            
            # Cari semua ?sub dimana current_topic cso:superTopicOf ?sub
            # Di CSO, relasi ke bawah menggunakan superTopicOf
            for obj in graph.objects(subject=current_topic, predicate=CSO.superTopicOf):
                if obj not in topics_found:
                    topics_found.add(obj)
                    topics_to_process.append(obj)
                    
        return topics_found

    print(f"\nMencari semua turunan dari: {TARGET_TOPIC_URI}")
    relevant_topics = get_all_subtopics(g_original, TARGET_TOPIC_URI)
    print(f"Ditemukan {len(relevant_topics)} topik yang relevan.")

    # 4. Buat graph baru untuk menyimpan hasil filter
    g_filtered = Graph()
    
    # Bind namespace agar hasil outputnya rapi (menggunakan prefix cso:, bukan URL panjang)
    g_filtered.bind("cso", CSO)
    g_filtered.bind("cso_topic", CSO_TOPIC)

    print("\nMengekstrak relasi untuk topik-topik tersebut...")
    # 5. Salin semua triple yang subjeknya adalah topik relevan (label, tipe, sameAs, dll.)
    for topic in relevant_topics:
        for pred, obj in g_original.predicate_objects(subject=topic):
            g_filtered.add((topic, pred, obj))

    # 6. Simpan graph baru ke file
    print(f"\nMenyimpan hasil ke {OUTPUT_FILE}...")
    g_filtered.serialize(destination=str(OUTPUT_FILE), format="turtle")
    print(f"Selesai! Graph hasil filter memiliki {len(g_filtered)} triples.")

if __name__ == "__main__":
    main()