# test_crc_efficiency.py
import config
from frame import Frame
from channel import global_channel
from colors import Colors
import struct


def run_detection_test(iterations=10000, mode='BSC', prob=0.01):
    """
    Testuje skuteczność wykrywania błędów przez CRC-32.
    Generuje tabelkę zliczeń: Uszkodzone Fizycznie vs Wykryte vs Niewykryte.
    """
    total_frames = 0
    corrupted_physically = 0  # Fizycznie zmienione przez kanał
    detected_errors = 0  # CRC=Fail (Odrzucone)
    undetected_errors = 0  # CRC=OK, ale Dane=Złe (KATASTROFA!)

    print(f"\n--- TEST: {mode} (Prob/Force={prob}) | Próbek: {iterations} ---")

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
    print(f"  -> NIEWYKRYTE:       {undetected_errors} (To są błędy, które przechodzą cicho)")

    if corrupted_physically > 0:
        det_rate = (detected_errors / corrupted_physically) * 100
        print(f"Skuteczność CRC:       {det_rate:.4f}%")
    else:
        print("Brak uszkodzeń w kanale.")


if __name__ == "__main__":
    print("Symulacja weryfikacji modelu błędów i skuteczności CRC-32")

    # Zgodnie z notatkami: "poziomy prawdopodobieństw: mało, średnio, dużo"

    # 1. MAŁO (BSC p=0.001) -> Powinno być 100% wykrytych
    run_detection_test(iterations=5000, mode='BSC', prob=0.001)

    # 2. ŚREDNIO (BSC p=0.01) -> Dużo błędów, CRC wciąż powinno trzymać
    run_detection_test(iterations=5000, mode='BSC', prob=0.01)

    # 3. DUŻO / EKSTREMALNIE (BSC p=0.3) -> 30% bitów zepsutych.
    # Tutaj struktura ramki może się tak rozsypać, że CRC przypadkiem spasuje (bardzo rzadkie, ale możliwe)
    run_detection_test(iterations=5000, mode='BSC', prob=0.3)