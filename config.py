PROB_LOSS = 0.15  # Prawdopodobieństwo utraty pakietu/ACK
PROB_ERROR = 0.10  # Prawdopodobieństwo błędu bitowego w pakiecie/ACK
TIMEOUT = 0.6  # Czas oczekiwania na ACK (w sekundach)
WINDOW_SIZE = 4  # Rozmiar okna (N)
SEQ_BITS = 3  # Liczba bitów na numer sekwencyjny (2^3 = 8 numerów)
MAX_SEQ = 2 ** SEQ_BITS  # Maksymalna liczba numerów sekwencyjnych (0 do 7)
TARGET_PACKETS = 15  # Cel: liczba pakietów do poprawnego przesłania