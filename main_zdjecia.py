import os
import time
import base64
import matplotlib.pyplot as plt

from logika.sender import Sender
from logika.receiver import Receiver
from logika.frame import Frame
from logika.colors import Colors
from logika import channel
import config

from gui.live_preview import LivePreviewTk

# ───────────────────────────────────────────
#   USTAWIENIA PLIKÓW
# ───────────────────────────────────────────

CHUNK_SIZE = 2048
SRC_FILE = "input/kot.jpg"
DEST_FILE = "output/zdjecie/kot_copy.jpg"
REFRESH_EVERY_CHUNKS = 1
OUTPUT_DIR = "output/histogram"


# ───────────────────────────────────────────
#   POMOCNICZE
# ───────────────────────────────────────────

def _read_file_chunks(path, chunk_size):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def _ensure_parent_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


# ───────────────────────────────────────────
#   GŁÓWNA SYMULACJA
# ───────────────────────────────────────────

def run_file_copy_over_gbn(
        return_stats=False,
        disable_gui=False,
        chunk_size_override=None
):
    global CHUNK_SIZE

    if chunk_size_override is not None:
        CHUNK_SIZE = chunk_size_override

    sender = Sender(config.WINDOW_SIZE, config.MAX_SEQ)
    receiver = Receiver(config.MAX_SEQ)

    if not os.path.exists(SRC_FILE):
        raise FileNotFoundError(f"Plik nie istnieje: {SRC_FILE}")

    raw_chunks = list(_read_file_chunks(SRC_FILE, CHUNK_SIZE))
    data_to_send = [base64.b64encode(ch).decode("ascii") for ch in raw_chunks]
    total_chunks = len(data_to_send)

    _ensure_parent_dir(DEST_FILE)
    open(DEST_FILE, "wb").close()

    preview = None
    if not disable_gui:
        preview = LivePreviewTk(DEST_FILE, refresh_every_chunks=REFRESH_EVERY_CHUNKS)
        preview.force_show_once()

    delivered_chunks = 0

    def flush_new_payloads():
        nonlocal delivered_chunks
        while delivered_chunks < len(receiver.received_payload):
            b64 = receiver.received_payload[delivered_chunks]
            try:
                data_bytes = base64.b64decode(b64.encode("ascii"))
            except Exception:
                data_bytes = b""

            if data_bytes:
                with open(DEST_FILE, "ab") as out:
                    out.write(data_bytes)
                if preview:
                    preview.on_new_bytes(data_bytes)

            delivered_chunks += 1

    sent_data_idx = 0
    total_transmissions = 0
    retransmissions = 0

    # ───── HISTOGRAM (FIX) ─────
    # Mapujemy ChunkIndex -> count
    tx_count_by_chunk_idx = {}

    # Pomocnicza mapa: seq_num -> chunk_idx
    active_sn_mapping = {}

    print(
        f"\n{Colors.GRAY}"
        f"--- START FOTO-TRANSMISJI "
        f"(Gilbert P={config.GILBERT_P}, R={config.GILBERT_R}) ---"
        f"{Colors.RESET}"
    )

    start_time = time.time()

    # ───── PĘTLA GŁÓWNA ─────
    while len(receiver.received_payload) < total_chunks:
        time.sleep(0.001)
        ack_bytes_from_receiver = None

        # A) Normalne wysyłanie
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < total_chunks:
            data = data_to_send[sent_data_idx]
            frame_obj = sender.process_data(data)

            sn = frame_obj.seq_num

            # 1. Przypisujemy SN do unikalnego indeksu danych
            active_sn_mapping[sn] = sent_data_idx
            # 2. Inicjujemy licznik
            tx_count_by_chunk_idx[sent_data_idx] = 1

            raw_bytes_out = channel.channel_simulate(frame_obj.to_bytes())

            sent_data_idx += 1
            total_transmissions += 1
            ack_bytes_from_receiver = receiver.receive_frame(raw_bytes_out)

        # B) Watchdog
        if sender.base != sender.next_seq_num and sender.timer_start is None:
            sender.start_timer()

        # C) Timeout → retransmisje
        if sender.is_timeout():
            frames = sender.retransmit_window(receiver)

            for f in frames:
                sn = f.seq_num
                # Zliczamy retransmisję dla konkretnego kawałka danych
                if sn in active_sn_mapping:
                    chunk_idx = active_sn_mapping[sn]
                    tx_count_by_chunk_idx[chunk_idx] += 1

            added = len(frames)
            total_transmissions += added
            retransmissions += added
            sender.stop_timer()
            sender.start_timer()

        # D) ACK
        if ack_bytes_from_receiver is not None:
            ack_frame = Frame.from_bytes(ack_bytes_from_receiver)
            if not ack_frame.is_corrupt():
                sender.on_ack(ack_frame.seq_num)

        # E) Stop timer
        if sender.base == sender.next_seq_num and sent_data_idx >= total_chunks:
            sender.stop_timer()

        # F) GUI + zapis
        flush_new_payloads()
        if preview:
            try:
                preview.root.update_idletasks()
                preview.root.update()
            except Exception:
                pass

    # ───── PODSUMOWANIE ─────
    duration = time.time() - start_time
    flush_new_payloads()

    if preview:
        preview.force_show_once()

    efficiency = total_chunks / total_transmissions if total_transmissions else 0

    print(f"\n{Colors.GRAY}--- KONIEC ---{Colors.RESET}")
    print(
        f"Czas: {duration:.2f}s | "
        f"Retransmisje: {retransmissions} | "
        f"Wydajność: {efficiency:.2f}"
    )

    # ───── BUDOWA HISTOGRAMU (ZAKRES 1..10+) ─────

    # Inicjalizacja kubełków od 1 do 9
    hist = {i: 0 for i in range(1, 10)}
    hist["10+"] = 0

    for cnt in tx_count_by_chunk_idx.values():
        if cnt >= 10:
            hist["10+"] += 1
        else:
            hist[cnt] += 1

    # Lista etykiet w kolejności do wyświetlania/zapisu
    sorted_keys = list(range(1, 10)) + ["10+"]

    print("\nHistogram liczby wysłań ramki:")
    for k in sorted_keys:
        print(f"{k}: {hist[k]}")

    # ───── ZAPIS HISTOGRAMU DO output/ ─────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # CSV
    csv_path = os.path.join(OUTPUT_DIR, "histogram_transmisji.csv")
    with open(csv_path, "w") as f:
        f.write("liczba_wyslan,liczba_ramek\n")
        for k in sorted_keys:
            f.write(f"{k},{hist[k]}\n")

    # Wykres
    labels = [str(k) for k in sorted_keys]
    values = [hist[k] for k in sorted_keys]

    plt.figure(figsize=(10, 6))  # Nieco szerszy wykres
    bar_container = plt.bar(labels, values, color='skyblue', edgecolor='black')
    plt.xlabel("Liczba wysłań danej ramki")
    plt.ylabel("Liczba ramek (chunków)")
    plt.title("Histogram retransmisji ramek (GBN)")
    plt.bar_label(bar_container)
    plt.tight_layout()

    plot_path = os.path.join(OUTPUT_DIR, "histogram_transmisji.png")
    plt.savefig(plot_path)
    plt.close()

    print(f"\nHistogram zapisany do:")
    print(f"- {csv_path}")
    print(f"- {plot_path}")

    if return_stats:
        return {
            "time": duration,
            "retransmissions": retransmissions,
            "efficiency": efficiency,
            "histogram": hist
        }


# ───────────────────────────────────────────
#   URUCHOMIENIE NORMALNE
# ───────────────────────────────────────────

if __name__ == "__main__":
    run_file_copy_over_gbn()