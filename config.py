# config.py

# --- Konfiguracja Modelu Gilberta-Elliotta ---

# P: Szansa wejścia w burzę.
# Zmniejszamy drastycznie, bo losujemy to co każdy bit!
# 0.03% szans na bit daje sporą szansę, że w ramce (160 bitów) zdarzy się przejście.
GILBERT_P = 0.0003

# R: Szansa wyjścia z burzy.
# Zmniejszamy, aby burza trwała dłużej (średnio 20 bitów: 1/0.05).
# To stworzy realną "wiązkę", która zniszczy fragment ramki.
GILBERT_R = 0.05

# K: Błędy w stanie Dobrym.
# Powinno być czysto. Dajmy bardzo małą szansę na losowy "flip".
GILBERT_K = 0.0001

# H: Błędy w stanie Złym.
# Tutaj jest rzeźnia (50% szans na zmianę bitu).
GILBERT_H = 0.50

# --- Reszta ---
# Timeout 0.6s jest OK, jeśli time.sleep w kanale to 0.01-0.05s.
TIMEOUT = 1.0       # Zwiększyłbym lekko dla bezpieczeństwa
WINDOW_SIZE = 4
SEQ_BITS = 3
MAX_SEQ = 2 ** SEQ_BITS
TARGET_PACKETS = 30