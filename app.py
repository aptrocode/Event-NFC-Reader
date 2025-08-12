import os, csv, time, base64
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from smartcard.System import readers
import smartcard

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

# ================== Routes ==================
@app.route("/")
def home():
    return "<h3>NFC Web UI</h3><p><a href='/register'>Register</a> | <a href='/booth'>Booth</a></p>"

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/booth")
def booth_page():
    return render_template("booth.html")

# serve file gambar dari foto_peserta
@app.route("/foto_peserta/<path:filename>")
def foto_peserta(filename):
    return send_from_directory(PHOTO_DIR, filename)

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
    if not photo_dataurl or not photo_dataurl.startswith("data:image"):
        return jsonify({"ok": False, "error": "Foto tidak valid."}), 400

    # simpan foto ke folder
    try:
        head, b64 = photo_dataurl.split(",", 1)
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({"ok": False, "error": "Decode foto gagal."}), 400

    fname = f"{name}_{int(time.time())}.jpg"
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

if __name__ == "__main__":
    socketio.start_background_task(poll_nfc)
    socketio.run(app, host="0.0.0.0", port=5000)
