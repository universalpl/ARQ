from logika.frame import Frame
from logika.channel import channel_simulate
from config import TIMEOUT
from logika.colors import Colors
import time


class Sender:
    """
    Implementuje warstwę nadawczą protokołu Go-Back-N ARQ.

    Zarządza oknem przesuwnym (Sliding Window), które ogranicza liczbę ramek wysłanych
    bez potwierdzenia. Odpowiada za buforowanie ramek na wypadek konieczności ich retransmisji
    oraz obsługę timera, który chroni przed nieskończonym oczekiwaniem na potwierdzenie (Deadlock).

    Attributes:
        window_size (int): Rozmiar okna nadawczego (N). Definiuje przepustowość łącza.
        max_seq (int): Maksymalny numer sekwencyjny. Po jego osiągnięciu licznik wraca do 0.
        base (int): Numer sekwencyjny najstarszej, wysłanej, ale jeszcze NIEpotwierdzonej ramki.
                    Jest to początek okna przesuwnego.
        next_seq_num (int): Numer sekwencyjny dla następnej nowej ramki danych (koniec okna).
        buffer (dict): Bufor retransmisji. Przechowuje kopie obiektów Frame indeksowane przez SeqNum.
        timer_start (float or None): Czas systemowy uruchomienia timera dla ramki o numerze `base`.
    """

    def __init__(self, window_size, max_seq):
        self.window_size = window_size
        self.max_seq = max_seq
        self.base = 0
        self.next_seq_num = 0
        self.buffer = {}
        self.timer_start = None

    def _is_within_window(self, seq_num):
        """
        Weryfikuje, czy dany numer sekwencyjny mieści się w bieżącym oknie logicznym.

        Uwzględnia cykliczność numeracji (modulo max_seq).
        Warunek: (seq_num - base) % max_seq < window_size.
        """
        return (seq_num - self.base) % self.max_seq < self.window_size

    def start_timer(self):
        """Inicjalizuje odliczanie czasu dla najstarszej niepotwierdzonej ramki (Base)."""
        if self.timer_start is None:
            self.timer_start = time.time()
            # print(f"{Colors.GRAY}[NADAJNIK]: STARTUJĘ timer dla Base={self.base}{Colors.RESET}")

    def stop_timer(self):
        """Zatrzymuje odliczanie czasu (np. gdy wszystkie ramki w oknie zostały potwierdzone)."""
        if self.timer_start is not None:
            self.timer_start = None
            # print(f"{Colors.GRAY}[NADAJNIK]: Okno puste – STOP timer.{Colors.RESET}")

    def is_timeout(self):
        """
        Sprawdza stan timera.

        Returns:
            bool: True, jeśli czas oczekiwania przekroczył stałą TIMEOUT zdefiniowaną w konfiguracji.
                  Sygnalizuje to konieczność retransmisji.
        """
        if self.timer_start is not None and (time.time() - self.timer_start) > TIMEOUT:
            print(f"{Colors.GRAY}[NADAJNIK]: TIMEOUT! dla Base={self.base}{Colors.RESET}")
            return True
        return False

    def send_frame(self, frame):
        """Metoda pomocnicza serializująca ramkę i przekazująca ją do symulatora kanału."""
        color = Colors.for_sn(frame.seq_num)
        print(f"{color}[NADAJNIK]: Wysyłam [DATA: SN={frame.seq_num}]{Colors.RESET}")
        return channel_simulate(frame.to_bytes())

    def process_data(self, data):
        """
        Przetwarza dane warstwy wyższej.

        Tworzy ramkę, nadaje jej numer sekwencyjny `next_seq_num`, dodaje do bufora retransmisji
        i wysyła w kanał. Po wysłaniu przesuwa wskaźnik `next_seq_num`.
        """
        frame = Frame('DATA', self.next_seq_num, data)

        # Buforowanie ramki jest kluczowe dla mechanizmu ARQ
        self.buffer[self.next_seq_num] = frame

        self.send_frame(frame)

        if self.base == self.next_seq_num:
            self.start_timer()

        self.next_seq_num = (self.next_seq_num + 1) % self.max_seq
        return frame

    def on_ack(self, ack_num):
        """
        Obsługuje potwierdzenie ACK.

        Implementuje mechanizm **Cumulative ACK** (Potwierdzenie Kumulacyjne).
        Oznacza to, że otrzymanie ACK n potwierdza poprawny odbiór wszystkich ramek
        o numerach sekwencyjnych wcześniejszych niż n (w sensie modulo).

        Działanie:
        1. Przesuwa krawędź okna (`base`) do wartości `ack_num`.
        2. Usuwa potwierdzone ramki z bufora retransmisji (zwalnia pamięć).
        3. Restartuje timer dla nowej ramki `base` (jeśli okno nie jest puste).
        """
        moved = 0
        while self.base != ack_num:
            print(
                f"{Colors.GRAY}[NADAJNIK]: Otrzymano POPRAWNE ACK SN={ack_num}. Przesuwam BASE z {self.base} do {ack_num}.{Colors.RESET}")
            self.buffer.pop(self.base, None)
            self.base = (self.base + 1) % self.max_seq
            moved += 1

        if moved > 0:
            if self.base == self.next_seq_num:
                self.stop_timer()
            else:
                self.stop_timer()  # Timer musi liczyć czas dla nowej najstarszej ramki
                self.start_timer()
        return moved

    def retransmit_window(self, receiver):
        """
        Procedura obsługi błędu (Timeout).

        Zgodnie z protokołem Go-Back-N, w przypadku timeoutu nadajnik musi cofnąć się
        do ramki `base` i **ponownie wysłać wszystkie ramki** znajdujące się aktualnie
        w buforze (od `base` do `next_seq_num - 1`).

        Metoda symuluje również natychmiastowy odbiór ewentualnych ACK, aby przyspieszyć symulację.
        """
        retransmitted_count = 0
        current_seq = self.base

        while current_seq != self.next_seq_num:
            frame = self.buffer.get(current_seq)
            if frame:
                raw_bytes_out = self.send_frame(frame)
                retransmitted_count += 1

                ack_bytes = receiver.receive_frame(raw_bytes_out)
                if ack_bytes is not None:
                    ack_frame = Frame.from_bytes(ack_bytes)
                    if not ack_frame.is_corrupt():
                        self.on_ack(ack_frame.seq_num)

            current_seq = (current_seq + 1) % self.max_seq

        return retransmitted_count