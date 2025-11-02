# receiver.py
from frame import Frame
from channel import channel_simulate
from colors import Colors


class Receiver:
    def __init__(self, max_seq, sender_id="B", receiver_id="A"):
        self.expected_seq_num = 0  # Oczekiwany numer (RN)
        self.max_seq = max_seq
        self.last_sent_ack = -1
        self.sender = sender_id
        self.receiver = receiver_id
        self.received_payload = []

    def _ack_color_for_data_sn(self, ack_sn: int):
        # ACK SN = (expected next) → powiązana data-ramka ma SN = (ack_sn - 1) mod max_seq
        data_sn = (ack_sn - 1) % self.max_seq
        return Colors.for_sn(data_sn)

    def receive_frame(self, frame):
        """Obsługa odebranej ramki DATA."""
        if frame is None:
            return None  # Ramka utracona w kanale

        sn = frame.seq_num

        # 1) Sprawdzenie błędu bitowego
        if frame.is_corrupt():
            print(f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano USZKODZONĄ ramkę DATA SN={sn}. ODRZUCAM.{Colors.RESET}")
            return None

        # 2) Oczekiwana ramka?
        if sn == self.expected_seq_num:
            print(f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano POPRAWNĄ i OCZEKIWANĄ ramkę DATA SN={sn}.{Colors.RESET}")
            self.received_payload.append(frame.payload)
            self.expected_seq_num = (self.expected_seq_num + 1) % self.max_seq

            # 3) Wysłanie ACK dla kolejnej oczekiwanej
            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            self.last_sent_ack = ack_sn
            print(f"{self._ack_color_for_data_sn(ack_sn)}[ODBIORNIK]: Wysyłam ACK SN={ack_sn}{Colors.RESET}")
            return channel_simulate(ack_frame)

        else:
            # Poza kolejnością → odrzuć i powtórz ACK dla expected_seq_num
            print(
                f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano ramkę DATA SN={sn} poza kolejnością. "
                f"Oczekiwano SN={self.expected_seq_num}. ODRZUCAM.{Colors.RESET}"
            )
            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            print(f"{self._ack_color_for_data_sn(ack_sn)}[ODBIORNIK]: Powtarzam ACK SN={ack_sn} "
                  f"(by wrócił do Base={self.expected_seq_num}).{Colors.RESET}")
            return channel_simulate(ack_frame)
