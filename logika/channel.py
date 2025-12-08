# channel.py
import random
import time
import config
from logika.colors import Colors

# Funkcja pomocnicza do wyświetlania bitów
def bits_to_string(data_bytes):
    # Zamienia bajty na ciąg zer i jedynek (np. "01001000 11100101")
    return ' '.join(format(b, '08b') for b in data_bytes)

class GilbertChannel:
    def __init__(self):
        # Zaczynamy w stanie Dobrym ('G')
        self.state = 'G'

    def propagate(self, data_bytes: bytearray) -> bytearray:
        """
        Symuluje fizyczną propagację sygnału przez medium.
        """
        if data_bytes is None:
            return None

        # Symulacja opóźnienia fizycznego
       # time.sleep(0.001)

        # 1. PODEJRZYJ BITY NA WEJŚCIU (Przed zmianami)
        # Warto to robić tylko przy małej liczbie pakietów, bo zaśmieci konsolę
        # print(f"   [KANAŁ WEJŚCIE]: {bits_to_string(data_bytes)}")

        corrupted_data = bytearray(data_bytes)
        bit_errors_count = 0

        # Iteracja po bajtach
        for i in range(len(corrupted_data)):
            byte_val = corrupted_data[i]
            new_byte_val = 0

            # Iteracja po bitach w bajcie
            for bit_pos in range(8):
                # Pobierz bit (0 lub 1)
                current_bit = (byte_val >> bit_pos) & 1

                # A. Zmiana stanu Gilberta (Łańcuch Markowa)
                if self.state == 'G':
                    if random.random() < config.GILBERT_P:
                        self.state = 'B'
                else:  # self.state == 'B'
                    if random.random() < config.GILBERT_R:
                        self.state = 'G'

                # B. Decyzja o błędzie (Bernoulli trial) zależna od stanu
                error_prob = config.GILBERT_K if self.state == 'G' else config.GILBERT_H

                if random.random() < error_prob:
                    current_bit = current_bit ^ 1  # Inwersja bitu (XOR 1)
                    bit_errors_count += 1

                # Zapisz bit do nowego bajtu
                new_byte_val |= (current_bit << bit_pos)

            # Zapisz przetworzony bajt z powrotem do tablicy
            corrupted_data[i] = new_byte_val

        # Logowanie błędów
        if bit_errors_count > 0:
            print(f"{Colors.RED}  [KANAŁ]: Model Gilberta zmienił {bit_errors_count} bitów (Wiązka!).{Colors.RESET}")
            # 2. PODEJRZYJ BITY NA WYJŚCIU (Tylko jeśli zaszła zmiana)
            # Pokażemy, jak wygląda oryginał vs zepsute
            print(f"   [KANAŁ WEJŚCIE]: {bits_to_string(data_bytes)}")
            print(f"   [KANAŁ WYJŚCIE]: {bits_to_string(corrupted_data)}")

        return corrupted_data

# Instancja globalna kanału
global_channel = GilbertChannel()

def channel_simulate(data_bytes):
    return global_channel.propagate(data_bytes)