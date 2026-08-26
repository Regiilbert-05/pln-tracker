import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="PLN Electricity Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CURRENT_DIR = str(Path(__file__).parent.resolve())
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import importlib
import db
importlib.reload(db)
from ui_helper import apply_custom_css, inject_wheel_js, utc_to_local

apply_custom_css()
inject_wheel_js()

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

        # Visualisasi Grafik Interaktif: Grafik Konsumsi Listrik (Dual-Axis)
        st.markdown("##### ⚡ Grafik Konsumsi Listrik")
        st.caption("Grafik garis biru menunjukkan sisa kWh di meteran Anda yang terus menurun, sedangkan garis merah menunjukkan laju tarikan daya (kWh per jam) di rentang waktu tersebut.")

        # Filter Rentang: Keseluruhan atau Per Hari
        f_c1, f_c2, _ = st.columns([1.6, 2.4, 3], vertical_alignment="center")
        with f_c1:
            mode_grafik = st.radio(
                "Filter Tampilan:",
                ["🌐 Keseluruhan", "📅 Per Hari"],
                horizontal=True,
                label_visibility="collapsed"
            )

        if mode_grafik == "📅 Per Hari":
            daftar_tanggal = sorted(df['tanggal'].dt.date.unique(), reverse=True)
            with f_c2:
                pilihan_tanggal = st.selectbox(
                    "Pilih Tanggal:",
                    daftar_tanggal,
                    format_func=lambda d: d.strftime('%A, %d %B %Y'),
                    label_visibility="collapsed"
                )
            
            df_hari_ini = df[df['tanggal'].dt.date == pilihan_tanggal].copy()
            idx_first = df_hari_ini.index[0] if not df_hari_ini.empty else None
            if idx_first is not None and idx_first > 0:
                df_view = df.iloc[idx_first - 1 : df_hari_ini.index[-1] + 1].copy()
            else:
                df_view = df_hari_ini
                
            judul_grafik = f"Grafik Konsumsi Listrik Harian ({pilihan_tanggal.strftime('%d %B %Y')})"
        else:
            df_view = df.copy()
            judul_grafik = "Grafik Konsumsi Listrik (Keseluruhan)"

        if len(df_view) >= 1:
            fig1 = go.Figure()

            # 1. Garis Biru (Sisa Meteran - Sumbu Kiri / yaxis1)
            fig1.add_trace(go.Scatter(
                x=df_view['tanggal'],
                y=df_view['kwh_meter'],
                mode='lines+markers',
                name='Sisa Meteran (kWh)',
                line=dict(color='#1D4ED8', width=3),
                marker=dict(size=7, color='#1D4ED8'),
                yaxis='y1',
                hovertemplate='<b>Waktu:</b> %{x|%d/%m/%Y %H:%M}<br><b>Sisa Meteran:</b> %{y:.2f} kWh<extra></extra>'
            ))

            # 2. Garis Merah (Laju Pemakaian kWh/jam - Sumbu Kanan / yaxis2)
            if len(df_view) > 1:
                x_red = []
                y_red = []
                for i in range(1, len(df_view)):
                    t_start = df_view['tanggal'].iloc[i-1]
                    t_end = df_view['tanggal'].iloc[i]
                    durasi_jam = max((t_end - t_start).total_seconds() / 3600.0, 0.001)
                    kwh_used = max(float(df_view['kwh_terpakai'].iloc[i]), 0.0)
                    rate = kwh_used / durasi_jam
                    
                    x_red.extend([t_start, t_end, None])
                    y_red.extend([rate, rate, None])

                fig1.add_trace(go.Scatter(
                    x=x_red,
                    y=y_red,
                    mode='lines',
                    name='Laju Pemakaian (kWh/jam)',
                    line=dict(color='#DC2626', width=3.5),
                    yaxis='y2',
                    connectgaps=False,
                    hovertemplate='<b>Rentang:</b> %{x|%d/%m/%Y %H:%M}<br><b>Laju Tarikan:</b> %{y:.2f} kWh/jam<extra></extra>'
                ))

            # 3. Marker Bintang Hijau (Pengisian Token)
            isi_df = df_view[df_view['isi_token_kwh'] > 0]
            if not isi_df.empty:
                fig1.add_trace(go.Scatter(
                    x=isi_df['tanggal'],
                    y=isi_df['kwh_meter'],
                    mode='markers+text',
                    name='Isi Token',
                    text=[f"+{k:.1f} kWh" for k in isi_df['isi_token_kwh']],
                    textposition='top center',
                    marker=dict(color='#16A34A', size=13, symbol='star'),
                    yaxis='y1',
                    hovertemplate='<b>Token Masuk:</b> +%{text}<br><b>Nominal:</b> Rp %{customdata:,.0f}<extra></extra>',
                    customdata=isi_df['isi_token_rp']
                ))

            fig1.update_layout(
                title=dict(text=judul_grafik, font=dict(size=14, color='gray'), x=0.01, y=0.98),
                height=380,
                margin=dict(l=10, r=10, t=40, b=15),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(148, 163, 184, 0.15)',
                    tickformat='%d %b\n%H:%M' if mode_grafik == "🌐 Keseluruhan" else '%H:%M'
                ),
                yaxis=dict(
                    title=dict(text='Sisa Meteran (kWh)', font=dict(color='#1D4ED8', size=12)),
                    tickfont=dict(color='#1D4ED8'),
                    showgrid=True,
                    gridcolor='rgba(148, 163, 184, 0.15)'
                ),
                yaxis2=dict(
                    title=dict(text='Laju Pemakaian (kWh/jam)', font=dict(color='#DC2626', size=12)),
                    tickfont=dict(color='#DC2626'),
                    overlaying='y',
                    side='right',
                    showgrid=False,
                    rangemode='tozero'
                )
            )
            st.plotly_chart(fig1, width="stretch")
        else:
            st.info("ℹ️ Belum ada pencatatan pada rentang tanggal yang dipilih.")

        # Agregasi Pemakaian Harian (kWh & Estimasi Rupiah)
        st.markdown("---")
        st.markdown("##### 📅 Total Konsumsi Listrik per Hari Kalender")
        st.caption(f"Kalkulasi pemakaian harian berdasarkan estimasi tarif: **~Rp {harga_per_kwh:,.2f} / kWh**")
        
        df_daily = df.copy()
        df_daily['tgl_hari'] = df_daily['tanggal'].dt.date
        summary_hari = df_daily.groupby('tgl_hari').agg(
            total_kwh=('kwh_terpakai', 'sum'),
            total_rp=('isi_token_rp', 'sum'),
            total_token_kwh=('isi_token_kwh', 'sum'),
            kali_catat=('kwh_meter', 'count')
        ).reset_index()

        summary_hari['estimasi_biaya_rp'] = summary_hari['total_kwh'] * harga_per_kwh
        summary_hari['tgl_str'] = summary_hari['tgl_hari'].apply(lambda x: x.strftime('%d/%m/%Y'))
        summary_hari['label_bar'] = summary_hari.apply(
            lambda r: f"{r['total_kwh']:.2f} kWh<br>(~Rp {r['estimasi_biaya_rp']:,.0f})", axis=1
        )

        fig3 = px.bar(
            summary_hari,
            x='tgl_str',
            y='total_kwh',
            text='label_bar',
            labels={'tgl_str': 'Tanggal', 'total_kwh': 'Total Konsumsi (kWh)'},
            color='estimasi_biaya_rp',
            color_continuous_scale='Blues',
            custom_data=['estimasi_biaya_rp', 'kali_catat', 'total_rp']
        )
        fig3.update_traces(
            textposition='outside',
            hovertemplate='<b>Tanggal:</b> %{x}<br><b>Konsumsi:</b> %{y:.2f} kWh<br><b>Estimasi Biaya:</b> ~Rp %{customdata[0]:,.0f}<br><b>Beli Token:</b> Rp %{customdata[2]:,.0f}<br><b>Jumlah Pencatatan:</b> %{customdata[1]}x<extra></extra>'
        )
        fig3.update_layout(
            height=340,
            margin=dict(l=10, r=10, t=30, b=10),
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.2)', title='Konsumsi (kWh)'),
            xaxis=dict(title=None)
        )
        st.plotly_chart(fig3, width="stretch")

        # Rincian Tabel Harian (Konsumsi kWh & Biaya Rupiah)
        with st.expander("🔍 Lihat Rincian Tabel Harian (kWh & Rupiah)"):
            detail_daily = summary_hari.copy()
            detail_daily['Tanggal'] = detail_daily['tgl_str']
            detail_daily['Total Konsumsi'] = detail_daily['total_kwh'].apply(lambda v: f"{v:.2f} kWh")
            detail_daily['Estimasi Biaya'] = detail_daily['estimasi_biaya_rp'].apply(lambda v: f"Rp {v:,.0f}")
            detail_daily['Beli Token'] = detail_daily['total_rp'].apply(lambda v: f"Rp {v:,.0f}" if v > 0 else "-")
            detail_daily['Pencatatan'] = detail_daily['kali_catat'].apply(lambda v: f"{v} kali")
            
            st.dataframe(
                detail_daily[['Tanggal', 'Total Konsumsi', 'Estimasi Biaya', 'Beli Token', 'Pencatatan']],
                width="stretch",
                hide_index=True
            )

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

    # 1. Waktu Pencatatan (Langsung di Form: Mendukung Scroll Wheel & Preset Cepat)
    st.markdown("##### 📅 1. Waktu Pencatatan")
    
    # Ambil waktu sekarang sesuai timezone lokal
    now_local = utc_to_local(datetime.now(timezone.utc))

    # Inisialisasi state widget kunci jika belum ada
    if "tgl_input_key" not in st.session_state:
        st.session_state["tgl_input_key"] = now_local.date()
    if "jam_input_key" not in st.session_state:
        st.session_state["jam_input_key"] = now_local.hour
    if "menit_input_key" not in st.session_state:
        st.session_state["menit_input_key"] = now_local.minute

    # Preset Cepat 1-Klik - Update key widget & rerun
    q_col1, q_col2, q_col3, q_col4, _ = st.columns([1.2, 1.2, 1.2, 1.2, 3])
    with q_col1:
        if st.button("🕒 Sekarang", use_container_width=True, key="preset_now"):
            now_dt = utc_to_local(datetime.now(timezone.utc))
            st.session_state["input_date"] = now_dt.date()
            st.session_state["input_hour"] = now_dt.hour
            st.session_state["input_minute"] = now_dt.minute
            st.session_state["tgl_input_key"] = now_dt.date()
            st.session_state["jam_input_key"] = now_dt.hour
            st.session_state["menit_input_key"] = now_dt.minute
            st.rerun()
    with q_col2:
        if st.button("🌅 08:00", use_container_width=True, key="preset_8"):
            st.session_state["input_hour"] = 8
            st.session_state["input_minute"] = 0
            st.session_state["jam_input_key"] = 8
            st.session_state["menit_input_key"] = 0
            st.rerun()
    with q_col3:
        if st.button("☀️ 13:00", use_container_width=True, key="preset_13"):
            st.session_state["input_hour"] = 13
            st.session_state["input_minute"] = 0
            st.session_state["jam_input_key"] = 13
            st.session_state["menit_input_key"] = 0
            st.rerun()
    with q_col4:
        if st.button("🌙 21:00", use_container_width=True, key="preset_21"):
            st.session_state["input_hour"] = 21
            st.session_state["input_minute"] = 0
            st.session_state["jam_input_key"] = 21
            st.session_state["menit_input_key"] = 0
            st.rerun()

    # Kolom Input Tanggal, Jam, dan Menit
    def sync_time_to_state():
        st.session_state["input_date"] = st.session_state["tgl_input_key"]
        st.session_state["input_hour"] = st.session_state["jam_input_key"]
        st.session_state["input_minute"] = st.session_state["menit_input_key"]
    
    col_tgl, col_jam, col_menit = st.columns([2, 1, 1])
    with col_tgl:
        tgl_pick = st.date_input(
            "Tanggal Pencatatan", 
            key="tgl_input_key",
            on_change=sync_time_to_state
        )
    with col_jam:
        jam_pick = st.number_input(
            "Jam (00 - 23)",
            min_value=0,
            max_value=23,
            step=1,
            format="%02d",
            help="Hover mouse dan scroll roda mouse untuk mengubah jam",
            key="jam_input_key",
            on_change=sync_time_to_state
        )
    with col_menit:
        menit_pick = st.number_input(
            "Menit (00 - 59)",
            min_value=0,
            max_value=59,
            step=1,
            format="%02d",
            help="Hover mouse dan scroll roda mouse untuk mengubah menit",
            key="menit_input_key",
            on_change=sync_time_to_state
        )

    waktu_terpilih = datetime(
        tgl_pick.year, tgl_pick.month, tgl_pick.day,
        int(jam_pick), int(menit_pick)
    )

    st.caption(f"🕒 *Waktu Tersimpan:* **{waktu_terpilih.strftime('%A, %d/%m/%Y — %H:%M')} WIB** (Arahkan kursor & scroll roda mouse pada Jam / Menit untuk mengubah)")
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
            
            # Tampilkan waktu lokal
            waktu_display = utc_to_local(pd.to_datetime(row['tanggal_raw'])).strftime('%d/%m/%Y %H:%M')
            
            with c1: st.markdown(f"**{waktu_display}**")
            with c2: st.markdown(f"{row['kwh_meter']:.2f} kWh")
            with c3: st.markdown(f"{row['kwh_terpakai']:.2f} kWh")
            with c4: st.markdown(beli_str)
            with c5: st.markdown(token_str)
            with c6:
                if st.button("🗑️", key=f"btn_del_{idx}", help=f"Hapus catatan {waktu_display}"):
                    st.session_state["delete_target_item"] = {
                        "tanggal_raw": row['tanggal_raw'],
                        "waktu": waktu_display,
                        "kwh": row['kwh_meter']
                    }
                    st.rerun()
            
            st.markdown("<hr style='margin: 0.15rem 0; border: none; border-top: 1px dashed rgba(148,163,184,0.2);'>", unsafe_allow_html=True)
    else:
        st.info("Belum ada riwayat pencatatan pada profil ini.")
