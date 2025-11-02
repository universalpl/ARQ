# sender.py
from frame import Frame
from channel import channel_simulate
from config import TIMEOUT
from colors import Colors
import time


class Sender:
    def __init__(self, window_size, max_seq):
        self.window_size = window_size
        self.max_seq = max_seq
        self.base = 0
        self.next_seq_num = 0
        self.buffer = {}
        self.timer_start = None

    # ---- Pomocnicze ----
    def _is_within_window(self, seq_num):
        return (seq_num - self.base) % self.max_seq < self.window_size

    def start_timer(self):
        if self.timer_start is None:
            self.timer_start = time.time()
            print(f"{Colors.GRAY}[NADAJNIK]: STARTUJĘ timer dla Base={self.base}{Colors.RESET}")

    def stop_timer(self):
        if self.timer_start is not None:
            self.timer_start = None
            print(f"{Colors.GRAY}[NADAJNIK]: Okno puste – STOP timer.{Colors.RESET}")

    def is_timeout(self):
        if self.timer_start is not None and (time.time() - self.timer_start) > TIMEOUT:
            if self.base != self.next_seq_num:  # <-- DODAJ TO
                print(f"{Colors.GRAY}[NADAJNIK]: TIMEOUT! dla Base={self.base}{Colors.RESET}")
                self.timer_start = None
                return True
            else:
                # okno jest puste – nie ma co retransmitować
                self.stop_timer()
        return False

    # ---- Wysyłanie ----
    def send_frame(self, frame: Frame):
        sn = frame.seq_num
        print(f"{Colors.for_sn(sn)}[NADAJNIK]: Wysyłam {frame}{Colors.RESET}")
        return channel_simulate(frame)

    def process_data(self, data_packet):
        if not self._is_within_window(self.next_seq_num):
            return None
        frame = Frame('DATA', self.next_seq_num, data_packet)
        self.buffer[self.next_seq_num] = frame
        self.next_seq_num = (self.next_seq_num + 1) % self.max_seq
        return frame

    # ---- Obsługa ACK ----
    def on_ack(self, ack_num):
        """
        ACK kumulacyjny: ACK=k oznacza „mam wszystko do k-1”.
        Kolorujemy wg powiązanej data-ramki: SN=(k-1) mod MAX_SEQ.
        Chroni przed spóźnionymi ACK-ami cofającymi base.
        """
        moved = 0
        related_sn = (ack_num - 1) % self.max_seq
        color = Colors.for_sn(related_sn)

        # Oblicz odległość (modułowo)
        distance = (ack_num - self.base) % self.max_seq

        # ACK duplikat (dla aktualnej bazy)
        if distance == 0:
            print(f"{color}[NADAJNIK]: Zignorowano duplikat ACK SN={ack_num} (base={self.base}).{Colors.RESET}")
            return 0

        # ACK „przed” base (czyli stary z poprzedniej rundy)
        if distance > (self.max_seq // 2):
            print(f"{color}[NADAJNIK]: Odrzucono stary ACK SN={ack_num} (base={self.base}).{Colors.RESET}")
            return 0

        # Przesuwanie base do przodu (prawidłowe)
        while self.base != ack_num:
            print(f"{color}[NADAJNIK]: Otrzymano POPRAWNE ACK SN={ack_num}. "
                  f"Przesuwam BASE z {self.base} do {ack_num}.{Colors.RESET}")
            self.buffer.pop(self.base, None)
            self.base = (self.base + 1) % self.max_seq
            moved += 1

        # Zarządzanie timerem
        if moved > 0:
            if self.base == self.next_seq_num:
                self.stop_timer()
            else:
                self.start_timer()

        return moved

    # ---- Retransmisja ----
    def retransmit_window(self, receiver):
        """
        GBN: retransmituje wszystkie ramki [base, next_seq_num) i od razu przekazuje do odbiornika.
        """
        retransmitted_count = 0
        current_seq = self.base

        while current_seq != self.next_seq_num:
            frame = self.buffer.get(current_seq)
            if frame:
                _out = self.send_frame(frame)
                retransmitted_count += 1
                ack = receiver.receive_frame(_out)
                if ack is not None and not ack.is_corrupt():
                    self.on_ack(ack.seq_num)
            current_seq = (current_seq + 1) % self.max_seq

        if self.base != self.next_seq_num and self.timer_start is None:
            self.start_timer()

        return retransmitted_count
