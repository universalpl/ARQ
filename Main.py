import random
import time

# --- 1. Konfiguracja Globalna ---
PROB_LOSS = 0.15  # Prawdopodobieństwo utraty pakietu/ACK
PROB_ERROR = 0.10  # Prawdopodobieństwo błędu bitowego w pakiecie/ACK
TIMEOUT = 3.0  # Czas oczekiwania na ACK (w sekundach)
WINDOW_SIZE = 4  # Rozmiar okna (N)
SEQ_BITS = 3  # Liczba bitów na numer sekwencyjny (2^3 = 8 numerów)
MAX_SEQ = 2 ** SEQ_BITS  # Maksymalna liczba numerów sekwencyjnych (0 do 7)
TARGET_PACKETS = 15  # Cel: liczba pakietów do poprawnego przesłania


# --- 2. Struktury Danych ---

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


# --- 3. Moduł Kanału (Channel) ---

def channel_simulate(frame):
    """Symuluje kanał z utratą i błędami."""

    if random.random() < PROB_LOSS:
        print(f"  [KANAŁ]: ZGUBIONO ramkę {frame.type} o SN={frame.seq_num}")
        return None  # Utrata (Losowe Gubienie)

    if random.random() < PROB_ERROR:
        print(f"  [KANAŁ]: BŁĄD BITOWY w ramce {frame.type} o SN={frame.seq_num}. Zepsuto CRC.")
        frame.corrupt_frame()  # Zmiana (Losowe Zmiany)

    time.sleep(random.uniform(0.1, 0.5))  # Symulacja opóźnienia
    return frame


# --- 4. Moduł Nadawcy (Sender) ---

class Sender:
    def __init__(self, window_size, max_seq):
        self.window_size = window_size
        self.max_seq = max_seq
        self.base = 0  # Baza okna (najstarszy pakiet, na który czekamy)
        self.next_seq_num = 0  # Numer sekwencyjny następnego pakietu
        self.buffer = {}  # Bufor retransmisji {SN: Frame}
        self.timer_start = None  # Czas startu głównego timera

    def _is_within_window(self, seq_num):
        """Sprawdza, czy numer sekwencyjny mieści się w buforze okna."""
        return (seq_num - self.base) % self.max_seq < self.window_size

    def send_frame(self, frame):
        """Symuluje wysłanie ramki do kanału."""
        print(f"[NADAJNIK]: Wysyłam {frame}")
        return channel_simulate(frame)

    def process_data(self, data_packet):
        """Przygotowuje i buforuje dane do wysłania."""
        frame = Frame('DATA', self.next_seq_num, data_packet)
        if self._is_within_window(self.next_seq_num):
            self.buffer[self.next_seq_num] = frame
            self.next_seq_num = (self.next_seq_num + 1) % self.max_seq
            return frame
        else:
            # Okno jest pełne - musimy czekać.
            # W symulacji zakładamy, że dane są dodawane tylko, gdy jest miejsce.
            return None

    def start_timer(self):
        """Uruchamia timer dla najstarszego pakietu w oknie (Base)."""
        self.timer_start = time.time()
        print(f"[NADAJNIK]: STARTUJĘ timer dla Base={self.base}")

    def is_timeout(self):
        """Sprawdza, czy upłynął limit czasu."""
        if self.timer_start is not None and time.time() - self.timer_start > TIMEOUT:
            print(f"[NADAJNIK]: TIMEOUT! dla Base={self.base}")
            self.timer_start = None  # Zresetuj, aby wywołać retransmisję
            return True
        return False

    def retransmit_window(self, channel):
        """Retransmituje wszystkie pakiety z aktualnego okna (Go-Back-N)."""
        retransmitted_count = 0
        current_seq = self.base

        while current_seq != self.next_seq_num:
            frame = self.buffer.get(current_seq)
            if frame:
                channel.send(frame)
                retransmitted_count += 1
            current_seq = (current_seq + 1) % self.max_seq

        self.start_timer()  # Uruchom timer ponownie
        return retransmitted_count


# --- 5. Moduł Odbiorcy (Receiver) ---

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


# --- 6. Główna Symulacja ---

def run_go_back_n_simulation():
    sender = Sender(WINDOW_SIZE, MAX_SEQ)
    receiver = Receiver(MAX_SEQ)

    data_to_send = [f"Pakiet_{i + 1}" for i in range(TARGET_PACKETS)]
    sent_data_idx = 0
    total_transmissions = 0
    total_retransmissions = 0

    print("--- START SYMULACJI GO-BACK-N ARQ ---")
    print(f"Parametry: N={WINDOW_SIZE}, Strata={PROB_LOSS * 100}%, Błąd={PROB_ERROR * 100}%")

    start_time = time.time()

    while len(receiver.received_payload) < TARGET_PACKETS:

        # --- Krok 1: Wysłanie nowych danych (jeśli okno nie jest pełne) ---

        # Sprawdzamy, czy w oknie jest jeszcze miejsce i czy są jeszcze dane do wysłania
        if sender._is_within_window(sender.next_seq_num) and sent_data_idx < TARGET_PACKETS:
            data = data_to_send[sent_data_idx]
            frame_to_send = sender.process_data(data)

            if frame_to_send:
                # Jeśli to jest pierwszy pakiet w oknie, uruchamiamy timer
                if sender.base == frame_to_send.seq_num:
                    sender.start_timer()

                # Symulacja wysłania
                ack_from_channel = sender.send_frame(frame_to_send)
                total_transmissions += 1
                sent_data_idx += 1

                # Natychmiastowa obsługa ramki DATA przez odbiornik
                ack_from_receiver = receiver.receive_frame(ack_from_channel)

        # --- Krok 2: Obsługa timeout'u i retransmisji ---

        if sender.is_timeout():
            # W GBN: Jeśli upłynął limit czasu, wracamy do Base i retransmitujemy od tego miejsca.
            retrans_count = 0
            current_seq = sender.base

            # Musimy retransmitować wszystkie pakiety od Base do Next_Seq_Num - 1
            while current_seq != sender.next_seq_num:
                frame_to_resend = sender.buffer.get(current_seq)
                if frame_to_resend:
                    ack_from_channel = sender.send_frame(frame_to_resend)
                    total_transmissions += 1
                    retrans_count += 1

                    # Natychmiastowa obsługa ramki DATA przez odbiornik (w prostym modelu)
                    ack_from_receiver = receiver.receive_frame(ack_from_channel)

                current_seq = (current_seq + 1) % sender.max_seq

            total_retransmissions += retrans_count
            sender.start_timer()  # Uruchom timer ponownie

        # --- Krok 3: Obsługa potwierdzeń (ACK) ---

        # W prostym modelu ACK z KANAŁU jest przekazywane bezpośrednio do Nadawcy,
        # ale w realistycznym scenariuszu Nadawca musiałby odbierać z kanału.
        # W naszej pętli, symulujemy to poprzez analizę wyniku ACK od odbiornika:

        if 'ack_from_receiver' in locals() and ack_from_receiver is not None:
            if not ack_from_receiver.is_corrupt():
                ack_num = ack_from_receiver.seq_num

                # Go-Back-N (ACK kumulacyjne):
                # ACK informuje o następnym OCZEKIWANYM pakiecie (czyli wszystkie do ACK_num-1 zostały odebrane)

                # Obliczanie, ile pakietów potwierdzono (posuwamy BASE)
                while sender.base != ack_num:
                    print(
                        f"[NADAJNIK]: Otrzymano POPRAWNE ACK SN={ack_num}. Przesuwam BASE z {sender.base} do {ack_num}.")
                    sender.buffer.pop(sender.base, None)  # Usuwamy potwierdzone pakiety z bufora
                    sender.base = (sender.base + 1) % sender.max_seq

                    if sender.base == sender.next_seq_num:
                        # Jeśli okno jest puste, zatrzymaj timer
                        sender.timer_start = None
                        break

                # Jeśli przesunęliśmy bazę, uruchom timer dla nowego pierwszego elementu
                if sender.base != ack_num and sender.base != sender.next_seq_num:
                    sender.start_timer()
            else:
                print(f"[NADAJNIK]: Otrzymano USZKODZONE ACK. IGNORUJĘ. Czekam na retransmisję lub timeout.")

        time.sleep(0.1)  # Krótka pauza symulacyjna

    end_time = time.time()

    # --- Wyniki ---
    print("\n--- PODSUMOWANIE SYMULACJI ---")
    print(f"Pakiety dostarczone: {len(receiver.received_payload)}/{TARGET_PACKETS}")
    print(f"Całkowity czas: {end_time - start_time:.2f} s")
    print(f"Całkowita liczba transmisji: {total_transmissions}")
    print(f"Liczba retransmisji (DATA): {total_retransmissions}")
    efficiency = TARGET_PACKETS / total_transmissions
    print(f"Wydajność (Pakiety Użyteczne / Wszystkie Transmisje): {efficiency:.2f}")

# Uruchomienie symulacji:
run_go_back_n_simulation()