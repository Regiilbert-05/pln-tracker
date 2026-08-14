import os
from datetime import datetime
import pandas as pd
import streamlit as st

DATA_FILE = 'data_listrik.csv'
PROFILES_FILE = 'profil_meteran.csv'
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
    """Mengembalikan objek collection MongoDB untuk records jika berhasil terhubung."""
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

def get_mongo_profiles_collection():
    """Mengembalikan objek collection MongoDB untuk daftar profil meteran."""
    uri, db_name, _ = _get_mongo_credentials()
    if not uri:
        return None, "Kredensial MongoDB belum disetel"
    
    client, error = _init_mongo_client(uri)
    if client is None:
        return None, error
    
    try:
        db = client[db_name]
        collection = db["meter_profiles"]
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
# Profile / Meter Registry Operations
# ==========================================

def get_meter_list():
    """Mengambil daftar seluruh profil meteran yang terdaftar dan memiliki data."""
    meters = set()
    meters.add(DEFAULT_METER)

    # 1. Cek dari MongoDB
    coll_prof, _ = get_mongo_profiles_collection()
    if coll_prof is not None:
        try:
            for doc in coll_prof.find({}, {"name": 1}):
                name = str(doc.get("name", "")).strip()
                if name:
                    meters.add(name)
        except Exception:
            pass

    coll_rec, _ = get_mongo_collection()
    if coll_rec is not None:
        try:
            for m in coll_rec.distinct("meter_id"):
                name = str(m).strip()
                if name:
                    meters.add(name)
        except Exception:
            pass

    # 2. Cek dari CSV Profil Lokal
    if os.path.exists(PROFILES_FILE):
        try:
            df_prof = pd.read_csv(PROFILES_FILE)
            if 'meter_id' in df_prof.columns:
                for m in df_prof['meter_id'].dropna():
                    name = str(m).strip()
                    if name:
                        meters.add(name)
        except Exception:
            pass

    # 3. Cek dari CSV Data Lokal
    if os.path.exists(DATA_FILE):
        try:
            df_data = pd.read_csv(DATA_FILE)
            if 'meter_id' in df_data.columns:
                for m in df_data['meter_id'].dropna():
                    name = str(m).strip()
                    if name:
                        meters.add(name)
        except Exception:
            pass

    sorted_meters = sorted(list(meters))
    # Pastikan DEFAULT_METER selalu berada di urutan awal jika ada
    if DEFAULT_METER in sorted_meters:
        sorted_meters.remove(DEFAULT_METER)
        sorted_meters.insert(0, DEFAULT_METER)
        
    return sorted_meters

def register_meter(meter_name: str):
    """Mendaftarkan profil meteran baru ke database agar tersimpan permanen."""
    name = str(meter_name).strip()
    if not name:
        return False, "Nama meteran tidak boleh kosong."

    # 1. Simpan ke MongoDB jika tersedia
    coll_prof, _ = get_mongo_profiles_collection()
    if coll_prof is not None:
        try:
            coll_prof.update_one(
                {"name": name},
                {"$set": {"name": name, "updated_at": datetime.utcnow()}},
                upsert=True
            )
        except Exception as e:
            return False, f"Gagal mendaftarkan profil di MongoDB: {e}"

    # 2. Simpan juga ke file profil lokal
    try:
        if os.path.exists(PROFILES_FILE):
            df_prof = pd.read_csv(PROFILES_FILE)
            if 'meter_id' not in df_prof.columns:
                df_prof = pd.DataFrame(columns=['meter_id'])
        else:
            df_prof = pd.DataFrame(columns=['meter_id'])

        if name not in df_prof['meter_id'].astype(str).values:
            new_row = pd.DataFrame([{'meter_id': name}])
            df_prof = pd.concat([df_prof, new_row], ignore_index=True)
            df_prof.to_csv(PROFILES_FILE, index=False)

        return True, f"Profil '{name}' berhasil didaftarkan dan disimpan permanen!"
    except Exception as e:
        return False, f"Gagal menyimpan profil lokal: {e}"

def delete_meter_profile(meter_name: str):
    """Menghapus profil meteran beserta seluruh catatan riwayatnya."""
    name = str(meter_name).strip()
    if name == DEFAULT_METER:
        return False, f"Profil '{DEFAULT_METER}' adalah profil bawaan dan tidak dapat dihapus."

    # 1. Hapus dari MongoDB
    coll_prof, _ = get_mongo_profiles_collection()
    if coll_prof is not None:
        try:
            coll_prof.delete_many({"name": name})
        except Exception:
            pass

    coll_rec, _ = get_mongo_collection()
    if coll_rec is not None:
        try:
            coll_rec.delete_many({"meter_id": name})
        except Exception:
            pass

    # 2. Hapus dari CSV Profil Lokal
    if os.path.exists(PROFILES_FILE):
        try:
            df_prof = pd.read_csv(PROFILES_FILE)
            if 'meter_id' in df_prof.columns:
                df_prof = df_prof[df_prof['meter_id'].astype(str) != name]
                df_prof.to_csv(PROFILES_FILE, index=False)
        except Exception:
            pass

    # 3. Hapus data dari CSV Data Lokal
    if os.path.exists(DATA_FILE):
        try:
            df_data = pd.read_csv(DATA_FILE)
            if 'meter_id' in df_data.columns:
                df_data = df_data[df_data['meter_id'].astype(str) != name]
                df_data.to_csv(DATA_FILE, index=False)
        except Exception:
            pass

    return True, f"Profil '{name}' dan seluruh riwayatnya berhasil dihapus."

# ==========================================
# CRUD Operations (Data Records)
# ==========================================

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
    meter_name = str(meter_id).strip()
    tanggal_str = tanggal_dt.strftime('%Y-%m-%d %H:%M')
    
    # Pastikan profil terdaftar secara otomatis
    register_meter(meter_name)
    
    coll, _ = get_mongo_collection()
    if coll is not None:
        try:
            doc = {
                "meter_id": meter_name,
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
            'meter_id': meter_name
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
