import time
import config
from logika.sender import Sender
from logika.receiver import Receiver
from logika.frame import Frame
from logika.colors import Colors
from logika import channel


def run_go_back_n_simulation(override_p=None, override_r=None):
    """
    Orkiestrator symulacji protokołu Go-Back-N.

    Funkcja ta zarządza przebiegiem eksperymentu, inicjalizując komponenty (Nadajnik, Odbiornik, Kanał)
    i wykonując pętlę zdarzeń (Event Loop) do momentu przesłania zadanej liczby pakietów.

    Kluczowe etapy w pętli:
    1. **Transmisja:** Pobranie danych, utworzenie ramki i wysłanie jej (jeśli okno pozwala).
    2. **Watchdog:** Zabezpieczenie przed zakleszczeniem (Deadlock) w przypadku utraty synchronizacji timera.
    3. **Obsługa Timeoutu:** Wywołanie procedury `retransmit_window` w przypadku braku ACK.
    4. **Odbiór ACK:** Przetworzenie odpowiedzi od odbiornika i przesunięcie okna.

    Args:
        override_p (float, optional): Nadpisuje prawdopodobieństwo przejścia G->B (start burzy).
        override_r (float, optional): Nadpisuje prawdopodobieństwo przejścia B->G (koniec burzy).

    Returns:
        float: Współczynnik wydajności (Efficiency) zdefiniowany jako iloraz liczby pakietów
               użytecznych do całkowitej liczby transmisji (w tym retransmisji).
    """

    if override_p is not None:
        config.GILBERT_P = override_p
    if override_r is not None:
        config.GILBERT_R = override_r

    sender = Sender(config.WINDOW_SIZE, config.MAX_SEQ)
    receiver = Receiver(config.MAX_SEQ)

    data_to_send = [f"Pakiet_{i + 1}" for i in range(config.TARGET_PACKETS)]
    sent_data_idx = 0

    total_transmissions = 0
    retransmissions = 0

    print(f"\n{Colors.GRAY}--- START SYMULACJI (P={config.GILBERT_P}, R={config.GILBERT_R}) ---{Colors.RESET}")

    start_time = time.time()

    while len(receiver.received_payload) < config.TARGET_PACKETS:
        # Krótki sleep zapobiega zużyciu 100% CPU w pętli oczekiwania (Busy Waiting)
        time.sleep(0.001)

        ack_bytes_from_receiver = None

        # A) Nadajnik: Wysyłanie nowych danych (Flow Control)
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < config.TARGET_PACKETS:
            data = data_to_send[sent_data_idx]
            frame_obj = sender.process_data(data)

            raw_bytes_out = channel.channel_simulate(frame_obj.to_bytes())

            sent_data_idx += 1
            total_transmissions += 1

            ack_bytes_from_receiver = receiver.receive_frame(raw_bytes_out)

        # Watchdog: Zapobiega sytuacji, gdzie okno jest pełne, ale timer nie działa (np. błąd logiczny).
        if sender.base != sender.next_seq_num and sender.timer_start is None:
            sender.start_timer()

        # B) Nadajnik: Obsługa Timeout (ARQ Mechanism)
        if sender.is_timeout():
            added_transmissions = sender.retransmit_window(receiver)
            total_transmissions += added_transmissions
            retransmissions += added_transmissions

            sender.stop_timer()
            sender.start_timer()

        # C) Nadajnik: Obsługa ACK
        if ack_bytes_from_receiver is not None:
            ack_frame = Frame.from_bytes(ack_bytes_from_receiver)
            if not ack_frame.is_corrupt():
                sender.on_ack(ack_frame.seq_num)

        # D) Zarządzanie timerem
        if sender.base == sender.next_seq_num and sent_data_idx >= config.TARGET_PACKETS:
            sender.stop_timer()

    end_time = time.time()
    duration = end_time - start_time

    efficiency = config.TARGET_PACKETS / total_transmissions if total_transmissions > 0 else 0

    print(f"{Colors.GRAY}--- KONIEC PRZEBIEGU ---")
    print(f"Czas: {duration:.2f}s | Retransmisje: {retransmissions}")
    print(f"Wydajność: {efficiency:.2f}{Colors.RESET}")

    return efficiency


if __name__ == "__main__":
    run_go_back_n_simulation()