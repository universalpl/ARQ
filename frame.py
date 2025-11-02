class Frame:
    """Reprezentuje ramkę danych lub sterującą (ACK/NACK)."""

    def __init__(self, frame_type, seq_num, payload=None, sender_id="A", receiver_id="B"):
        self.type = frame_type  # 'DATA', 'ACK', 'NACK'
        self.seq_num = seq_num
        self.payload = payload
        self.sender = sender_id
        self.receiver = receiver_id
        self.crc = self._calculate_crc()  # suma kontrolna

    def _calculate_crc(self):
        """Prosta 'CRC' (suma mod 256) działająca także dla payloadu jako bytes."""
        def to_bytes(x):
            if x is None:
                return b""
            if isinstance(x, (bytes, bytearray)):
                return bytes(x)
            return str(x).encode("utf-8")

        data = (
            to_bytes(self.type) +
            to_bytes(self.seq_num) +
            to_bytes(self.payload) +
            to_bytes(self.sender) +
            to_bytes(self.receiver)
        )
        return sum(data) % 256

    def is_corrupt(self):
        return self.crc != self._calculate_crc()

    def corrupt_frame(self):
        self.crc = (self.crc + 1) % 256

    def __str__(self):
        if self.type == 'DATA':
            if isinstance(self.payload, (bytes, bytearray)):
                return f"[DATA: SN={self.seq_num}, Bytes={len(self.payload)}]"
            return f"[DATA: SN={self.seq_num}, Pkt={self.payload}]"
        elif self.type == 'ACK':
            return f"[ACK: SN={self.seq_num}]"
        return f"[{self.type}: SN={self.seq_num}]"
