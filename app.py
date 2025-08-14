import os, csv, time, base64
from datetime import datetime, timedelta
from collections import defaultdict

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

from smartcard.System import readers
import smartcard

# ================== Path & App Config ==================
APP_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_FILE   = os.path.join(APP_DIR, "db_peserta.csv")
PHOTO_DIR = os.path.join(APP_DIR, "foto_peserta")
os.makedirs(PHOTO_DIR, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SECRET_KEY'] = 'dev'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ================== CSV Utils ==================
def save_or_update(uid, nama, foto_relpath):
    rows = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            r = csv.reader(f)
            headers = next(r, None)
            if headers:
                rows.append(headers)
            for row in r:
                if row and row[0] != uid:
                    rows.append(row)
    else:
        rows.append(["UID", "Nama", "Foto"])
    rows.append([uid, nama, foto_relpath])
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(rows)

def find_by_uid(uid):
    if not os.path.exists(DB_FILE):
        return None
    with open(DB_FILE, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            if row["UID"] == uid:
                return row
    return None

def _read_all_participants():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

def _write_all_participants(rows):
    # rows: list[dict] dengan keys: UID, Nama, Foto
    with open(DB_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["UID", "Nama", "Foto"])
        w.writeheader()
        for row in rows:
            w.writerow({
                "UID": row.get("UID",""),
                "Nama": row.get("Nama",""),
                "Foto": row.get("Foto","")
            })

# ================== NFC Poll Thread ==================
def poll_nfc():
    try:
        rlist = readers()
        if not rlist:
            print("No NFC reader found. Server tetap jalan tanpa NFC.")
            return
        reader = rlist[0]
        conn = None
        last_uid = None
        print("NFC polling started.")
        while True:
            try:
                if conn is None:
                    conn = reader.createConnection()
                conn.connect()
                # GET UID (ACR122U)
                data, sw1, sw2 = conn.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                if sw1 == 0x90 and sw2 == 0x00 and data:
                    uid = ''.join(['%02X' % b for b in data])
                    if uid != last_uid:
                        last_uid = uid
                        socketio.emit("nfc_tapped", {"uid": uid})
                socketio.sleep(0.2)
            except smartcard.Exceptions.NoCardException:
                last_uid = None
                socketio.sleep(0.2)
            except Exception as e:
                print("NFC error:", e)
                socketio.sleep(1)
    except Exception as e:
        print("NFC init error:", e)

@socketio.on('connect')
def on_connect():
    emit('connected', {'ok': True})

# ================== Routes (Legacy Templates, optional) ==================
@app.route("/")
def home():
    # Jika masih memakai template lama:
    return render_template("index.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/booth")
def booth_page():
    return render_template("booth.html")

@app.route("/analytics")
def analytics_page():
    return render_template("analytics.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

# serve file gambar dari foto_peserta
@app.route("/foto_peserta/<path:filename>")
def foto_peserta(filename):
    return send_from_directory(PHOTO_DIR, filename)

# ================== Register API ==================
@app.post("/api/register")
def api_register():
    # payload: { uid, name, photo(dataURL) }
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    uid  = (data.get("uid") or "").strip()
    photo_dataurl = data.get("photo")

    if not uid:
        return jsonify({"ok": False, "error": "UID belum diterima dari tap."}), 400
    if not name:
        return jsonify({"ok": False, "error": "Nama kosong."}), 400
    if not photo_dataurl or not isinstance(photo_dataurl, str) or not photo_dataurl.startswith("data:image"):
        return jsonify({"ok": False, "error": "Foto tidak valid."}), 400

    # simpan foto ke folder
    try:
        head, b64 = photo_dataurl.split(",", 1)
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({"ok": False, "error": "Decode foto gagal."}), 400

    safe_name = name.replace(" ", "_")
    fname = f"{safe_name}_{int(time.time())}.jpg"
    fpath = os.path.join(PHOTO_DIR, fname)
    with open(fpath, "wb") as f:
        f.write(raw)

    foto_rel = f"foto_peserta/{fname}"
    save_or_update(uid, name, foto_rel)

    return jsonify({"ok": True, "uid": uid, "name": name, "photo": foto_rel})

@app.get("/api/participant/<uid>")
def api_participant(uid):
    row = find_by_uid(uid)
    if not row:
        return jsonify({"ok": False}), 404
    return jsonify({"ok": True, "data": row})

# ================== Analytics helpers & API ==================
def _parse_photo_ts(fname):
    """
    Ekstrak timestamp dari pola nama foto: {nama}_{unix}.jpg
    Contoh: 'andi_1723559012.jpg'
    """
    try:
        base = os.path.basename(fname)
        stem = os.path.splitext(base)[0]
        ts = int(stem.split("_")[-1])
        return datetime.fromtimestamp(ts)
    except Exception:
        return None

def _scan_photos_dir():
    total_bytes = 0
    if not os.path.isdir(PHOTO_DIR):
        return 0, 0.0
    for root, _, files in os.walk(PHOTO_DIR):
        for f in files:
            try:
                total_bytes += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
    return total_bytes, round(total_bytes / (1024*1024), 2)

def _read_csv_rows():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

@app.get("/api/stats")
def api_stats():
    rows = _read_csv_rows()
    total = len(rows)

    # foto tersedia?
    with_photo = 0
    recent = []
    per_day = defaultdict(int)

    for row in rows:
        foto_rel = (row.get("Foto") or "").strip()
        if foto_rel:
            foto_path = os.path.join(APP_DIR, foto_rel.replace("/", os.sep))
            exists = os.path.exists(foto_path)
            if exists:
                with_photo += 1

        # pakai timestamp dari nama file jika ada
        ts = _parse_photo_ts(foto_rel)
        if ts:
            per_day[ts.date()] += 1
            recent.append({
                "uid": row.get("UID"),
                "nama": row.get("Nama"),
                "foto": "/" + foto_rel if foto_rel else "",
                "waktu": ts.isoformat(timespec="seconds")
            })
        else:
            recent.append({
                "uid": row.get("UID"),
                "nama": row.get("Nama"),
                "foto": "/" + foto_rel if foto_rel else "",
                "waktu": None
            })

    # sort recent by waktu (None di bawah)
    recent.sort(key=lambda x: x["waktu"] or "", reverse=True)
    recent = recent[:10]

    # 14 hari terakhir (termasuk hari ini)
    today = datetime.now().date()
    labels, counts = [], []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        labels.append(d.strftime("%d %b"))
        counts.append(per_day.get(d, 0))

    total_bytes, total_mb = _scan_photos_dir()

    return jsonify({
        "ok": True,
        "kpi": {
            "total_peserta": total,
            "dengan_foto": with_photo,
            "tanpa_foto": max(total - with_photo, 0),
            "foto_storage_mb": total_mb,
            "foto_storage_bytes": total_bytes
        },
        "series": {
            "labels_14d": labels,
            "registrations_14d": counts
        },
        "recent": recent
    })

# ================== CSV CRUD APIs (List, Update, Delete) ==================
@app.get("/api/participants")
def api_list_participants():
    q = (request.args.get("q") or "").strip().lower()
    rows = _read_all_participants()
    if q:
        rows = [
            r for r in rows
            if q in (r.get("UID","").lower() + " " + r.get("Nama","").lower())
        ]

    # urut terbaru berdasar timestamp dari nama foto (kalau ada)
    def _ts(r):
        ts = _parse_photo_ts(r.get("Foto",""))
        return ts or datetime.fromtimestamp(0)

    rows.sort(key=_ts, reverse=True)
    return jsonify({"ok": True, "data": rows})

@app.put("/api/participant/<uid>")
def api_update_participant(uid):
    data = request.get_json(force=True, silent=True) or {}
    new_name = (data.get("name") or "").strip()
    new_photo_dataurl = data.get("photoDataURL")  # optional (dataURL string)

    rows = _read_all_participants()
    found = False
    old_photo_rel = None  # untuk dihapus setelah CSV tersimpan

    for r in rows:
        if r.get("UID") == uid:
            # 1) Update nama (jika ada)
            if new_name:
                r["Nama"] = new_name

            # 2) Jika ada foto baru → simpan, tandai foto lama
            if new_photo_dataurl and isinstance(new_photo_dataurl, str) and new_photo_dataurl.startswith("data:image"):
                try:
                    head, b64 = new_photo_dataurl.split(",", 1)
                    raw = base64.b64decode(b64)
                    safe_name = (r.get("Nama") or "user").replace(" ", "_")
                    fname = f"{safe_name}_{int(time.time())}.jpg"
                    fpath = os.path.join(PHOTO_DIR, fname)
                    with open(fpath, "wb") as f:
                        f.write(raw)

                    new_rel = f"foto_peserta/{fname}"
                    old_photo_rel = r.get("Foto") or None  # simpan untuk dihapus nanti
                    r["Foto"] = new_rel
                except Exception as e:
                    return jsonify({"ok": False, "error": f"Foto baru gagal diproses: {e}"}), 400

            found = True
            break

    if not found:
        return jsonify({"ok": False, "error": "UID tidak ditemukan."}), 404

    # 3) Tulis CSV
    _write_all_participants(rows)

    # 4) Hapus foto lama (jika memang ganti foto)
    if old_photo_rel:
        old_basename = os.path.basename(old_photo_rel)  # aman, cegah path traversal
        old_path = os.path.join(PHOTO_DIR, old_basename)
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
                # print("Hapus foto lama:", old_path)
        except Exception:
            # tidak blokir response
            pass

    return jsonify({"ok": True})

@app.delete("/api/participant/<uid>")
def api_delete_participant(uid):
    # ?deletePhoto=1 untuk ikut hapus file foto
    delete_photo = (request.args.get("deletePhoto") == "1")

    rows = _read_all_participants()
    new_rows = []
    removed = None

    for r in rows:
        if r.get("UID") == uid:
            removed = r
            continue
        new_rows.append(r)

    if removed is None:
        return jsonify({"ok": False, "error": "UID tidak ditemukan."}), 404

    _write_all_participants(new_rows)

    if delete_photo:
        foto_rel = (removed.get("Foto") or "").strip()
        if foto_rel:
            old_basename = os.path.basename(foto_rel)
            old_path = os.path.join(PHOTO_DIR, old_basename)
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass

    return jsonify({"ok": True})

# ================== Main ==================
if __name__ == "__main__":
    socketio.start_background_task(poll_nfc)
    socketio.run(app, host="0.0.0.0", port=5000)
