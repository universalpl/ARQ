# config.py

# --- Konfiguracja Modelu Gilberta-Elliotta ---

# P: Szansa wejścia w burzę (na bit).
# 0.0005 = Raz na 2000 bitów. Burze będą rzadkie, ale widoczne.
GILBERT_P = 0.0005

# R: Szansa wyjścia z burzy.
# 0.02 = Średnia długość burzy to 50 bitów (1/0.02).
# Dzięki temu zobaczysz wyraźny fioletowy napis START i po chwili KONIEC.
GILBERT_R = 0.02

# K: Szum tła
GILBERT_K = 0.0001

# H: Burza (50% błędów)
GILBERT_H = 0.50

# --- Reszta ---
TIMEOUT = 1.0
WINDOW_SIZE = 4
SEQ_BITS = 3
MAX_SEQ = 2 ** SEQ_BITS
TARGET_PACKETS = 30