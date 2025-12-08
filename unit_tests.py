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
import config
from frame import Frame
from sender import Sender
from receiver import Receiver
from channel import GilbertChannel


class TestGoBackN(unittest.TestCase):

    def setUp(self):
        """
        Uruchamiane przed KAŻDYM testem.
        Wyłączamy losowość kanału, aby testy logiki były stabilne.
        """
        print(f"\n[TEST]: {self._testMethodName}")

        # Zapamiętujemy oryginalne ustawienia
        self.orig_p = config.GILBERT_P
        self.orig_k = config.GILBERT_K

        # Ustawiamy idealny kanał dla testów logicznych
        config.GILBERT_P = 0.0
        config.GILBERT_K = 0.0
        config.GILBERT_R = 1.0

    def tearDown(self):
        """Przywracamy ustawienia po teście."""
        config.GILBERT_P = self.orig_p
        config.GILBERT_K = self.orig_k

    # --- TESTY RAMEK (FRAME) ---

    def test_frame_serialization_clean(self):
        """Sprawdza, czy ramka po zamianie na bajty i powrocie jest identyczna."""
        original_frame = Frame(frame_type='DATA', seq_num=5, payload="TestPayload", sender_id="A", receiver_id="B")

        # Serializacja do bajtów
        raw_bytes = original_frame.to_bytes()

        # Deserializacja z bajtów
        restored_frame = Frame.from_bytes(raw_bytes)

        self.assertEqual(original_frame.seq_num, restored_frame.seq_num)
        self.assertEqual(original_frame.payload, restored_frame.payload)
        self.assertFalse(restored_frame.is_corrupt(), "Poprawna ramka nie powinna mieć flagi corrupt!")
        print("   -> Serializacja/Deserializacja OK.")

    def test_crc_detection(self):
        """Sprawdza, czy ręczna zmiana 1 bitu powoduje błąd CRC."""
        frame = Frame('DATA', 1, "WazneDane")
        raw_bytes = bytearray(frame.to_bytes())

        # Zmieniamy ostatni bajt (wymuszamy błąd fizyczny)
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

    def test_sender_cumulative_ack(self):
        """Sprawdza, czy ACK czyści bufor nadajnika (zwolnienie pamięci)."""
        sender = Sender(window_size=4, max_seq=8)
        sender.base = 0

        # Symulujemy dodanie ramek do bufora
        sender.buffer[0] = Frame('DATA', 0)
        sender.buffer[1] = Frame('DATA', 1)

        # Otrzymujemy ACK 2 (potwierdza 0 i 1)
        sender.on_ack(2)

        self.assertEqual(sender.base, 2, "Base powinien przesunąć się na 2.")
        self.assertNotIn(0, sender.buffer, "Pakiet 0 powinien zniknąć z bufora.")
        self.assertNotIn(1, sender.buffer, "Pakiet 1 powinien zniknąć z bufora.")
        print("   -> Kumulacyjne ACK poprawnie czyści bufor.")

    # --- TESTY ODBIORNIKA (RECEIVER) ---

    def test_receiver_out_of_order_logic(self):
        """Sprawdza, czy Odbiornik odrzuca ramki spoza kolejności."""
        receiver = Receiver(max_seq=8)
        receiver.expected_seq_num = 1  # Czeka na 1

        # Tworzymy ramkę z numerem 5 (duża dziura)
        frame_bad = Frame('DATA', 5, "ZlaKolejnosc")

        # Odbiornik przetwarza bajty
        ack_bytes = receiver.receive_frame(frame_bad.to_bytes())

        # Odbiornik powinien odesłać ACK dla tego, na co czeka (czyli 1)
        if ack_bytes:
            ack_frame = Frame.from_bytes(ack_bytes)
            self.assertEqual(ack_frame.seq_num, 1, "Powinien wysłać ACK dla oczekiwanego numeru (1)")

        self.assertEqual(receiver.expected_seq_num, 1, "Odbiornik nie powinien przesunąć okna.")
        print("   -> Odbiornik prawidłowo odrzuca pakiety spoza kolejności.")

    # --- TESTY KANAŁU ---

    def test_channel_pass_through(self):
        """Sprawdza czy kanał przepuszcza dane (przy wyłączonych błędach)."""
        # W setUp wyłączyliśmy błędy, więc kanał powinien być przezroczysty
        channel = GilbertChannel()
        data = b'Test1234'

        output = channel.propagate(bytearray(data))

        self.assertEqual(data, output, "Przy zerowym P i K kanał nie powinien zmieniać danych.")
        print("   -> Kanał poprawnie przekazuje dane w idealnych warunkach.")


if __name__ == '__main__':
    unittest.main()