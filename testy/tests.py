
"""
Moduł realizujący testy integracyjne (scenariuszowe).
Uruchamia pełną symulację dla trzech zdefiniowanych scenariuszy pogodowych (Czyste niebo, Deszcz, Burza)
i weryfikuje wydajność protokołu.
"""
# ... reszta kodu bez zmian ...


# tests.py
import main
import config
from logika.colors import Colors


def run_tests():
    print(f"{Colors.RED}=== ROZPOCZYNAM TESTY AUTOMATYCZNE ZGODNE ZE SPRAWOZDANIEM ==={Colors.RESET}\n")

    # Zapiszmy oryginalne wartości
    original_target = config.TARGET_PACKETS
    original_k = config.GILBERT_K

    config.TARGET_PACKETS = 20
    YELLOW = Colors.FRAME_COLORS[2]

    # --- SCENARIUSZ 1: CZYSTE NIEBO ---
    print(f"{YELLOW}SCENARIUSZ 1: Czyste Niebo (Idealny Kanał){Colors.RESET}")
    print("Parametry: P = 0.0, R = 1.0, K = 0.0 (Absolutny brak błędów)")

    # WYŁĄCZAMY SZUM TŁA (K=0), żeby kanał był idealny
    config.GILBERT_K = 0.0

    eff1 = main.run_go_back_n_simulation(override_p=0.0, override_r=1.0)

    print(f"-> Wynik raportu: 1.00. Wynik testu: {eff1:.2f}\n")

    # --- PRZYWRACAMY SZUM DLA RESZTY ---
    config.GILBERT_K = original_k

    # --- SCENARIUSZ 2: LEKKI DESZCZ ---
    print(f"{YELLOW}SCENARIUSZ 2: Lekki Deszcz (Realistyczny){Colors.RESET}")
    print("Parametry: P = 0.0003, R = 0.05")

    eff2 = main.run_go_back_n_simulation(override_p=0.0003, override_r=0.05)

    print(f"-> Wynik raportu: ~0.85-0.95. Wynik testu: {eff2:.2f}\n")

    # --- SCENARIUSZ 3: CIĘŻKA BURZA ---
    print(f"{YELLOW}SCENARIUSZ 3: Ciężka Burza (Ekstremalny){Colors.RESET}")
    print("Parametry: P = 0.001, R = 0.02")

    eff3 = main.run_go_back_n_simulation(override_p=0.001, override_r=0.02)

    print(f"-> Wynik raportu: < 0.50. Wynik testu: {eff3:.2f}\n")

    # Przywracanie konfiguracji
    config.TARGET_PACKETS = original_target


if __name__ == "__main__":
    run_tests()