# channel.py

import random
import time
import copy
from frame import Frame
from config import PROB_LOSS, PROB_ERROR
from colors import Colors


def channel_simulate(frame: Frame):
    """Symuluje kanał z utratą i błędami (BSC), bez modyfikowania oryginalnej ramki."""
    if frame is None:
        return None

    sn = frame.seq_num

    # Utrata
    if random.random() < PROB_LOSS:
        print(f"{Colors.RED}  [KANAŁ]: ZGUBIONO ramkę {frame.type} o SN={sn}{Colors.RESET}")
        return None

    # Pracujemy na kopii, by nie psuć bufora nadawcy
    tx = copy.deepcopy(frame)

    # Błąd bitowy
    if random.random() < PROB_ERROR:
        print(f"{Colors.for_sn(sn)}  [KANAŁ]: BŁĄD BITOWY w ramce {tx.type} o SN={sn}. Zepsuto CRC.{Colors.RESET}")
        tx.corrupt_frame()

    time.sleep(random.uniform(0.01, 0.05))  # szybsza symulacja
    return tx
