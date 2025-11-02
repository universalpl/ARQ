# main.py
import os
import time
import tempfile
from PIL import Image

from sender import Sender
from receiver import Receiver
from config import *
from channel import channel_simulate  # pozostaje jak było
from live_preview import LivePreviewTk as LivePreview  # Tkinter + bufor w RAM


def read_file_chunks(path, chunk_size):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def ensure_parent_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def ensure_progressive_jpeg(src_path: str) -> str:
    """
    Jeśli src nie jest JPEG progresywnym, twórz tymczasową kopię jako progresywny JPEG.
    Zwraca ścieżkę do pliku, którego należy użyć w symulacji.
    """
    try:
        with Image.open(src_path) as im:
            fmt = (im.format or "").upper()
            info = im.info
            is_jpeg = fmt == "JPEG"
            is_progressive = info.get("progressive", 0) == 1

            if is_jpeg and is_progressive:
                return src_path  # już OK

            # Konwersja do RGB i zapis jako progresywny JPEG
            im = im.convert("RGB")
            tmp_dir = tempfile.gettempdir()
            base = os.path.splitext(os.path.basename(src_path))[0]
            dst_path = os.path.join(tmp_dir, f"{base}_progressive.jpg")
            im.save(dst_path, format="JPEG", quality=85, optimize=True, progressive=True)
            print(f"[PREP] Utworzono progresywny JPEG: {dst_path}")
            return dst_path
    except Exception as e:
        print(f"[PREP] Problem z przygotowaniem progresywnego JPG: {e}")
        # Jeśli się nie uda – używamy oryginału (podgląd może wskoczyć dopiero pod koniec)
        return src_path


def run_go_back_n_simulation():
    sender = Sender(WINDOW_SIZE, MAX_SEQ)

    ensure_parent_dir(DEST_FILE)
    # wyczyść plik docelowy
    open(DEST_FILE, "wb").close()

    # --- podgląd na żywo (Tkinter, karmiony bajtami) ---
    preview = LivePreview(DEST_FILE, refresh_every_chunks=REFRESH_EVERY_CHUNKS)
    preview.force_show_once()

    # callback — zapisuje nowy fragment NA DYSK i jednocześnie karmi podgląd bajtami z RAM
    def on_chunk_write_and_refresh(b: bytes):
        # 1) zapis na dysk (kopiowanie „prawdziwego” pliku)
        with open(DEST_FILE, "ab") as out:
            out.write(b)
        # 2) karmienie podglądu tym samym bajtowym kawałkiem (nie czekamy na „domkniecie” pliku)
        preview.on_new_bytes(b)

    receiver = Receiver(MAX_SEQ, on_chunk=on_chunk_write_and_refresh)

    # Wczytaj źródło — jeśli nie istnieje, rzuć czytelny błąd
    if not os.path.exists(SRC_FILE):
        raise FileNotFoundError(f"Plik źródłowy nie istnieje: {SRC_FILE}")

    # Dla żywego podglądu najlepiej mieć progresywny JPEG
    src_for_sim = ensure_progressive_jpeg(SRC_FILE)

    chunks = list(read_file_chunks(src_for_sim, CHUNK_SIZE))
    total_chunks = len(chunks)
    sent_data_idx = 0
    total_transmissions = 0
    total_retransmissions = 0

    print("--- START SYMULACJI GO-BACK-N ARQ (KOPIOWANIE PLIKU + PODGLĄD INKREMENTALNY) ---")
    print(f"Plik źródłowy: {SRC_FILE}")
    print(f"Plik do transmisji: {src_for_sim}")
    print(f"Docelowy:      {DEST_FILE}")
    print(f"Parametry: N={WINDOW_SIZE}, Strata={PROB_LOSS * 100}%, "
          f"Błąd={PROB_ERROR * 100}%, Chunk={CHUNK_SIZE} B, "
          f"Łącznie chunków={total_chunks}")

    start_time = time.time()

    while len(receiver.received_payload) < total_chunks:
        ack_from_receiver = None

        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < total_chunks:
            data = chunks[sent_data_idx]  # bytes
            frame_to_send = sender.process_data(data)

            if frame_to_send:
                if sender.base == frame_to_send.seq_num:
                    sender.start_timer()

                ack_from_channel = sender.send_frame(frame_to_send)
                total_transmissions += 1
                sent_data_idx += 1

                ack_from_receiver = receiver.receive_frame(ack_from_channel)

        if sender.is_timeout():
            retrans_count = sender.retransmit_window(receiver)
            total_transmissions += retrans_count
            total_retransmissions += retrans_count

        if ack_from_receiver is not None:
            if not ack_from_receiver.is_corrupt():
                sender.on_ack(ack_from_receiver.seq_num)
            else:
                print("[NADAJNIK]: Otrzymano USZKODZONE ACK. IGNORUJĘ.")

        if sender.base == sender.next_seq_num and sent_data_idx >= total_chunks:
            sender.stop_timer()

        # utrzymuj responsywność okna Tk
        try:
            preview.root.update_idletasks()
            preview.root.update()
        except Exception:
            pass

    end_time = time.time()

    # Po zakończeniu: ostatnie odświeżenie
    preview.force_show_once()

    print("\n--- PODSUMOWANIE SYMULACJI ---")
    print(f"Chunki dostarczone: {len(receiver.received_payload)}/{total_chunks}")
    print(f"Całkowity czas: {end_time - start_time:.2f} s")
    print(f"Liczba transmisji (DATA): {total_transmissions}")
    print(f"Liczba retransmisji (DATA): {total_retransmissions}")
    efficiency = total_chunks / total_transmissions if total_transmissions else 0.0
    print(f"Wydajność (Użyteczne / Wszystkie Transmisje): {efficiency:.2f}")


if __name__ == "__main__":
    run_go_back_n_simulation()
