# colors.py
# Kolor stały dla danego SN w całej symulacji.
# Działa w Windows (PyCharm/VSCode) dzięki colorama, jeśli jest zainstalowana.

try:
    import colorama  # type: ignore
    colorama.just_fix_windows_console()
except Exception:
    pass


class Colors:
    RESET = "\033[0m"
    # Mapowanie kolorów na kolejne SN (modulo długości listy)
    FRAME_COLORS = [
        "\033[38;2;255;51;153m",  # SN=0  - magneta
        "\033[92m",  # SN=1  - zielony
        "\033[93m",  # SN=2  - żółty
        "\033[94m",  # SN=3  - niebieski
        "\033[38;2;204;102;255m",  # SN=4  - jasny fiolet
        "\033[96m",  # SN=5  - turkusowy
        "\033[38;2;255;153;0m",  # SN=6  - pomaranczowy
        "\033[97m",  # SN=7  - biały
    ]

    # Neutralne/techniczne
    GRAY = "\033[90m"
    RED = "\033[38;2;255;0;0m"

    @staticmethod
    def for_sn(sn: int) -> str:
        return Colors.FRAME_COLORS[sn % len(Colors.FRAME_COLORS)]
