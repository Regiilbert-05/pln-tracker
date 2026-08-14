import os
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# 1. Konfigurasi Halaman Web (WAJIB pertama)
st.set_page_config(
    page_title="PLN Electricity Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Pastikan direktori root masuk ke sys.path
CURRENT_DIR = str(Path(__file__).parent.resolve())
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import importlib
import db
importlib.reload(db)

# 2. Custom CSS Modern (Harmonis Penuh Light & Dark Mode via Streamlit Theme Variables)
st.markdown("""
<style>
    /* Hilangkan spasi berlebih di atas halaman */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Typography & Header */
    .app-title {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        font-weight: 800;
        font-size: 1.85rem;
        letter-spacing: -0.02em;
        color: var(--text-color) !important;
        margin-bottom: 0.1rem;
    }
    .app-subtitle {
        color: var(--text-color) !important;
        opacity: 0.75;
        font-size: 0.95rem;
        margin-bottom: 1.2rem;
    }
    
    /* Top Header Bar Container */
    .top-header-box {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Form & Card Containers */
    .form-card {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 14px;
        padding: 1.5rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
    }
    .card-header-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-color) !important;
        margin-bottom: 0.4rem;
    }
    .card-header-subtitle {
        font-size: 0.85rem;
        color: var(--text-color) !important;
        opacity: 0.75;
        margin-bottom: 1.2rem;
    }
    
    /* Metric Cards */
    .metric-box {
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25) !important;
        border-radius: 14px;
        padding: 1.2rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12);
    }
    .metric-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--text-color) !important;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .metric-val {
        font-size: 1.7rem;
        font-weight: 800;
        color: var(--text-color) !important;
    }
    .metric-desc {
        font-size: 0.82rem;
        color: #3B82F6 !important;
        font-weight: 600;
        margin-top: 0.3rem;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.3rem 0.85rem;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 9999px;
    }
    .badge-success { background-color: rgba(34, 197, 94, 0.15); color: #22C55E !important; border: 1px solid rgba(34, 197, 94, 0.35); }
    .badge-warning { background-color: rgba(234, 179, 8, 0.15); color: #EAB308 !important; border: 1px solid rgba(234, 179, 8, 0.35); }
    .badge-danger  { background-color: rgba(239, 68, 68, 0.15); color: #EF4444 !important; border: 1px solid rgba(239, 68, 68, 0.35); }
    
    /* Database Status Pill */
    .db-pill {
        font-size: 0.78rem;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        text-align: center;
    }
    .db-pill-mongo {
        background-color: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.4);
        color: #22C55E !important;
    }
    .db-pill-csv {
        background-color: rgba(234, 179, 8, 0.15);
        border: 1px solid rgba(234, 179, 8, 0.4);
        color: #EAB308 !important;
    }
    .db-pill-error {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #EF4444 !important;
    }

    /* Tab Header Enhancement */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: var(--secondary-background-color) !important;
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-bottom: none;
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        color: var(--text-color) !important;
        opacity: 0.75;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-color: #2563EB !important;
        opacity: 1.0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Injeksi JavaScript untuk Mouse Hover Scroll Wheel Override pada input angka, jam, menit, dan sisa kWh
wheel_js_code = """
<script>
(function() {
    try {
        const parentDoc = window.parent ? window.parent.document : document;
        const parentWin = window.parent || window;

        if (parentWin.__wheelOverrideInitialized) return;
        parentWin.__wheelOverrideInitialized = true;

        parentDoc.addEventListener('wheel', function(e) {
            const container = e.target.closest('div[data-testid="stNumberInput"]');
            if (!container) return;

            const input = container.querySelector('input');
            if (!input) return;

            e.preventDefault();
            e.stopPropagation();

            let currentVal = parseFloat(input.value);
            if (isNaN(currentVal)) currentVal = 0;

            let stepAttr = input.getAttribute('step');
            let step = stepAttr ? parseFloat(stepAttr) : (input.value.includes('.') ? 0.1 : 1.0);
            if (isNaN(step) || step <= 0) step = 1.0;

            let minAttr = input.getAttribute('min');
            let maxAttr = input.getAttribute('max');
            let min = minAttr !== null ? parseFloat(minAttr) : null;
            let max = maxAttr !== null ? parseFloat(maxAttr) : null;

            // Scroll Up = Tambah (+), Scroll Down = Kurang (-)
            let delta = e.deltaY < 0 ? step : -step;
            
            let decimals = 0;
            if (step.toString().includes('.')) {
                decimals = step.toString().split('.')[1].length;
            } else if (input.value.includes('.')) {
                decimals = input.value.split('.')[1].length;
            }
            
            let newVal = parseFloat((currentVal + delta).toFixed(Math.max(decimals, 0)));

            if (min !== null && newVal < min) newVal = min;
            if (max !== null && newVal > max) newVal = max;

            // Fokus, set value, dan dispatch event komplit agar langsung ter-commit ke backend Streamlit
            try { input.focus(); } catch(e) {}
            
            const nativeSetter = Object.getOwnPropertyDescriptor(parentWin.HTMLInputElement.prototype, 'value').set;
            nativeSetter.call(input, newVal);

            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Simulasi Enter key & Blur agar Streamlit widget manager langsung mengirim nilai baru ke Python
            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));
        }, { passive: false });
    } catch (err) {}
})();
</script>
"""

if hasattr(st, "iframe"):
    st.iframe(wheel_js_code, height=1)
else:
    components.html(wheel_js_code, height=0, width=0)

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


# ==========================================
# 4. TOP APP BAR & METER PROFILE SELECTOR
# ==========================================

status_type, status_text = db.get_db_status()
meter_list = db.get_meter_list()

# Sinkronisasi parameter URL
query_meter = st.query_params.get("meter", None)
if query_meter and query_meter in meter_list:
    current_meter = query_meter
elif "selected_meter" in st.session_state and st.session_state["selected_meter"] in meter_list:
    current_meter = st.session_state["selected_meter"]
else:
    current_meter = meter_list[0]

# Tampilan Header Atas
header_col1, header_col2 = st.columns([3, 2], vertical_alignment="center")

with header_col1:
    st.markdown("<h1 class='app-title'>⚡ PLN Electricity Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p class='app-subtitle'>Sistem Pemantauan Konsumsi Listrik & Token Mandiri</p>", unsafe_allow_html=True)

with header_col2:
    h_sub1, h_sub2 = st.columns([2, 1], vertical_alignment="center")
    with h_sub1:
        # Dropdown Pemilih Profil Meteran
        selected_meter = st.selectbox(
            "Profil Meteran",
            options=meter_list,
            index=meter_list.index(current_meter) if current_meter in meter_list else 0,
            label_visibility="collapsed"
        )
        if selected_meter != current_meter:
            st.session_state["selected_meter"] = selected_meter
            st.query_params["meter"] = selected_meter
            st.rerun()
            
    with h_sub2:
        # Popover / Dialog Tambah Profil Baru
        with st.popover("➕ Tambah", use_container_width=True):
            st.markdown("##### ➕ Profil Meteran Baru")
            new_meter_input = st.text_input("Nama Profil", placeholder="Misal: Kost 03, Toko").strip()
            if st.button("Simpan Profil", type="primary", use_container_width=True):
                if new_meter_input:
                    ok, msg = db.register_meter(new_meter_input)
                    if ok:
                        st.session_state["selected_meter"] = new_meter_input
                        st.query_params["meter"] = new_meter_input
                        st.success(f"Profil '{new_meter_input}' berhasil dibuat!")
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Nama profil tidak boleh kosong.")

active_meter = selected_meter

# Baris Status & Lokasi Aktif
status_col1, status_col2 = st.columns([3, 1], vertical_alignment="center")
with status_col1:
    st.markdown(f"📍 Profil Aktif: **{active_meter}**")
with status_col2:
    st.markdown(f"<div style='text-align:right;'><span class='db-pill db-pill-{status_type}'>{status_text}</span></div>", unsafe_allow_html=True)

st.write("")

# Memuat Data Meteran Aktif
df_raw = db.load_data(active_meter)
df = calculate_usage(df_raw)


# ==========================================
# 5. TABS NAVIGASI UTAMA (DASHBOARD, CATAT, RIWAYAT)
# ==========================================

tab_dash, tab_input, tab_history = st.tabs([
    "📊 Dashboard & Analisis",
    "📝 Catat Meteran Baru",
    "📋 Riwayat & Kelola Data"
])


# ----------------------------------------------------
# TAB 1: DASHBOARD & ANALISIS
# ----------------------------------------------------
with tab_dash:
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

        # Status Meteran
        if sisa_kwh_terakhir > 20:
            badge_html = "<span class='badge badge-success'>🟢 Kondisi Aman</span>"
        elif sisa_kwh_terakhir >= 10:
            badge_html = "<span class='badge badge-warning'>🟡 Perlu Perhatian</span>"
        else:
            badge_html = "<span class='badge badge-danger'>🔴 Segera Isi Token!</span>"

        # Banner Ringkasan Status
        status_bar_c1, status_bar_c2 = st.columns([3, 1], vertical_alignment="center")
        with status_bar_c1:
            st.markdown(f"**Status Kuota Saat Ini:** &nbsp; {badge_html} &nbsp; • &nbsp; Terakhir dicatat: **{df['tanggal'].iloc[-1].strftime('%d/%m/%Y %H:%M')}**", unsafe_allow_html=True)
        with status_bar_c2:
            st.markdown(f"<div style='text-align:right; color: var(--text-color); opacity: 0.8;'>Estimasi: ~<b>{estimasi_hari_sisa:.1f} hari lagi</b></div>", unsafe_allow_html=True)

        st.write("")

        # 4 Kartu Metrik Utama
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">🔋 Sisa di Meteran</div>
                <div class="metric-val">{sisa_kwh_terakhir:.2f} <span style="font-size:1rem; font-weight:600;">kWh</span></div>
                <div class="metric-desc">Ketahanan: ~{estimasi_hari_sisa:.1f} hari</div>
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

        # Visualisasi Grafik Interaktif
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("##### ⚡ Pemakaian Listrik per Sesi (kWh)")
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
                    height=350,
                    margin=dict(l=10, r=10, t=15, b=10),
                    showlegend=False,
                    coloraxis_showscale=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis=dict(title='kWh Terpakai', showgrid=True, gridcolor='rgba(148, 163, 184, 0.2)'),
                    xaxis=dict(title=None, showgrid=False)
                )
                st.plotly_chart(fig1, width="stretch")
            else:
                st.info("ℹ️ Butuh minimal 2 pencatatan untuk menghitung konsumsi listrik per sesi.")

        with col_g2:
            st.markdown("##### 📈 Tren Sisa Meteran & Pengisian Token")
            df_line = df.copy()
            df_line['waktu_str'] = df_line['tanggal'].dt.strftime('%d/%m %H:%M')
            
            fig2 = go.Figure()
            # Garis Sisa Meteran
            fig2.add_trace(go.Scatter(
                x=df_line['waktu_str'],
                y=df_line['kwh_meter'],
                mode='lines+markers',
                name='Sisa kWh',
                line=dict(color='#2563EB', width=3),
                marker=dict(size=7, color='#1D4ED8'),
                hovertemplate='<b>Waktu:</b> %{x}<br><b>Sisa:</b> %{y:.2f} kWh<extra></extra>'
            ))
            
            # Marker Pengisian Token
            isi_df = df_line[df_line['isi_token_kwh'] > 0]
            if not isi_df.empty:
                fig2.add_trace(go.Scatter(
                    x=isi_df['waktu_str'],
                    y=isi_df['kwh_meter'],
                    mode='markers+text',
                    name='Isi Token',
                    text=[f"+{k:.1f} kWh" for k in isi_df['isi_token_kwh']],
                    textposition='top center',
                    marker=dict(color='#16A34A', size=13, symbol='star'),
                    hovertemplate='<b>Token:</b> +%{text}<br><b>Nominal:</b> Rp %{customdata:,.0f}<extra></extra>',
                    customdata=isi_df['isi_token_rp']
                ))
            
            fig2.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=15, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                yaxis=dict(title='Sisa Meteran (kWh)', showgrid=True, gridcolor='rgba(148, 163, 184, 0.2)'),
                xaxis=dict(title=None, showgrid=False)
            )
            st.plotly_chart(fig2, width="stretch")

        # Agregasi Pemakaian Harian
        st.markdown("---")
        st.markdown("##### 📅 Total Konsumsi Listrik per Hari Kalender")
        df_daily = df.copy()
        df_daily['tgl_hari'] = df_daily['tanggal'].dt.date
        summary_hari = df_daily.groupby('tgl_hari').agg(
            total_kwh=('kwh_terpakai', 'sum'),
            total_rp=('isi_token_rp', 'sum'),
            total_token_kwh=('isi_token_kwh', 'sum'),
            kali_catat=('kwh_meter', 'count')
        ).reset_index()

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
            height=280,
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.2)'),
            xaxis=dict(title=None)
        )
        st.plotly_chart(fig3, width="stretch")

    else:
        st.info(f"👋 **Selamat datang di profil '{active_meter}'!** Belum ada catatan meteran. Buka tab **📝 Catat Meteran Baru** di atas untuk memasukkan data pertama Anda.")


# ----------------------------------------------------
# TAB 2: CATAT METERAN BARU (FORM UTAMA)
# ----------------------------------------------------
with tab_input:
    st.markdown("### 📝 Formulir Pencatatan Meteran")
    st.caption(f"Menyimpan data pencatatan untuk profil meteran: **{active_meter}**")

    # Banner Info Pencatatan Sebelumnya
    if not df.empty:
        last_row = df.iloc[-1]
        last_time_str = pd.to_datetime(last_row['tanggal']).strftime('%d/%m/%Y %H:%M')
        last_kwh_val = float(last_row['kwh_meter'])
        st.info(f"📌 **Pencatatan Terakhir:** {last_time_str} &nbsp; | &nbsp; **Sisa Meteran Terakhir:** **{last_kwh_val:.2f} kWh**")
    else:
        last_kwh_val = 20.0
        st.info("📌 Masukkan angka sisa kWh yang sedang tertera pada layar meteran fisik Anda.")

    # 1. Waktu Pencatatan (2-in-1 Pop-up Picker: Otomatis Collapse saat Klik Luar)
    st.markdown("##### 📅 1. Waktu Pencatatan")
    
    if "input_datetime" not in st.session_state:
        st.session_state["input_datetime"] = datetime.now()
        
    dt_current = st.session_state["input_datetime"]
    dt_formatted = dt_current.strftime('%d/%m/%Y — %H:%M WIB')

    col_btn, col_info = st.columns([1.6, 2.4], vertical_alignment="center")
    
    with col_btn:
        with st.popover(f"🗓️ {dt_formatted}", use_container_width=True):
            st.markdown("###### 🕒 Atur Tanggal & Jam")
            
            # Preset Cepat
            st.caption("Pilihan Cepat:")
            p_c1, p_c2, p_c3, p_c4 = st.columns(4)
            with p_c1:
                if st.button("🕒 Sekarang", use_container_width=True):
                    st.session_state["input_datetime"] = datetime.now()
                    st.rerun()
            with p_c2:
                if st.button("🌅 08:00", use_container_width=True):
                    st.session_state["input_datetime"] = dt_current.replace(hour=8, minute=0)
                    st.rerun()
            with p_c3:
                if st.button("☀️ 13:00", use_container_width=True):
                    st.session_state["input_datetime"] = dt_current.replace(hour=13, minute=0)
                    st.rerun()
            with p_c4:
                if st.button("🌙 21:00", use_container_width=True):
                    st.session_state["input_datetime"] = dt_current.replace(hour=21, minute=0)
                    st.rerun()
                    
            st.markdown("---")
            
            # Pemilih Kalender Tanggal
            tgl_pick = st.date_input("Tanggal", value=dt_current.date())
            
            # Pemilih Jam & Menit (Scroll Wheel & Stepper +/- Ready)
            cj, cm = st.columns(2)
            with cj:
                jam_pick = st.number_input("Jam (00 - 23)", min_value=0, max_value=23, value=dt_current.hour, step=1, format="%02d", help="Hover mouse lalu scroll roda mouse untuk mengganti jam")
            with cm:
                menit_pick = st.number_input("Menit (00 - 59)", min_value=0, max_value=59, value=dt_current.minute, step=1, format="%02d", help="Hover mouse lalu scroll roda mouse untuk mengganti menit")
                
            new_dt = datetime(tgl_pick.year, tgl_pick.month, tgl_pick.day, int(jam_pick), int(menit_pick))
            if new_dt != dt_current:
                st.session_state["input_datetime"] = new_dt
                st.rerun()
                
    with col_info:
        st.caption("👈 *Klik tombol waktu untuk ubah kalender/jam. Hover mouse & scroll roda untuk ubah jam/menit.*")

    waktu_terpilih = st.session_state["input_datetime"]
    st.markdown("---")

    # 2. Input Sisa Meteran Fisik & Token
    col_in1, col_in2 = st.columns(2, gap="large")

    with col_in1:
        st.markdown("##### 📟 2. Sisa kWh di Meteran Fisik")
        kwh_input = st.number_input(
            "Angka pada Layar LCD Meteran (kWh)",
            min_value=0.0,
            value=last_kwh_val,
            format="%.2f",
            step=0.1,
            help="Hover mouse di kotak ini dan scroll roda mouse untuk menaikkan/menurunkan angka secara cepat"
        )
        
        # Live Preview Perhitungan Konsumsi
        if not df.empty:
            delta_kwh = last_kwh_val - kwh_input
            if delta_kwh >= 0:
                st.caption(f"💡 *Estimasi Terpakai Sesi Ini:* **~{delta_kwh:.2f} kWh**")
            else:
                st.caption(f"💡 *Sisa meteran bertambah (+{abs(delta_kwh):.2f} kWh). Jangan lupa isi data token di sebelah kanan jika baru beli token.*")

    with col_in2:
        st.markdown("##### 🔋 3. Pembelian Token (Opsional)")
        ada_isi_token = st.checkbox("➕ Baru saja membeli & mengisi token listrik?", value=False)
        
        if ada_isi_token:
            sub_tok1, sub_tok2 = st.columns(2)
            with sub_tok1:
                isi_rp = st.number_input("Nominal Beli (Rp)", min_value=0, step=10000, value=50000)
            with sub_tok2:
                isi_kwh = st.number_input("Token Masuk (kWh)", min_value=0.0, format="%.2f", step=0.1, value=34.0)
        else:
            isi_rp = 0
            isi_kwh = 0.0
            st.caption("Biarkan tidak tercentang jika pencatatan ini hanya pengecekan sisa kuota biasa.")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 Simpan Data Pencatatan", type="primary", use_container_width=True):
        ok, msg = db.insert_entry(
            meter_id=active_meter,
            tanggal_dt=waktu_terpilih,
            kwh_meter=float(kwh_input),
            isi_token_rp=int(isi_rp),
            isi_token_kwh=float(isi_kwh)
        )
        if ok:
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.error(f"❌ {msg}")


# ----------------------------------------------------
# TAB 3: RIWAYAT & KELOLA DATA
# ----------------------------------------------------
with tab_history:
    st.markdown("### 📋 Riwayat Database & Manajemen Data")
    st.caption(f"Total baris data terdata: **{len(df_raw)} entri** pada profil **{active_meter}**")

    # Toolbar Aksi Atas
    tool_c1, tool_c2 = st.columns([2.5, 1.5], vertical_alignment="center")

    with tool_c1:
        if not df_raw.empty:
            csv_bytes = db.export_meter_csv(active_meter)
            safe_filename = "".join(c for c in active_meter if c.isalnum() or c in (' ', '_', '-')).rstrip()
            st.download_button(
                label=f"⬇️ Unduh Backup CSV ({len(df_raw)} Baris)",
                data=csv_bytes,
                file_name=f"pln_{safe_filename}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    with tool_c2:
        if active_meter != db.DEFAULT_METER:
            with st.popover("🚨 Hapus Profil Ini", use_container_width=True):
                st.markdown(f"⚠️ Yakin ingin menghapus profil **'{active_meter}'** dan seluruh riwayatnya?")
                if st.button("Hapus Permanen", type="primary", use_container_width=True):
                    ok, msg = db.delete_meter_profile(active_meter)
                    if ok:
                        st.session_state["selected_meter"] = db.DEFAULT_METER
                        st.query_params["meter"] = db.DEFAULT_METER
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.markdown("---")

    # Daftar Riwayat Data dengan Tombol Hapus per Baris
    if not df.empty:
        view_df = df.copy().sort_values('tanggal', ascending=False).reset_index(drop=True)
        view_df['tanggal_raw'] = view_df['tanggal'].dt.strftime('%Y-%m-%d %H:%M')
        view_df['Waktu'] = view_df['tanggal'].dt.strftime('%d/%m/%Y %H:%M')
        
        # Banner Konfirmasi Hapus (Otomatis Collapse setelah Hapus/Batal)
        if "delete_target_item" in st.session_state and st.session_state["delete_target_item"]:
            target = st.session_state["delete_target_item"]
            st.warning(f"⚠️ **Konfirmasi Penghapusan:** Yakin ingin menghapus data tanggal **{target['waktu']}** (Sisa: {target['kwh']:.2f} kWh)?")
            conf_c1, conf_c2, _ = st.columns([1.8, 1.5, 5])
            with conf_c1:
                if st.button("🗑️ Ya, Hapus Sekarang", type="primary", use_container_width=True):
                    ok, msg = db.delete_specific_entry(active_meter, target['tanggal_raw'])
                    st.session_state["delete_target_item"] = None
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
            with conf_c2:
                if st.button("❌ Batal", use_container_width=True):
                    st.session_state["delete_target_item"] = None
                    st.rerun()
            st.markdown("<br>", unsafe_allow_html=True)

        # Header Kolom Tabel
        h1, h2, h3, h4, h5, h6 = st.columns([2.4, 1.8, 1.8, 2.0, 1.8, 1.2], vertical_alignment="center")
        with h1: st.markdown("**📅 Waktu**")
        with h2: st.markdown("**🔋 Sisa (kWh)**")
        with h3: st.markdown("**📉 Terpakai**")
        with h4: st.markdown("**💸 Beli Token**")
        with h5: st.markdown("**⚡ Token Masuk**")
        with h6: st.markdown("**🗑️ Aksi**")
        
        st.markdown("<hr style='margin: 0.2rem 0 0.6rem 0; border: none; border-top: 1.5px solid rgba(148,163,184,0.3);'>", unsafe_allow_html=True)
        
        # Baris per Baris Data
        for idx, row in view_df.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([2.4, 1.8, 1.8, 2.0, 1.8, 1.2], vertical_alignment="center")
            
            beli_str = f"Rp {int(row['isi_token_rp']):,}" if row['isi_token_rp'] > 0 else "-"
            token_str = f"{row['isi_token_kwh']:.2f} kWh" if row['isi_token_kwh'] > 0 else "-"
            
            with c1: st.markdown(f"**{row['Waktu']}**")
            with c2: st.markdown(f"{row['kwh_meter']:.2f} kWh")
            with c3: st.markdown(f"{row['kwh_terpakai']:.2f} kWh")
            with c4: st.markdown(beli_str)
            with c5: st.markdown(token_str)
            with c6:
                if st.button("🗑️", key=f"btn_del_{idx}", help=f"Hapus catatan {row['Waktu']}"):
                    st.session_state["delete_target_item"] = {
                        "tanggal_raw": row['tanggal_raw'],
                        "waktu": row['Waktu'],
                        "kwh": row['kwh_meter']
                    }
                    st.rerun()
            
            st.markdown("<hr style='margin: 0.15rem 0; border: none; border-top: 1px dashed rgba(148,163,184,0.2);'>", unsafe_allow_html=True)
    else:
        st.info("Belum ada riwayat pencatatan pada profil ini.")
