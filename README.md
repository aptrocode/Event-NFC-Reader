# 🎟️ NFC Event Check-in (Registration + Booth Scanner)

This project lets you:

- **Register participants** → Scan NFC wristband, enter name, capture/save a photo, and store `{UID, Name, PhotoPath}` in `db_peserta.csv`.
- **Scan at booths** → Tap a wristband to **show the participant’s name & photo**.
- Wristband stores **UID only**; all details live in the local CSV + photo folder.

---

## 📦 1) Requirements

### Hardware
- NFC reader (**ACS ACR122U** recommended)
- A webcam (or use existing photos)

### OS
- Windows 10/11 (recommended for quickest start)

### Python
- Python 3.10+ (3.12 works)
- Tkinter (bundled with Python on Windows)

---
NFC Software Driver
-
ACS NFC Reader Driver for ACR122U : https://www.acs.com.hk/en/products/3/acr122u-usb-nfc-reader/

ACS QuicView for Utility : https://www.acs.com.hk/en/utility-tools/
