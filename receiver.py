from frame import Frame
from channel import channel_simulate
from colors import Colors


class Receiver:
    def __init__(self, max_seq, sender_id="B", receiver_id="A", on_chunk=None):
        self.expected_seq_num = 0
        self.max_seq = max_seq
        self.last_sent_ack = -1
        self.sender = sender_id
        self.receiver = receiver_id
        self.received_payload = []
        self.on_chunk = on_chunk  # callback po każdym poprawnym kawałku

    def _ack_color_for_data_sn(self, ack_sn: int):
        data_sn = (ack_sn - 1) % self.max_seq
        return Colors.for_sn(data_sn)

    def receive_frame(self, frame):
        """Obsługa odebranej ramki DATA."""
        if frame is None:
            return None

        sn = frame.seq_num

        # 1) Sprawdzenie błędu
        if frame.is_corrupt():
            print(f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano USZKODZONĄ ramkę DATA SN={sn}. ODRZUCAM.{Colors.RESET}")
            return None

        # 2) Czy to oczekiwany numer?
        if sn == self.expected_seq_num:
            print(f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano POPRAWNĄ i OCZEKIWANĄ ramkę DATA SN={sn}.{Colors.RESET}")
            self.received_payload.append(frame.payload)

            # --- callback: zapis i podgląd ---
            if callable(self.on_chunk):
                try:
                    self.on_chunk(frame.payload)
                except Exception as e:
                    print(f"{Colors.RED}[ODBIORNIK]: Błąd w on_chunk: {e}{Colors.RESET}")

            self.expected_seq_num = (self.expected_seq_num + 1) % self.max_seq

            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            self.last_sent_ack = ack_sn
            print(f"{self._ack_color_for_data_sn(ack_sn)}[ODBIORNIK]: Wysyłam ACK SN={ack_sn}{Colors.RESET}")
            return channel_simulate(ack_frame)

        # 3) Ramka poza kolejnością
        print(
            f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano ramkę DATA SN={sn} poza kolejnością. "
            f"Oczekiwano SN={self.expected_seq_num}. ODRZUCAM.{Colors.RESET}"
        )
        ack_sn = self.expected_seq_num
        ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
        print(f"{self._ack_color_for_data_sn(ack_sn)}[ODBIORNIK]: Powtarzam ACK SN={ack_sn} "
              f"(by wrócił do Base={self.expected_seq_num}).{Colors.RESET}")
        return channel_simulate(ack_frame)
