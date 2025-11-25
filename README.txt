========================================================================
INSTRUKCJA URUCHOMIENIA PROJEKTU (Go-Back-N ARQ Simulation)
========================================================================

1. INSTALACJA WYMAGANYCH BIBLIOTEK
------------------------------------------------------------------------
Otwórz terminal w folderze projektu i wpisz:

pip install sphinx sphinx-rtd-theme colorama


2. URUCHAMIANIE PROGRAMU
------------------------------------------------------------------------
Masz do wyboru trzy tryby pracy:

A) Standardowa symulacja (parametry z pliku config.py):
   python main.py

B) Testy Scenariuszowe (Czyste Niebo / Deszcz / Burza - do sprawozdania):
   python tests.py

C) Testy Jednostkowe (sprawdzenie poprawności funkcji CRC, okna itp.):
   python unit_tests.py


3. GENEROWANIE DOKUMENTACJI TECHNICZNEJ (HTML)
------------------------------------------------------------------------
Aby wygenerować stronę z dokumentacją kodu, wykonaj te kroki w terminalu
(będąc w głównym folderze projektu):

KROK 1: Zaktualizuj pliki źródłowe dokumentacji
   sphinx-apidoc -o docs . -f

KROK 2: Zbuduj stronę HTML
   cd docs
   .\make.bat html
   cd ..

KROK 3: Otwórz wynik
   Wejdź do folderu: docs/_build/html
   Otwórz plik: index.html