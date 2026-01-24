#Konfiguracja Modelu Gilberta-Elliotta

#Szansa wejścia w burzę - na bit
GILBERT_P = 0.00001

#Szansa wyjścia z burzy
GILBERT_R = 0.2

#Błędy w stanie dobrym - szum tła
GILBERT_K = 0.00001

#Błędy w stanie złym - intensywność burzy
GILBERT_H = 0.30


#Reszta
TIMEOUT = 1.0
WINDOW_SIZE = 4
SEQ_BITS = 3
MAX_SEQ = 2 ** SEQ_BITS
TARGET_PACKETS = 30