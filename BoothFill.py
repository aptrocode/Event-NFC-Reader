from smartcard.System import readers
import time
import smartcard

JUMLAH_BOOTH = 5      # Ubah sesuai jumlah booth di eventmu
NOMOR_BOOTHSAYA = 2   # Ubah sesuai nomor booth (contoh: booth 2)

def pad16(text):
    b = [ord(c) for c in text]
    if len(b) > 16:
        return b[:16]
    while len(b) < 16:
        b.append(0x20)
    return b

def parse_booth(text, jumlah_booth):
    # Ambil data dari blok, isi default kalau belum pernah ada
    text = text.rstrip().replace(' ', '')
    booth = {f"Booth{i+1}": '0' for i in range(jumlah_booth)}
    for pair in text.split(','):
        if '=' in pair:
            key, val = pair.split('=', 1)
            if key in booth:
                booth[key] = val
    return booth

def booth_to_string(booth):
    return ','.join([f"{k}={v}" for k, v in booth.items()])

def read_block4(reader):
    # Authenticate blok 4
    AUTH_CMD = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x04, 0x60, 0x00]
    reader.transmit(AUTH_CMD)
    # Read blok 4
    READ_CMD = [0xFF, 0xB0, 0x00, 0x04, 0x10]
    data, sw1, sw2 = reader.transmit(READ_CMD)
    if sw1 == 0x90 and sw2 == 0x00:
        return ''.join([chr(b) for b in data]).strip()
    else:
        return ""

def write_block4(reader, text):
    AUTH_CMD = [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, 0x04, 0x60, 0x00]
    reader.transmit(AUTH_CMD)
    data = pad16(text)
    WRITE_CMD = [0xFF, 0xD6, 0x00, 0x04, 0x10] + data
    response, sw1, sw2 = reader.transmit(WRITE_CMD)
    return (sw1, sw2)

def main():
    r = readers()
    if len(r) == 0:
        print("Tidak ada NFC reader terdeteksi!")
        return
    reader = r[0]

    print("Tempelkan gelang/tag NFC ke reader booth ini...")
    while True:
        try:
            conn = reader.createConnection()
            conn.connect()
            # 1. Baca data lama
            olddata = read_block4(conn)
            booth = parse_booth(olddata, JUMLAH_BOOTH)
            print("Data sebelum update:", booth)
            # 2. Update status booth ini ke 1
            booth[f"Booth{NOMOR_BOOTHSAYA}"] = '1'
            newdata = booth_to_string(booth)
            print("Data akan diupdate:", newdata)
            # 3. Tulis kembali
            sw1, sw2 = write_block4(conn, newdata)
            if sw1 == 0x90 and sw2 == 0x00:
                print("Berhasil update status booth!")
            else:
                print("Gagal update:", sw1, sw2)
            # Tunggu kartu diangkat sebelum siap berikutnya
            while True:
                try:
                    conn.connect()
                    time.sleep(0.2)
                except smartcard.Exceptions.NoCardException:
                    break
            print("Siap untuk gelang berikutnya...")
        except smartcard.Exceptions.NoCardException:
            time.sleep(0.5)
        except Exception as e:
            print("Error:", e)
            time.sleep(1)

if __name__ == "__main__":
    main()
