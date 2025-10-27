from frame import Frame
from channel import channel_simulate
import random
import time

TIMEOUT = 3.0  # Czas oczekiwania na ACK (w sekundach)
class Sender:
    def __init__(self, window_size, max_seq):
        self.window_size = window_size
        self.max_seq = max_seq
        self.base = 0  # Baza okna (najstarszy pakiet, na który czekamy)
        self.next_seq_num = 0  # Numer sekwencyjny następnego pakietu
        self.buffer = {}  # Bufor retransmisji {SN: Frame}
        self.timer_start = None  # Czas startu głównego timera

    def _is_within_window(self, seq_num):
        """Sprawdza, czy numer sekwencyjny mieści się w buforze okna."""
        return (seq_num - self.base) % self.max_seq < self.window_size

    def send_frame(self, frame):
        """Symuluje wysłanie ramki do kanału."""
        print(f"[NADAJNIK]: Wysyłam {frame}")
        return channel_simulate(frame)

    def process_data(self, data_packet):
        """Przygotowuje i buforuje dane do wysłania."""
        frame = Frame('DATA', self.next_seq_num, data_packet)
        if self._is_within_window(self.next_seq_num):
            self.buffer[self.next_seq_num] = frame
            self.next_seq_num = (self.next_seq_num + 1) % self.max_seq
            return frame
        else:
            # Okno jest pełne - musimy czekać.
            # W symulacji zakładamy, że dane są dodawane tylko, gdy jest miejsce.
            return None

    def start_timer(self):
        """Uruchamia timer dla najstarszego pakietu w oknie (Base)."""
        self.timer_start = time.time()
        print(f"[NADAJNIK]: STARTUJĘ timer dla Base={self.base}")

    def is_timeout(self):
        """Sprawdza, czy upłynął limit czasu."""
        if self.timer_start is not None and time.time() - self.timer_start > TIMEOUT:
            print(f"[NADAJNIK]: TIMEOUT! dla Base={self.base}")
            self.timer_start = None  # Zresetuj, aby wywołać retransmisję
            return True
        return False

    def retransmit_window(self, channel):
        """Retransmituje wszystkie pakiety z aktualnego okna (Go-Back-N)."""
        retransmitted_count = 0
        current_seq = self.base

        while current_seq != self.next_seq_num:
            frame = self.buffer.get(current_seq)
            if frame:
                channel.send(frame)
                retransmitted_count += 1
            current_seq = (current_seq + 1) % self.max_seq

        self.start_timer()  # Uruchom timer ponownie
        return retransmitted_count