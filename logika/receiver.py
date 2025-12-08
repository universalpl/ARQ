from logika.frame import Frame
from logika.channel import channel_simulate
from logika.colors import Colors


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

        # 1. Sprawdzenie CRC - priorytetowa weryfikacja integralności
        if frame.is_corrupt():
            print(
                f"{Colors.RED}[ODBIORNIK]: Otrzymano USZKODZONĄ ramkę DATA SN={sn} (Błąd CRC). ODRZUCAM.{Colors.RESET}")
            # Wysłanie duplikatu ACK (Duplicate ACK) informuje nadawcę, że coś poszło nie tak
            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            print(f"{Colors.RED}[ODBIORNIK]: Powtarzam ACK SN={ack_sn} (po błędzie CRC w DATA).{Colors.RESET}")
            return channel_simulate(ack_frame.to_bytes())

        # 2. Sprawdzenie Kolejności (Logika "Sliding Window" rozmiar 1)
        if sn == self.expected_seq_num:
            # SUKCES: Ramka jest tą, na którą czekaliśmy
            print(f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano POPRAWNĄ i OCZEKIWANĄ ramkę DATA SN={sn}.{Colors.RESET}")
            self.received_payload.append(frame.payload)
            self.expected_seq_num = (self.expected_seq_num + 1) % self.max_seq

            # Wysłanie ACK dla NASTĘPNEGO oczekiwanego numeru (Next Expected)
            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            print(f"{self._ack_color_for_data_sn(ack_sn)}[ODBIORNIK]: Wysyłam ACK SN={ack_sn}{Colors.RESET}")
            return channel_simulate(ack_frame.to_bytes())

        else:
            # BŁĄD KOLEJNOŚCI: Ramka z przyszłości lub duplikat starej
            print(
                f"{Colors.for_sn(sn)}[ODBIORNIK]: Otrzymano ramkę DATA SN={sn} poza kolejnością. "
                f"Oczekiwano SN={self.expected_seq_num}. ODRZUCAM.{Colors.RESET}"
            )
            # Ponowne wysłanie ACK dla oczekiwanego numeru (wymuszenie retransmisji u nadawcy)
            ack_sn = self.expected_seq_num
            ack_frame = Frame('ACK', ack_sn, sender_id=self.sender, receiver_id=self.receiver)
            print(f"{Colors.GRAY}[ODBIORNIK]: Powtarzam ACK SN={ack_sn} (by wrócił do Base={ack_sn}).{Colors.RESET}")
            return channel_simulate(ack_frame.to_bytes())