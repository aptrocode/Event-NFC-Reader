import os, csv, time, base64, io, zipfile
from datetime import datetime, timedelta
from collections import defaultdict

from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_socketio import SocketIO, emit

from smartcard.System import readers
import smartcard

# ================== Path & App Config ==================
APP_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_FILE   = os.path.join(APP_DIR, "db_peserta.csv")
PHOTO_DIR = os.path.join(APP_DIR, "foto_peserta")
os.makedirs(PHOTO_DIR, exist_ok=True)

app = Flask(__name__)
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

# ================== Static photo route ==================
@app.route("/foto_peserta/<path:filename>")
def foto_peserta(filename):
    return send_from_directory(PHOTO_DIR, filename)

# ================== Register API ==================
@app.post("/api/register")
def api_register():
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

# ================== Analytics helpers ==================
def _parse_photo_ts(fname):
    try:
        base = os.path.basename(fname or "")
        stem = os.path.splitext(base)[0]
        ts = int(stem.split("_")[-1])
        return datetime.fromtimestamp(ts)
    except Exception:
        return None

def _scan_photos_dir():
    total_bytes = 0
    sizes = []
    if not os.path.isdir(PHOTO_DIR):
        return 0, 0.0, sizes
    for root, _, files in os.walk(PHOTO_DIR):
        for f in files:
            try:
                fp = os.path.join(root, f)
                sz = os.path.getsize(fp)
                total_bytes += sz
                sizes.append(sz)
            except Exception:
                pass
    return total_bytes, round(total_bytes / (1024*1024), 2), sizes

def _read_csv_rows():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

def _build_stats():
    rows = _read_csv_rows()
    total = len(rows)

    with_photo = 0
    recent = []
    per_day = defaultdict(int)
    per_weekday = [0]*7     # 0=Mon .. 6=Sun
    per_hour = [0]*24       # 0..23
    ts_all = []

    for row in rows:
        foto_rel = (row.get("Foto") or "").strip()
        if foto_rel:
            foto_path = os.path.join(APP_DIR, foto_rel.replace("/", os.sep))
            if os.path.exists(foto_path):
                with_photo += 1

        ts = _parse_photo_ts(foto_rel)
        if ts:
            ts_all.append(ts)
            per_day[ts.date()] += 1
            per_weekday[ts.weekday()] += 1
            per_hour[ts.hour] += 1
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

    recent.sort(key=lambda x: x["waktu"] or "", reverse=True)
    recent = recent[:10]

    today = datetime.now().date()
    labels_14d, counts_14d = [], []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        labels_14d.append(d.strftime("%d %b"))
        counts_14d.append(per_day.get(d, 0))

    total_bytes, total_mb, sizes = _scan_photos_dir()
    avg_kb = round((sum(sizes) / len(sizes) / 1024), 2) if sizes else 0.0
    max_kb = round((max(sizes) / 1024), 2) if sizes else 0.0

    earliest = min(ts_all).isoformat(timespec="seconds") if ts_all else None
    latest   = max(ts_all).isoformat(timespec="seconds") if ts_all else None

    # labels weekdays Indonesia singkat
    labels_weekday = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
    labels_hour = [f"{h:02d}" for h in range(24)]

    return {
        "ok": True,
        "kpi": {
            "total_peserta": total,
            "dengan_foto": with_photo,
            "tanpa_foto": max(total - with_photo, 0),
            "foto_storage_mb": total_mb,
            "foto_storage_bytes": total_bytes,
            "foto_avg_kb": avg_kb,
            "foto_max_kb": max_kb,
            "earliest_ts": earliest,
            "latest_ts": latest
        },
        "series": {
            "labels_14d": labels_14d,
            "registrations_14d": counts_14d,
            "labels_weekday": labels_weekday,
            "registrations_weekday": per_weekday,
            "labels_hour": labels_hour,
            "registrations_hour": per_hour
        },
        "recent": recent
    }

# ================== Analytics API ==================
@app.get("/api/stats")
def api_stats():
    return jsonify(_build_stats())

# ================== CSV CRUD APIs ==================
@app.get("/api/participants")
def api_list_participants():
    q = (request.args.get("q") or "").strip().lower()
    rows = _read_all_participants()
    if q:
        rows = [
            r for r in rows
            if q in (r.get("UID","").lower() + " " + r.get("Nama","").lower())
        ]

    def _ts(r):
        ts = _parse_photo_ts(r.get("Foto",""))
        return ts or datetime.fromtimestamp(0)

    rows.sort(key=_ts, reverse=True)
    return jsonify({"ok": True, "data": rows})

@app.put("/api/participant/<uid>")
def api_update_participant(uid):
    data = request.get_json(force=True, silent=True) or {}
    new_name = (data.get("name") or "").strip()
    new_photo_dataurl = data.get("photoDataURL")

    rows = _read_all_participants()
    found = False
    old_photo_rel = None

    for r in rows:
        if r.get("UID") == uid:
            if new_name:
                r["Nama"] = new_name

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
                    old_photo_rel = r.get("Foto") or None
                    r["Foto"] = new_rel
                except Exception as e:
                    return jsonify({"ok": False, "error": f"Foto baru gagal diproses: {e}"}), 400

            found = True
            break

    if not found:
        return jsonify({"ok": False, "error": "UID tidak ditemukan."}), 404

    _write_all_participants(rows)

    if old_photo_rel:
        old_basename = os.path.basename(old_photo_rel)
        old_path = os.path.join(PHOTO_DIR, old_basename)
        try:
            if os.path.exists(old_path):
                os.remove(old_path)
        except Exception:
            pass

    return jsonify({"ok": True})

@app.delete("/api/participant/<uid>")
def api_delete_participant(uid):
    delete_photo = (request.args.get("deletePhoto") == "1")
    rows = _read_all_participants()
    new_rows, removed = [], None

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

# ================== Export Endpoints ==================
@app.get("/api/export/participants.csv")
def export_participants_csv():
    q = (request.args.get("q") or "").strip().lower()
    rows = _read_all_participants()
    if q:
        rows = [r for r in rows if q in (r.get("UID","").lower() + " " + r.get("Nama","").lower())]

    def generate():
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["UID", "Nama", "Foto"])
        yield out.getvalue()
        out.seek(0); out.truncate(0)

        for r in rows:
            w.writerow([r.get("UID",""), r.get("Nama",""), r.get("Foto","")])
            yield out.getvalue()
            out.seek(0); out.truncate(0)

    filename = f"participants_{int(time.time())}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "text/csv; charset=utf-8"
    }
    return Response(generate(), headers=headers)

@app.get("/api/export/stats.json")
def export_stats_json():
    data = _build_stats()
    filename = f"stats_{int(time.time())}.json"
    buf = io.BytesIO()
    buf.write((jsonify(data).get_data()))
    buf.seek(0)
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name=filename)

@app.get("/api/export/photos.zip")
def export_photos_zip():
    # Zip semua foto yang ada. WARNING: bisa besar.
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(PHOTO_DIR):
            for f in files:
                fp = os.path.join(root, f)
                arcname = f  # simpan nama file saja
                try:
                    zf.write(fp, arcname=arcname)
                except Exception:
                    pass
    mem.seek(0)
    filename = f"photos_{int(time.time())}.zip"
    return send_file(mem, mimetype="application/zip", as_attachment=True, download_name=filename)

# ================== Main ==================
if __name__ == "__main__":
    socketio.start_background_task(poll_nfc)
    socketio.run(app, host="0.0.0.0", port=5000)
