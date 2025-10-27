# channel.py

import random
import time
# Pamiętaj, aby zaimportować Frame, bo jej używasz w argumencie!
from frame import Frame

# Zmienne globalne muszą być dostępne lub przekazane
PROB_LOSS = 0.15
PROB_ERROR = 0.10


def channel_simulate(frame: Frame):
    """Symuluje kanał z utratą i błędami."""

    if frame is None:
        return None  # Obsługa pustego wejścia

    # UWAGA: W symulacji GBN, Nadawca wywołuje channel_simulate.
    # Aby Channel miał dostęp do stałych globalnych (PROB_LOSS, PROB_ERROR),
    # muszą one być albo globalnie zdefiniowane, albo przekazane.
    global PROB_LOSS, PROB_ERROR

    if random.random() < PROB_LOSS:
        print(f"  [KANAŁ]: ZGUBIONO ramkę {frame.type} o SN={frame.seq_num}")
        return None  # Utrata (Losowe Gubienie)

    if random.random() < PROB_ERROR:
        print(f"  [KANAŁ]: BŁĄD BITOWY w ramce {frame.type} o SN={frame.seq_num}. Zepsuto CRC.")
        frame.corrupt_frame()  # Zmiana (Losowe Zmiany)

    time.sleep(random.uniform(0.1, 0.5))  # Symulacja opóźnienia
    return frame