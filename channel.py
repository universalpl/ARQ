# channel.py
import random
import time
from config import GILBERT_P, GILBERT_R, GILBERT_K, GILBERT_H
from colors import Colors


class GilbertChannel:
    def __init__(self):
        # Zaczynamy w stanie Dobrym ('G')
        self.state = 'G'

    def propagate(self, data_bytes: bytearray) -> bytearray:
        """
        Przepuszcza dane przez kanał Gilberta-Elliotta.
        Operuje na bitach. Może zmienić bity w data_bytes.
        """
        if data_bytes is None:
            return None

        # Symulacja opóźnienia fizycznego
        time.sleep(random.uniform(0.01, 0.05))

        # Tworzymy kopię, żeby nie psuć oryginału u nadawcy!
        corrupted_data = bytearray(data_bytes)

        bit_errors_count = 0
        total_bits = len(corrupted_data) * 8

        # Iterujemy przez każdy BAJT
        for i in range(len(corrupted_data)):
            byte_val = corrupted_data[i]
            new_byte_val = 0

            # Iterujemy przez każdy BIT w bajcie (od 0 do 7)
            for bit_pos in range(8):
                # 1. Pobierz aktualny bit (0 lub 1)
                current_bit = (byte_val >> bit_pos) & 1

                # 2. Model Gilberta: Zmiana stanu (G <-> B)
                if self.state == 'G':
                    if random.random() < GILBERT_P:
                        self.state = 'B'
                else:  # self.state == 'B'
                    if random.random() < GILBERT_R:
                        self.state = 'G'

                # 3. Model Gilberta: Decyzja o błędzie (flip bit)
                error_prob = GILBERT_K if self.state == 'G' else GILBERT_H

                if random.random() < error_prob:
                    # Błąd! Odwracamy bit (XOR 1)
                    current_bit = current_bit ^ 1
                    bit_errors_count += 1

                # Składamy bajt z powrotem
                new_byte_val |= (current_bit << bit_pos)

            corrupted_data[i] = new_byte_val

        # Logowanie (opcjonalne, żebyś widział co się dzieje)
        if bit_errors_count > 0:
            print(f"{Colors.RED}  [KANAŁ]: Model Gilberta zmienił {bit_errors_count} bitów (Wiązka!).{Colors.RESET}")

        return corrupted_data


# Instancja globalna kanału (żeby pamiętał stan między ramkami, jeśli chcesz)
# Lub można tworzyć nową w main.
# Tutaj użyjemy globalnej dla uproszczenia importów.
global_channel = GilbertChannel()


def channel_simulate(data_bytes):
    # Wrapper zachowujący starą nazwę funkcji
    return global_channel.propagate(data_bytes)