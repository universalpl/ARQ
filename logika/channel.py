# logika/channel.py
import random
import time
import config
from logika.colors import Colors


class GilbertChannel:
    def __init__(self):
        self.state = 'G'

    def propagate(self, data_bytes: bytearray) -> bytearray:
        """
        Symuluje kanał z wizualizacją bitową.
        Pokazuje dokładnie, które bity zostały zmienione (na czerwono)
        i gdzie trwała burza (na fioletowo).
        """
        if data_bytes is None:
            return None

        # Symulacja opóźnienia
        time.sleep(random.uniform(0.001, 0.005))

        corrupted_data = bytearray(data_bytes)
        bit_errors_count = 0

        # Bufory do budowania wizualizacji (stringi)
        visual_input_str = ""
        visual_output_str = ""

        # Iteracja po bajtach
        for i in range(len(corrupted_data)):
            byte_val = corrupted_data[i]
            new_byte_val = 0

            # Spacja co bajt dla czytelności
            if i > 0:
                visual_input_str += " "
                visual_output_str += " "

            # Iteracja po bitach (od 7 do 0 - Big Endian display)
            for bit_index in range(7, -1, -1):
                bit_pos = bit_index
                original_bit = (byte_val >> bit_pos) & 1
                current_bit = original_bit

                # --- 1. LOGIKA GILBERTA (Maszyna Stanów) ---
                if self.state == 'G':
                    if random.random() < config.GILBERT_P:
                        self.state = 'B'
                else:  # self.state == 'B'
                    if random.random() < config.GILBERT_R:
                        self.state = 'G'

                # --- 2. DECYZJA O BŁĘDZIE ---
                error_prob = config.GILBERT_K if self.state == 'G' else config.GILBERT_H
                is_flipped = False

                if random.random() < error_prob:
                    current_bit = current_bit ^ 1
                    is_flipped = True
                    bit_errors_count += 1

                # Zapisz bit do nowego bajtu
                new_byte_val |= (current_bit << bit_pos)

                # --- 3. BUDOWANIE WIZUALIZACJI ---
                visual_input_str += str(original_bit)

                if is_flipped:
                    # Błąd (Czerwony)
                    visual_output_str += f"{Colors.RED}{current_bit}{Colors.RESET}"
                elif self.state == 'B':
                    # Wewnątrz wiązki, ale ocalał (Fioletowy)
                    visual_output_str += f"{Colors.MAGENTA}{current_bit}{Colors.RESET}"
                else:
                    # Czysto (Szary/Zwykły)
                    visual_output_str += f"{Colors.GRAY}{current_bit}{Colors.RESET}"

            corrupted_data[i] = new_byte_val

        # --- WYPISYWANIE LOGÓW ---
        # Pokaż wizualizację tylko jeśli wystąpiły błędy, żeby nie spamować przy poprawnych
        if bit_errors_count > 0:
            #print(f"   [WEJŚCIE]: {visual_input_str}")
            #print(f"   [WYJŚCIE]: {visual_output_str}")
            print(
                f"{Colors.RED}  [KANAŁ]: Zmieniono {bit_errors_count} bitów (Legenda: {Colors.RED}Błąd{Colors.RESET}, {Colors.MAGENTA}Wiązka{Colors.RESET}).{Colors.RESET}")

        return corrupted_data

    def propagate_bsc(self, data_bytes: bytearray, error_prob: float) -> bytearray:
        """Wersja dla testów statystycznych (bez wizualizacji)"""
        if data_bytes is None: return None
        corrupted = bytearray(data_bytes)
        for i in range(len(corrupted)):
            val = corrupted[i]
            new_val = 0
            for b in range(8):
                bit = (val >> b) & 1
                if random.random() < error_prob:
                    bit ^= 1
                new_val |= (bit << b)
            corrupted[i] = new_val
        return corrupted


# Instancja globalna
global_channel = GilbertChannel()


def channel_simulate(data_bytes):
    return global_channel.propagate(data_bytes)