import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import db

# 1. Konfigurasi Halaman Web
st.set_page_config(
    page_title="PLN Electricity Tracker (Multi-User Cloud)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS Modern
st.markdown("""
<style>
    .main-header {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        color: #64748B;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.08);
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .metric-val {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0F172A;
    }
    .metric-desc {
        font-size: 0.8rem;
        color: #2563EB;
        font-weight: 500;
        margin-top: 0.3rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 9999px;
    }
    .badge-success { background-color: #DCFCE7; color: #166534; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-danger  { background-color: #FEE2E2; color: #991B1B; }
    .db-badge {
        font-size: 0.78rem;
        padding: 0.3rem 0.6rem;
        border-radius: 6px;
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        margin-bottom: 0.8rem;
        display: inline-block;
        width: 100%;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 3. Logika Perhitungan Konsumsi Listrik
def calculate_usage(df_input):
    if df_input.empty:
        return df_input
    
    df_calc = df_input.copy().sort_values('tanggal').reset_index(drop=True)
    df_calc['kwh_terpakai'] = 0.0
    
    for i in range(1, len(df_calc)):
        kwh_sebelum = df_calc.loc[i-1, 'kwh_meter']
        kwh_sekarang = df_calc.loc[i, 'kwh_meter']
        isi_token = df_calc.loc[i, 'isi_token_kwh']
        
        # Rumus kWh Terpakai = (Sisa kWh Sebelumnya + Token yang diisi) - Sisa kWh Sekarang
        terpakai = (kwh_sebelum + isi_token) - kwh_sekarang
        df_calc.loc[i, 'kwh_terpakai'] = round(max(0.0, terpakai), 2)
        
    return df_calc

# --- SIDEBAR ---
st.sidebar.markdown("## ⚡ PLN Tracker Cloud")
st.sidebar.caption("Sistem Pelacakan Konsumsi Token Listrik Multi-User")

# Status Database
status_type, status_text = db.get_db_status()
st.sidebar.markdown(f"<div class='db-badge'>{status_text}</div>", unsafe_allow_html=True)

# --- Profil / Pilihan Meteran ---
st.sidebar.markdown("### 🏠 Pilih Meteran / Pengguna")
meter_list = db.get_meter_list()
options = meter_list + ["➕ Tambah Profil Baru"]

if "selected_meter" not in st.session_state or st.session_state["selected_meter"] not in meter_list:
    st.session_state["selected_meter"] = meter_list[0]

selected_option = st.sidebar.selectbox(
    "Profil Meteran Aktif",
    options=options,
    index=meter_list.index(st.session_state["selected_meter"]) if st.session_state["selected_meter"] in meter_list else 0,
    label_visibility="collapsed"
)

if selected_option == "➕ Tambah Profil Baru":
    new_meter_name = st.sidebar.text_input("Nama Meteran / Lokasi Baru", placeholder="Contoh: Kost Kamar 03, Rumah Ortu")
    if st.sidebar.button("✨ Aktifkan Profil Baru", width="stretch"):
        if new_meter_name.strip():
            active_meter = new_meter_name.strip()
            st.session_state["selected_meter"] = active_meter
            st.sidebar.success(f"Profil '{active_meter}' diaktifkan!")
            st.rerun()
        else:
            st.sidebar.warning("Masukkan nama profil terlebih dahulu.")
    active_meter = new_meter_name.strip() if new_meter_name.strip() else "Meteran Baru"
else:
    active_meter = selected_option
    st.session_state["selected_meter"] = active_meter

st.sidebar.markdown("---")

# Load Data untuk Meteran Aktif
df_raw = db.load_data(active_meter)
df = calculate_usage(df_raw)

# Navigasi Menu Sidebar
tab_nav = st.sidebar.radio("Navigasi Sidebar", ["📝 Catat Baru", "⚙️ Kelola Data"], label_visibility="collapsed")

if tab_nav == "📝 Catat Baru":
    st.sidebar.markdown(f"### 📝 Catat Meteran: **{active_meter}**")
    with st.sidebar.form("input_form", clear_on_submit=True):
        now = datetime.now()
        tgl_input = st.date_input("Tanggal Pencatatan", now.date())
        waktu_input = st.time_input("Waktu (Jam:Menit)", now.time())
        
        last_kwh = float(df['kwh_meter'].iloc[-1]) if not df.empty else 20.0
        kwh_input = st.number_input(
            "Sisa kWh di Meteran",
            min_value=0.0,
            value=last_kwh,
            format="%.2f",
            step=0.1,
            help="Masukkan angka sisa kWh yang tertera pada layar meteran fisik Anda."
        )
        
        st.markdown("---")
        st.markdown("**🔋 Isi Ulang Token (Opsional)**")
        st.caption("Isi bagian ini HANYA jika Anda baru saja membeli & memasukkan token baru ke meteran.")
        isi_rp = st.number_input("Nominal Beli (Rp)", min_value=0, step=10000, value=0)
        isi_kwh = st.number_input("Token Didapat (kWh)", min_value=0.0, format="%.2f", step=0.1, value=0.0)
        
        submitted = st.form_submit_button("💾 Simpan Data", width="stretch")
        if submitted:
            dt_combined = datetime.combine(tgl_input, waktu_input)
            success, msg = db.insert_entry(
                meter_id=active_meter,
                tanggal_dt=dt_combined,
                kwh_meter=float(kwh_input),
                isi_token_rp=int(isi_rp),
                isi_token_kwh=float(isi_kwh)
            )
            if success:
                st.sidebar.success(f"✅ {msg}")
                st.rerun()
            else:
                st.sidebar.error(f"❌ {msg}")

else:
    st.sidebar.markdown(f"### ⚙️ Manajemen Data: **{active_meter}**")
    st.sidebar.markdown(f"**Total Baris Data:** {len(df_raw)} entri")
    
    if not df_raw.empty:
        st.sidebar.markdown("#### ↩️ Hapus Entri Terakhir")
        last_row = df_raw.iloc[-1]
        st.sidebar.caption(
            f"Entri terakhir: **{pd.to_datetime(last_row['tanggal']).strftime('%d/%m/%Y %H:%M')}** "
            f"({float(last_row['kwh_meter']):.2f} kWh)"
        )
        if st.sidebar.button("🗑️ Hapus Baris Terakhir", type="secondary", width="stretch"):
            success, msg = db.delete_last_entry(active_meter)
            if success:
                st.sidebar.success(msg)
                st.rerun()
            else:
                st.sidebar.error(msg)

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 📥 Unduh / Backup CSV")
    if not df_raw.empty:
        csv_bytes = db.export_meter_csv(active_meter)
        safe_meter_filename = "".join(c for c in active_meter if c.isalnum() or c in (' ', '_', '-')).rstrip()
        st.sidebar.download_button(
            label=f"⬇️ Download CSV ({active_meter})",
            data=csv_bytes,
            file_name=f"pln_{safe_meter_filename}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            width="stretch"
        )


# --- DASHBOARD UTAMA ---
st.markdown(f"<h1 class='main-header'>⚡ Dashboard Listrik: <span style='color:#2563EB;'>{active_meter}</span></h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Aplikasi pelacakan konsumsi listrik prabayar, efisiensi harian, dan riwayat token berbasis cloud.</p>", unsafe_allow_html=True)

if not df.empty:
    sisa_kwh_terakhir = df['kwh_meter'].iloc[-1]
    total_pemakaian = df['kwh_terpakai'].sum()
    total_beli_rp = df['isi_token_rp'].sum()
    total_token_kwh = df['isi_token_kwh'].sum()
    
    # Hitung rata-rata pemakaian
    rata_harian = 0.0
    estimasi_hari_sisa = 0.0
    
    if len(df) > 1:
        selisih_detik = (df['tanggal'].iloc[-1] - df['tanggal'].iloc[0]).total_seconds()
        durasi_hari = max(selisih_detik / 86400.0, 0.04) # minimal ~1 jam
        rata_harian = total_pemakaian / durasi_hari
        if rata_harian > 0:
            estimasi_hari_sisa = sisa_kwh_terakhir / rata_harian
            
    # Estimasi harga rata-rata per kWh
    harga_per_kwh = (total_beli_rp / total_token_kwh) if total_token_kwh > 0 else 1444.70
    estimasi_biaya_harian = rata_harian * harga_per_kwh

    # Status Badge Meteran
    if sisa_kwh_terakhir > 20:
        badge_html = "<span class='badge badge-success'>🟢 Status: Kondisi Aman</span>"
    elif sisa_kwh_terakhir >= 10:
        badge_html = "<span class='badge badge-warning'>🟡 Status: Perlu Perhatian</span>"
    else:
        badge_html = "<span class='badge badge-danger'>🔴 Status: Segera Isi Token!</span>"

    st.markdown(f"Status Meteran: &nbsp; {badge_html}", unsafe_allow_html=True)
    st.write("")

    # Kartu Metrik Ringkasan
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">🔋 Sisa Meteran</div>
            <div class="metric-val">{sisa_kwh_terakhir:.2f} <span style="font-size:1rem; font-weight:600;">kWh</span></div>
            <div class="metric-desc">Estimasi: ~{estimasi_hari_sisa:.1f} hari lagi</div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">📉 Total Pemakaian</div>
            <div class="metric-val">{total_pemakaian:.2f} <span style="font-size:1rem; font-weight:600;">kWh</span></div>
            <div class="metric-desc">Dari {len(df)} kali pencatatan</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">📊 Rata-rata / Hari</div>
            <div class="metric-val">{rata_harian:.2f} <span style="font-size:1rem; font-weight:600;">kWh</span></div>
            <div class="metric-desc">~ Rp {estimasi_biaya_harian:,.0f} / hari</div>
        </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">💸 Total Pembelian</div>
            <div class="metric-val"><span style="font-size:1rem; font-weight:600;">Rp</span> {total_beli_rp:,.0f}</div>
            <div class="metric-desc">{total_token_kwh:.1f} kWh total dibeli</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs Grafik Visualisasi
    tab_grafik1, tab_grafik2 = st.tabs(["📊 Analitik Konsumsi & Tren", "📅 Agregasi per Hari"])

    with tab_grafik1:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("#### ⚡ Pemakaian Listrik per Sesi (kWh)")
            if len(df) > 1:
                df_bar = df.iloc[1:].copy()
                df_bar['waktu_str'] = df_bar['tanggal'].dt.strftime('%d/%m %H:%M')
                
                fig1 = px.bar(
                    df_bar,
                    x='waktu_str',
                    y='kwh_terpakai',
                    text='kwh_terpakai',
                    labels={'kwh_terpakai': 'kWh Terpakai', 'waktu_str': 'Waktu Sesi'},
                    color='kwh_terpakai',
                    color_continuous_scale='Oranges'
                )
                fig1.update_traces(
                    texttemplate='%{text:.2f}',
                    textposition='outside',
                    hovertemplate='<b>Waktu:</b> %{x}<br><b>Pemakaian:</b> %{y:.2f} kWh<extra></extra>'
                )
                fig1.update_layout(
                    height=360,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False,
                    coloraxis_showscale=False,
                    plot_bgcolor='#FAFAFA',
                    yaxis=dict(title='kWh Terpakai', showgrid=True, gridcolor='#E2E8F0'),
                    xaxis=dict(title='Waktu Pencatatan')
                )
                st.plotly_chart(fig1, width="stretch")
            else:
                st.info("ℹ️ Butuh minimal 2 pencatatan untuk menghitung konsumsi listrik antar waktu.")

        with col_g2:
            st.markdown("#### 📈 Tren Sisa Meteran & Pengisian Token")
            df_line = df.copy()
            df_line['waktu_str'] = df_line['tanggal'].dt.strftime('%d/%m %H:%M')
            
            fig2 = go.Figure()
            # Garis Sisa Meteran
            fig2.add_trace(go.Scatter(
                x=df_line['waktu_str'],
                y=df_line['kwh_meter'],
                mode='lines+markers',
                name='Sisa di Meteran (kWh)',
                line=dict(color='#2563EB', width=3),
                marker=dict(size=7, color='#1D4ED8'),
                hovertemplate='<b>Waktu:</b> %{x}<br><b>Sisa kWh:</b> %{y:.2f}<extra></extra>'
            ))
            
            # Marker Pengisian Token
            isi_df = df_line[df_line['isi_token_kwh'] > 0]
            if not isi_df.empty:
                fig2.add_trace(go.Scatter(
                    x=isi_df['waktu_str'],
                    y=isi_df['kwh_meter'],
                    mode='markers+text',
                    name='Pengisian Token',
                    text=[f"+{k:.1f} kWh" for k in isi_df['isi_token_kwh']],
                    textposition='top center',
                    marker=dict(color='#16A34A', size=14, symbol='star'),
                    hovertemplate='<b>Isi Token:</b> +%{text}<br><b>Nominal:</b> Rp %{customdata:,.0f}<extra></extra>',
                    customdata=isi_df['isi_token_rp']
                ))
            
            fig2.update_layout(
                height=360,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor='#FAFAFA',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title='Sisa Meteran (kWh)', showgrid=True, gridcolor='#E2E8F0'),
                xaxis=dict(title='Waktu Pencatatan')
            )
            st.plotly_chart(fig2, width="stretch")

    with tab_grafik2:
        df_daily = df.copy()
        df_daily['tgl_hari'] = df_daily['tanggal'].dt.date
        summary_hari = df_daily.groupby('tgl_hari').agg(
            total_kwh=('kwh_terpakai', 'sum'),
            total_rp=('isi_token_rp', 'sum'),
            total_token_kwh=('isi_token_kwh', 'sum'),
            kali_catat=('kwh_meter', 'count')
        ).reset_index()

        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            fig3 = px.bar(
                summary_hari,
                x='tgl_hari',
                y='total_kwh',
                text='total_kwh',
                labels={'tgl_hari': 'Tanggal', 'total_kwh': 'Total Konsumsi (kWh)'},
                color_discrete_sequence=['#3B82F6']
            )
            fig3.update_traces(texttemplate='%{text:.2f} kWh', textposition='outside')
            fig3.update_layout(
                height=340,
                margin=dict(l=20, r=20, t=20, b=20),
                plot_bgcolor='#FAFAFA',
                yaxis=dict(showgrid=True, gridcolor='#E2E8F0')
            )
            st.plotly_chart(fig3, width="stretch")
            
        with col_d2:
            st.markdown("##### 📌 Rangkuman Periode:")
            st.markdown(f"- **Jumlah Hari Terdata:** {len(summary_hari)} hari")
            st.markdown(f"- **Rata-rata Pemakaian:** {rata_harian:.2f} kWh/hari")
            st.markdown(f"- **Estimasi Pengeluaran:** ~Rp {estimasi_biaya_harian:,.0f}/hari")
            st.markdown(f"- **Ketahanan Kuota Saat Ini:** ~{estimasi_hari_sisa:.1f} hari lagi")

    st.markdown("---")

    # Tabel Data Terstruktur
    st.subheader(f"📋 Riwayat Database ({active_meter})")
    
    view_df = df.copy().sort_values('tanggal', ascending=False).reset_index(drop=True)
    view_df['Waktu'] = view_df['tanggal'].dt.strftime('%d/%m/%Y %H:%M')
    view_df['Sisa Meteran (kWh)'] = view_df['kwh_meter'].map('{:.2f}'.format)
    view_df['kWh Terpakai'] = view_df['kwh_terpakai'].map('{:.2f}'.format)
    view_df['Beli Token (Rp)'] = view_df['isi_token_rp'].apply(lambda x: f"Rp {x:,.0f}" if x > 0 else "-")
    view_df['Token Masuk (kWh)'] = view_df['isi_token_kwh'].apply(lambda x: f"{x:.2f}" if x > 0 else "-")
    
    st.dataframe(
        view_df[['Waktu', 'Sisa Meteran (kWh)', 'kWh Terpakai', 'Beli Token (Rp)', 'Token Masuk (kWh)']],
        width="stretch",
        hide_index=True
    )

else:
    st.info(f"👋 **Selamat datang di profil '{active_meter}'!** Belum ada data pencatatan untuk meteran ini. Silakan masukkan data pertama Anda pada form di sidebar sebelah kiri.")
