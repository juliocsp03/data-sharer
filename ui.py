import tkinter as tk
from tkinter import scrolledtext
import threading
import logging
import os
import sys
import sync_upload
import sync_download
from queue import Queue, Empty


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()
LOG_PATH = os.path.join(BASE_PATH, "logs.txt")


logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


log_queue = Queue()
        
def ui_event(tipo, data):
    log_queue.put((tipo, data))

def log(msg, level="info"):
    log_queue.put(("log", msg))

    if level == "error":
        logging.error(msg)
    else:
        logging.info(msg)

    
def ejecutar(funcion, nombre):
    ui_event("estado", f"ESTADO: {nombre}...")

    log(f"--- INICIO DE {nombre} ---")

    try:
        funcion(log_callback=log)
    except Exception as e:
        log(f"ERROR: {str(e)}", "error")

    log(f"--- FIN DE {nombre} ---")

    ui_event("estado", f"ESTADO: {nombre} FINALIZADA")
    ui_event("botones", "enable")


def iniciar_carga():
    threading.Thread(
        target=ejecutar,
        args=(sync_upload.upload, "CARGA"),
        daemon=True
    ).start()


def iniciar_descarga():
    boton_cargar.config(state="disabled")
    boton_descargar.config(state="disabled")

    threading.Thread(
        target=ejecutar,
        args=(sync_download.download, "DESCARGA"),
        daemon=True
    ).start()

def procesar_logs():
    try:
        while True:
            tipo, data = log_queue.get_nowait()

            if tipo == "log":
                caja_logs.config(state="normal")
                caja_logs.insert(tk.END, data + "\n")
                caja_logs.see(tk.END)
                caja_logs.config(state="disabled")

            elif tipo == "estado":
                etiqueta_estado.config(text=data, fg="blue")

            elif tipo == "botones":
                boton_cargar.config(state="normal")
                boton_descargar.config(state="normal")

    except:
        pass

    ventana.after(100, procesar_logs)

ventana = tk.Tk()
ventana.title("JDS")
ventana.geometry("500x550")

tk.Label(ventana, text="Compartidor de archivos", font=("Arial", 14, "bold")).pack(pady=10)

etiqueta_estado = tk.Label(ventana, text="", font=("Arial", 11), fg="gray")
etiqueta_estado.pack(pady=5)

frame_btns = tk.Frame(ventana)
frame_btns.pack(pady=10)

boton_cargar = tk.Button(frame_btns, text="Cargar archivos", command=iniciar_carga, width=18)
boton_cargar.grid(row=0, column=0, padx=5)

boton_descargar = tk.Button(frame_btns, text="Descargar archivos", command=iniciar_descarga, width=18)
boton_descargar.grid(row=0, column=1, padx=5)

tk.Label(ventana, text="Logs:", font=("Arial", 9, "italic")).pack(anchor="w", padx=25)

caja_logs = scrolledtext.ScrolledText(
    ventana, width=55, height=15,
    font=("Consolas", 9),
    bg="#1e1e1e", fg="#d4d4d4"
)
caja_logs.pack(pady=5, padx=20)
caja_logs.config(state="disabled")

def abrir_logs():
    os.startfile(LOG_PATH)

tk.Button(ventana, text="Ver logs", command=abrir_logs).pack(pady=5)
tk.Button(ventana, text="Salir", command=ventana.destroy, fg="red").pack(pady=10)

ventana.after(100, procesar_logs)

ventana.mainloop()