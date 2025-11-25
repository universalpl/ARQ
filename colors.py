"""
Moduł odpowiedzialny za kolorowanie wyjścia w konsoli (ANSI codes).
Ułatwia wizualną analizę logów symulacji.
"""

try:
    import colorama

    colorama.just_fix_windows_console()
except Exception:
    pass


class Colors:
    """
    Kontener na kody kolorów ANSI.

    Attributes:
        FRAME_COLORS (list): Lista kodów kolorów przypisanych do kolejnych numerów sekwencyjnych (SN).
    """
    RESET = "\033[0m"

    FRAME_COLORS = [
        "\033[38;2;255;51;153m",  # SN=0
        "\033[92m",  # SN=1
        "\033[93m",  # SN=2
        "\033[94m",  # SN=3
        "\033[38;2;204;102;255m",  # SN=4
        "\033[96m",  # SN=5
        "\033[38;2;255;153;0m",  # SN=6
        "\033[97m",  # SN=7
    ]

    GRAY = "\033[90m"
    RED = "\033[91m"

    @staticmethod
    def for_sn(sn):
        """Zwraca kod koloru przypisany do danego numeru sekwencyjnego (modulo długość listy)."""
        idx = sn % len(Colors.FRAME_COLORS)
        return Colors.FRAME_COLORS[idx]