# Alur Deployment Production — Academic Industry Skill Graph

Dokumen ini merangkum alur deployment production yang sudah dilakukan untuk project **Academic Industry Skill Graph**.

## Arsitektur Production

```text
Internet
   |
Nginx host :80/:443
   |-- frontend static files
   `-- /api -> 127.0.0.1:8000
      |
    backend FastAPI container
      |
    private Docker network
      |
    Apache Jena Fuseki container :3030
      |
    persistent TDB2 volume
```

Prinsip utama:

- **Nginx** berjalan langsung di host VPS dan menjadi satu-satunya entry point publik.
- **Frontend React** dibuild menjadi static files, bukan dijalankan menggunakan Vite development server.
- **FastAPI** berjalan di Docker container dan hanya dipublish ke `127.0.0.1:8000`.
- **Fuseki** berjalan di Docker container tanpa publish port `3030` ke host.
- FastAPI mengakses Fuseki melalui private Docker network.
- Data RDF/TDB2 disimpan di persistent Docker volume.
- Kubernetes tidak digunakan.

---

## 1. Login ke VPS

Login awal dilakukan menggunakan akun `root`.

```bash
ssh root@<IP_VPS>
```

Cek sistem:

```bash
cat /etc/os-release
uname -a
```

VPS menggunakan Ubuntu 24.04 LTS.

---

## 2. Update sistem dan install package dasar

```bash
apt update
apt upgrade -y
```

Install package dasar yang dibutuhkan:

```bash
apt install -y git curl ca-certificates nginx ufw
```

---

## 3. Menyiapkan Swap

VPS memiliki RAM sekitar 4 GB. Untuk mengurangi risiko Out Of Memory (OOM),
buat swap 2 GB sebelum menjalankan Fuseki.

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Verifikasi:

```bash
free -h
swapon --show
```

Expected:

```text
Swap: 2.0Gi
```

Agar swap tetap aktif setelah reboot:

```bash
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Optional, kurangi kecenderungan Linux menggunakan swap terlalu agresif:

```bash
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

> Swap bukan pengganti RAM. Swap digunakan sebagai safety net agar lonjakan memory
> tidak langsung menyebabkan proses dibunuh oleh kernel.

## 4. Membuat user deployment

User khusus deployment dibuat agar aplikasi tidak dikelola sehari-hari menggunakan `root`.

```bash
adduser deploy
```

Tambahkan user ke grup `sudo`:

```bash
usermod -aG sudo deploy
```

Cek:

```bash
groups deploy
```

Expected:

```text
deploy : deploy sudo ...
```

Jika SSH key root ingin digunakan juga oleh user `deploy`:

```bash
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
```

Kemudian login ulang sebagai:

```bash
ssh deploy@<IP_VPS>
```

---

## 5. Konfigurasi firewall

Izinkan hanya layanan yang memang harus publik:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

Cek:

```bash
sudo ufw status verbose
```

Port publik yang diharapkan:

```text
22/tcp   SSH
80/tcp   HTTP
443/tcp  HTTPS
```

Port berikut **tidak** dibuka ke publik:

```text
8000     FastAPI
3030     Fuseki
```

---

## 6. Install Docker dan Docker Compose

Install Docker Engine dan Docker Compose Plugin dari repository resmi Docker:

```bash
sudo apt update
sudo apt install -y ca-certificates curl
```

Siapkan keyring:

```bash
sudo install -m 0755 -d /etc/apt/keyrings

sudo curl -fsSL \
  https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc

sudo chmod a+r /etc/apt/keyrings/docker.asc
```

Tambahkan repository Docker:

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Kemudian install Docker Engine dan Docker Compose Plugin:

```bash
sudo apt update

sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

Verifikasi:

```bash
docker --version
docker compose version
```

Pastikan service Docker aktif:

```bash
sudo systemctl enable --now docker
```

Tambahkan user `deploy` ke grup Docker:

```bash
sudo usermod -aG docker deploy
```

Logout dan login ulang agar group membership aktif.

Jangan menggunakan package `docker.io` dan jangan menggunakan binary legacy
`docker-compose` terpisah. Dokumentasi ini menggunakan Docker Compose Plugin dengan
command `docker compose`.

Test:

```bash
docker ps
```

---

## 7. Menyiapkan direktori project

Project ditempatkan di:

```text
/opt/academic-industry-skill-graph
```

Buat directory dan ubah ownership:

```bash
sudo mkdir -p /opt/academic-industry-skill-graph
sudo chown deploy:deploy /opt/academic-industry-skill-graph
```

Masuk ke directory:

```bash
cd /opt/academic-industry-skill-graph
```

Clone repository:

```bash
git clone https://github.com/harishalrasyidi/academic-industry-skill-graph.git .
```

Verifikasi:

```bash
git status
ls -la
```

---

## 8. Menyiapkan environment production

Dari root project:

```bash
cp .env.production.example .env.production
chmod 600 .env.production
```

Konfigurasi penting:

```env
FUSEKI_QUERY_URL=http://fuseki:3030/myDataset/query
FUSEKI_TIMEOUT_SECONDS=30
CORS_ALLOW_ORIGINS=
BACKEND_HOST_PORT=8000
```

Catatan:

- Antar-container menggunakan hostname service `fuseki`, bukan `localhost`.
- `.env.production` tidak boleh di-commit.

---

## 9. Konfigurasi Memory Fuseki

Apache Jena Fuseki menggunakan Java/JVM.

Script bawaan `fuseki-server` menggunakan nilai default `-Xmx4G` jika environment
variable `JVM_ARGS` tidak diberikan. Nilai tersebut terlalu besar untuk VPS dengan
RAM sekitar 4 GB karena Java heap bukan satu-satunya penggunaan memory. JVM juga
membutuhkan memory untuk metaspace, thread stack, direct buffer, native memory,
serta TDB2/filesystem cache.

Karena itu, pada production gunakan konfigurasi memory yang lebih konservatif.

Pada `deploy/compose.production.yml`, service `fuseki` menggunakan:

```yaml
services:
  fuseki:
    environment:
      JVM_ARGS: "-Xms256m -Xmx768m"
    restart: unless-stopped
```

Artinya:

```text
-Xms256m   initial Java heap = 256 MB
-Xmx768m   maximum Java heap = 768 MB
```

Nilai ini dapat dievaluasi kembali berdasarkan ukuran dataset dan kebutuhan query,
tetapi jangan menggunakan default `-Xmx4G` pada VPS dengan RAM 4 GB.

## 10. Build dan Start Backend + Fuseki

Dari root project:

```bash
cd /opt/academic-industry-skill-graph
```

Validasi konfigurasi Compose:

```bash
docker compose --file deploy/compose.production.yml config
```

Build image:

```bash
docker compose --file deploy/compose.production.yml build
```

Untuk first deployment, start Fuseki terlebih dahulu:

```bash
docker compose --file deploy/compose.production.yml up -d fuseki
```

Cek status dan penggunaan resource:

```bash
docker compose --file deploy/compose.production.yml ps
free -h
docker stats --no-stream
```

Pastikan JVM menggunakan konfigurasi memory production:

```bash
docker compose \
  --file deploy/compose.production.yml \
  exec fuseki \
  ps -ef
```

Expected terdapat `-Xms256m -Xmx768m` dan bukan `-Xmx4G`.

Cek health dan restart count Fuseki:

```bash
docker inspect \
  "$(docker compose --file deploy/compose.production.yml ps -q fuseki)" \
  --format='RestartCount={{.RestartCount}} Health={{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

Expected:

```text
RestartCount=0
Health=healthy
```

Setelah Fuseki healthy, start backend:

```bash
docker compose --file deploy/compose.production.yml up -d backend
docker compose --file deploy/compose.production.yml ps
```

Jika bermasalah, lihat log:

```bash
docker compose --file deploy/compose.production.yml logs --tail=100 backend
docker compose --file deploy/compose.production.yml logs --tail=100 fuseki
```

---

## 11. Verifikasi backend dan isolasi Fuseki

Test backend dari VPS:

```bash
curl http://127.0.0.1:8000/api/health
```

Backend harus merespons.

Fuseki tidak dipublish ke host, sehingga ini seharusnya gagal:

```bash
curl http://127.0.0.1:3030
```

Dari internet, port berikut juga tidak boleh dapat diakses:

```text
<IP_VPS>:8000
<IP_VPS>:3030
```

---

## 12. Initial Dataset Import

Import RDF dataset dilakukan **manual dan satu kali**, terpisah dari lifecycle startup container.

Import tidak dimasukkan ke `entrypoint` atau startup Compose.

Fuseki tidak mem-publish port `3030` ke host. Karena itu import dilakukan melalui
`docker compose exec` dari dalam container Fuseki.

Contoh import file Turtle OBC-ONTO:

```bash
cd /opt/academic-industry-skill-graph

docker compose \
  --file deploy/compose.production.yml \
  exec -T fuseki \
  curl \
  --fail \
  --show-error \
  --request POST \
  --header "Content-Type: text/turtle" \
  --data-binary @- \
  http://127.0.0.1:3030/myDataset/data \
  < ontology/OBC-ONTO/OBC-ONTO-Instance.ttl
```

Setelah import, cek jumlah triple:

```bash
docker compose \
  --file deploy/compose.production.yml \
  exec -T fuseki \
  curl \
  --silent \
  --get \
  --header "Accept: application/sparql-results+json" \
  --data-urlencode \
  'query=SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }' \
  http://127.0.0.1:3030/myDataset/query
```

Alternatif verifikasi melalui backend:

```bash
curl --fail \
  --request POST \
  http://127.0.0.1:8000/api/query \
  --header 'Content-Type: application/json' \
  --data '{"query":"SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }"}'
```

Pastikan jumlah triple lebih dari 0.

---

## 13. Verifikasi persistence TDB2

Stop Compose:

```bash
docker compose --file deploy/compose.production.yml down
```

Jalankan kembali:

```bash
docker compose --file deploy/compose.production.yml up --detach
```

Setelah `up --detach`, cek status service:

```bash
docker compose --file deploy/compose.production.yml ps
```

Sebelum menjalankan query validasi jumlah triple, pastikan kedua service sudah
healthy:

```text
backend   healthy
fuseki    healthy
```

Jika Fuseki masih berstatus `health: starting`, tunggu sampai menjadi `healthy`.
Setelah kedua service healthy, jalankan query jumlah triple dan pastikan dataset
masih tersedia.

Dataset harus tetap ada.

Jangan gunakan:

```bash
docker compose down --volumes
```

untuk restart biasa karena dapat menghapus volume TDB2.

---

## 14. Install Node.js

Node.js hanya dibutuhkan untuk build frontend React/Vite.

Install Node.js LTS:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

Verifikasi:

```bash
node --version
npm --version
```

Jika belum terpasang, install Node.js LTS.

Node.js dan npm tidak digunakan sebagai web server production.

---

## 15. Build frontend React

Masuk ke frontend:

```bash
cd /opt/academic-industry-skill-graph/frontend
```

Install dependency:

```bash
npm ci
```

Build production:

```bash
npm run build
```

Hasil build berada di:

```text
frontend/dist/
```

Cek:

```bash
ls -lah dist
```

Expected minimal:

```text
index.html
assets/
```

Vite development server tidak digunakan di production.

---

## 16. Deploy static frontend ke Nginx

Buat directory web:

```bash
sudo mkdir -p /var/www/academic-industry-skill-graph
```

Copy hasil build:

```bash
sudo cp -r dist/* /var/www/academic-industry-skill-graph/
```

Atur ownership:

```bash
sudo chown -R www-data:www-data /var/www/academic-industry-skill-graph
```

Atur permission:

```bash
sudo find /var/www/academic-industry-skill-graph -type d -exec chmod 755 {} \;
sudo find /var/www/academic-industry-skill-graph -type f -exec chmod 644 {} \;
```

---

## 17. Konfigurasi Nginx

Template konfigurasi project berada di:

```text
deploy/nginx/academic-industry-skill-graph.conf.example
```

Copy ke Nginx:

```bash
sudo cp   /opt/academic-industry-skill-graph/deploy/nginx/academic-industry-skill-graph.conf.example   /etc/nginx/sites-available/academic-industry-skill-graph
```

Enable site:

```bash
sudo ln -s   /etc/nginx/sites-available/academic-industry-skill-graph   /etc/nginx/sites-enabled/academic-industry-skill-graph
```

Jika default site masih aktif:

```bash
sudo rm /etc/nginx/sites-enabled/default
```

Konfigurasi Nginx harus melakukan:

```text
/       -> frontend static files
/api/   -> http://127.0.0.1:8000
```

React SPA juga perlu fallback ke `index.html` agar route client-side tetap berfungsi.

---

## 18. Verifikasi konfigurasi Nginx

Test syntax:

```bash
sudo nginx -t
```

Jika berhasil:

```bash
sudo systemctl reload nginx
```

Cek status:

```bash
sudo systemctl status nginx
```

---

## 19. Verifikasi aplikasi melalui Nginx

Dari VPS:

```bash
curl -I http://127.0.0.1
```

Frontend harus merespons HTTP 200.

Test API melalui Nginx:

```bash
curl http://127.0.0.1/api/health
```

Kemudian dari browser:

```text
http://<IP_VPS>
```

Test juga:

- halaman utama;
- `/query`;
- entity/property navigation;
- eksekusi query SPARQL;
- hasil query tampil pada frontend.

---

## 20. Arsitektur setelah deployment HTTP berhasil

```text
Browser
   |
   v
Nginx host :80
   |-----------------------------|
   |                             |
React static                /api/*
                                 |
                                 v
                         127.0.0.1:8000
                                 |
                         FastAPI container
                                 |
                         Docker private network
                                 |
                         Fuseki container
                                 |
                         TDB2 volume
```

Security boundary:

```text
<IP_VPS>:80       public
<IP_VPS>:443      public setelah HTTPS
<IP_VPS>:8000     tidak public
<IP_VPS>:3030     tidak public
```

---

## 21. Monitoring Resource

Karena VPS memiliki RAM sekitar 4 GB, penggunaan memory perlu dipantau terutama
saat menjalankan Fuseki dan saat melakukan import ontology.

Cek memory host:

```bash
free -h
```

Cek penggunaan resource container:

```bash
docker stats --no-stream
```

Cek proses host dengan penggunaan RAM terbesar:

```bash
ps -eo pid,ppid,user,%mem,rss,cmd --sort=-rss | head -20
```

Monitoring realtime:

```bash
docker stats
```

atau:

```bash
top
```

Pada `top`, tekan `Shift + M` untuk mengurutkan proses berdasarkan penggunaan
memory.

Cek health dan restart Fuseki:

```bash
docker inspect \
  "$(docker compose --file deploy/compose.production.yml ps -q fuseki)" \
  --format='RestartCount={{.RestartCount}} Health={{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

Jika container mengalami exit code `137`, restart berulang, atau host menjadi tidak
responsif, cek kemungkinan Out Of Memory:

```bash
sudo journalctl -k | grep -Ei 'out of memory|oom|killed process'
sudo dmesg -T | grep -Ei 'out of memory|oom|killed process'
```

## 22. Next step

Setelah HTTP melalui IP berhasil, tahap berikutnya:

```text
Domain
  ->
DNS A Record
  ->
Nginx server_name
  ->
Certbot / Let's Encrypt
  ->
HTTPS
  ->
redirect HTTP ke HTTPS
```

Setelah HTTPS stabil, baru lanjut ke:

- backup TDB2 yang production-safe;
- hardening SPARQL query;
- logging dan log rotation;
- deployment update procedure;
- GitHub Actions CI/CD.

---

## Update Deployment

### Update backend

```bash
cd /opt/academic-industry-skill-graph
git pull origin main

docker compose --file deploy/compose.production.yml build backend
docker compose --file deploy/compose.production.yml up --detach backend
```

### Update frontend

```bash
cd /opt/academic-industry-skill-graph
git pull origin main

cd frontend
npm ci
npm run build
```

Deploy static build terbaru:

```bash
sudo rm -rf /var/www/academic-industry-skill-graph/*
sudo cp -r dist/* /var/www/academic-industry-skill-graph/
sudo chown -R www-data:www-data /var/www/academic-industry-skill-graph
```

Validasi dan reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## Hal yang Tidak Boleh Dilakukan

- Jangan commit `.env.production`.
- Jangan menggunakan default Fuseki `-Xmx4G` pada VPS dengan RAM 4 GB.
- Jangan menjalankan Fuseki tanpa memonitor penggunaan RAM setelah deployment pertama.
- Jangan menghapus atau menonaktifkan swap tanpa alasan yang jelas.
- Jangan menyimpan private SSH key di VPS.
- Jangan membuka Fuseki port `3030` ke internet.
- Jangan membuka FastAPI port `8000` ke public interface.
- Jangan menjalankan Uvicorn dengan `--reload` di production.
- Jangan menjalankan Vite development server di production.
- Jangan import ontology/dataset otomatis setiap container startup.
- Jangan menganggap container sebagai tempat penyimpanan data permanen.
- Jangan menjalankan `docker compose down --volumes` untuk restart biasa.
- Jangan menjalankan aplikasi sehari-hari sebagai `root`.
- Jika ditemukan executable atau proses asing yang berjalan sebagai `root`, jangan
  hanya menghapus proses tersebut dan menganggap server aman. Rebuild/reinstall host
  dari image bersih dan rotasi credential yang relevan.
