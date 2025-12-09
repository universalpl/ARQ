# test_crc_efficiency.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from logika.frame import Frame
from logika.channel import global_channel
import random
import zlib
import csv
import matplotlib.pyplot as plt

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "testy_output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# =====================================================================
#  TEST BSC (druk + zwracanie wyników do tabeli i wykresu)
# =====================================================================
def run_detection_test(iterations=10000, mode='BSC', prob=0.01):
    total_frames = 0
    corrupted_physically = 0
    detected_errors = 0
    undetected_errors = 0

    print(f"\n--- TEST: {mode} (Prob/Force={prob:.6f}) | Próbek: {iterations} ---")

    original_payload = "TestData_1234567890" * 5
    original_frame = Frame('DATA', 1, original_payload)
    original_bytes = original_frame.to_bytes()

    for _ in range(iterations):
        total_frames += 1

        if mode == 'BSC':
            received_bytes = global_channel.propagate_bsc(original_bytes, prob)
        else:
            config.GILBERT_H = prob
            config.GILBERT_P = 0.05
            config.GILBERT_R = 0.1
            received_bytes = global_channel.propagate(original_bytes)

        if received_bytes != original_bytes:
            corrupted_physically += 1
            decoded = Frame.from_bytes(received_bytes)

            if decoded.is_corrupt():
                detected_errors += 1
            else:
                undetected_errors += 1

    print(f"Wysłane ramki:         {total_frames}")
    print(f"Uszkodzone fizycznie:  {corrupted_physically}")
    print(f"  -> Wykryte (CRC):    {detected_errors}")
    print(f"  -> NIEWYKRYTE:       {undetected_errors}")

    if corrupted_physically > 0:
        detection_rate = detected_errors / corrupted_physically * 100
        undetected_rate = undetected_errors / corrupted_physically * 100
        print(f"Skuteczność CRC:       {detection_rate:.4f}%")
    else:
        detection_rate = 100.0
        undetected_rate = 0.0

    return {
        "prob": prob,
        "frames": total_frames,
        "corrupted": corrupted_physically,
        "detected": detected_errors,
        "undetected": undetected_errors,
        "detection_rate": detection_rate,
        "undetected_rate": undetected_rate
    }


# =====================================================================
#  TEST KOLIZJI CRC (szybki)
# =====================================================================
def run_crc_collision_hunt(iterations=1_000_000):
    print(f"\n--- TEST: CRC_COLLISION_HUNT | Próbek: {iterations:,} ---")

    payload = b"HELLO_WORLD_TEST"
    crc_ok = zlib.crc32(payload)

    corrupted = detected = undetected = 0

    for _ in range(iterations):
        corrupted_bytes = bytearray(payload)

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
        "prob": "-",                   # brak p → w tabeli będzie "-"
        "frames": iterations,
        "corrupted": corrupted,
        "detected": detected,
        "undetected": undetected,
        "detection_rate": detection_rate,
        "undetected_rate": undetected_rate
    }


# =====================================================================
#  CSV EXPORT
# =====================================================================
def save_results_csv(results, filename="crc_results.csv"):
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["p", "frames", "corrupted", "detected", "undetected",
                    "detection_rate (%)", "undetected_rate (%)"])
        for r in results:
            w.writerow([
                r["prob"], r["frames"], r["corrupted"],
                r["detected"], r["undetected"],
                f"{r['detection_rate']:.4f}",
                f"{r['undetected_rate']:.6f}"
            ])
    print(f"\n[TABELA ZAPISANA] → {filepath}")



# =====================================================================
#  WYKRES
# =====================================================================
def plot_results(results, filename="crc_plot.png"):
    filepath = os.path.join(OUTPUT_DIR, filename)

    xs = [r["prob"] for r in results]
    ys_detect = [r["detection_rate"] for r in results]
    ys_undetect = [r["undetected_rate"] for r in results]

    plt.figure(figsize=(10, 6))
    plt.plot(xs, ys_detect, marker="o", label="Wykryte błędy (%)")
    plt.plot(xs, ys_undetect, marker="x", label="Niewykryte błędy (%)")

    plt.xscale("log")
    plt.xlabel("p (Prawdopodobieństwo błędu bitu)")
    plt.ylabel("Procent błędów")
    plt.grid(True)
    plt.legend()
    plt.title("Skuteczność CRC-32 vs poziom szumu w kanale BSC")

    plt.savefig(filepath)
    print(f"[WYKRES ZAPISANY] → {filepath}")



# =====================================================================
#  MAIN
# =====================================================================
if __name__ == "__main__":
    print("Symulacja weryfikacji modelu błędów i skuteczności CRC-32")

    results = []  # ← JEDYNA LISTA

    # dodaj collision hunt DO tabeli
    results.append(run_crc_collision_hunt(500_000))

    probability_levels = [
        0.00001, 0.00003, 0.0001, 0.0003, 0.001,
        0.003, 0.005, 0.007, 0.01, 0.02,
        0.03, 0.25, 0.5
    ]

    for p in probability_levels:
        r = run_detection_test(iterations=5000, mode='BSC', prob=p)
        results.append(r)

    save_results_csv(results)
    plot_results(results)
