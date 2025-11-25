import random
import time
import config
from colors import Colors


class GilbertChannel:
    """
    Symulator kanału transmisyjnego wykorzystujący model Gilberta-Elliotta.

    Model ten jest standardem w symulacji łączy o zmiennej jakości (np. radiowych).
    Opiera się na dwustanowym łańcuchu Markowa:
    - **Stan G (Good):** Niski poziom błędów (szum tła), prawdopodobieństwo błędu = K.
    - **Stan B (Bad):** Wysoki poziom błędów (zakłócenia/zanik sygnału), prawdopodobieństwo błędu = H.

    Model generuje błędy typu **burst** (wiązki), co jest trudniejsze do wykrycia dla prostych
    sum kontrolnych niż błędy pojedyncze (losowe).

    Attributes:
        state (str): Aktualny stan automatu ('G' lub 'B').
    """

    def __init__(self):
        self.state = 'G'

    def propagate(self, data_bytes: bytearray) -> bytearray:
        """
        Symuluje fizyczną propagację sygnału przez medium.

        Algorytm przetwarza dane na poziomie pojedynczych bitów:
        1. Dla każdego bitu następuje losowanie przejścia stanu kanału (wg prawdopodobieństw P i R).
        2. W zależności od aktualnego stanu (G/B), losowana jest inwersja bitu (Bit Flip).

        Args:
            data_bytes (bytearray): Dane wejściowe (ramka zserializowana).

        Returns:
            bytearray: Dane wyjściowe, potencjalnie zawierające przekłamania bitowe.
        """
        if data_bytes is None:
            return None

        # Symulacja opóźnienia fizycznego (propagacja + przetwarzanie)
        time.sleep(random.uniform(0.01, 0.05))

        corrupted_data = bytearray(data_bytes)
        bit_errors_count = 0

        # Iteracja po bajtach
        for i in range(len(corrupted_data)):
            byte_val = corrupted_data[i]
            new_byte_val = 0

            # Iteracja po bitach w bajcie
            for bit_pos in range(8):
                current_bit = (byte_val >> bit_pos) & 1

                # 1. Zmiana stanu Gilberta (Łańcuch Markowa)
                if self.state == 'G':
                    if random.random() < config.GILBERT_P:
                        self.state = 'B'
                else:  # self.state == 'B'
                    if random.random() < config.GILBERT_R:
                        self.state = 'G'

                # 2. Decyzja o błędzie (Bernoulli trial) zależna od stanu
                error_prob = config.GILBERT_K if self.state == 'G' else config.GILBERT_H

                if random.random() < error_prob:
                    current_bit = current_bit ^ 1  # Inwersja bitu (XOR 1)
                    bit_errors_count += 1

                new_byte_val |= (current_bit << bit_pos)

            corrupted_data[i] = new_byte_val

        return corrupted_data


# Globalna instancja kanału (Singleton w kontekście modułu)
channel_instance = GilbertChannel()


def channel_simulate(data: bytes) -> bytes:
    """Wrapper udostępniający funkcjonalność kanału dla innych modułów."""
    return channel_instance.propagate(data)