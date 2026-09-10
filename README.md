# Academic Industry Skill Graph

Aplikasi Linked Open Data sederhana dengan FastAPI, Apache Jena Fuseki, SPARQL, dan React/Vite. Fokus tahap awal adalah menjalankan query SPARQL ke dataset lokal.

## Struktur project

```text
academic-industry-skill-graph/
├── README.md                         # Panduan instalasi, konfigurasi, dan penggunaan aplikasi
├── doc.md                            # Dokumentasi dan catatan penelitian versi sebelumnya
├── docs/                             # Dokumentasi tambahan untuk penggunaan aplikasi
│   └── demo-queries.md               # Kumpulan query SPARQL demo beserta penjelasannya
│   └── project-summary-for-ai.md     # Ringkasan project untuk diskusi dengan AI
├── deploy/                            # Artefak deployment production
│   ├── compose.production.yml         # Compose untuk backend dan Fuseki
│   ├── fuseki/Dockerfile              # Image Fuseki 6.2.0 berbasis Java 21
│   └── nginx/                         # Contoh konfigurasi Nginx host
│       └── academic-industry-skill-graph.conf.example
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
- Apache Jena Fuseki 6.2.0 sudah diekstrak di `C:\jena-fuseki\apache-jena-fuseki-6.2.0`
- Python 3.10 atau lebih baru
- Node.js 18 atau lebih baru
- `curl.exe`, biasanya sudah tersedia di Windows 10/11

### Cek versi tool

```powershell
java -version
python --version
node --version
npm --version
docker --version
docker compose version
```

Java digunakan oleh Fuseki, Python oleh FastAPI, dan Node.js hanya digunakan untuk install dependency serta build frontend. Docker diperlukan hanya untuk workflow Compose production.

## 1. Jalankan Fuseki

Buka PowerShell pertama:

```powershell
cd "C:\jena-fuseki\apache-jena-fuseki-6.2.0"
New-Item -ItemType Directory -Force -Path "C:\jena-fuseki\lod-data"
.\fuseki-server.bat --loc="C:\jena-fuseki\lod-data" --update /myDataset
```

Fuseki berjalan di `http://localhost:3030` dengan nama dataset `myDataset`, sehingga endpoint query yang valid adalah `http://localhost:3030/myDataset/query`.

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

Opsi `--update` diperlukan agar endpoint Graph Store dapat menerima upload. Perintah upload dapat dijalankan ulang, tetapi data akan bertambah/tergabung. Untuk dataset bersih, hentikan Fuseki, hapus folder `C:\jena-fuseki\lod-data`, buat ulang folder tersebut, lalu jalankan Fuseki dan upload kembali.

## 2. Jalankan FastAPI

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FUSEKI_QUERY_URL = "http://localhost:3030/myDataset/query"
$env:CORS_ALLOW_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
python -m uvicorn app.main:app --reload --port 8000
```

Jika PowerShell memblokir aktivasi script, jalankan `Set-ExecutionPolicy -Scope Process Bypass` terlebih dahulu. URL API adalah `http://localhost:8000`; dokumentasi otomatis tersedia di `/docs`.

Frontend development menggunakan proxy Vite untuk `/api`, sehingga browser tetap memanggil URL relatif dan tidak membutuhkan URL backend production di source code.

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

### Urutan local development

Gunakan tiga terminal:

```text
Terminal 1: Fuseki
Terminal 2: FastAPI
Terminal 3: Vite
```

Kemudian:

1. Upload dataset ke Fuseki.
2. Cek `http://localhost:8000/api/health`.
3. Buka `http://localhost:5173/query`.
4. Jalankan query SPARQL dari `docs/demo-queries.md`.

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

### Endpoint local untuk verifikasi

Health check FastAPI:

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

Query langsung ke backend:

```powershell
$body = @{ query = 'SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }' } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/query -Method Post -ContentType 'application/json' -Body $body
```

Jika menggunakan konfigurasi production Compose, endpoint FastAPI tetap tersedia di `http://127.0.0.1:8000`, sedangkan Fuseki hanya dapat diakses dari network Docker.

## Production dengan Docker Compose

Production menggunakan Compose untuk backend dan Fuseki saja. Frontend tetap dibuild sebagai static files lalu disajikan oleh Nginx host; Vite development server tidak digunakan di production.

### Arsitektur production

```text
Internet
   |
Nginx host :80/:443
   |-- frontend/dist/
   `-- /api -> 127.0.0.1:8000
      |
    backend container
      |
    private Docker network
      |
    Fuseki container :3030
      |
    named volume TDB2
```

Fuseki tidak mem-publish port ke host. Backend hanya mem-publish port `127.0.0.1:8000`, sehingga tidak tersedia langsung dari internet. Keduanya tetap berkomunikasi melalui private Docker network, dan Nginx host menjadi satu-satunya entry point publik. Fuseki dijalankan dengan flag `--update` agar proses import manual melalui Graph Store dapat menulis dataset.

### Build frontend production

Di host deployment yang memiliki Node.js:

```bash
cd frontend
npm ci
npm run build
```

Sajikan `frontend/dist/` dengan konfigurasi contoh di `deploy/nginx/`.

### Siapkan environment Compose

Dari root project:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Nilai penting dalam `.env.production`:

```env
FUSEKI_QUERY_URL=http://fuseki:3030/myDataset/query
FUSEKI_TIMEOUT_SECONDS=30
CORS_ALLOW_ORIGINS=
BACKEND_HOST_PORT=8000
```

`FUSEKI_QUERY_URL` memakai nama service Compose `fuseki`, bukan `localhost`. File `.env.production` tidak boleh di-commit.

### Build dan start service

Perintah `docker compose build` otomatis membaca `backend/Dockerfile` dan `deploy/fuseki/Dockerfile` melalui bagian `build.context`; tidak perlu menjalankan `docker build` manual.

```bash
docker compose --file deploy/compose.production.yml build
docker compose --file deploy/compose.production.yml up --detach
docker compose --file deploy/compose.production.yml ps
```

Compose menjalankan Uvicorn tanpa `--reload`. Restart container tidak meng-import ontology secara otomatis.

Verifikasi status dan log:

```bash
docker compose --file deploy/compose.production.yml ps
docker compose --file deploy/compose.production.yml logs --tail=100 backend
docker compose --file deploy/compose.production.yml logs --tail=100 fuseki
```

Kedua service harus berstatus `healthy`.

### Initial dataset import, manual dan satu kali

Import dataset adalah lifecycle terpisah dari startup aplikasi. Setelah service Fuseki sehat, upload ontology secara eksplisit:

```bash
docker run --rm \
  --network academic-industry-skill-graph_lod-internal \
  --volume "$PWD/ontology/OBC-ONTO/OBC-ONTO-Instance copy.ttl:/tmp/obc-instance.ttl:ro" \
  curlimages/curl:8.12.1 \
  --fail --request POST \
  --url http://fuseki:3030/myDataset/data \
  --header 'Content-Type: text/turtle' \
  --data-binary @/tmp/obc-instance.ttl
```

Jika menjalankan perintah tersebut dari Git Bash dan muncul path Windows seperti `C:/Users/.../tmp/obc-instance.ttl`, tambahkan `MSYS_NO_PATHCONV=1` di awal command. Jika menggunakan PowerShell, gunakan format berikut:

```powershell
$source = "E:\Polban\Semester 6\Bu Ade\penelitian\academic-industry-skill-graph\ontology\OBC-ONTO\OBC-ONTO-Instance copy.ttl"
docker run --rm `
  --network academic-industry-skill-graph_lod-internal `
  --mount "type=bind,source=$source,target=/tmp/obc-instance.ttl,readonly" `
  curlimages/curl:8.12.1 `
  --fail --request POST `
  --url http://fuseki:3030/myDataset/data `
  --header "Content-Type: text/turtle" `
  --data-binary "@/tmp/obc-instance.ttl"
```

Verifikasi jumlah triple melalui backend:

```bash
curl --fail --request POST http://127.0.0.1:8000/api/query \
  --header 'Content-Type: application/json' \
  --data '{"query":"SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }"}'
```

Pada Compose production port Fuseki sengaja tidak dipublish. Command admin di atas hanya membuat container curl sementara yang bergabung ke private Docker network; proses ini tetap manual dan tidak berjalan saat startup. Jangan menambahkan import otomatis ke `entrypoint`.

### Backup dan update

Volume TDB2 bernama `academic-industry-skill-graph-fuseki-data` dan tetap hidup walaupun container di-rebuild:

```bash
docker volume inspect academic-industry-skill-graph-fuseki-data
docker compose --file deploy/compose.production.yml down
docker compose --file deploy/compose.production.yml up --detach
```

Jangan menjalankan `docker compose down --volumes` kecuali memang ingin menghapus dataset. Backup volume harus disimpan di lokasi terpisah dari VPS.

Contoh backup volume ke file tar:

```bash
docker run --rm \
  --volume academic-industry-skill-graph-fuseki-data:/source:ro \
  --volume "$PWD/backups:/backup" \
  alpine:3.21 \
  tar --create --gzip --file /backup/fuseki-$(date +%F).tar.gz --directory /source .
```

Simpan hasil backup di storage terpisah. Backup di VPS yang sama tidak cukup jika VPS rusak atau hilang.

Untuk update image aplikasi:

```bash
git pull origin main
docker compose --file deploy/compose.production.yml build backend
docker compose --file deploy/compose.production.yml up --detach backend
```

Update backend tidak mengubah volume Fuseki dan tidak menjalankan import dataset.

### Update frontend production

```bash
git pull origin main
cd frontend
npm ci
npm run build
```

Setelah itu reload Nginx host agar static files terbaru digunakan:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Konfigurasi Nginx host

Salin template berikut ke konfigurasi Nginx:

```text
deploy/nginx/academic-industry-skill-graph.conf.example
```

Konfigurasi tersebut melakukan dua hal:

- menyajikan `frontend/dist/`;
- meneruskan `/api/` ke `http://127.0.0.1:8000`.

FastAPI dan Fuseki tidak perlu dibuka ke public interface VPS. Setelah domain tersedia, aktifkan HTTPS menggunakan Certbot/Let's Encrypt.

### Troubleshooting umum

**`dependency failed to start` pada Fuseki**

Periksa status dan log:

```bash
docker compose --file deploy/compose.production.yml ps
docker compose --file deploy/compose.production.yml logs fuseki
```

Fuseki harus berstatus `healthy` sebelum backend digunakan.

**`HTTP 405 Method Not Allowed: Read-only` saat upload**

Pastikan Fuseki dijalankan dengan:

```text
--update
```

Setelah mengubah Dockerfile atau Compose, rebuild dan recreate service:

```bash
docker compose --file deploy/compose.production.yml up --build --detach --force-recreate fuseki
```

**`Could not resolve host: fuseki`**

Pastikan command admin bergabung ke network:

```text
academic-industry-skill-graph_lod-internal
```

dan service Fuseki memiliki alias `fuseki`.

**Backend tidak dapat menghubungi Fuseki**

Di dalam Compose, gunakan:

```env
FUSEKI_QUERY_URL=http://fuseki:3030/myDataset/query
```

Jangan gunakan `localhost` untuk komunikasi antar-container.

**Dataset hilang setelah restart**

Periksa volume:

```bash
docker volume inspect academic-industry-skill-graph-fuseki-data
```

Jangan gunakan `docker compose down --volumes` jika ingin mempertahankan dataset.

### Hal yang tidak boleh dilakukan

- Jangan commit `.env.production`.
- Jangan menggunakan `docker compose down --volumes` untuk restart biasa.
- Jangan meng-import ontology otomatis di entrypoint container.
- Jangan membuka port Fuseki `3030` ke internet.
- Jangan membuka port FastAPI `8000` ke public interface.
- Jangan menggunakan Vite development server sebagai frontend production.
- Jangan menjalankan Uvicorn dengan `--reload` di production.
- Jangan menganggap image/container sebagai tempat penyimpanan dataset; data berada di volume TDB2.
