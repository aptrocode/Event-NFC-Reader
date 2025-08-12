import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import csv
from smartcard.System import readers
import time
import smartcard
import os

DB_FILE = "db_peserta.csv"

def baca_uid(reader):
    GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    data, sw1, sw2 = reader.transmit(GET_UID)
    uid = ''.join(['%02X' % b for b in data])
    return uid

def cari_peserta(uid):
    if not os.path.exists(DB_FILE):
        return None, None
    with open(DB_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["UID"] == uid:
                return row["Nama"], row["Foto"]
    return None, None

def tampilkan_nama_foto(nama, foto_path):
    win = tk.Toplevel()
    win.title("Peserta")
    tk.Label(win, text=f"Nama: {nama}", font=("Arial", 18)).pack(pady=8)
    try:
        img = Image.open(foto_path)
        img = img.resize((200, 200))
        imgTk = ImageTk.PhotoImage(img)
        panel = tk.Label(win, image=imgTk)
        panel.image = imgTk
        panel.pack()
    except Exception as e:
        tk.Label(win, text="(Foto tidak ditemukan)").pack()
    # Window tetap tampil selama kartu masih ditempel
    return win

def main():
    root = tk.Tk()
    root.withdraw()
    r = readers()
    if len(r) == 0:
        messagebox.showerror("Error", "Tidak ada NFC reader terdeteksi!")
        return
    reader = r[0]
    messagebox.showinfo("Scan", "Tempelkan gelang/tag NFC untuk melihat nama dan foto.")
    while True:
        try:
            conn = reader.createConnection()
            while True:
                try:
                    conn.connect()
                    break
                except smartcard.Exceptions.NoCardException:
                    time.sleep(0.1)
            uid = baca_uid(conn)
            nama, foto = cari_peserta(uid)
            if nama:
                win = tampilkan_nama_foto(nama, foto)
                # Tunggu kartu masih ditempel, tutup window jika dilepas
                while True:
                    try:
                        conn.connect()
                        win.update()
                        time.sleep(0.1)
                    except smartcard.Exceptions.NoCardException:
                        break
                win.destroy()
            else:
                messagebox.showerror("Tidak Ditemukan", "Data peserta tidak ditemukan di database.")
                # Tunggu kartu dilepas sebelum lanjut
                while True:
                    try:
                        conn.connect()
                        time.sleep(0.2)
                    except smartcard.Exceptions.NoCardException:
                        break
        except Exception as e:
            messagebox.showerror("Error", str(e))
            time.sleep(1)

if __name__ == "__main__":
    main()
