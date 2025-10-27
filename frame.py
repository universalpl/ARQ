class Frame:
    """Reprezentuje ramkę danych lub sterującą (ACK/NACK)."""

    def __init__(self, frame_type, seq_num, payload=None, sender_id="A", receiver_id="B"):
        self.type = frame_type  # 'DATA', 'ACK', 'NACK'
        self.seq_num = seq_num  # Numer sekwencyjny
        self.payload = payload  # Dane (tylko dla DATA)
        self.sender = sender_id
        self.receiver = receiver_id
        self.crc = self._calculate_crc()  # Suma kontrolna

    def _calculate_crc(self):
        """Symulacja obliczania sumy kontrolnej (CRC)."""
        # W realistycznym scenariuszu tu byłby złożony algorytm CRC
        data = f"{self.type}{self.seq_num}{self.payload}{self.sender}{self.receiver}"
        return sum(ord(c) for c in data if c is not None) % 256

    def is_corrupt(self):
        """Sprawdza, czy ramka jest uszkodzona."""
        # W symulacji, sprawdzamy, czy CRC zgadza się z danymi
        return self.crc != self._calculate_crc()

    def corrupt_frame(self):
        """Symuluje błąd bitowy - zmienia CRC."""
        self.crc = (self.crc + 1) % 256

    def __str__(self):
        if self.type == 'DATA':
            return f"[DATA: SN={self.seq_num}, Pkt={self.payload}]"
        elif self.type == 'ACK':
            return f"[ACK: SN={self.seq_num}]"
        return f"[{self.type}: SN={self.seq_num}]"