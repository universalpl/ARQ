# test_crc_efficiency.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import config
from logika.frame import Frame
from logika.channel import global_channel
import random
import zlib


def run_detection_test(iterations=10000, mode='BSC', prob=0.01):
    """
    Testuje skuteczność wykrywania błędów przez CRC-32.
    Generuje tabelkę zliczeń: Uszkodzone Fizycznie vs Wykryte vs Niewykryte.
    """
    total_frames = 0
    corrupted_physically = 0  # Fizycznie zmienione przez kanał
    detected_errors = 0  # CRC=Fail (Odrzucone)
    undetected_errors = 0  # CRC=OK, ale Dane=Złe (KATASTROFA!)

    print(f"\n--- TEST: {mode} (Prob/Force={prob:.6f}) | Próbek: {iterations} ---")

    # Przykładowy payload
    original_payload = "TestData_1234567890" * 5
    original_frame = Frame('DATA', 1, original_payload)
    original_bytes = original_frame.to_bytes()

    for _ in range(iterations):
        total_frames += 1

        # 1. Przepuść przez kanał (omijamy logikę ARQ, testujemy samą fizykę i CRC)
        if mode == 'BSC':
            received_bytes = global_channel.propagate_bsc(original_bytes, prob)
        else:
            # Dla Gilberta wymuszamy parametry
            config.GILBERT_H = prob
            config.GILBERT_P = 0.05
            config.GILBERT_R = 0.1
            received_bytes = global_channel.propagate(original_bytes)

        # 2. Sprawdź, czy fizycznie doszło do zmiany bitów (porównanie bajtów)
        if original_bytes != received_bytes:
            corrupted_physically += 1

            # 3. Deserializacja i sprawdzenie werdyktu CRC
            # (Uwaga: normalnie receiver by to robił, tu robimy ręcznie do statystyki)
            decoded_frame = Frame.from_bytes(received_bytes)

            if decoded_frame.is_corrupt():
                detected_errors += 1
            else:
                # CRC mówi "OK", ale bajty są inne -> BŁĄD NIEWYKRYTY!
                undetected_errors += 1
                # print(f"{Colors.RED}!!! NIEWYKRYTY BŁĄD !!!{Colors.RESET}")

    # --- WYNIKI (TABELKA) ---
    print(f"Wysłane ramki:         {total_frames}")
    print(f"Uszkodzone fizycznie:  {corrupted_physically}")
    print(f"  -> Wykryte (CRC):    {detected_errors}")
    print(f"  -> NIEWYKRYTE:       {undetected_errors} ")

    if corrupted_physically > 0:
        det_rate = (detected_errors / corrupted_physically) * 100
        print(f"Skuteczność CRC:       {det_rate:.4f}%")
    else:
        print("Brak uszkodzeń w kanale.")

def run_crc_collision_hunt(iterations=1_000_000):
    """
    Szybki test kolizji CRC – zgodny formatem z testami BSC.
    Uszkadza losowe bajty i sprawdza, czy CRC je wykryje.
    """
    print(f"\n--- TEST: CRC_COLLISION_HUNT | Próbek: {iterations:,} ---")

    # Ramka testowa (mała, aby działało bardzo szybko)
    payload = b"HELLO_WORLD_TEST"
    crc_ok = zlib.crc32(payload)

    total_frames = iterations
    corrupted_physically = 0
    detected_errors = 0
    undetected_errors = 0

    for _ in range(iterations):
        corrupted = bytearray(payload)

        # wprowadzamy 1–3 losowe zmiany
        for _ in range(random.randint(1, 3)):
            idx = random.randrange(len(corrupted))
            corrupted[idx] ^= random.randrange(1, 256)

        # zmieniono fizycznie? (zawsze tak, ale zostawiamy licznik dla spójności)
        corrupted_physically += 1

        # CRC sprawdzamy jak w normalnej ramce
        if zlib.crc32(corrupted) != crc_ok:
            detected_errors += 1
        else:
            undetected_errors += 1

    print(f"Wysłane ramki:         {total_frames}")
    print(f"Uszkodzone fizycznie:  {corrupted_physically}")
    print(f"  -> Wykryte (CRC):    {detected_errors}")
    print(f"  -> NIEWYKRYTE:       {undetected_errors}")

    det_rate = (detected_errors / corrupted_physically) * 100
    print(f"Skuteczność CRC:       {det_rate:.4f}%")


if __name__ == "__main__":
    print("Symulacja weryfikacji modelu błędów i skuteczności CRC-32")


    run_crc_collision_hunt(5_000_00) #symulacja nie przez kanał, NIEWYKRYTE BŁĘDY

    # 20 poziomów szumu BSC – od bardzo małych do ekstremalnych
    probability_levels = [
        0.00001, 0.00003, 0.0001, 0.0003, 0.001,
        0.003, 0.005, 0.007, 0.01, 0.02,
        0.03, 0.25, 0.5
    ]

    for p in probability_levels:
        # dynamiczna liczba prób, żeby test trwał rozsądnie

        '''
        if p < 0.005:
            iters = 20000
        elif p < 0.05:
            iters = 10000
        else:
            iters = 5000
            '''
        iters = 5000

        run_detection_test(iterations=iters, mode='BSC', prob=p)



