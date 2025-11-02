PROB_LOSS = 0.15   # Prawdopodobieństwo utraty pakietu/ACK
PROB_ERROR = 0.10  # Prawdopodobieństwo błędu bitowego w pakiecie/ACK
TIMEOUT = 0.6      # Czas oczekiwania na ACK (s)
WINDOW_SIZE = 4    # Rozmiar okna (N)
SEQ_BITS = 3       # Liczba bitów na numer sekwencyjny (2^3 = 8 numerów)
MAX_SEQ = 2 ** SEQ_BITS
TARGET_PACKETS = 15  # (nieużywane już bezpośrednio, ale zostaje)

# --- NOWE: ustawienia pliku i podglądu ---
CHUNK_SIZE = 2048                       # bajtów w jednej ramce DATA
SRC_FILE = "input/kot.jpg"            # ścieżka pliku źródłowego
DEST_FILE = "output/kot_copy.jpg"     # ścieżka pliku docelowego
REFRESH_EVERY_CHUNKS = 1                # co ile chunków odświeżać podgląd
