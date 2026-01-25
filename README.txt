========================================================================
1. WYMAGANIA

Wymagane biblioteki zewnętrzne:
- matplotlib
- pillow (PIL)

Instalacja:
pip install matplotlib pillow

Pozostałe biblioteki (time, random, csv, zlib, base64, struct, tkinter)


========================================================================
2. STRUKTURA PROJEKTU

gui/
  live_preview.py
    -> podgląd progresywnego odtwarzania obrazu JPG w trakcie transmisji

input/
  kot.jpg
    -> obraz wejściowy przesyłany przez protokół Go-Back-N

logika/
  frame.py
    -> definicja ramki (DATA / ACK), serializacja, CRC32
  channel.py
    -> symulator kanału (BSC oraz Gilbert–Elliott)
  sender.py
    -> nadajnik Go-Back-N (okno przesuwne, timeout, retransmisje)
  receiver.py
    -> odbiornik Go-Back-N (CRC, kolejność, duplicate ACK)
  colors.py
    -> kolory logów konsolowych

testy/
  unit_tests.py
    -> testy jednostkowe komponentów (frame, sender, receiver, channel)
  tests.py
    -> testy scenariuszowe (idealny kanał, lekki błąd, ciężkie zakłócenia)
  test_crc_efficiency.py
    -> testy skuteczności CRC32 na danych obrazu + wykres + CSV
  test_optimization.py
    -> testy optymalizacyjne (różne chunk size, różne parametry kanału)
  test_optimization_average.py
    -> uśrednianie wyników z wielu przebiegów

testy/optimization_output/
  -> wyniki testów optymalizacyjnych (CSV + wykresy)

output/
  histogram/
    -> histogram retransmisji

zdjecie/
  kot_copy.jpg
    -> obraz wynikowy po zakończeniu transmisji

config.py
  -> centralna konfiguracja: timeout, parametry kanału, okno GBN

main_zdjecia.py
  -> główna symulacja: kopiowanie obrazu przez Go-Back-N

README.txt
  -> niniejszy plik


================================================================================================================================================
3. URUCHAMIANIE PROGRAMU

A) GŁÓWNA SYMULACJA:
python main_zdjecia.py

- obraz wejściowy: input/kot.jpg
- obraz wynikowy: zdjecie/kot_copy.jpg

B) TESTY JEDNOSTKOWE:
python testy/unit_tests.py


C) TESTY SCENARIUSZOWE:
python testy/tests.py


D) TESTY SKUTECZNOŚCI CRC:
python testy/test_crc_efficiency.py
-test CRC32 na rzeczywistych danych obrazu JPG
-wyniki: testy/testy_output

E) TESTY OPTYMALIZACYJNE:
------------------------------------------------------------
python testy/test_optimization.py

- 25 konfiguracji (chunk size × parametry kanału)
- pełne uruchomienia symulacji
-wyniki: testy/optimization_output po koleji od 1-10

python testy/test_optimization_average.py
-wyniki: testy/optimization_output/average

========================================================================
