import cv2
import os
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk
from smartcard.System import readers
import time
import smartcard
import csv

JUMLAH_BOOTH = 5
FOLDER_FOTO = "foto_peserta"
DB_FILE = "db_peserta.csv"

def buat_data_booth(jumlah_booth):
    return ','.join([f"Booth{i+1}=0" for i in range(jumlah_booth)])

def pad16(text):
    b = [ord(c) for c in text]
    if len(b) > 16:
        return b[:16]
    while len(b) < 16:
        b.append(0x20)
    return b

def tulis_ke_tag(reader, text):
    AUTH_CMD = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x04, 0x60, 0x00]
    reader.transmit(AUTH_CMD)
    data = pad16(text)
    WRITE_CMD = [0xFF, 0xD6, 0x00, 0x04, 0x10] + data
    response, sw1, sw2 = reader.transmit(WRITE_CMD)
    return (sw1, sw2)

def ambil_foto(nama):
    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Ambil Foto - Tekan SPACE untuk capture, ESC untuk batal")
    foto_path = ""
    while True:
        ret, frame = cap.read()
        cv2.imshow("Ambil Foto - Tekan SPACE untuk capture, ESC untuk batal", frame)
        k = cv2.waitKey(1)
        if k%256 == 27:
            # ESC pressed
            break
        elif k%256 == 32:
            # SPACE pressed
            if not os.path.exists(FOLDER_FOTO):
                os.makedirs(FOLDER_FOTO)
            foto_path = os.path.join(FOLDER_FOTO, f"{nama}_{int(time.time())}.jpg")
            cv2.imwrite(foto_path, frame)
            break
    cap.release()
    cv2.destroyAllWindows()
    return foto_path

def simpan_db(uid, nama, path_foto):
    data = []
    # Baca semua baris lama (kalau file ada)
    if os.path.isfile(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                data.append(headers)
            for row in reader:
                if row and row[0] != uid:
                    data.append(row)
    else:
        data.append(["UID", "Nama", "Foto"])
    # Tambahkan/replace data baru
    data.append([uid, nama, path_foto])
    # Tulis ulang seluruh file
    with open(DB_FILE, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

def baca_uid(reader):
    # Get UID (command ACR122U)
    GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    data, sw1, sw2 = reader.transmit(GET_UID)
    uid = ''.join(['%02X' % b for b in data])
    return uid

def main():
    root = tk.Tk()
    root.withdraw()
    r = readers()
    if len(r) == 0:
        messagebox.showerror("Error", "Tidak ada NFC reader terdeteksi!")
        return
    reader = r[0]
    messagebox.showinfo("NFC Writer", "Siap daftar peserta baru.\nTempelkan gelang/tag NFC ke reader.")
    while True:
        # Tunggu tempel gelang
        msg = tk.Toplevel()
        msg.title("NFC Writer")
        label = tk.Label(msg, text="Sedang menunggu gelang/tempelkan gelang...", font=("Arial", 14))
        label.pack(padx=30, pady=20)
        msg.update()
        try:
            conn = reader.createConnection()
            while True:
                try:
                    conn.connect()
                    break
                except smartcard.Exceptions.NoCardException:
                    msg.update()
                    time.sleep(0.2)
            msg.destroy()

            # Ambil UID gelang
            uid = baca_uid(conn)
            # Input nama
            nama = simpledialog.askstring("Input Nama", "Masukkan nama peserta:", parent=root)
            if nama is None or nama.strip() == "":
                messagebox.showwarning("Peringatan", "Nama tidak boleh kosong! Ulangi proses dari awal.")
                # Tunggu kartu dilepas
                while True:
                    try:
                        conn.connect()
                        time.sleep(0.2)
                    except smartcard.Exceptions.NoCardException:
                        break
                continue
            nama = nama.strip()

            # Ambil foto
            messagebox.showinfo("Ambil Foto", "Akan membuka kamera.\nTekan SPACE untuk mengambil foto, ESC untuk batal.")
            foto_path = ambil_foto(nama)
            if foto_path == "":
                messagebox.showwarning("Gagal", "Foto tidak diambil.")
                continue

            booth_data = buat_data_booth(JUMLAH_BOOTH)
            data_write = f"{uid}"
            sw1, sw2 = tulis_ke_tag(conn, data_write)
            if sw1 == 0x90 and sw2 == 0x00:
                simpan_db(uid, nama, foto_path)
                messagebox.showinfo("Berhasil", f"Pendaftaran peserta '{nama}' berhasil!\nGelang bisa dicabut.")
            else:
                messagebox.showerror("Gagal", f"Gagal menulis data ke gelang! [{sw1}, {sw2}]")
            while True:
                try:
                    conn.connect()
                    time.sleep(0.2)
                except smartcard.Exceptions.NoCardException:
                    break
        except Exception as e:
            msg.destroy()
            messagebox.showerror("Error", f"{str(e)}")
            time.sleep(1)

if __name__ == "__main__":
    main()
