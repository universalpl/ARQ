from PIL import Image, ImageTk, ImageFile
import tkinter as tk
from io import BytesIO
from typing import Optional

# Pozwala Pillow wczytać niekompletny obraz (np. „ucięty” JPEG/PNG)
ImageFile.LOAD_TRUNCATED_IMAGES = True


class LivePreviewTk:
    """
    Podgląd na żywo karmiony przychodzącymi bajtami:
    - trzyma bufor w pamięci (bytearray),
    - po każdym nowym kawałku próbuje parsować i rysować,
    - działa bez czekania aż plik na dysku będzie kompletny.
    """
    def __init__(self, path_for_info_only, refresh_every_chunks=1, title="Podgląd kopiowanego obrazu (Tk)"):
        # path_for_info_only: tylko do logów/diagnostyki; render idzie z bufora w RAM
        self.path = path_for_info_only
        self.refresh_every_chunks = max(1, int(refresh_every_chunks))
        self._counter = 0
        self._buf = bytearray()

        self.root = tk.Tk()
        self.root.title(title)
        self.label = tk.Label(self.root, bg="black")
        self.label.pack()
        self._imgtk = None  # trzymaj referencję, inaczej GC „zje” obraz

        # pokaż okno natychmiast
        self.root.update_idletasks()
        self.root.update()

    def on_new_bytes(self, data: Optional[bytes] = None):
        """Wywołuj po każdym dopisanym kawałku (receiver -> callback)."""
        if data:
            self._buf.extend(data)

        self._counter += 1
        if self._counter % self.refresh_every_chunks != 0:
            return

        self._try_refresh()

    def force_show_once(self):
        self._try_refresh(force=True)

    def _try_refresh(self, force=False):
        if not self._buf and not force:
            return

        # Spróbuj sparsować to, co mamy w buforze (może być niepełne!)
        try:
            bio = BytesIO(self._buf)
            with Image.open(bio) as im:
                # Nie wywołujemy tu .close() na bio przed skopiowaniem
                im.load()     # wczytaj ile się da
                im = im.copy()  # oderwij od źródła
        except Exception:
            # Normalne na starcie / przy zbyt małej ilości danych
            if force:
                self._draw_placeholder()
            return

        # --- skalowanie podglądu ---
        target_width = 1450  # szerokość okna podglądu (dopasuj jak chcesz)
        ratio = target_width / im.width
        target_height = int(im.height * ratio)
        im_resized = im.resize((target_width, target_height))

        self._imgtk = ImageTk.PhotoImage(im_resized)
        self.label.configure(image=self._imgtk)

        # nie zmieniaj geometrii okna przy każdej klatce
        self.root.update_idletasks()
        self.root.update()

    def _draw_placeholder(self):
        self.label.configure(text="Oczekiwanie na dane...", fg="white", bg="black")
        self.root.update_idletasks()
        self.root.update()
