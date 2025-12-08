import os
import time
import base64

from logika.sender import Sender
from logika.receiver import Receiver
from logika.frame import Frame
from logika.colors import Colors
from logika import channel
import config

from gui.live_preview import LivePreviewTk  # plik dodany wyżej

# Ustawienia specyficzne dla kopiowania pliku (NIE ruszamy config.py z protokołem)
CHUNK_SIZE = 2048
SRC_FILE = "input/kot.jpg"
DEST_FILE = "output/kot_copy.jpg"
REFRESH_EVERY_CHUNKS = 1


def _read_file_chunks(path, chunk_size):
    """Czyta plik binarnie i zwraca kolejne chunki bajtów."""
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


def run_file_copy_over_gbn():
    sender = Sender(config.WINDOW_SIZE, config.MAX_SEQ)
    receiver = Receiver(config.MAX_SEQ)

    if not os.path.exists(SRC_FILE):
        raise FileNotFoundError(f"Plik źródłowy nie istnieje: {SRC_FILE}")

    # --- przygotowanie danych: bajty -> base64 (string) ---
    raw_chunks = list(_read_file_chunks(SRC_FILE, CHUNK_SIZE))
    data_to_send = [
        base64.b64encode(ch).decode("ascii")  # ASCII string, pasuje do Frame.payload
        for ch in raw_chunks
    ]
    total_chunks = len(data_to_send)

    _ensure_parent_dir(DEST_FILE)
    # wyczyść plik docelowy
    open(DEST_FILE, "wb").close()

    # --- podgląd na żywo (Tkinter, karmiony bajtami) ---
    preview = LivePreviewTk(DEST_FILE, refresh_every_chunks=REFRESH_EVERY_CHUNKS)
    preview.force_show_once()

    # liczba chunków, które JUŻ zdekodowaliśmy z receivera i zapisaliśmy
    delivered_chunks = 0

    def flush_new_payloads():
        """
        Sprawdza, czy receiver przyjął nowe payloady (stringi base64) i
        zamienia je na bajty + dopisuje do pliku + odświeża podgląd.
        """
        nonlocal delivered_chunks

        while delivered_chunks < len(receiver.received_payload):
            b64_payload = receiver.received_payload[delivered_chunks]
            try:
                data_bytes = base64.b64decode(b64_payload.encode("ascii"))
            except Exception:
                data_bytes = b""
            if data_bytes:
                with open(DEST_FILE, "ab") as out:
                    out.write(data_bytes)
                preview.on_new_bytes(data_bytes)
            delivered_chunks += 1

    sent_data_idx = 0
    total_transmissions = 0
    retransmissions = 0

    print(f"\n{Colors.GRAY}--- START KOPIOWANIA PLIKU PRZEZ GO-BACK-N + KANAŁ GILBERTA ---{Colors.RESET}")
    print(f"Plik źródłowy: {SRC_FILE}")
    print(f"Docelowy:      {DEST_FILE}")
    print(f"Chunki:        {total_chunks} (po {CHUNK_SIZE} bajtów)")
    print(f"Parametry kanału: P={config.GILBERT_P}, R={config.GILBERT_R}, "
          f"K={config.GILBERT_K}, H={config.GILBERT_H}")
    start_time = time.time()

    # Główna pętla: dopóki nie dostarczymy wszystkich chunków
    while len(receiver.received_payload) < total_chunks:
        # Mały sleep jak w oryginalnym mainie – żeby nie mielić 100% CPU
        time.sleep(0.001)

        ack_bytes_from_receiver = None

        # A) Nadajnik: wysyłanie nowych danych, jeśli okno na to pozwala
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < total_chunks:
            data = data_to_send[sent_data_idx]
            frame_obj = sender.process_data(data)

            # serializacja -> kanał Gilberta (bajty) -> do odbiornika
            raw_bytes_out = channel.channel_simulate(frame_obj.to_bytes())
            sent_data_idx += 1
            total_transmissions += 1

            ack_bytes_from_receiver = receiver.receive_frame(raw_bytes_out)

        # Watchdog: okno niepuste, timer nie chodzi -> odpal
        if sender.base != sender.next_seq_num and sender.timer_start is None:
            sender.start_timer()

        # B) Timeout → retransmisja okna
        if sender.is_timeout():
            added_transmissions = sender.retransmit_window(receiver)
            total_transmissions += added_transmissions
            retransmissions += added_transmissions

            sender.stop_timer()
            sender.start_timer()

        # C) Obsługa ACK
        if ack_bytes_from_receiver is not None:
            ack_frame = Frame.from_bytes(ack_bytes_from_receiver)
            if not ack_frame.is_corrupt():
                sender.on_ack(ack_frame.seq_num)

        # D) Zatrzymanie timera, gdy wszystko poszło i zostało potwierdzone
        if sender.base == sender.next_seq_num and sent_data_idx >= total_chunks:
            sender.stop_timer()

        # E) Nowe payloady z receivera → do pliku + podglądu
        flush_new_payloads()

        # F) Utrzymanie responsywności okna Tk
        try:
            preview.root.update_idletasks()
            preview.root.update()
        except Exception:
            # jak ktoś zamknie okno na krzyżyk – nie zabijaj całej symulacji
            pass

    end_time = time.time()
    duration = end_time - start_time

    # Ostatnie dociągnięcie i odświeżenie
    flush_new_payloads()
    preview.force_show_once()

    efficiency = total_chunks / total_transmissions if total_transmissions > 0 else 0.0

    print(f"{Colors.GRAY}--- KONIEC KOPIOWANIA ---{Colors.RESET}")
    print(f"Czas: {duration:.2f}s | Retransmisje: {retransmissions}")
    print(f"Wydajność (chunks / transmisje): {efficiency:.2f}")


if __name__ == "__main__":
    run_file_copy_over_gbn()