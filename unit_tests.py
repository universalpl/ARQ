"""
Moduł zawierający testy jednostkowe (Unit Tests).
Weryfikuje poprawność działania poszczególnych komponentów systemu w izolacji:
- Ramki (serializacja, CRC)
- Nadajnika (logika okna, bufor)
- Odbiornika (odrzucanie duplikatów)
"""
# ... reszta kodu bez zmian ...

# unit_tests.py
import unittest
import struct
from frame import Frame
from sender import Sender
from receiver import Receiver  # <--- POPRAWKA 1: Dodano brakujący import
from channel import GilbertChannel
import config


class TestGoBackN(unittest.TestCase):

    def setUp(self):
        """Uruchamiane przed każdym testem."""
        print(f"\n[TEST]: {self._testMethodName}")

    # --- TESTY RAMEK (FRAME) ---

    def test_frame_serialization_clean(self):
        """Sprawdza, czy ramka po wysłaniu i odebraniu jest taka sama."""
        original_frame = Frame(frame_type='DATA', seq_num=5, payload="TestPayload", sender_id="A", receiver_id="B")

        # Serializacja do bajtów
        raw_bytes = original_frame.to_bytes()

        # Deserializacja z bajtów
        restored_frame = Frame.from_bytes(raw_bytes)

        self.assertEqual(original_frame.seq_num, restored_frame.seq_num)
        self.assertEqual(original_frame.payload, restored_frame.payload)
        self.assertFalse(restored_frame.is_corrupt(), "Poprawna ramka nie powinna mieć flagi corrupt!")

    def test_crc_detection(self):
        """Sprawdza, czy zmiana 1 bitu powoduje błąd CRC."""
        frame = Frame('DATA', 1, "WazneDane")
        raw_bytes = bytearray(frame.to_bytes())

        # Zmieniamy ostatni bajt (symulujemy błąd)
        raw_bytes[-1] = raw_bytes[-1] ^ 0xFF

        # Próbujemy otworzyć uszkodzoną ramkę
        corrupt_frame = Frame.from_bytes(raw_bytes)

        self.assertTrue(corrupt_frame.is_corrupt(), "CRC powinno wykryć zmianę bitów!")
        print("   -> CRC poprawnie wykryło uszkodzenie.")

    # --- TESTY NADAJNIKA (SENDER) ---

    def test_sender_window_logic(self):
        """Sprawdza matematykę przesuwanego okna."""
        # Okno rozmiar 4, Max Seq 8
        sender = Sender(window_size=4, max_seq=8)
        sender.base = 0

        # Dla Base=0, w oknie są: 0, 1, 2, 3.
        self.assertTrue(sender._is_within_window(0))
        self.assertTrue(sender._is_within_window(3))
        self.assertFalse(sender._is_within_window(4), "4 powinno być poza oknem [0,1,2,3]")

        print("   -> Logika okna (base=0) działa.")

    def test_sender_window_wrap_around(self):
        """Sprawdza 'zawijanie się' licznika (modulo)."""
        sender = Sender(window_size=4, max_seq=8)
        # Przesuwamy okno na koniec zakresu
        sender.base = 6
        # Okno to teraz: 6, 7, 0, 1 (bo max_seq=8)

        self.assertTrue(sender._is_within_window(6))
        self.assertTrue(sender._is_within_window(7))
        self.assertTrue(sender._is_within_window(0))
        self.assertTrue(sender._is_within_window(1))
        self.assertFalse(sender._is_within_window(2), "2 powinno być poza oknem [6,7,0,1]")

        print("   -> Logika okna na krawędzi (modulo) działa.")

    # --- TESTY KANAŁU ---

    def test_channel_structure(self):
        """Sprawdza czy kanał nie gubi bajtów (niezależnie od błędów)."""
        channel = GilbertChannel()
        data = b'1234567890'

        # Wyłączamy model Gilberta na chwilę, żeby nie flipował bitów losowo
        # Chcemy sprawdzić tylko czy długość się zgadza
        # (Wymaga configu bez błędów lub szczęścia, ale sprawdzamy strukturę)
        output = channel.propagate(data)

        self.assertEqual(len(data), len(output), "Kanał nie powinien zmieniać długości danych!")

    # --- NOWE TESTY ODBIORNIKA (RECEIVER) ---

    def test_receiver_out_of_order_logic(self):
        """Sprawdza, czy Odbiornik odrzuca ramki spoza kolejności (GBN)."""
        receiver = Receiver(max_seq=8)
        # Odbiornik oczekuje SN=0

        # 1. Tworzymy poprawne ramki
        frame_0 = Frame('DATA', 0, "Payload0")
        frame_2 = Frame('DATA', 2, "Payload2_SKIPPED")  # Dziura! Brakuje 1

        # 2. Wysyłamy poprawną (0)
        try:
            receiver.receive_frame(frame_0.to_bytes())
        except:
            pass

        self.assertEqual(receiver.expected_seq_num, 1, "Po odebraniu SN=0, odbiornik powinien czekać na 1.")

        # 3. Wysyłamy ramkę z dziurą (2 zamiast 1)
        try:
            receiver.receive_frame(frame_2.to_bytes())
        except:
            pass

        self.assertEqual(receiver.expected_seq_num, 1,
                         "Odbiornik NIE POWINIEN przesunąć okna po otrzymaniu SN=2, gdy czeka na 1!")
        print("   -> Odbiornik prawidłowo odrzuca pakiety spoza kolejności.")

    # --- NOWE TESTY LOGIKI BUFORA (SENDER) ---

    def test_sender_cumulative_ack(self):
        """Sprawdza, czy ACK czyści bufor nadajnika (zwolnienie pamięci)."""
        sender = Sender(window_size=4, max_seq=8)
        sender.base = 0

        # 1. Symulujemy, że wysłaliśmy 3 pakiety (są w buforze)
        sender.buffer[0] = Frame('DATA', 0)
        sender.buffer[1] = Frame('DATA', 1)
        sender.buffer[2] = Frame('DATA', 2)

        sender.on_ack(2)

        self.assertEqual(sender.base, 2, "Base powinien przesunąć się na 2.")
        self.assertNotIn(0, sender.buffer, "Pakiet 0 powinien zniknąć z bufora.")
        self.assertNotIn(1, sender.buffer, "Pakiet 1 powinien zniknąć z bufora.")
        self.assertIn(2, sender.buffer, "Pakiet 2 powinien NADAL być w buforze (czeka na ACK=3).")

        print("   -> Kumulacyjne ACK poprawnie czyści bufor.")

    # --- TESTY STRUKTURY DANYCH ---

    def test_ack_frame_integrity(self):
        """Sprawdza, czy ramka typu ACK jest poprawnie rozróżniana od DATA."""
        # POPRAWKA 2: Używamy pojedynczych znaków dla ID ("B", "A"), bo struct wymaga 1 bajta
        ack_frame = Frame(frame_type='ACK', seq_num=7, sender_id="B", receiver_id="A")
        bytes_obj = ack_frame.to_bytes()

        restored = Frame.from_bytes(bytes_obj)

        self.assertEqual(restored.type, 'ACK', "Typ ramki powinien pozostać ACK.")
        self.assertEqual(restored.seq_num, 7)
        self.assertEqual(restored.payload, "", "Ramka ACK nie powinna mieć payloadu.")

        print("   -> Rozróżnianie typów ramek (ACK/DATA) działa.")


if __name__ == '__main__':
    unittest.main()