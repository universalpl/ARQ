import os
import pandas as pd
import matplotlib.pyplot as plt

# tu jest folder z 1..10
BASE_DIR = os.path.join(os.path.dirname(__file__), "optimization_output")

# gdzie zapiszemy średnią
OUT_DIR = os.path.join(BASE_DIR, "average")
os.makedirs(OUT_DIR, exist_ok=True)

OUT_CSV = os.path.join(OUT_DIR, "optimization_results_avg.csv")

# wczytanie wszystkich csv z folderów 1..10
dfs = []
for i in range(1, 11):
    csv_path = os.path.join(BASE_DIR, str(i), "optimization_results.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"brak pliku: {csv_path}")
    df = pd.read_csv(csv_path)
    df["run_id"] = i  # tylko informacyjnie
    dfs.append(df)

all_df = pd.concat(dfs, ignore_index=True)

# upewniamy się, że liczby są liczbami (czas/eff mogą być stringami)
for col in ["chunk_size", "H", "R", "time_s", "retransmissions", "efficiency"]:
    all_df[col] = pd.to_numeric(all_df[col], errors="coerce")

# średnia po tej samej konfiguracji testu
avg_df = (
    all_df
    .groupby(["chunk_size", "H", "R"], as_index=False)
    .agg({
        "time_s": "mean",
        "retransmissions": "mean",
        "efficiency": "mean"
    })
)

# zapis csv ze średnią
avg_df.to_csv(OUT_CSV, index=False)
print(f"✅ zapisano: {OUT_CSV}")

# listy do zachowania kolejności osi i legendy
CHUNK_SIZES = sorted(avg_df["chunk_size"].unique().tolist())

# unikalne konfiguracje kanału
CHANNEL_CONFIGS = (
    avg_df[["H", "R"]]
    .drop_duplicates()
    .sort_values(["H", "R"])
    .to_dict("records")
)

def plot_avg(metric, ylabel, out_name):
    plt.figure(figsize=(10, 6))

    for ch in CHANNEL_CONFIGS:
        sub = avg_df[(avg_df["H"] == ch["H"]) & (avg_df["R"] == ch["R"])].copy()
        sub = sub.sort_values("chunk_size")

        xs = sub["chunk_size"].tolist()
        ys = sub[metric].tolist()

        label = f"H={ch['H']}, R={ch['R']}"
        plt.plot(xs, ys, marker="o", label=label)

    plt.xlabel("Chunk size [B]")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} vs Chunk size (średnia z 10 uruchomień)")
    plt.grid(True)
    plt.legend()

    out_path = os.path.join(OUT_DIR, out_name)
    plt.savefig(out_path)
    plt.close()
    print(f"📈 zapisano: {out_path}")

# wykresy średnie
plot_avg("efficiency", "Wydajność", "efficiency_avg.png")
plot_avg("retransmissions", "Retransmisje", "retransmissions_avg.png")
plot_avg("time_s", "Czas [s]", "time_s_avg.png")

print("✅ gotowe: średnia z 10 folderów")
