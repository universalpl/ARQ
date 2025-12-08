# config.py

# --- Konfiguracja Modelu Gilberta-Elliotta ---


# P: Szansa wejścia w burzę.
GILBERT_P = 0.00005
# R: Szansa wyjścia z burzy.
GILBERT_R = 0.1
# K: Błędy w stanie Dobrym.
GILBERT_K = 0.000005
# H: Błędy w stanie Złym.
GILBERT_H = 0.005


# --- Reszta ---
# Timeout 0.6s jest OK, jeśli time.sleep w kanale to 0.01-0.05s.
TIMEOUT = 0.4       # Zwiększyłbym lekko dla bezpieczeństwa
WINDOW_SIZE = 4
SEQ_BITS = 3
MAX_SEQ = 2 ** SEQ_BITS
TARGET_PACKETS = 30