# Academic Industry Skill Graph

Aplikasi Linked Open Data sederhana dengan Apache Jena Fuseki, FastAPI, SPARQL,
dan React/Vite. README ini berisi panduan instalasi dan menjalankan aplikasi secara
lokal di Windows.

Panduan deployment ke VPS/server dipisahkan di
[docs/production-deployment-flow.md](docs/production-deployment-flow.md).

## Struktur Dokumentasi

- [README ini](README.md): instalasi dan penggunaan lokal.
- [docs/demo-queries.md](docs/demo-queries.md): contoh query SPARQL OBC-ONTO.
- [docs/production-deployment-flow.md](docs/production-deployment-flow.md): deployment ke VPS.
- [ontology/OBC-ONTO/README.md](ontology/OBC-ONTO/README.md): ringkasan ontology OBC-ONTO.

## Prasyarat

Install tool berikut pada Windows:

- Java 21 LTS, untuk menjalankan Fuseki;
- Python 3.10 atau lebih baru, untuk FastAPI;
- Node.js LTS dan npm, untuk frontend React/Vite;
- Git;
- PowerShell.

Verifikasi:

```powershell
java -version
python --version
node --version
npm --version
git --version
```

## 1. Install Apache Jena Fuseki

Download Apache Jena Fuseki 6.2.0 dari Apache Archive:

<https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-6.2.0.tar.gz>

Ekstrak sehingga folder berikut tersedia:

```text
C:\jena-fuseki\apache-jena-fuseki-6.2.0
```

Pastikan file berikut ada:

```text
C:\jena-fuseki\apache-jena-fuseki-6.2.0\fuseki-server.bat
```

Verifikasi Java sebelum menjalankan Fuseki:

```powershell
java -version
```

### Menjalankan Fuseki

Buka PowerShell pertama:

```powershell
cd "C:\jena-fuseki\apache-jena-fuseki-6.2.0"
New-Item -ItemType Directory -Force -Path "C:\jena-fuseki\lod-data"
.\fuseki-server.bat --loc="C:\jena-fuseki\lod-data" --update /myDataset
```

Fuseki berjalan pada:

```text
http://localhost:3030
```

Dataset yang digunakan adalah `myDataset`. Endpoint query dan upload:

```text
http://localhost:3030/myDataset/query
http://localhost:3030/myDataset/data
```

Biarkan terminal Fuseki tetap terbuka selama aplikasi digunakan.

### Mengisi dataset contoh

Buka PowerShell kedua dari root project. Jalankan perintah berikut untuk meng-upload
dataset contoh:

```powershell
curl.exe --fail --request POST "http://localhost:3030/myDataset/data" `
  --header "Content-Type: text/turtle" `
  --data-binary "@backend/data/sample.ttl"
```

Untuk menggunakan dataset OBC-ONTO, gunakan file utama berikut:

```powershell
curl.exe --fail --request POST "http://localhost:3030/myDataset/data" `
  --header "Content-Type: text/turtle" `
  --data-binary "@ontology/OBC-ONTO/OBC-ONTO-Instance.ttl"
```

File `OBC-ONTO-Instance copy.ttl` adalah varian demo yang memiliki contoh tambahan
`owl:sameAs` ke Wikidata. Gunakan file tersebut hanya jika ingin mencoba navigasi
ke Wikidata.

> Upload dapat dijalankan ulang, tetapi triple dapat menjadi duplikat atau tergabung.
> Untuk dataset bersih, hentikan Fuseki, hapus isi `C:\jena-fuseki\lod-data`, buat
> ulang foldernya, lalu jalankan Fuseki dan upload kembali.

## 2. Setup FastAPI dengan virtual environment

Buka PowerShell kedua dari root project, atau gunakan terminal baru:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jika PowerShell menolak aktivasi script, jalankan perintah berikut hanya untuk sesi
PowerShell saat ini, lalu ulangi aktivasi:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Atur environment variable agar backend mengakses Fuseki lokal:

```powershell
$env:FUSEKI_QUERY_URL = "http://localhost:3030/myDataset/query"
$env:FUSEKI_TIMEOUT_SECONDS = "30"
$env:CORS_ALLOW_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"
```

Jalankan FastAPI:

```powershell
python -m uvicorn app.main:app --reload --port 8000
```

Backend tersedia pada:

```text
http://localhost:8000
http://localhost:8000/docs
```

Biarkan terminal FastAPI tetap terbuka. Prefix `.venv` pada prompt PowerShell
menandakan virtual environment sedang aktif.

## 3. Setup dan menjalankan frontend

Buka PowerShell ketiga dari root project:

```powershell
cd frontend
npm ci
npm run dev
```

Jika `package-lock.json` belum tersedia atau dependency perlu diperbarui, gunakan
`npm install` sekali. Untuk penggunaan berikutnya, `npm ci` menjaga dependency sesuai
lockfile.

Vite menampilkan URL frontend, biasanya:

```text
http://localhost:5173
```

Buka halaman query:

```text
http://localhost:5173/query
```

Frontend menggunakan proxy Vite untuk meneruskan `/api` ke FastAPI. Karena itu,
frontend lokal tidak memerlukan URL backend production.

## 4. Urutan Menjalankan Aplikasi

Gunakan tiga terminal:

```text
Terminal 1: Fuseki
Terminal 2: FastAPI dengan .venv aktif
Terminal 3: Vite frontend
```

Urutannya:

1. Jalankan Fuseki.
2. Upload `backend/data/sample.ttl` atau dataset OBC-ONTO.
3. Aktifkan `.venv`, install dependency, dan jalankan FastAPI.
4. Install dependency frontend dan jalankan Vite.
5. Buka `http://localhost:5173/query`.
6. Jalankan query dari [docs/demo-queries.md](docs/demo-queries.md).

## 5. Verifikasi

Health check FastAPI:

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

Query langsung melalui backend:

```powershell
$body = @{ query = 'SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }' } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/query `
  -Method Post `
  -ContentType 'application/json' `
  -Body $body
```

Query langsung ke Fuseki:

```powershell
curl.exe --get "http://localhost:3030/myDataset/query" `
  --header "Accept: application/sparql-results+json" `
  --data-urlencode "query=SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }"
```

Jumlah triple harus lebih dari `0` setelah dataset di-upload.

## Endpoint Aplikasi

| Method | Endpoint | Kegunaan |
|---|---|---|
| `GET` | `/api/health` | Memeriksa backend |
| `POST` | `/api/query` | Menjalankan query SPARQL |
| `GET` | `/api/resources?uri=...` | Detail entity/resource RDF |
| `GET` | `/api/properties?uri=...` | Detail property RDF |
| `GET` | `/api/term-info?uri=...` | Mengklasifikasikan URI RDF |

Route frontend:

```text
/                    Halaman awal
/query               SPARQL Query Service
/entity/:id          Detail entity/resource
/property/:id        Detail property
```

## Menghentikan Aplikasi

Hentikan proses pada setiap terminal dengan `Ctrl+C`.

Virtual environment dapat dinonaktifkan dengan:

```powershell
deactivate
```

Folder `.venv` dan `node_modules` tidak perlu di-commit ke Git.

## Deployment ke Server

Jangan menjalankan langkah deployment production dari README ini. Gunakan modul
terpisah:

[Alur Deployment Production](docs/production-deployment-flow.md)
