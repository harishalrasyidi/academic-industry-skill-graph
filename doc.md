# Dokumentasi Proyek: LOD Endpoint dengan Neo4j (CSO)

**Konteks penelitian:** Ekstraksi Computer Science Ontology (CSO), transformasi ke *property graph* di Neo4j, dan eksposur sebagai Linked Open Data (LOD) / SPARQL untuk kebutuhan *web application* dan analitik.

---

## Struktur folder

```
1. CSO Ontology/
├── doc.md                          # Dokumentasi ini
├── ontology/
│   ├── CSO.3.5.ttl                 # Ontology CSO lengkap (~166k triple)
│   └── CSO.3.5.owl
└── script ambil part/
    ├── filter_cso.py               # Skrip filter sub-topik Software Engineering
    ├── requirements.txt
    ├── cso_software_engineering_filtered.ttl   # Output filter (dihasilkan skrip)
    └── notes.txt                   # Catatan import Neo4j
```

---

## Prasyarat

| Komponen | Keterangan |
|----------|------------|
| Python 3.x | Untuk filter RDF |
| `rdflib` | `pip install -r requirements.txt` di folder `script ambil part` |
| Neo4j 4.x / 5.x | Desktop atau Docker |
| Neosemantics (n10s) | Plugin RDF di Neo4j |

---

## Langkah 1: Filter ontology CSO (Software Engineering)

CSO penuh terlalu besar untuk langsung diimpor. Skrip `filter_cso.py` mengambil topik **software_engineering** dan seluruh sub-topiknya (relasi `cso:superTopicOf`).

### Menjalankan skrip

```powershell
cd "1. CSO Ontology\script ambil part"
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python filter_cso.py
```

### Input & output

| | Path |
|---|------|
| Input | `../ontology/CSO.3.5.ttl` |
| Output | `cso_software_engineering_filtered.ttl` (folder skrip) |

### Output yang diharapkan

Contoh keluaran konsol:

```
Total triples di graph asli: 166518
Ditemukan 826 topik yang relevan.
Graph hasil filter memiliki 7519 triples.
```

### Namespace penting

| Prefix | URI | Catatan |
|--------|-----|---------|
| `cso:` | `http://cso.kmi.open.ac.uk/schema/cso#` | Predikat skema (mis. `superTopicOf`) |
| `cso_topic:` | `https://cso.kmi.open.ac.uk/topics/` | **Harus `https`** — topik di CSO 3.5 memakai HTTPS |

Jika URI topik memakai `http://` alih-alih `https://`, hasil filter akan **kosong** karena RDF memperlakukan keduanya sebagai URI berbeda.

### Troubleshooting filter

| Gejala | Penyebab | Solusi |
|--------|----------|--------|
| `FileNotFoundError` pada input | Path relatif salah (Windows + folder ber-spasi) | Skrip sudah memakai `Path(__file__)` — pastikan `ontology/CSO.3.5.ttl` ada |
| Output `.ttl` kosong / 0 triple | Namespace topik `http` bukan `https` | Pastikan `CSO_TOPIC` memakai `https://cso.kmi.open.ac.uk/topics/` |
| Hanya 1 topik ditemukan | URI akar tidak cocok dengan file `.ttl` | Cek URI di file: `<https://cso.kmi.open.ac.uk/topics/software_engineering>` |

*Langkah penggabungan ontology skill (jika ada) tidak dicakup di dokumen ini.*

---

## Langkah 2: Import RDF ke Neo4j (n10s)

### Persiapan file

1. Salin `cso_software_engineering_filtered.ttl` ke folder **`import`** database Neo4j Anda.
   - Neo4j Desktop: biasanya di `%USERPROFILE%\.Neo4jDesktop2\Data\dbmss\<id-db>\import\`
2. Sesuaikan path `file:///` di query import (Windows membutuhkan **empat** slash setelah `file:`).

### Query Cypher (jalankan berurutan di Neo4j Browser)

```cypher
// 1. Constraint URI unik (wajib untuk n10s)
CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS
FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

// 2. Inisialisasi konfigurasi graph
CALL n10s.graphconfig.init({
  handleVocabUris: "SHORTEN"
});

// 3. Import file Turtle — GANTI path sesuai lokasi import Anda
CALL n10s.rdf.import.fetch(
  "file:////C:/path/ke/neo4j/import/cso_software_engineering_filtered.ttl",
  "Turtle"
);
```

### Verifikasi import

```cypher
// Sample node dan relasi
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50;

// Hierarki superTopicOf (label relasi bisa cso__ atau ns0__ tergantung versi n10s)
MATCH (parent)-[:cso__superTopicOf]->(child)
RETURN parent.uri, child.uri LIMIT 10;

// Anak langsung Software Engineering
MATCH (induk)-[:cso__superTopicOf]->(anak)
WHERE induk.uri CONTAINS "software_engineering"
RETURN induk.rdfs__label AS topik_utama, anak.rdfs__label AS sub_topik
LIMIT 15;
```

### Visualisasi (opsional)

```cypher
// Hierarki induk → anak
MATCH (induk:ns0__Topic)-[r:ns0__superTopicOf]->(anak:ns0__Topic)
WHERE induk.uri CONTAINS "software_engineering"
RETURN induk, r, anak LIMIT 30;

// Kontribusi horizontal (contributesTo)
MATCH (n:ns0__Topic)-[r:ns0__contributesTo]->(m:ns0__Topic)
WHERE n.uri CONTAINS "software_engineering"
RETURN n, r, m LIMIT 30;

// Topik setara / sinonim
MATCH (n:ns0__Topic)-[r:ns0__relatedEquivalent]->(m:ns0__Topic)
RETURN n, r, m LIMIT 20;
```

> **Catatan label:** Dengan `handleVocabUris: "SHORTEN"`, prefix `ns0` di file TTL (skema CSO) bisa muncul sebagai label `ns0__Topic`, `ns0__superTopicOf`, dll. Gunakan **Schema** di Neo4j Browser (`CALL db.schema.visualization()`) untuk melihat nama relasi yang aktif di database Anda.

---

## Langkah 3: Konfigurasi LOD / SPARQL endpoint

Aktifkan ekstensi HTTP n10s di `neo4j.conf`:

```ini
# Neo4j 5.x
server.unmanaged_extension_classes=n10s.endpoint=/rdf

# Neo4j 4.x (jika perlu)
# dbms.unmanaged_extension_classes=n10s.endpoint=/rdf
```

Restart Neo4j (stop & start). Verifikasi:

```
http://localhost:7474/rdf/ping
```

Respons sukses: `{"ping":"here!"}`

---

## Langkah 4: Pengujian API (LOD)

### A. Cypher → RDF (disarankan untuk web app)

**POST** `http://localhost:7474/rdf/neo4j/cypher`

| Header | Nilai |
|--------|-------|
| `Accept` | `text/turtle` |
| `Content-Type` | `application/json` |
| `Authorization` | `Basic` (Base64 `neo4j:password`) |

**Body:**

```json
{
  "cypher": "MATCH (n:ns0__Topic)-[r]->(m) WHERE n.uri CONTAINS 'software_engineering' RETURN n, r, m LIMIT 10"
}
```

Sesuaikan label `ns0__Topic` dengan schema aktif di database Anda (lihat Langkah 2).

### B. SPARQL endpoint

**POST** `http://localhost:7474/rdf/neo4j/sparql`

| Header | Nilai |
|--------|-------|
| `Accept` | `application/json` atau `text/turtle` |
| `Content-Type` | `application/sparql-query` |

**Body:**

```sparql
PREFIX cso: <http://cso.kmi.open.ac.uk/schema/cso#>
PREFIX cso_topic: <https://cso.kmi.open.ac.uk/topics/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?subTopik ?namaTopik
WHERE {
  cso_topic:software_engineering cso:superTopicOf ?subTopik .
  ?subTopik rdfs:label ?namaTopik .
}
LIMIT 10
```

---

## Referensi

- CSO: [Computer Science Ontology](https://cso.kmi.open.ac.uk/)
- Neosemantics (n10s): [dokumentasi plugin](https://neo4j.com/labs/neosemantics/)
- Skrip filter: `script ambil part/filter_cso.py`
- Catatan import tambahan: `script ambil part/notes.txt`
