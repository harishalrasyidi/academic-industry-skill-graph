# Project Summary: Academic Industry Skill Graph

Gunakan dokumen ini sebagai konteks saat mendiskusikan project dengan AI.

## 1. Tujuan Aplikasi

Project ini adalah aplikasi Linked Open Data / Semantic Web sederhana yang fokus utamanya adalah SPARQL Query Interface, dengan konsep mirip Wikidata Query Service.

Aplikasi memungkinkan pengguna untuk:

- menulis query SPARQL melalui web interface;
- menjalankan query ke dataset RDF lokal;
- mengirim query melalui backend FastAPI;
- meneruskan query dari FastAPI ke Apache Jena Fuseki;
- menampilkan hasil query dalam tabel;
- menampilkan error ketika query tidak valid atau Fuseki tidak tersedia;
- membuka detail entity/resource RDF;
- membuka detail property RDF;
- membuka link `owl:sameAs` ke Wikidata;
- memilih tampilan URI lengkap atau URI singkat.

Fokus aplikasi adalah query generic terhadap dataset lokal, bukan endpoint domain-specific seperti `/books` atau `/authors`.

## 2. Arsitektur Saat Ini

```text
Browser / React frontend
        |
        | HTTP JSON
        v
FastAPI backend
        |
        | SPARQL HTTP request
        v
Apache Jena Fuseki
        |
        v
RDF dataset / TDB2
```

Komponen utama:

- Frontend: React + Vite
- Backend: Python + FastAPI + Uvicorn
- RDF/triple store: Apache Jena Fuseki 6.2.0
- Query language: SPARQL
- RDF format: Turtle, RDF/XML, OWL
- HTTP client backend: `httpx`
- Validation backend: Pydantic

## 3. Struktur Project

```text
academic-industry-skill-graph/
├── README.md
├── docs/
│   ├── demo-queries.md
│   └── project-summary-for-ai.md
├── backend/
│   ├── requirements.txt
│   ├── old_main.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── fuseki.py
│   │   ├── main.py
│   │   └── schemas.py
│   └── data/
│       └── sample.ttl
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       │   └── Navbar.jsx
│       └── pages/
│           ├── Home.jsx
│           ├── EntityExplorer.jsx
│           ├── PropertyExplorer.jsx
│           └── QueryService.jsx
├── ontology/
│   ├── CSO.3.5.owl
│   ├── CSO.3.5.ttl
│   ├── esco-v1.2.1.ttl
│   └── OBC-ONTO/
│       ├── OBC-ONTO.ttl
│       ├── OBC-ONTO.owl
│       ├── OBC-ONTO-Instance.ttl
│       ├── OBC-ONTO-Instance.owl
│       └── OBC-ONTO-Instance copy.ttl
└── script ambil part/
    ├── 1_cso_filtering/
    ├── 2_esco_filtering/
    ├── 3_wikidata_mapping/
    └── 4_llm_semantic_mapping/
```

File ontology dan script penelitian merupakan sumber data/pipeline penelitian. Runtime aplikasi utama berada di folder `backend/` dan `frontend/`.

## 4. Backend API

### Health check

```http
GET /api/health
```

### Execute SPARQL query

```http
POST /api/query
Content-Type: application/json

{
  "query": "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
}
```

Backend mengirim query ke Fuseki dengan:

```http
Content-Type: application/sparql-query
Accept: application/sparql-results+json
```

### Resource/entity detail

```http
GET /api/resources?uri={encoded_uri}
```

Endpoint ini mengambil semua predicate dan object dari sebuah RDF resource.

### Property detail

```http
GET /api/properties?uri={encoded_uri}
```

Endpoint ini mengambil metadata property, yaitu tipe, domain, range, dan contoh penggunaan property.

### RDF term classification

```http
GET /api/term-info?uri={encoded_uri}
```

Endpoint ini memeriksa apakah URI bertipe:

- `owl:ObjectProperty`;
- `owl:DatatypeProperty`;
- `owl:Class`.

Jika bertipe object/datatype property, frontend menganggapnya sebagai property; selain itu dianggap sebagai entity.

## 5. Frontend Routes

```text
/                    Home / halaman awal
/query               SPARQL Query Service
/entity/:id          Detail RDF entity/resource
/property/:id        Detail RDF property
```

Pada halaman `/query`:

- hasil bertipe `literal` ditampilkan sebagai teks;
- URI entity dibuat menjadi link ke `/entity/...`;
- URI property dibuat menjadi link ke `/property/...`;
- URI Wikidata dibuat menjadi link ke `https://www.wikidata.org/wiki/Q...`;
- checkbox `Full URI` mengubah tampilan URI singkat menjadi URI lengkap tanpa mengubah target link.

## 6. Dataset dan Ontology

Dataset uji awal berada di:

```text
backend/data/sample.ttl
```

Dataset tersebut berisi contoh person, course, dan Linked Open Data.

Ontology utama yang ingin digunakan adalah OBC-ONTO:

```text
ontology/OBC-ONTO/OBC-ONTO-Instance copy.ttl
```

Ontology OBC berisi konsep seperti:

- `Course`
- `Curriculum`
- `StudyProgram`
- `ProgramEducationalObjective`
- `ProgramLearningOutcome`
- `CourseLearningOutcome`
- `LearningDomain`
- `AffectiveDomain`
- `CognitiveDomain`
- `PsychomotoricDomain`
- `SubjectMatter`

Beberapa property OBC:

- `courseName`
- `credit`
- `semester`
- `hasPLO`
- `ploHasCourse`
- `hasCLO`
- `hasDomain`
- `hasContent`
- `owl:sameAs`

File `OBC-ONTO-Instance copy.ttl` memiliki contoh tambahan `owl:sameAs` ke Wikidata untuk demonstrasi navigasi. Link tersebut masih bersifat contoh dan perlu diverifikasi sebelum dianggap sebagai mapping produksi.

## 7. Fuseki

Fuseki yang digunakan adalah Apache Jena Fuseki 6.2.0.

Pada environment pengembangan saat ini, dataset yang aktif bernama:

```text
myDataset
```

Endpoint query:

```text
http://localhost:3030/myDataset/query
```

Endpoint upload data:

```text
http://localhost:3030/myDataset/data
```

Konfigurasi backend default:

```text
FUSEKI_QUERY_URL=http://localhost:3030/myDataset/query
```

## 8. Instalasi Lokal

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend biasanya tersedia di:

```text
http://localhost:5173
```

Query Service tersedia di:

```text
http://localhost:5173/query
```

## 9. Tidak Digunakan oleh Runtime Aplikasi

Saat ini aplikasi web tidak menggunakan:

- Docker atau Docker Compose;
- Kubernetes;
- PostgreSQL;
- MySQL;
- MongoDB;
- Redis;
- Neo4j;
- vector database;
- embedding service;
- AI/LLM API.

Folder `script ambil part/4_llm_semantic_mapping/` memiliki eksperimen semantic matching dan embedding, termasuk model `all-MiniLM-L6-v2`, tetapi itu bukan bagian dari runtime web saat ini.

## 10. Java, Python, dan Node.js

### Java

Java digunakan untuk menjalankan Apache Jena Fuseki.

Environment pengembangan menggunakan Java:

```text
OpenJDK 21 LTS, Eclipse Temurin
```

### Python

Python digunakan untuk:

- menjalankan FastAPI;
- menjalankan Uvicorn;
- menerima request query dari frontend;
- meneruskan query ke Fuseki;
- mengambil resource/property metadata dari Fuseki;
- mengembalikan JSON ke frontend.

### Node.js

Node.js digunakan untuk:

- meng-install dependency frontend;
- menjalankan Vite development server;
- melakukan lint;
- melakukan production build.

Node.js bukan runtime backend production aplikasi ini. Hasil React production dapat disajikan sebagai static files melalui Nginx.

## 11. Rekomendasi Deployment Global

Untuk kondisi awal, aplikasi dapat dideploy di satu VPS menggunakan:

```text
Nginx
FastAPI/Uvicorn sebagai systemd service
Apache Jena Fuseki sebagai systemd service
React production build sebagai static files
```

Docker bersifat opsional. Kubernetes belum diperlukan karena aplikasi masih memiliki satu VPS dan beberapa service sederhana.

Fuseki dan FastAPI sebaiknya hanya listen pada localhost; hanya Nginx yang dibuka ke publik melalui port 80/443.

Database RDF Fuseki dapat berada di VPS yang sama untuk tahap awal. Dataset Fuseki harus memiliki backup terpisah.

Spesifikasi VPS yang tersedia:

- Ubuntu 24.04 LTS;
- 4 vCPU;
- RAM sekitar 4 GB;
- storage sekitar 67 GB;
- public IP `117.53.145.23`.

Spesifikasi tersebut cukup untuk demo, penelitian, dan sekitar 1-10 user bersamaan dengan query SPARQL ringan sampai menengah.

## 12. Pertanyaan yang Ingin Didiskusikan dengan AI

Gunakan konteks di atas untuk mendiskusikan:

- apakah deployment sebaiknya menggunakan Docker Compose atau systemd langsung;
- bagaimana membuat Fuseki production-ready;
- bagaimana backup dan restore dataset TDB2;
- bagaimana membuat CI/CD dari GitHub ke VPS;
- bagaimana mengatur HTTPS, Nginx, dan firewall;
- bagaimana meningkatkan klasifikasi entity/property;
- bagaimana mengelola mapping `owl:sameAs` ke Wikidata;
- bagaimana menangani query SPARQL yang mahal atau berbahaya;
- kapan perlu memisahkan Fuseki ke server berbeda;
- apakah perlu menambahkan autentikasi dan histori query.
