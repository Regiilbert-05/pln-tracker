import os
from datetime import datetime
import pandas as pd
import streamlit as st

DATA_FILE = 'data_listrik.csv'
DEFAULT_METER = "Rumah Utama"

def _get_mongo_credentials():
    """Mengecek apakah kredensial MongoDB tersedia di st.secrets atau Environment Variables."""
    try:
        if hasattr(st, "secrets") and "mongo" in st.secrets and "connection_string" in st.secrets["mongo"]:
            uri = st.secrets["mongo"]["connection_string"]
            db_name = st.secrets["mongo"].get("database", "pln_tracker")
            coll_name = st.secrets["mongo"].get("collection", "meter_records")
            return uri, db_name, coll_name
    except Exception:
        # st.secrets akan raise StreamlitSecretNotFoundError jika file secrets.toml belum ada sama sekali
        pass
    
    # Cek environment variable alternatif
    env_uri = os.environ.get("MONGODB_URI")
    if env_uri:
        db_name = os.environ.get("MONGODB_DATABASE", "pln_tracker")
        coll_name = os.environ.get("MONGODB_COLLECTION", "meter_records")
        return env_uri, db_name, coll_name
        
    return None, None, None

@st.cache_resource(show_spinner=False)
def _init_mongo_client(uri: str):
    """Inisialisasi MongoClient dengan caching agar koneksi tidak dibuat berulang kali."""
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        
        client = MongoClient(
            uri,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000
        )
        # Test ping koneksi cepat
        client.admin.command('ping')
        return client, None
    except Exception as e:
        return None, str(e)

def get_mongo_collection():
    """Mengembalikan objek collection MongoDB jika berhasil terhubung, atau None jika gagal/tidak ada."""
    uri, db_name, coll_name = _get_mongo_credentials()
    if not uri:
        return None, "Kredensial MongoDB belum disetel di .streamlit/secrets.toml"
    
    client, error = _init_mongo_client(uri)
    if client is None:
        return None, error
    
    try:
        db = client[db_name]
        collection = db[coll_name]
        return collection, None
    except Exception as e:
        return None, str(e)

def get_db_status():
    """Mengembalikan status mode database yang sedang aktif (mongo / csv)."""
    coll, err = get_mongo_collection()
    if coll is not None:
        return "mongo", "🟢 Terhubung ke MongoDB Atlas Cloud"
    
    uri, _, _ = _get_mongo_credentials()
    if uri:
        return "error", f"🟡 Gagal konek MongoDB ({err}) -> Menggunakan CSV Lokal"
    else:
        return "csv", "🟡 Mode Penyimpanan Lokal (data_listrik.csv)"

# ==========================================
# CRUD Operations (Support Multi-Meter & Multi-User)
# ==========================================

def get_meter_list():
    """Mengambil daftar nama profil meteran yang terdaftar."""
    coll, _ = get_mongo_collection()
    if coll is not None:
        try:
            meters = coll.distinct("meter_id")
            meters = [m for m in meters if m and str(m).strip()]
            if not meters:
                return [DEFAULT_METER]
            return sorted(meters)
        except Exception:
            pass

    # Fallback CSV
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if 'meter_id' in df.columns:
                meters = df['meter_id'].dropna().unique().tolist()
                meters = [str(m).strip() for m in meters if str(m).strip()]
                if meters:
                    return sorted(meters)
        except Exception:
            pass

    return [DEFAULT_METER]

def load_data(meter_id: str = DEFAULT_METER):
    """
    Memuat seluruh riwayat data pencatatan untuk meter_id tertentu.
    Mengembalikan DataFrame dengan kolom: ['tanggal', 'kwh_meter', 'isi_token_rp', 'isi_token_kwh', 'meter_id']
    """
    coll, _ = get_mongo_collection()
    if coll is not None:
        try:
            cursor = coll.find({"meter_id": meter_id}).sort("tanggal", 1)
            records = list(cursor)
            if records:
                df = pd.DataFrame(records)
                # Bersihkan kolom ObjectId _id
                if '_id' in df.columns:
                    df = df.drop(columns=['_id'])
                
                df['tanggal'] = pd.to_datetime(df['tanggal'])
                df['kwh_meter'] = pd.to_numeric(df['kwh_meter'], errors='coerce').fillna(0.0)
                df['isi_token_rp'] = pd.to_numeric(df['isi_token_rp'], errors='coerce').fillna(0)
                df['isi_token_kwh'] = pd.to_numeric(df['isi_token_kwh'], errors='coerce').fillna(0.0)
                df['meter_id'] = df.get('meter_id', meter_id)
                df = df.sort_values('tanggal').reset_index(drop=True)
                return df
            else:
                return pd.DataFrame(columns=['tanggal', 'kwh_meter', 'isi_token_rp', 'isi_token_kwh', 'meter_id'])
        except Exception as e:
            st.error(f"Gagal memuat data dari MongoDB: {e}")

    # Fallback CSV
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            if not df.empty and 'tanggal' in df.columns:
                if 'meter_id' not in df.columns:
                    df['meter_id'] = DEFAULT_METER
                
                # Filter berdasarkan meter_id
                df_filtered = df[df['meter_id'].astype(str) == str(meter_id)].copy()
                if not df_filtered.empty:
                    df_filtered['tanggal'] = pd.to_datetime(df_filtered['tanggal'])
                    df_filtered['kwh_meter'] = pd.to_numeric(df_filtered['kwh_meter'], errors='coerce').fillna(0.0)
                    df_filtered['isi_token_rp'] = pd.to_numeric(df_filtered['isi_token_rp'], errors='coerce').fillna(0)
                    df_filtered['isi_token_kwh'] = pd.to_numeric(df_filtered['isi_token_kwh'], errors='coerce').fillna(0.0)
                    df_filtered = df_filtered.sort_values('tanggal').reset_index(drop=True)
                    return df_filtered
        except Exception as e:
            st.error(f"Gagal memuat data CSV: {e}")

    return pd.DataFrame(columns=['tanggal', 'kwh_meter', 'isi_token_rp', 'isi_token_kwh', 'meter_id'])

def insert_entry(meter_id: str, tanggal_dt: datetime, kwh_meter: float, isi_token_rp: int = 0, isi_token_kwh: float = 0.0):
    """Menyimpan 1 baris pencatatan baru ke MongoDB atau CSV fallback."""
    tanggal_str = tanggal_dt.strftime('%Y-%m-%d %H:%M')
    
    coll, _ = get_mongo_collection()
    if coll is not None:
        try:
            doc = {
                "meter_id": str(meter_id).strip(),
                "tanggal": tanggal_str,
                "kwh_meter": float(kwh_meter),
                "isi_token_rp": int(isi_token_rp),
                "isi_token_kwh": float(isi_token_kwh),
                "created_at": datetime.utcnow()
            }
            coll.insert_one(doc)
            return True, "Data berhasil disimpan ke MongoDB Cloud!"
        except Exception as e:
            return False, f"Gagal menyimpan ke MongoDB: {e}"

    # Fallback CSV
    try:
        new_row = pd.DataFrame([{
            'tanggal': tanggal_str,
            'kwh_meter': float(kwh_meter),
            'isi_token_rp': int(isi_token_rp),
            'isi_token_kwh': float(isi_token_kwh),
            'meter_id': str(meter_id).strip()
        }])
        
        if os.path.exists(DATA_FILE):
            df_all = pd.read_csv(DATA_FILE)
            if 'meter_id' not in df_all.columns:
                df_all['meter_id'] = DEFAULT_METER
            df_updated = pd.concat([df_all, new_row], ignore_index=True)
        else:
            df_updated = new_row
            
        df_updated.to_csv(DATA_FILE, index=False)
        return True, "Data berhasil disimpan ke file CSV lokal!"
    except Exception as e:
        return False, f"Gagal menyimpan ke CSV: {e}"

def delete_last_entry(meter_id: str):
    """Menghapus baris pencatatan terakhir untuk meter_id yang ditentukan."""
    coll, _ = get_mongo_collection()
    if coll is not None:
        try:
            # Cari entri terakhir berdasarkan tanggal descending
            last_doc = coll.find_one({"meter_id": meter_id}, sort=[("tanggal", -1)])
            if last_doc:
                coll.delete_one({"_id": last_doc["_id"]})
                return True, "Entri terakhir berhasil dihapus dari MongoDB!"
            return False, "Tidak ada data untuk dihapus."
        except Exception as e:
            return False, f"Gagal menghapus dari MongoDB: {e}"

    # Fallback CSV
    try:
        if os.path.exists(DATA_FILE):
            df_all = pd.read_csv(DATA_FILE)
            if not df_all.empty:
                if 'meter_id' not in df_all.columns:
                    df_all['meter_id'] = DEFAULT_METER
                
                # Cari baris-baris milik meter_id ini
                matching_indices = df_all[df_all['meter_id'].astype(str) == str(meter_id)].index
                if len(matching_indices) > 0:
                    last_idx = matching_indices[-1]
                    df_updated = df_all.drop(last_idx)
                    df_updated.to_csv(DATA_FILE, index=False)
                    return True, "Entri terakhir berhasil dihapus dari CSV lokal!"
        return False, "Tidak ada data untuk dihapus."
    except Exception as e:
        return False, f"Gagal menghapus dari CSV: {e}"

def export_meter_csv(meter_id: str) -> bytes:
    """Mengekspor data riwayat meteran tertentu ke format CSV bytes untuk diunduh."""
    df = load_data(meter_id)
    if not df.empty:
        df_export = df.copy()
        if 'tanggal' in df_export.columns:
            df_export['tanggal'] = pd.to_datetime(df_export['tanggal']).dt.strftime('%Y-%m-%d %H:%M')
        return df_export.to_csv(index=False).encode('utf-8')
    return b""
