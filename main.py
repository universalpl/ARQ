# main.py
import time

from sender import Sender
from receiver import Receiver
from config import *
from channel import channel_simulate  # kanał używany przez receiver

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
        # reset ACK z poprzedniej iteracji
        ack_from_receiver = None

        # 1) Wysyłanie nowych danych, jeśli jest miejsce w oknie
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < TARGET_PACKETS:
            data = data_to_send[sent_data_idx]
            frame_to_send = sender.process_data(data)

            if frame_to_send:
                if sender.base == frame_to_send.seq_num:
                    sender.start_timer()

                ack_from_channel = sender.send_frame(frame_to_send)
                total_transmissions += 1
                sent_data_idx += 1

                # odbiornik przetwarza dane
                ack_from_receiver = receiver.receive_frame(ack_from_channel)

        # 2) Timeout → retransmisja całego okna
        if sender.is_timeout():
            retrans_count = sender.retransmit_window(receiver)
            total_transmissions += retrans_count
            total_retransmissions += retrans_count

        # 3) Obsługa poprawnego ACK
        if ack_from_receiver is not None:
            if not ack_from_receiver.is_corrupt():
                sender.on_ack(ack_from_receiver.seq_num)
            else:
                print("[NADAJNIK]: Otrzymano USZKODZONE ACK. IGNORUJĘ. Czekam na retransmisję lub timeout.")

        # 4) Zatrzymanie timera po ostatnim pakiecie
        if sender.base == sender.next_seq_num and sent_data_idx >= TARGET_PACKETS:
            sender.stop_timer()

         # drobna pauza symulacyjna

    end_time = time.time()

    # --- PODSUMOWANIE ---
    print("\n--- PODSUMOWANIE SYMULACJI ---")
    print(f"Pakiety dostarczone: {len(receiver.received_payload)}/{TARGET_PACKETS}")
    print(f"Całkowity czas: {end_time - start_time:.2f} s")
    print(f"Całkowita liczba transmisji (DATA): {total_transmissions}")
    print(f"Liczba retransmisji (DATA): {total_retransmissions}")
    efficiency = TARGET_PACKETS / total_transmissions if total_transmissions else 0.0
    print(f"Wydajność (Pakiety Użyteczne / Wszystkie Transmisje): {efficiency:.2f}")


if __name__ == "__main__":
    run_go_back_n_simulation()
