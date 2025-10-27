import random
import time

from frame import Frame
from sender import Sender
from receiver import Receiver
from channel import channel_simulate
from config import *


def run_go_back_n_simulation():
    sender = Sender(WINDOW_SIZE, MAX_SEQ)
    receiver = Receiver(MAX_SEQ)

    data_to_send = [f"Pakiet_{i + 1}" for i in range(TARGET_PACKETS)]
    sent_data_idx = 0
    total_transmissions = 0
    total_retransmissions = 0

    print("--- START SYMULACJI GO-BACK-N ARQ ---")
    print(f"Parametry: N={WINDOW_SIZE}, Strata={PROB_LOSS * 100}%, Błąd={PROB_ERROR * 100}%")

    start_time = time.time()

    while len(receiver.received_payload) < TARGET_PACKETS:

        # Wysłanie nowych danych (jeśli okno nie jest pełne)

        # Sprawdzamy, czy w oknie jest jeszcze miejsce i czy są jeszcze dane do wysłania
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < TARGET_PACKETS:
            data = data_to_send[sent_data_idx]
            frame_to_send = sender.process_data(data)

            if frame_to_send:
                # Jeśli to jest pierwszy pakiet w oknie, uruchamiamy timer
                if sender.base == frame_to_send.seq_num:
                    sender.start_timer()

                # Symulacja wysłania
                ack_from_channel = sender.send_frame(frame_to_send)
                total_transmissions += 1
                sent_data_idx += 1

                # Natychmiastowa obsługa ramki DATA przez odbiornik
                ack_from_receiver = receiver.receive_frame(ack_from_channel)

        # Obsługa timeout'u i retransmisji

        if sender.is_timeout():
            # W GBN: Jeśli upłynął limit czasu, wracamy do Base i retransmitujemy od tego miejsca.
            retrans_count = 0
            current_seq = sender.base

            # Musimy retransmitować wszystkie pakiety od Base do Next_Seq_Num - 1
            while current_seq != sender.next_seq_num:
                frame_to_resend = sender.buffer.get(current_seq)
                if frame_to_resend:
                    ack_from_channel = sender.send_frame(frame_to_resend)
                    total_transmissions += 1
                    retrans_count += 1

                    # Natychmiastowa obsługa ramki DATA przez odbiornik (w prostym modelu)
                    ack_from_receiver = receiver.receive_frame(ack_from_channel)

                current_seq = (current_seq + 1) % sender.max_seq

            total_retransmissions += retrans_count
            sender.start_timer()  # Uruchom timer ponownie

        # Krok 3: Obsługa potwierdzeń (ACK)

        # W prostym modelu ACK z KANAŁU jest przekazywane bezpośrednio do Nadawcy,
        # ale w realistycznym scenariuszu Nadawca musiałby odbierać z kanału.
        # W naszej pętli, symulujemy to poprzez analizę wyniku ACK od odbiornika:

        if 'ack_from_receiver' in locals() and ack_from_receiver is not None:
            if not ack_from_receiver.is_corrupt():
                ack_num = ack_from_receiver.seq_num

                # Go-Back-N (ACK kumulacyjne):
                # ACK informuje o następnym OCZEKIWANYM pakiecie (czyli wszystkie do ACK_num-1 zostały odebrane)

                # Obliczanie, ile pakietów potwierdzono (posuwamy BASE)
                while sender.base != ack_num:
                    print(
                        f"[NADAJNIK]: Otrzymano POPRAWNE ACK SN={ack_num}. Przesuwam BASE z {sender.base} do {ack_num}.")
                    sender.buffer.pop(sender.base, None)  # Usuwamy potwierdzone pakiety z bufora
                    sender.base = (sender.base + 1) % sender.max_seq

                    if sender.base == sender.next_seq_num:
                        # Jeśli okno jest puste, zatrzymaj timer
                        sender.timer_start = None
                        break

                # Jeśli przesunęliśmy bazę, uruchom timer dla nowego pierwszego elementu
                if sender.base != ack_num and sender.base != sender.next_seq_num:
                    sender.start_timer()
            else:
                print(f"[NADAJNIK]: Otrzymano USZKODZONE ACK. IGNORUJĘ. Czekam na retransmisję lub timeout.")

        time.sleep(0.1)  # Krótka pauza symulacyjna

    end_time = time.time()

    # --- Wyniki ---
    print("\n--- PODSUMOWANIE SYMULACJI ---")
    print(f"Pakiety dostarczone: {len(receiver.received_payload)}/{TARGET_PACKETS}")
    print(f"Całkowity czas: {end_time - start_time:.2f} s")
    print(f"Całkowita liczba transmisji: {total_transmissions}")
    print(f"Liczba retransmisji (DATA): {total_retransmissions}")
    efficiency = TARGET_PACKETS / total_transmissions
    print(f"Wydajność (Pakiety Użyteczne / Wszystkie Transmisje): {efficiency:.2f}")

# Uruchomienie symulacji:
run_go_back_n_simulation()