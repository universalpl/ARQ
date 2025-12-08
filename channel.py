# channel.py
import random
import time
import config
from colors import Colors

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
<<<<<<< HEAD
        Symuluje kanał z wizualizacją bitową.
        Pokazuje dokładnie, które bity zostały zmienione (na czerwono)
        i gdzie trwała burza (na fioletowo).
=======
        Symuluje fizyczną propagację sygnału przez medium.
>>>>>>> f8bb538 (printowanie zmiany bitów)
        """
        if data_bytes is None:
            return None

<<<<<<< HEAD
        # Symulacja opóźnienia
        time.sleep(random.uniform(0.001, 0.005))
=======
        # Symulacja opóźnienia fizycznego
        time.sleep(random.uniform(0.01, 0.05))
>>>>>>> f8bb538 (printowanie zmiany bitów)

        # 1. PODEJRZYJ BITY NA WEJŚCIU (Przed zmianami)
        # Warto to robić tylko przy małej liczbie pakietów, bo zaśmieci konsolę
        # print(f"   [KANAŁ WEJŚCIE]: {bits_to_string(data_bytes)}")

        corrupted_data = bytearray(data_bytes)
        bit_errors_count = 0

        # Bufory do budowania wizualizacji (stringi)
        visual_input_str = ""
        visual_output_str = ""

        # Iteracja po bajtach
        for i in range(len(corrupted_data)):
            byte_val = corrupted_data[i]
            new_byte_val = 0

<<<<<<< HEAD
            # Dodajemy spację co bajt dla czytelności
            if i > 0:
                visual_input_str += " "
                visual_output_str += " "

            # Iteracja po bitach (od 7 do 0, żeby zachować kolejność czytania)
            # Uwaga: bit_pos 0 to najmłodszy bit. Żeby wypisać ładnie "1000...",
            # musimy iterować albo wyświetlać w odpowiedniej kolejności.
            # Standardowo format(b, '08b') wyświetla od MSB do LSB.
            # Zróbmy pętlę range(8) i składajmy, ale wizualizację budujmy ostrożnie.

            # Żeby wizualizacja pasowała do binary stringa, musimy iterować od 7 w dół do 0
            # (Big Endian display)
            for bit_index in range(7, -1, -1):
                bit_pos = bit_index
                original_bit = (byte_val >> bit_pos) & 1
                current_bit = original_bit

                # --- LOGIKA GILBERTA ---
=======
            # Iteracja po bitach w bajcie
            for bit_pos in range(8):
                # Pobierz bit (0 lub 1)
                current_bit = (byte_val >> bit_pos) & 1

                # A. Zmiana stanu Gilberta (Łańcuch Markowa)
>>>>>>> f8bb538 (printowanie zmiany bitów)
                if self.state == 'G':
                    if random.random() < config.GILBERT_P:
                        self.state = 'B'
                else:  # self.state == 'B'
                    if random.random() < config.GILBERT_R:
                        self.state = 'G'

<<<<<<< HEAD
                # --- DECYZJA O BŁĘDZIE ---
=======
                # B. Decyzja o błędzie (Bernoulli trial) zależna od stanu
>>>>>>> f8bb538 (printowanie zmiany bitów)
                error_prob = config.GILBERT_K if self.state == 'G' else config.GILBERT_H
                is_flipped = False

                if random.random() < error_prob:
                    current_bit = current_bit ^ 1
                    is_flipped = True
                    bit_errors_count += 1

                # Zapisz bit do nowego bajtu
                new_byte_val |= (current_bit << bit_pos)

<<<<<<< HEAD
                # --- BUDOWANIE WIZUALIZACJI ---
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

        # WYPISYWANIE LOGÓW (Zawsze lub tylko przy błędach)
        # Prowadzący chce widzieć wiązki, więc wypiszmy, jeśli wystąpił błąd LUB byliśmy w burzy.
        # Ale najprościej: jeśli były błędy.

        if bit_errors_count > 0:
            print(f"   [WEJŚCIE]: {visual_input_str}")
            print(f"   [WYJŚCIE]: {visual_output_str}")
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


=======
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

>>>>>>> f8bb538 (printowanie zmiany bitów)
def channel_simulate(data_bytes):
    return global_channel.propagate(data_bytes)