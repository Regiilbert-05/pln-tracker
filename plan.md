```python
import zipfile
import os
import pandas as pd

# 1. Create a template CSV database
df = pd.DataFrame({
    'tanggal': ['2026-08-14 08:00', '2026-08-14 20:00', '2026-08-15 08:00'],
    'kwh_meter': [26.15, 24.13, 53.50],
    'isi_token_rp': [0, 0, 50000],
    'isi_token_kwh': [0, 0, 34.5]
})
df.to_csv('data_listrik.csv', index=False)

# 2. Create the Streamlit Web App code
app_code = """
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

st.set_page_config(page_title="PLN Tracker Dashboard", layout="wide")
st.title("⚡ Dashboard Tracker Listrik Prabayar")
st.markdown("Dashboard web lokal untuk memonitor konsumsi listrik harian dan isi ulang token.")

DATA_FILE = 'data_listrik.csv'

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['tanggal'] = pd.to_datetime(df['tanggal'])
        df = df.sort_values('tanggal').reset_index(drop=True)
        return df
    return pd.DataFrame(columns=['tanggal', 'kwh_meter', 'isi_token_rp', 'isi_token_kwh'])

df = load_data()

# --- SIDEBAR: FORM INPUT ---
st.sidebar.header("📝 Catat Meteran Baru")
with st.sidebar.form("input_form", clear_on_submit=True):
    tgl_input = st.date_input("Tanggal", datetime.today())
    waktu_input = st.time_input("Waktu", datetime.now().time())
    kwh_input = st.number_input("Sisa kWh di Meteran", min_value=0.0, format="%.2f", step=0.1)
    
    st.markdown("---")
    st.markdown("**Isi Ulang Token (Opsional)**")
    isi_rp = st.number_input("Nominal Beli (Rp)", min_value=0, step=10000)
    isi_kwh = st.number_input("Token Didapat (kWh)", min_value=0.0, format="%.2f", step=0.1)
    
    submitted = st.form_submit_button("Simpan Data")
    if submitted:
        dt_str = datetime.combine(tgl_input, waktu_input).strftime('%Y-%m-%d %H:%M:%S')
        new_data = pd.DataFrame({
            'tanggal': [dt_str], 
            'kwh_meter': [kwh_input],
            'isi_token_rp': [isi_rp], 
            'isi_token_kwh': [isi_kwh]
        })
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("✅ Data berhasil disimpan!")
        df = load_data() # Reload data

# --- MAIN DASHBOARD ---
if not df.empty:
    # Kalkulasi Konsumsi
    df['kwh_terpakai'] = 0.0
    for i in range(1, len(df)):
        kwh_sebelum = df.loc[i-1, 'kwh_meter']
        kwh_sekarang = df.loc[i, 'kwh_meter']
        isi_token = df.loc[i, 'isi_token_kwh']
        
        # Rumus: Sisa kemarin + Token masuk - Sisa sekarang
        terpakai = (kwh_sebelum + isi_token) - kwh_sekarang
        df.loc[i, 'kwh_terpakai'] = round(max(0, terpakai), 2)

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔋 Sisa kWh Saat Ini", f"{df['kwh_meter'].iloc[-1]:.2f} kWh")
    col2.metric("📉 Total Pemakaian", f"{df['kwh_terpakai'].sum():.2f} kWh")
    col3.metric("💸 Total Beli Token", f"Rp {df['isi_token_rp'].sum():,}")
    
    # Hitung rata-rata pemakaian harian (estimasi kasar)
    if len(df) > 1:
        selisih_hari = (df['tanggal'].iloc[-1] - df['tanggal'].iloc[0]).total_seconds() / 86400
        rata_harian = df['kwh_terpakai'].sum() / selisih_hari if selisih_hari > 0 else 0
        col4.metric("📊 Rata-rata Pemakaian/Hari", f"{rata_harian:.2f} kWh")

    st.markdown("---")
    
    # Charts Area
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Konsumsi Listrik (kWh) per Pencatatan")
        fig1 = px.bar(df.iloc[1:], x='tanggal', y='kwh_terpakai', text='kwh_terpakai',
                      labels={'kwh_terpakai': 'kWh Dipakai', 'tanggal': 'Waktu'},
                      color_discrete_sequence=['#ff7f0e'])
        fig1.update_traces(textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)
        
    with chart_col2:
        st.subheader("Tren Sisa Meteran & Pengisian")
        fig2 = px.line(df, x='tanggal', y='kwh_meter', markers=True,
                       labels={'kwh_meter': 'Sisa di Meteran (kWh)', 'tanggal': 'Waktu'},
                       color_discrete_sequence=['#1f77b4'])
        # Tambahkan marker khusus untuk saat ada pengisian token
        isi_df = df[df['isi_token_kwh'] > 0]
        if not isi_df.empty:
            fig2.add_scatter(x=isi_df['tanggal'], y=isi_df['kwh_meter'], mode='markers',
                             marker=dict(color='green', size=12, symbol='star'),
                             name='Isi Token')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    # Raw Data Table (Fungsi seperti Sheet)
    st.subheader("📋 Database Mentah (Edit via Excel/CSV)")
    st.dataframe(df.style.format({'kwh_meter': '{:.2f}', 'isi_token_rp': '{:,}', 'isi_token_kwh': '{:.2f}', 'kwh_terpakai': '{:.2f}'}), use_container_width=True)

else:
    st.info("👋 Selamat datang! Belum ada data. Silakan masukkan data meteran pertama Anda di menu samping.")
"""
with open('app.py', 'w') as f:
    f.write(app_code)

# 3. Create Requirements
req_code = "streamlit\npandas\nplotly\n"
with open('requirements.txt', 'w') as f:
    f.write(req_code)

# 4. Create README
readme_code = """# PLN Power Tracker Web App

Aplikasi web lokal (berbasis Python) untuk mencatat dan melacak penggunaan listrik harian secara visual. Data disimpan murni dalam file CSV, sehingga tetap bertindak seperti "Spreadsheet" namun dibalut dengan antarmuka web yang interaktif.

## Cara Instalasi & Menjalankan

1. Pastikan Anda sudah menginstal **Python** di komputer/server Anda.
2. Buka Terminal / CMD di dalam folder ini.
3. Install dependensi yang dibutuhkan dengan perintah:
   ```bash
   pip install -r requirements.txt

```

4. Jalankan server web lokal dengan perintah:
```bash
streamlit run app.py

```


5. Aplikasi akan otomatis terbuka di browser pada alamat `http://localhost:8501`.

## Deployment Lanjutan

Karena ini adalah aplikasi Python standar, Anda bisa dengan mudah membungkusnya menggunakan **Docker** atau menghostingnya di server *cloud* pribadi jika ingin diakses dari luar rumah.
"""
with open('README.md', 'w') as f:
f.write(readme_code)

# 5. Zip everything

zip_filename = "PLN_Tracker_Web.zip"
with zipfile.ZipFile(zip_filename, 'w') as zipf:
zipf.write('app.py')
zipf.write('requirements.txt')
zipf.write('data_listrik.csv')
zipf.write('README.md')

print(f"Zip created successfully: {zip_filename}")

```

```text?code_stdout&code_event_index=1
Zip created successfully: PLN_Tracker_Web.zip


```

Sistem pelacakan web lokal (PLN Tracker) Anda sudah siap:


Ide untuk tidak bergantung pada aplikasi pihak ketiga dan membuat sistem *host* lokal adalah langkah yang sangat tepat, terutama jika komputer Anda memang menyala terus-menerus (*24/7*).

Aplikasi web ini dibangun menggunakan **Streamlit (Python)**. Kelebihannya, aplikasi ini tetap mempertahankan sifat "Spreadsheet" seperti yang Anda mau. Semua basis datanya murni tersimpan dalam file `data_listrik.csv`. Jadi, jika sewaktu-waktu Anda ingin mengolah datanya secara manual di Excel atau Sheets, Anda tinggal membuka file CSV tersebut.

**Fitur di dalam web app ini:**

1. **Form Pencatatan:** Untuk memasukkan tanggal, jam, sisa kWh di meteran, dan riwayat isi token (Rupiah & jumlah kWh).
2. **Kalkulasi Otomatis:** Sistem akan secara otomatis menghitung selisih *kWh yang terpakai* di antara dua waktu pencatatan (memperhitungkan jika ada penambahan token di sela-sela waktu tersebut).
3. **Grafik Analitik:** Menampilkan *Bar Chart* untuk konsumsi listrik per pencatatan, dan *Line Chart* interaktif untuk melacak sisa meteran dengan indikator bintang khusus saat Anda melakukan isi ulang.

**Cara Menjalankan di Komputer Lokal:**

1. Ekstrak file `.zip` tersebut ke dalam sebuah folder baru.
2. Buka terminal/CMD di dalam folder tersebut.
3. Jalankan perintah `pip install -r requirements.txt` untuk menginstal *library* yang dibutuhkan.
4. Ketik perintah `streamlit run app.py`
5. Aplikasi web (*dashboard*) akan otomatis terbuka di browser Anda (biasanya di `http://localhost:8501`).

Jika ke depannya Anda ingin mengisolasi aplikasi ini dari *environment* utama PC, sistem berbasis Python ini juga sangat mudah dibungkus ke dalam *container* Docker. Silakan dicoba, dan beri tahu saya jika Anda butuh modifikasi perhitungan rumusnya!