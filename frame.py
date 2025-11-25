# frame.py
import struct
import zlib


class Frame:
    """
    Reprezentuje pojedynczą ramkę danych w protokole sieciowym.
    Klasa odpowiada za przechowywanie danych, numeru sekwencyjnego oraz
    za serializację (pakowanie do bajtów) i deserializację (rozpakowanie).

    Attributes:
        type (str): Typ ramki ('DATA' lub 'ACK').
        seq_num (int): Numer sekwencyjny ramki.
        payload (str): Dane użytkowe (tylko dla ramek DATA).
        sender (str): ID nadawcy (np. 'A').
        receiver (str): ID odbiorcy (np. 'B').
        corrupt_flag (bool): Flaga ustawiana na True, jeśli suma kontrolna CRC się nie zgadza.
    """

    def __init__(self, frame_type, seq_num, payload="", sender_id="A", receiver_id="B"):
        self.type = frame_type
        self.seq_num = seq_num
        self.payload = payload if payload is not None else ""
        self.sender = sender_id
        self.receiver = receiver_id
        self.corrupt_flag = False

    def to_bytes(self) -> bytes:
        """
        Serializuje obiekt ramki do ciągu bajtów gotowych do wysłania przez kanał.
        Oblicza sumę kontrolną CRC-32 i dokleja ją na początku ramki.

        Returns:
            bytes: Zserializowana ramka w formacie: [CRC(4b)][Header(4b)][Payload...].
        """
        # Mapowanie typu na liczbę (DATA=0, ACK=1) - oszczędzamy bity
        type_code = 0 if self.type == 'DATA' else 1

        # Kodowanie stringów na bajty
        payload_bytes = self.payload.encode('utf-8')
        sender_bytes = self.sender.encode('utf-8')
        receiver_bytes = self.receiver.encode('utf-8')

        # Budowa nagłówka (bez CRC)
        # Format '!BBcc': Network (Big Endian), Byte, Byte, char, char
        header = struct.pack('!BBcc', self.seq_num, type_code, sender_bytes, receiver_bytes)

        content = header + payload_bytes

        # Obliczenie CRC-32
        crc = zlib.crc32(content)

        # Doklejenie CRC na początek
        return struct.pack('!I', crc) + content

    @staticmethod
    def from_bytes(data: bytes):
        """
        Deserializuje ciąg bajtów z powrotem do obiektu Frame.
        Weryfikuje sumę kontrolną CRC-32.

        Args:
            data (bytes): Surowe dane odebrane z kanału.

        Returns:
            Frame: Obiekt ramki. Jeśli CRC jest błędne, ustawia flagę frame.corrupt_flag = True.
        """
        frame = Frame('DATA', 0)

        try:
            if len(data) < 8:
                frame.corrupt_flag = True
                return frame

            # 1. Wyciągnij CRC (pierwsze 4 bajty)
            received_crc = struct.unpack('!I', data[:4])[0]
            content = data[4:]

            # 2. Oblicz CRC ponownie z danych
            calculated_crc = zlib.crc32(content)

            # 3. Weryfikacja integralności
            if received_crc != calculated_crc:
                frame.corrupt_flag = True
                # Próba odzyskania SN dla logów (może być śmieciem)
                try:
                    frame.seq_num = struct.unpack('!B', content[:1])[0]
                except:
                    pass
                return frame

            # 4. Rozpakowanie poprawnej ramki
            seq_num, type_code, sender_b, receiver_b = struct.unpack('!BBcc', content[:4])
            payload_bytes = content[4:]

            frame.seq_num = seq_num
            frame.type = 'DATA' if type_code == 0 else 'ACK'
            frame.sender = sender_b.decode('utf-8', errors='ignore')
            frame.receiver = receiver_b.decode('utf-8', errors='ignore')
            frame.payload = payload_bytes.decode('utf-8', errors='ignore')

            return frame

        except Exception:
            f = Frame('DATA', 0)
            f.corrupt_flag = True
            return f

    def is_corrupt(self):
        """Zwraca informację, czy ramka jest uszkodzona (błąd sumy kontrolnej)."""
        return self.corrupt_flag