# frame.py
import struct
import zlib


class Frame:
    """Reprezentuje ramkę, którą można zamienić na bity (serializować)."""

    def __init__(self, frame_type, seq_num, payload="", sender_id="A", receiver_id="B"):
        self.type = frame_type  # 'DATA', 'ACK'
        self.seq_num = seq_num
        self.payload = payload if payload is not None else ""
        self.sender = sender_id
        self.receiver = receiver_id

        # Flaga, która zostanie ustawiona na True podczas deserializacji,
        # jeśli suma kontrolna się nie zgodzi.
        self.corrupt_flag = False

    def to_bytes(self) -> bytes:
        """Serializacja: Obiekt -> Ciąg Bajtów (z nagłówkiem i CRC)."""

        # Mapowanie typu na liczbę (DATA=0, ACK=1) - oszczędzamy bity
        type_code = 0 if self.type == 'DATA' else 1

        # Kodowanie stringów na bajty
        payload_bytes = self.payload.encode('utf-8')
        sender_bytes = self.sender.encode('utf-8')
        receiver_bytes = self.receiver.encode('utf-8')

        # Budowa zawartości (bez CRC) przy użyciu struct
        # Format '!BBcc':
        # ! = Network (Big Endian)
        # B = unsigned char (1 bajt) - SeqNum
        # B = unsigned char (1 bajt) - Type
        # c = char (1 bajt) - Sender
        # c = char (1 bajt) - Receiver
        # Reszta to payload

        header = struct.pack('!BBcc', self.seq_num, type_code, sender_bytes, receiver_bytes)
        content = header + payload_bytes

        # Obliczanie Prawdziwego CRC-32 (Dzielenie wielomianów)
        crc = zlib.crc32(content)

        # Doklejamy CRC na początek (4 bajty, unsigned int)
        # Format ramki: [CRC(4)] [SEQ(1)] [TYPE(1)] [S(1)] [R(1)] [PAYLOAD...]
        full_frame = struct.pack('!I', crc) + content

        return full_frame

    @staticmethod
    def from_bytes(data: bytes):
        """Deserializacja: Ciąg Bajtów -> Obiekt Frame."""
        try:
            # Musimy mieć przynajmniej 8 bajtów (4 CRC + 4 Nagłówek)
            if len(data) < 8:
                raise ValueError("Za krótka ramka")

            # 1. Wyciągamy CRC (pierwsze 4 bajty)
            received_crc = struct.unpack('!I', data[:4])[0]

            # 2. Reszta to zawartość
            content = data[4:]

            # 3. Weryfikacja CRC (Czy bity się zgadzają?)
            calculated_crc = zlib.crc32(content)

            # Tworzymy pustą ramkę, którą zaraz wypełnimy
            frame = Frame('DATA', 0)

            if calculated_crc != received_crc:
                # Jeśli CRC się nie zgadza, oznaczamy jako uszkodzoną
                frame.corrupt_flag = True
                # Mimo uszkodzenia, próbujemy odczytać numer sekwencyjny (do logów),
                # ale wiemy, że może być błędny.
                try:
                    frame.seq_num = content[0]  # Pierwszy bajt contentu to SN
                except:
                    pass
                return frame

            # 4. Jeśli CRC jest OK, rozpakowujemy resztę
            # Rozpakuj nagłówek (4 bajty)
            seq_num, type_code, sender_b, receiver_b = struct.unpack('!BBcc', content[:4])

            # Reszta to payload
            payload_bytes = content[4:]

            # Rekonstrukcja obiektu
            frame.seq_num = seq_num
            frame.type = 'DATA' if type_code == 0 else 'ACK'
            frame.sender = sender_b.decode('utf-8', errors='ignore')
            frame.receiver = receiver_b.decode('utf-8', errors='ignore')
            frame.payload = payload_bytes.decode('utf-8', errors='ignore')

            return frame

        except Exception as e:
            # Jeśli struktura bajtów jest tak zniszczona, że struct.unpack wyrzuci błąd
            # zwracamy ramkę oznaczoną jako totalnie zepsutą
            f = Frame('DATA', 0)
            f.corrupt_flag = True
            return f

    def is_corrupt(self):
        """Metoda zgodna z interfejsem używanym w receiver.py"""
        return self.corrupt_flag

    def __str__(self):
        status = " (CORRUPT)" if self.corrupt_flag else ""
        if self.type == 'DATA':
            return f"[DATA: SN={self.seq_num}, Pkt={self.payload}]{status}"
        elif self.type == 'ACK':
            return f"[ACK: SN={self.seq_num}]{status}"
        return f"[{self.type}: SN={self.seq_num}]{status}"