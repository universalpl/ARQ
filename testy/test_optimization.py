import os
import csv
import time
import importlib
import matplotlib.pyplot as plt

import config
import main_zdjecia


##########################################################
#   KONFIGURACJA EKSPERYMENTU

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "optimization_output/10")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CSV_PATH = os.path.join(OUTPUT_DIR, "optimization_results.csv")

# 5 rozmiarów chunków
CHUNK_SIZES = [256, 512, 1024, 2048, 4096]

# 5 konfiguracji kanału Gilberta
CHANNEL_CONFIGS = [
    {"H": 0.01, "R": 0.35},
    {"H": 0.03, "R": 0.30},
    {"H": 0.05, "R": 0.20},
    {"H": 0.08, "R": 0.18},
    {"H": 0.12, "R": 0.15},
]


#########################################################
#   POJEDYNCZY TEST
def run_single_test(chunk_size, H, R):
    # Tymczasowa zmiana configa
    config.GILBERT_H = H
    config.GILBERT_R = R

    # Reload maina
    importlib.reload(main_zdjecia)

    start = time.time()

    stats = main_zdjecia.run_file_copy_over_gbn(
        return_stats=True,
        disable_gui=True,
        chunk_size_override=chunk_size
    )

    duration = time.time() - start

    return {
        "chunk_size": chunk_size,
        "H": H,
        "R": R,
        "time_s": duration,
        "retransmissions": stats["retransmissions"],
        "efficiency": stats["efficiency"]
    }


##################################################################################################################
#   URUCHOMIENIE 25 TESTÓW

def run_all_tests():
    results = []
    total = len(CHUNK_SIZES) * len(CHANNEL_CONFIGS)
    idx = 1

    for chunk in CHUNK_SIZES:
        for ch in CHANNEL_CONFIGS:
            print(
                f"[{idx}/{total}] "
                f"CHUNK={chunk}, H={ch['H']}, R={ch['R']}"
            )

            res = run_single_test(
                chunk_size=chunk,
                H=ch["H"],
                R=ch["R"]
            )

            results.append(res)
            idx += 1

    return results


#########################################################
#   ZAPIS CSV
def save_csv(results):
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "chunk_size",
            "H",
            "R",
            "time_s",
            "retransmissions",
            "efficiency"
        ])
        for r in results:
            writer.writerow([
                r["chunk_size"],
                r["H"],
                r["R"],
                f"{r['time_s']:.3f}",
                r["retransmissions"],
                f"{r['efficiency']:.4f}"
            ])

    print(f"\n✅ CSV zapisany: {CSV_PATH}")


#########################################################
#   WYKRESY

def plot_results(results):
    metrics = {
        "time_s": "Czas [s]",
        "efficiency": "Wydajność",
        "retransmissions": "Retransmisje"
    }

    for metric, ylabel in metrics.items():
        plt.figure(figsize=(10, 6))

        for ch in CHANNEL_CONFIGS:
            xs = []
            ys = []
            for r in results:
                if r["H"] == ch["H"] and r["R"] == ch["R"]:
                    xs.append(r["chunk_size"])
                    ys.append(r[metric])

            label = f"H={ch['H']}, R={ch['R']}"
            plt.plot(xs, ys, marker="o", label=label)

        plt.xlabel("Chunk size [B]")
        plt.ylabel(ylabel)
        plt.title(f"{ylabel} vs Chunk size")
        plt.grid(True)
        plt.legend()

        out = os.path.join(OUTPUT_DIR, f"{metric}.png")
        plt.savefig(out)
        plt.close()

        print(f"📈 Wykres zapisany: {out}")


#########################################################
#   MAIN

if __name__ == "__main__":
    print("=== TESTY OPTYMALIZACYJNE (25 KONFIGURACJI) ===")

    results = run_all_tests()
    save_csv(results)
    plot_results(results)

    print("\n✅ WSZYSTKIE TESTY ZAKOŃCZONE")
