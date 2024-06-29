import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import string
import requests
from bs4 import BeautifulSoup
import threading
import time
import urllib.request
import urllib.error
import pandas as pd
from tkinter import filedialog

# Global variables and flags
pause_event = threading.Event()
stop_event = threading.Event()
is_paused = False

# Counter to track the number of attempts
attempt_counter = 0

def marka_ismi_olustur(harfler, uzunluk):
    harfler_seti = set(harfler)
    while True:
        isim = ''.join(random.choice(string.ascii_lowercase) for _ in range(uzunluk))
        if harfler_seti.issubset(isim):
            return isim

def check_internet_connection():
    try:
        urllib.request.urlopen('http://google.com', timeout=5)  # Timeout set to 5 seconds
        return True
    except (urllib.error.URLError, TimeoutError):
        return False

def google_ara(isim):
    if not check_internet_connection():
        messagebox.showwarning("Uyarı", "İnternet bağlantısı yok veya zaman aşımı. Lütfen bağlantınızı kontrol edin.")
        return False

    global attempt_counter
    attempt_counter += 1

    query = f'"{isim} markası"'
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)  # Timeout set to 10 seconds
        response.raise_for_status()  # Check for HTTP errors
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')
        if any(isim.lower() in result.text.lower() for result in results):
            return True, attempt_counter
        else:
            return False, None
    except requests.exceptions.RequestException as e:
        messagebox.showwarning("Uyarı", f"Arama sırasında hata oluştu: {str(e)}")
        return False, None

def marka_ismi_bul(harfler, uzunluk, adet):
    global attempt_counter
    uygun_isimler = []
    attempt_counter = 0
    while len(uygun_isimler) < adet and not stop_event.is_set():
        if pause_event.is_set():
            time.sleep(0.1)
            continue
        
        isim = marka_ismi_olustur(harfler, uzunluk)
        found, attempt = google_ara(isim)
        if found:
            uygun_isimler.append((isim, attempt))
            remaining = adet - len(uygun_isimler)
            status_label.config(text=f"{len(uygun_isimler)} isim bulundu, {remaining} isim daha bulunacak.")
            text_output.insert(tk.END, f"{isim} ({attempt})\n")
            print(f"Uygun isim bulundu: {isim} ({attempt})")
    
    if stop_event.is_set():
        status_label.config(text="İsim oluşturma iptal edildi.")
    else:
        status_label.config(text="İsimler oluşturuldu.")
    
    return uygun_isimler

def generate_brand_names():
    global is_paused
    if is_paused:
        resume_generation()
        return

    harfler = entry_harfler.get()
    uzunluk = int(entry_uzunluk.get())
    adet = int(entry_adet.get())

    if not harfler.isalpha():
        messagebox.showerror("Hata", "Harfler alanına sadece harf girişi yapılabilir.")
        return

    text_output.delete(1.0, tk.END)
    status_label.config(text=f"İsimler oluşturuluyor, lütfen bekleyin...")

    stop_event.clear()
    pause_event.clear()

    # Run brand name generation in a separate thread
    def generate_names_thread():
        nonlocal harfler, uzunluk, adet
        uygun_isimler = marka_ismi_bul(harfler, uzunluk, adet)
        if uygun_isimler:
            save_to_excel(uygun_isimler)

    thread = threading.Thread(target=generate_names_thread)
    thread.start()

def pause_generation():
    global is_paused
    is_paused = True
    pause_event.set()
    status_label.config(text="İsim oluşturma duraklatıldı.")

def resume_generation():
    global is_paused
    is_paused = False
    pause_event.clear()
    status_label.config(text="İsim oluşturma devam ediyor.")

def stop_generation():
    global stop_event
    stop_event.set()

def save_to_excel(uygun_isimler):
    df = pd.DataFrame(uygun_isimler, columns=['Marka İsmi', 'Deneme Sayısı'])
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if file_path:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Başarılı", "Veriler Excel dosyasına kaydedildi.")

# GUI setup
def setup_gui():
    global root, frame_inputs, frame_output, label_harfler, entry_harfler, label_uzunluk, entry_uzunluk
    global label_adet, entry_adet, button_generate, button_pause, button_resume, button_stop, status_label, label_output, text_output

    root = tk.Tk()
    root.title("Marka İsimi Oluşturucu")

    frame_inputs = ttk.Frame(root, padding="20")
    frame_inputs.grid(row=0, column=0, sticky="nsew")

    label_harfler = ttk.Label(frame_inputs, text="Karakter Seti:")
    label_harfler.grid(row=0, column=0, sticky="w")

    entry_harfler = ttk.Entry(frame_inputs, width=30)
    entry_harfler.grid(row=0, column=1)

    label_uzunluk = ttk.Label(frame_inputs, text="İsim Uzunluğu:")
    label_uzunluk.grid(row=1, column=0, sticky="w")

    entry_uzunluk = ttk.Entry(frame_inputs, width=10)
    entry_uzunluk.grid(row=1, column=1)

    label_adet = ttk.Label(frame_inputs, text="Kaç İsim Oluşturulsun:")
    label_adet.grid(row=2, column=0, sticky="w")

    entry_adet = ttk.Entry(frame_inputs, width=10)
    entry_adet.grid(row=2, column=1)

    button_generate = ttk.Button(frame_inputs, text="İsimleri Oluştur", command=generate_brand_names)
    button_generate.grid(row=3, columnspan=2, pady=10)

    button_pause = ttk.Button(frame_inputs, text="Durdur", command=pause_generation)
    button_pause.grid(row=4, column=0, pady=10)

    button_resume = ttk.Button(frame_inputs, text="Devam Et", command=resume_generation)
    button_resume.grid(row=4, column=1, pady=10)

    button_stop = ttk.Button(frame_inputs, text="İptal", command=stop_generation)
    button_stop.grid(row=5, columnspan=2, pady=10)

    status_label = ttk.Label(root, text="", anchor="w", padding=(20, 0))
    status_label.grid(row=1, column=0, sticky="ew")

    frame_output = ttk.Frame(root, padding="20")
    frame_output.grid(row=2, column=0, sticky="nsew")

    label_output = ttk.Label(frame_output, text="Uygun Marka İsimleri:")
    label_output.pack(anchor="w")

    text_output = scrolledtext.ScrolledText(frame_output, wrap=tk.WORD, width=50, height=10)
    text_output.pack()

    # Configure grid weights to make the frames expandable
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    frame_inputs.grid_rowconfigure(0, weight=1)
    frame_inputs.grid_columnconfigure(0, weight=1)
    frame_output.grid_rowconfigure(0, weight=1)
    frame_output.grid_columnconfigure(0, weight=1)

    root.mainloop()

if __name__ == "__main__":
    setup_gui()
