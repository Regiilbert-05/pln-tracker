# ⚡ PLN Electricity Tracker Web App

Aplikasi web lokal berbasis **Python + Streamlit** untuk mencatat, menghitung, dan memantau penggunaan listrik prabayar (token PLN) secara otomatis dan visual. Semua data tersimpan aman dalam file lokal `data_listrik.csv` tanpa bergantung pada server pihak ketiga.

---

## 🌟 Fitur Utama

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
  - Download / Backup database CSV langsung dari web UI.

---

## 🚀 Cara Menjalankan Aplikasi

### Cara 1: Menggunakan `run.bat` (Termudah di Windows)
Cukup **klik dua kali** file `run.bat`. Skrip akan otomatis menginstal library jika belum ada dan langsung membuka dashboard di browser Anda.

### Cara 2: Manual lewat Terminal / CMD / PowerShell
1. Buka Terminal atau Command Prompt di folder ini:
   ```bash
   cd c:\Users\wfvg2\Documents\CODE\listrik
   ```
2. Pasang dependensi yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
3. Jalankan aplikasi Streamlit:
   ```bash
   streamlit run app.py
   ```
4. Buka browser di alamat: `http://localhost:8501`.

---

## 📁 Struktur File

- `app.py` : Kode utama dashboard aplikasi web Streamlit.
- `data_listrik.csv` : File database lokal tempat semua riwayat pencatatan disimpan.
- `requirements.txt` : Daftar library Python (`streamlit`, `pandas`, `plotly`).
- `run.bat` : Launcher 1-klik untuk pengguna Windows.
- `README.md` : Dokumentasi petunjuk penggunaan aplikasi.
