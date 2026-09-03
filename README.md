# Academic Industry Skill Graph

Aplikasi Linked Open Data sederhana dengan FastAPI, Apache Jena Fuseki, SPARQL, dan React/Vite. Fokus tahap awal adalah menjalankan query SPARQL ke dataset lokal.

## Struktur project

```text
academic-industry-skill-graph/
├── README.md                         # Panduan instalasi, konfigurasi, dan penggunaan aplikasi
├── doc.md                            # Dokumentasi dan catatan penelitian versi sebelumnya
├── docs/                             # Dokumentasi tambahan untuk penggunaan aplikasi
│   └── demo-queries.md               # Kumpulan query SPARQL demo beserta penjelasannya
├── backend/                          # Backend FastAPI dan integrasi ke Fuseki
│   ├── requirements.txt               # Daftar dependency Python backend
│   ├── old_main.py                    # Entry point kompatibilitas yang mengekspor app FastAPI
│   ├── app/                           # Package aplikasi backend
│   │   ├── __init__.py                # Penanda bahwa app adalah Python package
│   │   ├── config.py                  # Konfigurasi URL Fuseki dan timeout melalui environment variable
│   │   ├── schemas.py                 # Model validasi request SPARQL dengan Pydantic
│   │   ├── fuseki.py                  # Client HTTP async untuk mengirim query ke Fuseki
│   │   └── main.py                    # Inisialisasi FastAPI, CORS, route health, dan route query
│   ├── data/                          # Dataset RDF yang digunakan untuk pengujian lokal
│   │   └── sample.ttl                 # Dataset Turtle sederhana berisi person, course, dan skill
│   └── .venv/                         # Virtual environment Python lokal, dibuat saat instalasi
├── frontend/                          # Aplikasi web React dengan Vite
│   ├── package.json                   # Dependency dan script npm frontend
│   ├── index.html                     # HTML entry point Vite
│   ├── vite.config.js                 # Konfigurasi Vite dan proxy /api ke FastAPI
│   ├── eslint.config.js               # Aturan linting JavaScript/React
│   ├── README.md                      # Dokumentasi bawaan template frontend
│   ├── .env.example                   # Contoh konfigurasi URL API frontend
│   ├── public/                        # Asset statis yang disajikan apa adanya
│   └── src/                           # Source code React
│       ├── main.jsx                   # Mount React ke elemen root HTML
│       ├── App.jsx                    # Router dan layout utama aplikasi
│       ├── App.css                    # Style sisa template aplikasi
│       ├── index.css                  # Variabel warna, reset, dan style global
│       ├── assets/                    # Asset yang diimpor oleh komponen React
│       ├── components/                # Komponen UI yang digunakan lintas halaman
│       │   ├── Navbar.jsx              # Navigasi utama aplikasi
│       │   └── Navbar.css              # Style navigasi utama
│       └── pages/                     # Halaman berdasarkan route aplikasi
│           ├── QueryService.jsx        # Editor SPARQL, eksekusi query, dan tabel hasil
│           ├── QueryService.css        # Style halaman SPARQL Query Service
│           ├── Home.jsx                # Halaman pencarian awal dari draft frontend
│           ├── Home.css                # Style halaman Home
│           ├── EntityExplorer.jsx      # Halaman detail entitas dari draft frontend
│           └── EntityExplorer.css      # Style halaman Entity Explorer
├── ontology/                          # File ontology RDF untuk kebutuhan penelitian
│   ├── CSO.3.5.owl                    # Computer Science Ontology dalam format RDF/XML
│   ├── CSO.3.5.ttl                    # Computer Science Ontology dalam format Turtle
│   └── esco-v1.2.1.ttl                # Ontology ESCO versi 1.2.1
└── script ambil part/                 # Script persiapan, filtering, dan mapping ontology
    ├── requirements.txt               # Dependency Python untuk script penelitian
    ├── notes.txt                      # Catatan proses dan keputusan pengolahan data
    ├── 1_cso_filtering/               # Filtering topik Computer Science Ontology
    │   ├── filter_cso.py              # Mengambil software engineering dan sub-topiknya
    │   └── cso_software_engineering_filtered.ttl # Hasil filtering CSO
    ├── 2_esco_filtering/              # Analisis dan filtering ontology ESCO
    │   ├── analyze_esco_schema.py     # Menganalisis struktur/schema ESCO
    │   ├── filter_esco.py             # Script filtering ESCO umum
    │   ├── filter_esco_ict.py         # Filtering khusus skill/pekerjaan ICT
    │   ├── esco-v1.2.1.ttl             # Salinan input ESCO lengkap
    │   └── esco-ict-english.ttl        # Hasil filtering ESCO ICT berbahasa Inggris
    ├── 3_wikidata_mapping/            # Pemetaan identifier CSO dan ESCO melalui Wikidata
    │   ├── extract_cso_wikidata_ids.py # Mengambil Wikidata ID dari data CSO
    │   ├── query_wikidata_esco_mapping.py # Query mapping Wikidata ke ESCO
    │   ├── cso_wikidata_ids.csv        # Daftar Wikidata ID dari CSO
    │   └── wikidata_cso_esco_mapping.csv # Hasil mapping CSO-ESCO berbasis Wikidata
    └── 4_llm_semantic_mapping/         # Pencocokan semantik label dengan LLM
        ├── prepare_labels_for_matching.py # Menyiapkan label CSO dan ESCO
        ├── llm_semantic_match.py       # Menghitung kecocokan semantik label
        ├── cso_labels.csv              # Label topic CSO
        ├── esco_skill_labels.csv       # Label skill ESCO
        ├── esco_occupation_labels.csv # Label occupation ESCO
        └── cso_esco_similarity_scores.csv # Skor kemiripan CSO-ESCO
```

Folder `backend/` dan `frontend/` membentuk aplikasi yang dijalankan oleh pengguna. Folder `ontology/` dan `script ambil part/` berisi sumber data serta pipeline penelitian yang dapat digunakan untuk menyiapkan dataset yang lebih besar sebelum diunggah ke Fuseki.

## Prasyarat

- Windows
- Java yang kompatibel dengan Apache Jena Fuseki 6.2.0
- Python 3.10 atau lebih baru
- Node.js 18 atau lebih baru

## 1. Jalankan Fuseki

Buka PowerShell pertama:

```powershell
cd "C:\jena-fuseki\apache-jena-fuseki-6.2.0"
New-Item -ItemType Directory -Force -Path "C:\jena-fuseki\lod-data"
.\fuseki-server.bat --loc="C:\jena-fuseki\lod-data" /lod
```

Fuseki berjalan di `http://localhost:3030`. Nama dataset yang aktif di mesin ini adalah `myDataset`, sehingga endpoint query yang valid adalah `http://localhost:3030/myDataset/query`.

Jika Anda memulai Fuseki dengan dataset lain, misalnya `/lod`, maka endpoint yang benar akan menjadi `http://localhost:3030/lod/query`. Pilih satu nama dataset dan gunakan nama itu secara konsisten di semua perintah.

Untuk mengisi dataset contoh, buka PowerShell kedua dari root project:

```powershell
curl.exe -X POST "http://localhost:3030/myDataset/data" `
  -H "Content-Type: text/turtle" `
  --data-binary "@backend/data/sample.ttl"
```

Jika dataset Anda bernama `/lod`, maka gunakan:

```powershell
curl.exe -X POST "http://localhost:3030/lod/data" `
  -H "Content-Type: text/turtle" `
  --data-binary "@backend/data/sample.ttl"
```

Perintah upload bisa dijalankan ulang setelah menghapus folder `C:\jena-fuseki\lod-data` dan menjalankan Fuseki kembali jika ingin dataset bersih.

## 2. Jalankan FastAPI

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Jika PowerShell memblokir aktivasi script, jalankan `Set-ExecutionPolicy -Scope Process Bypass` terlebih dahulu. URL API adalah `http://localhost:8000`; dokumentasi otomatis tersedia di `/docs`.

Fuseki dapat diarahkan ke URL lain dengan environment variable. Contoh untuk dataset `myDataset`:

```powershell
$env:FUSEKI_QUERY_URL = "http://localhost:3030/myDataset/query"
```

Jika dataset Anda memakai `/lod`, gunakan:

```powershell
$env:FUSEKI_QUERY_URL = "http://localhost:3030/lod/query"
```

## 3. Jalankan frontend

Buka PowerShell ketiga:

```powershell
cd frontend
npm install
npm run dev
```

Buka URL yang ditampilkan Vite, biasanya `http://localhost:5173/query`.

## Query uji

```sparql
PREFIX schema: <https://schema.org/>

SELECT ?person ?name ?role
WHERE {
  ?person a schema:Person ;
          schema:name ?name ;
          schema:jobTitle ?role .
}
ORDER BY ?name
```

Alur aplikasi: browser mengirim query JSON ke `POST /api/query`, FastAPI meneruskannya sebagai `application/sparql-query` ke Fuseki, lalu mengembalikan SPARQL Results JSON ke tabel frontend. Query yang tidak valid atau Fuseki yang tidak tersedia ditampilkan sebagai error di UI.
