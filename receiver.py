from frame import Frame
from channel import channel_simulate
import random
import time

class Receiver:
    def __init__(self, max_seq, sender_id="B", receiver_id="A"):
        self.expected_seq_num = 0  # Oczekiwany numer (RN)
        self.max_seq = max_seq
        self.last_sent_ack = -1
        self.sender = sender_id
        self.receiver = receiver_id
        self.received_payload = []

    def receive_frame(self, frame):
        """Obsługa odebranej ramki DATA."""
        if frame is None:
            return None  # Ramka utracona w kanale

        # 1. Sprawdzenie Błędu Bitowego (Losowe Zmiany)
        if frame.is_corrupt():
            print(f"[ODBIORNIK]: Otrzymano USZKODZONĄ ramkę DATA SN={frame.seq_num}. ODRZUCAM.")
            # W GBN, Odbiornik po prostu czeka na następny poprawny pakiet.
            # LUB wysyła NACK dla expected_seq_num (co jest równoważne ACK dla poprzedniego pakietu)
            return None

            # 2. Sprawdzenie Numeru Sekwencyjnego (Oczekiwana Ramka)
        if frame.seq_num == self.expected_seq_num:
            print(f"[ODBIORNIK]: Otrzymano POPRAWNĄ i OCZEKIWANĄ ramkę DATA SN={frame.seq_num}.")
            self.received_payload.append(frame.payload)
            self.expected_seq_num = (self.expected_seq_num + 1) % self.max_seq

            # 3. Wysłanie Potwierdzenia (ACK)
            ack_frame = Frame('ACK', self.expected_seq_num, sender_id=self.sender, receiver_id=self.receiver)
            self.last_sent_ack = self.expected_seq_num
            print(f"[ODBIORNIK]: Wysyłam ACK SN={ack_frame.seq_num}")
            return channel_simulate(ack_frame)

        else:
            # Otrzymano ramkę, ale nie jest oczekiwana (może być to duplikat lub ramka poza kolejnością)
            print(
                f"[ODBIORNIK]: Otrzymano ramkę DATA SN={frame.seq_num} poza kolejnością. Oczekiwano SN={self.expected_seq_num}. ODRZUCAM.")
            # Wysłanie powtórnego ACK dla ostatniej poprawnie odebranej ramki (wskazanie Nadawcy, by wrócił do tego miejsca)
            ack_frame = Frame('ACK', self.expected_seq_num, sender_id=self.sender, receiver_id=self.receiver)
            print(f"[ODBIORNIK]: Powtarzam ACK SN={ack_frame.seq_num} (by wrócił do Base={self.expected_seq_num}).")
            return channel_simulate(ack_frame)