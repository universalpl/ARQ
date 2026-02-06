from logika.frame import Frame
from logika.channel import channel_simulate
from logika.colors import Colors
import config

class Receiver:
    """
    Implementuje warstwę odbiorczą protokołu Go-Back-N ARQ.

    Klasa ta realizuje kluczową zasadę protokołu GBN: **akceptację wyłącznie ramek w poprawnej kolejności**.
    Wszelkie ramki uszkodzone lub nadesłane poza kolejnością (np. "dziury" w numeracji) są
    natychmiast odrzucane, a nadajnik jest informowany o konieczności retransmisji poprzez
    ponowne wysłanie potwierdzenia (ACK) dla ostatniej poprawnie odebranej ramki.

    Attributes:
        expected_seq_num (int): Numer sekwencyjny ramki, której aktualnie oczekuje odbiornik.
                                Jest to wskaźnik 'Next Expected' w oknie odbiorczym o rozmiarze 1.
        max_seq (int): Maksymalna wartość numeru sekwencyjnego (modulo przestrzeni adresowej).
        sender (str): Identyfikator nadawcy (używany w nagłówkach ACK).
        receiver (str): Identyfikator odbiorcy (używany w nagłówkach ACK).
        received_payload (list): Bufor przechowujący dane użytkowe z poprawnie zdekodowanych i
                                 ułożonych w kolejności ramek.
    """

    def __init__(self, max_seq, sender_id="B", receiver_id="A"):
        """
        Inicjalizuje stan odbiornika.

        Args:
            max_seq (int): Zakres numeracji sekwencyjnej (np. 8 dla 3 bitów).
            sender_id (str): ID strony wysyłającej ACK (czyli tego odbiornika).
            receiver_id (str): ID strony odbierającej ACK (czyli nadajnika danych).
        """
        self.expected_seq_num = 0
        self.max_seq = max_seq
        self.sender = sender_id
        self.receiver = receiver_id
        self.received_payload = []
        # NOWE: Licznik ramek odebranych poprawnie, ale jeszcze niepotwierdzonych
        self.pending_ack_count = 0

    def _ack_color_for_data_sn(self, ack_sn: int):
        """
        Oblicza kolor logowania dla ramki ACK.

        Ponieważ ACK N potwierdza odbiór ramki N-1 (w logice kumulacyjnej),
        funkcja ta mapuje kolor ACK na kolor ramki danych, którą to ACK potwierdza.
        """
        data_sn = (ack_sn - 1) % self.max_seq
        return Colors.for_sn(data_sn)

    def receive_frame(self, raw_bytes):
        """
        Główna metoda przetwarzająca dane wejściowe z kanału.

        Realizuje maszynę stanów odbiornika GBN:
        1. **Deserializacja:** Próba odtworzenia struktury ramki z ciągu bitów.
        2. **Weryfikacja CRC:** Sprawdzenie integralności danych. Jeśli suma kontrolna się nie zgadza,
           ramka jest traktowana jak niebyła (lub wysyłane jest zduplikowane ACK).
        3. **Weryfikacja Kolejności:** Porównanie `frame.seq_num` z `self.expected_seq_num`.
           - Zgodność: Dane są akceptowane, okno przesuwa się o 1.
           - Niezgodność: Ramka jest odrzucana (Silent Discard), a odbiornik wymusza retransmisję,
             wysyłając ACK dla numeru, na który wciąż czeka.

        Args:
            raw_bytes (bytes): Surowy ciąg bajtów odebrany z symulatora kanału.

        Returns:
            bytes: Zserializowana ramka ACK gotowa do wysłania zwrotnego przez kanał.
                   Zwraca None, jeśli wejściowe dane były puste (utrata w kanale).
        """
        if raw_bytes is None:
            return None

        frame = Frame.from_bytes(raw_bytes)
        sn = frame.seq_num

        # ---------------------------------------------------------
        # SCENARIUSZ A: BŁĄD (CRC lub Kolejność) -> ACK NATYCHMIAST
        # ---------------------------------------------------------
        # Jeśli coś jest nie tak, nie czekamy! Nadajnik musi wiedzieć o błędzie od razu.
        is_error = False

        if frame.is_corrupt():
            print(f"{Colors.RED}[ODBIORNIK]: Błąd CRC w ramce.{Colors.RESET}")
            is_error = True
        elif sn != self.expected_seq_num:
            print(
                f"{Colors.for_sn(sn)}[ODBIORNIK]: Ramka poza kolejnością (SN={sn}, oczekiwano {self.expected_seq_num}).{Colors.RESET}")
            is_error = True

        if is_error:
            # Zerujemy licznik, bo wysyłamy ACK (który i tak potwierdzi wszystko co było wcześniej)
            self.pending_ack_count = 0

            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            return channel_simulate(ack_frame.to_bytes())

        # ---------------------------------------------------------
        # SCENARIUSZ B: SUKCES -> ACK OPÓŹNIONE (Delayed ACK)
        # ---------------------------------------------------------
        # Ramka jest poprawna i oczekiwana
        self.received_payload.append(frame.payload)
        self.expected_seq_num = (self.expected_seq_num + 1) % self.max_seq

        # Zwiększamy licznik ramek "do potwierdzenia"
        self.pending_ack_count += 1

        print(
            f"{Colors.for_sn(sn)}[ODBIORNIK]: Odebrano SN={sn}. Oczekuję na ACK ({self.pending_ack_count}/{config.ACK_FREQUENCY}).{Colors.RESET}")

        # Sprawdzamy, czy uzbieraliśmy już wystarczająco dużo ramek, żeby wysłać ACK
        if self.pending_ack_count >= config.ACK_FREQUENCY:
            # Wysyłamy zbiorcze potwierdzenie
            ack_sn = self.expected_seq_num
            print(
                f"{Colors.for_sn(ack_sn)}[ODBIORNIK]: Limit osiągnięty. Wysyłam ZBIORCZE ACK SN={ack_sn}{Colors.RESET}")

            self.pending_ack_count = 0  # Reset licznika

            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            return channel_simulate(ack_frame.to_bytes())
        else:
            # Nie wysyłamy nic (oszczędzamy pasmo w kanale zwrotnym)
            return None