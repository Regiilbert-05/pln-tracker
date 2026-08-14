# ⚡ PLN Electricity Tracker Web App (Cloud & Multi-User)

Aplikasi web modern berbasis **Python + Streamlit** untuk mencatat, menghitung, dan memantau penggunaan listrik prabayar (token PLN) secara otomatis dan visual. Dilengkapi dengan dukungan **MongoDB Atlas Cloud Database**, memungkinkan aplikasi diakses oleh **banyak orang/keluarga secara bersamaan** serta di-deploy secara permanen ke **Streamlit Community Cloud**.

---

## 🌟 Fitur Utama

- **☁️ Cloud Multi-User & Multi-Meter**:
  - Mendukung penyimpanan berbasis cloud (**MongoDB Atlas**) sehingga data **permanen dan tidak hilang** saat di-deploy ke Streamlit Cloud.
  - Fitur **Profil Meteran** (misal: *Rumah Utama*, *Kost Kamar 01*, *Ruko*) sehingga banyak pengguna/lokasi bisa dipantau secara mandiri dalam satu aplikasi.
  - **Hybrid Fallback**: Jika dijalankan offline tanpa koneksi MongoDB, aplikasi otomatis beralih ke penyimpanan CSV lokal (`data_listrik.csv`).
- **📝 Input Fleksibel**: Form pencatatan tanggal, jam, sisa kWh di meteran, serta pengisian token baru (Rupiah & kWh).
- **🧮 Kalkulasi Otomatis**: Menghitung kWh terpakai antar sesi pencatatan dengan memperhitungkan isi ulang token:
  $$\text{kWh Terpakai} = (\text{kWh Sebelumnya} + \text{Token Masuk}) - \text{kWh Sekarang}$$
- **📊 Visualisasi Interaktif (Plotly)**:
  - *Bar Chart* konsumsi per pencatatan & per hari kalender.
  - *Line Chart* tren sisa meteran dengan penanda khusus (⭐) saat pengisian token.
- **💡 Metrik Cerdas**:
  - Estimasi sisa hari sebelum token habis berdasarkan rata-rata pemakaian.
  - Estimasi biaya per hari (Rp/hari).
  - Status indikator sisa meteran (Aman / Perhatian / Kritis).
- **⚙️ Manajemen Data Mudah**:
  - Hapus catatan terakhir jika terjadi kesalahan input.
  - Download / Backup database CSV per meteran langsung dari web UI.

---

## 🚀 Panduan Setup Database MongoDB Atlas (Gratis)

Agar data tidak hilang saat aplikasi di-deploy ke Streamlit Cloud, ikuti langkah mudah berikut:

### Langkah 1: Buat Database Gratis di MongoDB Atlas
1. Daftar / Login ke [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) (Gratis).
2. Buat Cluster baru: Pilih opsi **FREE (M0 Tier)**.
3. Di menu **Security > Database Access**, buat user database baru (misal: username `pln_user` dan password `password123`).
4. Di menu **Security > Network Access**, klik **Add IP Address** -> pilih **Allow Access from Anywhere (`0.0.0.0/0`)** agar server Streamlit Cloud dapat terhubung.
5. Di menu **Database > Clusters**, klik tombol **Connect** -> pilih **Drivers** -> salin connection string URI yang berformat:
   ```text
   mongodb+srv://pln_user:<password>@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority
   ```
   *(Ganti `<password>` dengan password user yang Anda buat).*

---

### Langkah 2: Konfigurasi Lokal (Opsional)
Jika ingin menguji koneksi MongoDB di komputer lokal:
1. Buat folder `.streamlit` jika belum ada.
2. Buat file `.streamlit/secrets.toml` (bisa salin dari `.streamlit/secrets.toml.example`).
3. Isi dengan connection string Anda:
   ```toml
   [mongo]
   connection_string = "mongodb+srv://pln_user:password_anda@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
   database = "pln_tracker"
   collection = "meter_records"
   ```

---

### Langkah 3: Deploy ke Streamlit Community Cloud
1. Push repository ini ke **GitHub** Anda.
2. Buka [share.streamlit.io](https://share.streamlit.io/) dan pilih repositori Anda.
3. Main file path: `app.py`.
4. Sebelum klik deploy (atau setelah deploy di menu **Settings > Secrets**), masukkan konfigurasi MongoDB Secrets:
   ```toml
   [mongo]
   connection_string = "mongodb+srv://pln_user:password_anda@cluster0.abcde.mongodb.net/?retryWrites=true&w=majority"
   database = "pln_tracker"
   collection = "meter_records"
   ```
5. Klik **Save**. Aplikasi Anda sekarang aktif secara online, aman, dan dapat digunakan oleh banyak orang!

---

## 💻 Cara Menjalankan Aplikasi di Komputer Lokal

1. Buka Terminal / CMD di folder ini:
   ```bash
   cd c:\Users\wfvg2\Documents\CODE\listrik
   ```
2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
4. Buka browser di: `http://localhost:8501`.

---

## 📁 Struktur File

- `app.py` : Antarmuka dashboard Streamlit, form multi-meter, dan visualisasi grafik Plotly.
- `db.py` : Modul koneksi & CRUD MongoDB Atlas dengan fallback otomatis ke CSV lokal.
- `data_listrik.csv` : File database lokal cadangan jika berjalan offline.
- `requirements.txt` : Daftar library Python (`streamlit`, `pandas`, `plotly`, `pymongo`, `dnspython`).
- `.streamlit/secrets.toml.example` : Template kredensial MongoDB untuk Streamlit Cloud.
- `run.bat` : Launcher 1-klik untuk pengguna Windows.
- `README.md` : Dokumentasi lengkap aplikasi.
