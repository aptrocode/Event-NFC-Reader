# NFC Event Check-in 🎟️

![Static Badge](https://img.shields.io/badge/license-MIT-brightgreen?label=LICENSE)

Sistem registrasi dan check-in event menggunakan gelang/tag NFC.  
Mendukung pendaftaran peserta dengan foto, penyimpanan data lokal (CSV + foto), dan pemindaian di booth untuk menampilkan nama dan foto peserta.

---

## Get Started 🚀

### Hardware

- NFC reader (**ACS ACR122U** recommended)
- Webcam (untuk ambil foto saat registrasi)

**Required** to install:

- [Python 3.12+](https://www.python.org/downloads/) (Tkinter sudah terbundel di Windows)
- [ACS ACR122U NFC Reader Driver](https://www.acs.com.hk/en/products/3/acr122u-usb-nfc-reader/)

**Optional** to install:

- [ACS QuicView for Utility](https://www.acs.com.hk/en/utility-tools/)

Clone Repository

```bash
git clone https://github.com/aptrocode/Event-NFC-Reader.git
```

---

## Installation ⚙️

1. **Clone Repository**

```bash
git clone https://github.com/aptrocode/Event-NFC-Reader.git
```

2. **Masuk ke folder proyek**

```bash
cd Event-NFC-Reader
```

3. **Buat dan aktifkan Virtual Environment**

```bash
python -m venv .venv
```

```bash
.\.venv\Scripts\activate
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Usage 💻

**Jalankan Web UI**

```bash
python app.py
```

- Buka http://localhost:5000/register → Halaman registrasi peserta

- Buka http://localhost:5000/booth → Halaman booth scanner

**Registrasi Offline + Tulis Tag Kosong**

```bash
python BoothWriteEmpty.py
```

**Update Status Booth di Tag**

```bash
python BootFill.py
```

**Tampilkan Nama & Foto dari Scan NFC (Desktop UI)**

```bash
python ShowNameandPhoto.py
```

---

## License

The code is licensed [MIT](LICENSE)
