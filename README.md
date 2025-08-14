# NFC Event Check-in 🎟️

![Static Badge](https://img.shields.io/badge/license-MIT-brightgreen?label=LICENSE)

Event registration and check-in system using `NFC` wristbands/tags.

Supports participant registration with photos, local data storage (CSV + photos), and scanning at the booth to display participant names and photos.

---

## Requirements 📝

**Hardware**

- NFC reader (**ACS ACR122U** recommended)
- Webcam (to take photos during registration)

**Required** to install:

- [Python 3.12+](https://www.python.org/downloads/)
- [Node 22.18.0+](https://nodejs.org/en/download/)
- [ACS ACR122U NFC Reader Driver](https://www.acs.com.hk/en/products/3/acr122u-usb-nfc-reader/)

**Optional** to install:

- [Bun](https://bun.com/)
- [ACS QuicView for Utility](https://www.acs.com.hk/en/utility-tools/)

---

## Get Started 🚀

1. **Clone Repository**

```bash
git clone https://github.com/aptrocode/Event-NFC-Reader.git
```

2. **Go to the project folder**

```bash
cd Event-NFC-Reader
```

3. **Create and activate a Virtual Environment**

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

5. **Go to frontend folder**

```bash
cd frontend
```

6. **Install dependencies**

```bash
bun install
```

> [!NOTE]
> if not using `bun` just delete `bun.lockb`, and switch to another package manager like:

```bash
# npm install
# yarn install
# pnpm install
```

---

## Usage 💻

**Run development**

```bash
bun dev
```

> [!NOTE]
> Make sure you run the command in the `/frontend` directory

---

## License

The code is licensed [MIT](LICENSE)
