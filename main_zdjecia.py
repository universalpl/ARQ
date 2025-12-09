import os
import time
import base64

from logika.sender import Sender
from logika.receiver import Receiver
from logika.frame import Frame
from logika.colors import Colors
from logika import channel
import config

from gui.live_preview import LivePreviewTk

# Ustawienia pliku
CHUNK_SIZE = 512 #4096
SRC_FILE = "input/kot.jpg"
DEST_FILE = "output/kot_copy.jpg"
REFRESH_EVERY_CHUNKS = 1


def _read_file_chunks(path, chunk_size):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk: break
            yield chunk


def _ensure_parent_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d): os.makedirs(d, exist_ok=True)


def run_file_copy_over_gbn():
    sender = Sender(config.WINDOW_SIZE, config.MAX_SEQ)
    receiver = Receiver(config.MAX_SEQ)

    if not os.path.exists(SRC_FILE):
        raise FileNotFoundError(f"Plik nie istnieje: {SRC_FILE}")

    raw_chunks = list(_read_file_chunks(SRC_FILE, CHUNK_SIZE))
    data_to_send = [base64.b64encode(ch).decode("ascii") for ch in raw_chunks]
    total_chunks = len(data_to_send)

    _ensure_parent_dir(DEST_FILE)
    open(DEST_FILE, "wb").close()

    preview = LivePreviewTk(DEST_FILE, refresh_every_chunks=REFRESH_EVERY_CHUNKS)
    preview.force_show_once()

    delivered_chunks = 0

    def flush_new_payloads():
        nonlocal delivered_chunks
        while delivered_chunks < len(receiver.received_payload):
            b64 = receiver.received_payload[delivered_chunks]
            try:
                data_bytes = base64.b64decode(b64.encode("ascii"))
            except:
                data_bytes = b""
            if data_bytes:
                with open(DEST_FILE, "ab") as out: out.write(data_bytes)
                preview.on_new_bytes(data_bytes)
            delivered_chunks += 1

    sent_data_idx = 0
    total_transmissions = 0
    retransmissions = 0

    print(
        f"\n{Colors.GRAY}--- START FOTO-TRANSMISJI (Gilbert P={config.GILBERT_P}, R={config.GILBERT_R}) ---{Colors.RESET}")
    start_time = time.time()

    # --- PĘTLA GŁÓWNA ---
    while len(receiver.received_payload) < total_chunks:
        time.sleep(0.001)
        ack_bytes_from_receiver = None

        # A) Nadajnik: Wysyłanie
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < total_chunks:
            data = data_to_send[sent_data_idx]
            frame_obj = sender.process_data(data)

            # Serializacja i wysyłka
            raw_bytes_out = channel.channel_simulate(frame_obj.to_bytes())

            sent_data_idx += 1
            total_transmissions += 1
            ack_bytes_from_receiver = receiver.receive_frame(raw_bytes_out)

        # B) Watchdog (Status dlaczego nic się nie dzieje)
        if sender.base != sender.next_seq_num and sender.timer_start is None:
            print(f"{Colors.GRAY}[INFO] Watchdog restartuje timer...{Colors.RESET}")
            sender.start_timer()

        # C) Timeout (Status dlaczego stoję)
        if sender.is_timeout():
            print(f"{Colors.RED}[STOP] Timeout na pakiecie SN={sender.base}. Retransmisja...{Colors.RESET}")
            added = sender.retransmit_window(receiver)
            total_transmissions += added
            retransmissions += added
            sender.stop_timer()
            sender.start_timer()

        # D) Obsługa ACK
        if ack_bytes_from_receiver is not None:
            ack_frame = Frame.from_bytes(ack_bytes_from_receiver)
            if not ack_frame.is_corrupt():
                sender.on_ack(ack_frame.seq_num)

        # E) Stop Timer
        if sender.base == sender.next_seq_num and sent_data_idx >= total_chunks:
            sender.stop_timer()

        # F) GUI
        flush_new_payloads()
        try:
            preview.root.update_idletasks()
            preview.root.update()
        except:
            pass

    # Podsumowanie
    duration = time.time() - start_time
    flush_new_payloads()
    preview.force_show_once()
    eff = total_chunks / total_transmissions if total_transmissions else 0

    print(f"\n{Colors.GRAY}--- KONIEC ---{Colors.RESET}")
    print(f"Czas: {duration:.2f}s | Retransmisje: {retransmissions} | Wydajność: {eff:.2f}")


if __name__ == "__main__":
    run_file_copy_over_gbn()