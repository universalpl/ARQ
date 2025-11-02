import tkinter as tk
root = tk.Tk()
root.title("Test Tk")
tk.Label(root, text="Jeśli widzisz ten tekst, Tk działa ✅").pack(padx=20, pady=20)
root.after(1500, root.destroy)
root.mainloop()
