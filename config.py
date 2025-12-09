# config.py

# --- Konfiguracja Modelu Gilberta-Elliotta ---

# P: Szansa wejścia w burzę (na bit).
# Zmniejszamy, żeby wchodził rzadziej.
GILBERT_P = 0.00001

# R: Szansa wyjścia z burzy.
# ZWIĘKSZAMY! 0.1 oznacza, że średnio burza trwa 10 bitów.
# Poprzednio miałeś małe R, co oznaczało burzę trwającą setki bitów (całe ramki).
GILBERT_R = 0.2

# K: Błędy w stanie Dobrym (szum tła).
GILBERT_K = 0.00001

# H: Błędy w stanie Złym (intensywność burzy).
# Zmniejszamy trochę, żeby dać szansę na przeżycie nagłówka
GILBERT_H = 0.30

# --- Reszta ---
TIMEOUT = 1.0
WINDOW_SIZE = 4
SEQ_BITS = 3
MAX_SEQ = 2 ** SEQ_BITS
TARGET_PACKETS = 30