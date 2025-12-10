import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from logika.frame import Frame
from logika.channel import global_channel
import random
import zlib
import csv
import base64


# ───────────────────────────────────────────
#   KONFIGURACJA ŚCIEŻEK
# ───────────────────────────────────────────

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "testy_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Poprawna ścieżka do obrazu — jeden katalog wyżej niż testy/
SRC_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "input",
    "kot.jpg"
)

CHUNK_SIZE = 512


# ───────────────────────────────────────────
#   WCZYTYWANIE OBRAZU I DZIELENIE NA CHUNKI
# ───────────────────────────────────────────
def load_image_chunks():
    """
    Wczytuje plik obrazu wykorzystywany w symulacji i dzieli go
    na fragmenty po CHUNK_SIZE bajtów. Każdy fragment jest później
    kodowany base64 — identycznie jak podczas transmisji w main_zdjecia.py.
    """
    with open(SRC_FILE, "rb") as f:
        raw = f.read()

    chunks = []
    for i in range(0, len(raw), CHUNK_SIZE):
        fragment = raw[i:i+CHUNK_SIZE]
        b64 = base64.b64encode(fragment).decode("ascii")
        chunks.append(b64)

    return chunks


# ───────────────────────────────────────────
#   GŁÓWNY TEST DETEKCJI CRC NA REALNYCH DANYCH
# ───────────────────────────────────────────
def run_detection_test(iterations=20, mode='BSC', prob=0.01):
    """
    Testuje skuteczność algorytmu CRC-32 na rzeczywistych danych obrazu.
    Każda ramka jest uszkadzana wiele razy przez kanał błędów, aby uzyskać
    stabilną statystykę (iterations ≈ 20).

    Mierzymy:
      • ile ramek zostało uszkodzonych fizycznie,
      • ile z nich CRC wykryło,
      • ile CRC NIE wykryło,
      • niezawodność kanału: (ramki nieuszkodzone / wszystkie),
      • skuteczność CRC.
    """
    total_frames = 0
    corrupted_physically = 0
    detected_errors = 0
    undetected_errors = 0

    print(f"\n--- TEST: {mode} (p={prob:.6f}) | Powtórzeń: {iterations} ---")

    payloads = load_image_chunks()

    frames_bytes = [
        Frame('DATA', 1, payload).to_bytes()
        for payload in payloads
    ]

    for _ in range(iterations):
        for original in frames_bytes:
            total_frames += 1

            # SZUM KANAŁOWY
            if mode == 'BSC':
                received = global_channel.propagate_bsc(original, prob)
            else:  # Model Gilberta
                config.GILBERT_H = prob
                config.GILBERT_P = 0.05
                config.GILBERT_R = 0.1
                received = global_channel.propagate(original)

            # Czy kanał faktycznie coś popsuł?
            if received != original:
                corrupted_physically += 1

                decoded = Frame.from_bytes(received)

                if decoded.is_corrupt():
                    detected_errors += 1
                else:
                    undetected_errors += 1

    # Statystyki
    if corrupted_physically > 0:
        detection_rate = detected_errors / corrupted_physically * 100
        undetected_rate = undetected_errors / corrupted_physically * 100
    else:
        detection_rate = 100.0
        undetected_rate = 0.0

    reliability = (total_frames - corrupted_physically) / total_frames

    # Wydruk
    print(f"Wysłane ramki:         {total_frames}")
    print(f"Uszkodzone fizycznie:  {corrupted_physically}")
    print(f"  -> Wykryte (CRC):    {detected_errors}")
    print(f"  -> NIEWYKRYTE:       {undetected_errors}")
    print(f"Skuteczność CRC:       {detection_rate:.4f}%")
    print(f"Niezawodność kanału:   {reliability:.4f}")

    return {
        "prob": prob,
        "frames": total_frames,
        "corrupted": corrupted_physically,
        "detected": detected_errors,
        "undetected": undetected_errors,
        "detection_rate": detection_rate,
        "undetected_rate": undetected_rate,
        "reliability": reliability
    }


# ───────────────────────────────────────────
#   TEST TEORETYCZNY KOLIZJI CRC
# ───────────────────────────────────────────
def run_crc_collision_hunt(iterations=500000):
    """
    Teoretyczny test kolizji CRC.
    Pokazuje, jak trudne jest niewykrycie błędu przez CRC-32 przy
    losowych zmianach bajtów.
    """
    print(f"\n--- TEST: CRC_COLLISION_HUNT | Próbek: {iterations:,} ---")

    payload = b"HELLO_WORLD_TEST"
    crc_ok = zlib.crc32(payload)

    corrupted = detected = undetected = 0

    for _ in range(iterations):
        corrupted_bytes = bytearray(payload)

        # losowo zmieniamy kilka bajtów
        for _ in range(random.randint(1, 3)):
            idx = random.randrange(len(corrupted_bytes))
            corrupted_bytes[idx] ^= random.randrange(1, 256)

        corrupted += 1

        if zlib.crc32(corrupted_bytes) != crc_ok:
            detected += 1
        else:
            undetected += 1

    detection_rate = detected / corrupted * 100
    undetected_rate = undetected / corrupted * 100

    print(f"Wysłane ramki:         {iterations}")
    print(f"Uszkodzone fizycznie:  {corrupted}")
    print(f"  -> Wykryte (CRC):    {detected}")
    print(f"  -> NIEWYKRYTE:       {undetected}")
    print(f"Skuteczność CRC:       {detection_rate:.4f}%")

    return {
        "prob": "-",
        "frames": iterations,
        "corrupted": corrupted,
        "detected": detected,
        "undetected": undetected,
        "detection_rate": detection_rate,
        "undetected_rate": undetected_rate,
        "reliability": 0.0  # nie dotyczy
    }


# ───────────────────────────────────────────
#   ZAPIS TABELI CSV
# ───────────────────────────────────────────
def save_results_csv(results, filename="crc_results.csv"):
    """
    Zapisuje dane: błędy fizyczne, wykryte, niewykryte, niezawodność kanału.
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "p",
            "frames",
            "corrupted",
            "detected",
            "undetected",
            "detection_rate (%)",
            "undetected_rate (%)",
            "reliability"
        ])
        for r in results:
            w.writerow([
                r["prob"], r["frames"], r["corrupted"],
                r["detected"], r["undetected"],
                f"{r['detection_rate']:.6f}",
                f"{r['undetected_rate']:.6f}",
                f"{r['reliability']:.6f}"
            ])
    print(f"\n[TABELA ZAPISANA] → {filepath}")


# ───────────────────────────────────────────
#   WYKRES WYNIKÓW
# ───────────────────────────────────────────
def plot_results(results, filename="crc_plot.png"):
    """
    Rysuje 3 krzywe:
      • % błędów wykrytych
      • % błędów niewykrytych
      • % ramek nieuszkodzonych (niezawodność kanału)
    """
    import matplotlib.pyplot as plt

    filepath = os.path.join(OUTPUT_DIR, filename)

    xs = [r["prob"] for r in results if r["prob"] != "-"]
    ys_detect = [r["detection_rate"] for r in results if r["prob"] != "-"]
    ys_undetect = [r["undetected_rate"] for r in results if r["prob"] != "-"]
    ys_reliability = [r["reliability"] * 100 for r in results if r["prob"] != "-"]

    plt.figure(figsize=(11, 6))

    plt.plot(xs, ys_detect, marker="o", label="Wykryte błędy (%)")
    plt.plot(xs, ys_undetect, marker="x", label="Niewykryte błędy (%)")
    plt.plot(xs, ys_reliability, marker="s", label="Ramki nieuszkodzone (%)")

    plt.xscale("log")
    plt.xlabel("p (Prawdopodobieństwo błędu bitu)")
    plt.ylabel("Wartość [%]")
    plt.grid(True)
    plt.legend()
    plt.title("Analiza skuteczności CRC i niezawodności kanału (dane JPG)")

    plt.savefig(filepath)
    print(f"[WYKRES ZAPISANY] → {filepath}")


# ───────────────────────────────────────────
#   MAIN
# ───────────────────────────────────────────
if __name__ == "__main__":
    print("Symulacja skuteczności CRC na danych obrazu")

    results = []

    # Teoretyczny test kolizji CRC
    results.append(run_crc_collision_hunt(500000))

    probability_levels = [
        0.00001, 0.00003, 0.0001, 0.0003, 0.001,
        0.003, 0.005, 0.007, 0.01, 0.02,
        0.03, 0.25, 0.5
    ]

    for p in probability_levels:
        results.append(run_detection_test(
            iterations=20,
            mode='BSC',
            prob=p
        ))

    save_results_csv(results)
    plot_results(results)
