import os
import pygame
from pygame import mixer
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional, Dict, List, Literal
from PIL import Image, ImageTk
import time

COLOR_PRIMARIO = "#1DB954"  
COLOR_SECUNDARIO = "#191414"  
COLOR_FONDO = "#121212"
COLOR_TEXTO = "#FFFFFF"
COLOR_TEXTO_SECUNDARIO = "#B3B3B3"
COLOR_ACTIVO = "#1ED760"
COLOR_HOVER = "#535353"

REPETIR_MODOS = ["Ninguno", "Una canción", "Toda la lista"]

class Cancion:
    def __init__(self, titulo: str, artista: str, duracion: float, ruta_archivo: str, genero: str):
        self.titulo = titulo
        self.artista = artista
        self.duracion = duracion
        self.ruta_archivo = ruta_archivo
        self.genero = genero
    
    def __str__(self) -> str:
        return f"{self.titulo} - {self.artista}"
    
    def obtener_duracion_formateada(self) -> str:
        minutos = int(self.duracion)
        segundos = int((self.duracion - minutos) * 60)
        return f"{minutos}:{segundos:02d}"
    
    def editar(self, nuevo_titulo: str, nuevo_artista: str, nueva_duracion: float, nuevo_genero: str):
        self.titulo = nuevo_titulo
        self.artista = nuevo_artista
        self.duracion = nueva_duracion
        self.genero = nuevo_genero

class Nodo:
    def __init__(self, cancion: Cancion):
        self.cancion = cancion
        self.siguiente: Optional['Nodo'] = None
        self.anterior: Optional['Nodo'] = None

class ListaReproduccion:
    def __init__(self):
        self.cabeza: Optional[Nodo] = None
        self.actual: Optional[Nodo] = None
        self.esta_reproduciendo = False
        self.modo_repeticion: Literal["Ninguno", "Una canción", "Toda la lista"] = "Ninguno"
        self.volumen = 0.7
        self.duracion_total = 0.0
    
    def agregar_cancion(self, cancion: Cancion) -> None:
        nuevo_nodo = Nodo(cancion)
        self.duracion_total += cancion.duracion
        
        if self.cabeza is None:
            self.cabeza = nuevo_nodo
            self.cabeza.siguiente = self.cabeza
            self.cabeza.anterior = self.cabeza
            self.actual = self.cabeza
        else:
            ultimo = self.cabeza.anterior
            ultimo.siguiente = nuevo_nodo
            nuevo_nodo.anterior = ultimo
            nuevo_nodo.siguiente = self.cabeza
            self.cabeza.anterior = nuevo_nodo
    
    def eliminar_cancion(self, titulo: str) -> bool:
        if self.cabeza is None:
            return False
        
        temp = self.cabeza
        while True:
            if temp.cancion.titulo == titulo:
                self.duracion_total -= temp.cancion.duracion
                
                if temp.siguiente == temp:  # Único nodo
                    self.cabeza = None
                    self.actual = None
                else:
                    temp.anterior.siguiente = temp.siguiente
                    temp.siguiente.anterior = temp.anterior
                    
                    if self.cabeza == temp:
                        self.cabeza = temp.siguiente
                    
                    if self.actual == temp:
                        self.actual = temp.siguiente
                
                return True
            
            temp = temp.siguiente
            if temp == self.cabeza:
                break
        
        return False
    
    def listar_canciones(self) -> List[Cancion]:
        canciones = []
        if self.cabeza is None:
            return canciones
        
        temp = self.cabeza
        while True:
            canciones.append(temp.cancion)
            temp = temp.siguiente
            if temp == self.cabeza:
                break
        return canciones
    
    def buscar_cancion(self, titulo: str) -> Optional[Cancion]:
        if self.cabeza is None:
            return None
        
        temp = self.cabeza
        while True:
            if temp.cancion.titulo == titulo:
                return temp.cancion
            temp = temp.siguiente
            if temp == self.cabeza:
                break
        return None
    
    def reproducir(self) -> None:
        if self.cabeza is None or self.actual is None:
            return
        
        if not os.path.exists(self.actual.cancion.ruta_archivo):
            messagebox.showerror("Error", f"Archivo no encontrado: {self.actual.cancion.ruta_archivo}")
            return
        
        try:
            mixer.init()
            mixer.music.load(self.actual.cancion.ruta_archivo)
            mixer.music.set_volume(self.volumen)
            mixer.music.play()
            self.esta_reproduciendo = True
            mixer.music.set_endevent(pygame.USEREVENT)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reproducir: {e}")
    
    def manejar_fin_reproduccion(self):
        if self.modo_repeticion == "Una canción":
            self.reproducir()
        elif self.modo_repeticion == "Toda la lista":
            self.siguiente_cancion()
        else:
            self.esta_reproduciendo = False
    
    def siguiente_cancion(self) -> None:
        if self.cabeza is None or self.actual is None:
            return
        
        self.actual = self.actual.siguiente
        self.reproducir()
    
    def cancion_anterior(self) -> None:
        if self.cabeza is None or self.actual is None:
            return
        
        self.actual = self.actual.anterior
        self.reproducir()
    
    def pausar(self) -> None:
        if self.esta_reproduciendo:
            mixer.music.pause()
            self.esta_reproduciendo = False
    
    def reanudar(self) -> None:
        if not self.esta_reproduciendo and self.actual:
            mixer.music.unpause()
            self.esta_reproduciendo = True
    
    def detener(self) -> None:
        if mixer.get_init() is not None:
            mixer.music.stop()
            self.esta_reproduciendo = False
    
    def cambiar_modo_repeticion(self) -> str:
        current_index = REPETIR_MODOS.index(self.modo_repeticion)
        new_index = (current_index + 1) % len(REPETIR_MODOS)
        self.modo_repeticion = REPETIR_MODOS[new_index]
        return self.modo_repeticion
    
    def seleccionar_cancion(self, cancion: Cancion) -> None:
        if self.cabeza is None:
            return
        
        temp = self.cabeza
        while True:
            if temp.cancion.titulo == cancion.titulo:
                self.actual = temp
                self.reproducir()
                break
            temp = temp.siguiente
            if temp == self.cabeza:
                break
    
    def obtener_duracion_total(self) -> str:
        minutos = int(self.duracion_total)
        segundos = int((self.duracion_total - minutos) * 60)
        return f"{minutos}:{segundos:02d}"

class GestorListas:
    def __init__(self):
        self.listas: Dict[str, ListaReproduccion] = {}
        self.lista_activa: Optional[ListaReproduccion] = None
    
    def crear_lista(self, nombre: str) -> bool:
        if nombre in self.listas:
            return False
        self.listas[nombre] = ListaReproduccion()
        return True
    
    def seleccionar_lista(self, nombre: str) -> bool:
        if nombre not in self.listas:
            return False
        self.lista_activa = self.listas[nombre]
        return True
    
    def eliminar_lista(self, nombre: str) -> bool:
        if nombre not in self.listas:
            return False
        
        if self.lista_activa == self.listas[nombre]:
            self.lista_activa.detener()
            self.lista_activa = None
        
        del self.listas[nombre]
        return True
    
    def obtener_listas(self) -> List[str]:
        return list(self.listas.keys())

class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLOR_PRIMARIO,
            fg=COLOR_TEXTO,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5,
            activebackground=COLOR_ACTIVO,
            activeforeground=COLOR_TEXTO,
            font=("Arial", 10, "bold")
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        self.config(bg=COLOR_ACTIVO)
    
    def on_leave(self, e):
        self.config(bg=COLOR_PRIMARIO)

class SecondaryButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            bg=COLOR_SECUNDARIO,
            fg=COLOR_TEXTO,
            relief=tk.FLAT,
            bd=0,
            padx=10,
            pady=5,
            activebackground=COLOR_HOVER,
            activeforeground=COLOR_TEXTO,
            font=("Arial", 10)
        )
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        self.config(bg=COLOR_HOVER)
    
    def on_leave(self, e):
        self.config(bg=COLOR_SECUNDARIO)

class ReproductorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.gestor = GestorListas()
        self.setup_ui()
        self.setup_bindings()
        self.tiempo_inicio_reproduccion = 0
        self.ultimo_tiempo_actualizado = 0
    
    def setup_ui(self):
        self.root.title("Modern Music Player")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLOR_FONDO)
        self.root.minsize(800, 600)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.root, bg=COLOR_FONDO)
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.setup_barra_superior()

        self.setup_contenido_principal()

        self.setup_barra_reproduccion()
    
    def setup_barra_superior(self):
        frame_superior = tk.Frame(self.main_frame, bg=COLOR_FONDO)
        frame_superior.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Logo
        logo_frame = tk.Frame(frame_superior, bg=COLOR_FONDO)
        logo_frame.pack(side=tk.LEFT)
        tk.Label(logo_frame, text="Modern Player", bg=COLOR_FONDO, fg=COLOR_PRIMARIO,
                font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=5)

        # Controles de lista
        list_controls = tk.Frame(frame_superior, bg=COLOR_FONDO)
        list_controls.pack(side=tk.RIGHT)

        self.combo_listas = ttk.Combobox(list_controls, state="readonly", width=25)
        self.combo_listas.pack(side=tk.LEFT, padx=5)
        self.combo_listas.bind("<<ComboboxSelected>>", self.cambiar_lista_activa)

        ModernButton(list_controls, text="Nueva", command=self.crear_lista).pack(side=tk.LEFT, padx=5)
        SecondaryButton(list_controls, text="Eliminar", command=self.eliminar_lista).pack(side=tk.LEFT, padx=5)
    
    def setup_contenido_principal(self):
        # Frame para el contenido principal
        content_frame = tk.Frame(self.main_frame, bg=COLOR_FONDO)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        self.setup_treeview(content_frame)

        toolbar_frame = tk.Frame(content_frame, bg=COLOR_FONDO)
        toolbar_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        ModernButton(toolbar_frame, text="+ Agregar Canción", command=self.agregar_cancion).pack(side=tk.LEFT, padx=5)
        SecondaryButton(toolbar_frame, text="- Eliminar Canción", command=self.eliminar_cancion).pack(side=tk.LEFT, padx=5)
        SecondaryButton(toolbar_frame, text="✏ Editar", command=self.editar_cancion).pack(side=tk.LEFT, padx=5)
    
    def setup_treeview(self, parent):
        # Frame para el treeview y scrollbar
        tree_frame = tk.Frame(parent, bg=COLOR_FONDO)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Configurar el estilo del treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background=COLOR_SECUNDARIO,
            foreground=COLOR_TEXTO,
            fieldbackground=COLOR_SECUNDARIO,
            rowheight=30,
            font=("Arial", 10)
        )
        style.configure("Treeview.Heading",
            background=COLOR_PRIMARIO,
            foreground=COLOR_TEXTO,
            relief="flat",
            font=("Arial", 10, "bold")
        )
        style.map("Treeview",
            background=[("selected", COLOR_HOVER)],
            foreground=[("selected", COLOR_TEXTO)]
        )

        self.tree = ttk.Treeview(tree_frame, columns=("titulo", "artista", "duracion", "genero"), 
                                show="headings", selectmode="browse")

        self.tree.heading("titulo", text="Título")
        self.tree.heading("artista", text="Artista")
        self.tree.heading("duracion", text="Duración")
        self.tree.heading("genero", text="Género")
        
        self.tree.column("titulo", width=300, anchor="w")
        self.tree.column("artista", width=200, anchor="w")
        self.tree.column("duracion", width=100, anchor="center")
        self.tree.column("genero", width=150, anchor="w")

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
    
    def setup_barra_reproduccion(self):
        # Frame para la barra de reproducción
        player_frame = tk.Frame(self.main_frame, bg=COLOR_SECUNDARIO, padx=20, pady=10)
        player_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.progress_frame = tk.Frame(player_frame, bg=COLOR_SECUNDARIO)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.tiempo_actual = tk.StringVar(value="0:00")
        self.tiempo_total = tk.StringVar(value="0:00")
        
        tk.Label(self.progress_frame, textvariable=self.tiempo_actual, 
                bg=COLOR_SECUNDARIO, fg=COLOR_TEXTO_SECUNDARIO).pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Scale(self.progress_frame, from_=0, to=100, value=0)
        self.progress_bar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        self.progress_bar.bind("<ButtonRelease-1>", self.saltar_a_tiempo)
        
        tk.Label(self.progress_frame, textvariable=self.tiempo_total, 
                bg=COLOR_SECUNDARIO, fg=COLOR_TEXTO_SECUNDARIO).pack(side=tk.RIGHT)

        controls_frame = tk.Frame(player_frame, bg=COLOR_SECUNDARIO)
        controls_frame.pack()

        self.btn_repetir = SecondaryButton(controls_frame, text="Repetir: Ninguno", 
                                         command=self.cambiar_repeticion)
        self.btn_repetir.pack(side=tk.LEFT, padx=10)

        self.btn_prev = SecondaryButton(controls_frame, text="⏮", 
                                      command=self.cancion_anterior, font=("Arial", 12))
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_play = ModernButton(controls_frame, text="▶", 
                                   command=self.reproducir_pausar, font=("Arial", 14))
        self.btn_play.pack(side=tk.LEFT, padx=5)

        self.btn_next = SecondaryButton(controls_frame, text="⏭", 
                                      command=self.siguiente_cancion, font=("Arial", 12))
        self.btn_next.pack(side=tk.LEFT, padx=5)

        volume_frame = tk.Frame(controls_frame, bg=COLOR_SECUNDARIO)
        volume_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(volume_frame, text="🔊", bg=COLOR_SECUNDARIO, fg=COLOR_TEXTO).pack(side=tk.LEFT)
        self.volumen_scale = ttk.Scale(volume_frame, from_=0, to=100, value=70,
                                      command=self.ajustar_volumen)
        self.volumen_scale.pack(side=tk.LEFT, padx=5)

        self.current_song_frame = tk.Frame(player_frame, bg=COLOR_SECUNDARIO)
        self.current_song_frame.pack(fill=tk.X, pady=(10, 0))

        self.current_song_title = tk.StringVar(value="No hay canción seleccionada")
        self.current_song_artist = tk.StringVar(value="")

        tk.Label(self.current_song_frame, textvariable=self.current_song_title, 
                bg=COLOR_SECUNDARIO, fg=COLOR_TEXTO, font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(self.current_song_frame, textvariable=self.current_song_artist, 
                bg=COLOR_SECUNDARIO, fg=COLOR_TEXTO_SECUNDARIO, font=("Arial", 10)).pack(anchor="w")
    
    def setup_bindings(self):
        self.tree.bind("<Double-1>", self.seleccionar_cancion)
        self.root.bind("<space>", lambda e: self.reproducir_pausar())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        if self.gestor.lista_activa:
            self.gestor.lista_activa.detener()
        mixer.quit()
        self.root.destroy()
    
    def cambiar_lista_activa(self, event=None):
        lista_seleccionada = self.combo_listas.get()
        if lista_seleccionada:
            self.gestor.seleccionar_lista(lista_seleccionada)
            self.actualizar_canciones()
            self.actualizar_info_lista()
    
    def actualizar_listas(self):
        listas = self.gestor.obtener_listas()
        self.combo_listas["values"] = listas
        if listas:
            self.combo_listas.current(0)
            self.cambiar_lista_activa()
    
    def actualizar_canciones(self):
        self.tree.delete(*self.tree.get_children())
        if self.gestor.lista_activa:
            for cancion in self.gestor.lista_activa.listar_canciones():
                self.tree.insert("", "end", values=(
                    cancion.titulo, 
                    cancion.artista, 
                    cancion.obtener_duracion_formateada(),
                    cancion.genero
                ))
    
    def actualizar_info_lista(self):
        if self.gestor.lista_activa:
            duracion_total = self.gestor.lista_activa.obtener_duracion_total()
            num_canciones = len(self.gestor.lista_activa.listar_canciones())
            
            if self.gestor.lista_activa.actual:
                cancion = self.gestor.lista_activa.actual.cancion
                self.current_song_title.set(cancion.titulo)
                self.current_song_artist.set(cancion.artista)
                self.tiempo_total.set(cancion.obtener_duracion_formateada())
            else:
                self.current_song_title.set("No hay canción seleccionada")
                self.current_song_artist.set("")
                self.tiempo_total.set("0:00")
        else:
            self.current_song_title.set("No hay lista activa")
            self.current_song_artist.set("")
            self.tiempo_total.set("0:00")
    
    def crear_lista(self):
        nombre = simpledialog.askstring("Nueva Lista", "Nombre de la lista:")
        if nombre:
            if self.gestor.crear_lista(nombre):
                self.actualizar_listas()
            else:
                messagebox.showerror("Error", "Ya existe una lista con ese nombre")
    
    def eliminar_lista(self):
        lista = self.combo_listas.get()
        if lista and messagebox.askyesno("Confirmar", f"¿Eliminar lista '{lista}'?"):
            if self.gestor.eliminar_lista(lista):
                self.actualizar_listas()
    
    def agregar_cancion(self):
        if not self.gestor.lista_activa:
            messagebox.showwarning("Advertencia", "Selecciona una lista primero")
            return
        
        archivos = filedialog.askopenfilenames(
            title="Seleccionar canciones",
            filetypes=[("Archivos de audio", "*.mp3 *.wav *.ogg"), ("Todos los archivos", "*.*")]
        )
        
        if archivos:
            for archivo in archivos:
                titulo = os.path.basename(archivo).split('.')[0]
                cancion = Cancion(titulo, "Desconocido", 0.0, archivo, "No especificado")
                self.gestor.lista_activa.agregar_cancion(cancion)
            
            self.actualizar_canciones()
            self.actualizar_info_lista()
    
    def editar_cancion(self):
        if not self.gestor.lista_activa:
            messagebox.showwarning("Advertencia", "No hay lista activa seleccionada")
            return
        
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una canción para editar")
            return
        
        try:
            valores = self.tree.item(seleccion[0])["values"]
            if not valores or len(valores) < 4:
                messagebox.showerror("Error", "Datos de canción incompletos")
                return
            
            titulo_actual = valores[0]
            cancion = self.gestor.lista_activa.buscar_cancion(titulo_actual)
            
            if not cancion:
                messagebox.showerror("Error", "Canción no encontrada en la lista")
                return

            ventana_edicion = tk.Toplevel(self.root)
            ventana_edicion.title("Editar canción")
            ventana_edicion.configure(bg=COLOR_FONDO)
            ventana_edicion.resizable(False, False)
            
            # Centrar la ventana
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_width = self.root.winfo_width()
            ventana_edicion.geometry(f"400x300+{root_x + root_width//2 - 200}+{root_y + 100}")

            # Campos de edición
            campos = [
                ("Título:", cancion.titulo),
                ("Artista:", cancion.artista),
                ("Duración (minutos):", str(cancion.duracion)),
                ("Género:", cancion.genero)
            ]
            
            entries = []
            for i, (label, value) in enumerate(campos):
                tk.Label(ventana_edicion, text=label, bg=COLOR_FONDO, fg=COLOR_TEXTO).grid(
                    row=i, column=0, padx=10, pady=5, sticky="e")
                
                entry = tk.Entry(ventana_edicion)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="we")
                entry.insert(0, value)
                entries.append(entry)
            
            # Botones
            btn_frame = tk.Frame(ventana_edicion, bg=COLOR_FONDO)
            btn_frame.grid(row=len(campos), column=0, columnspan=2, pady=20)
            
            ModernButton(btn_frame, text="Guardar cambios", command=lambda: self.guardar_cambios_cancion(
                cancion, entries[0].get(), entries[1].get(), entries[2].get(), entries[3].get(), ventana_edicion)
            ).pack(side=tk.LEFT, padx=10)
            
            SecondaryButton(btn_frame, text="Cancelar", command=ventana_edicion.destroy).pack(side=tk.LEFT, padx=10)

            ventana_edicion.grab_set()
            ventana_edicion.transient(self.root)
            ventana_edicion.wait_window(ventana_edicion)
            
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al editar: {str(e)}")
    
    def guardar_cambios_cancion(self, cancion, titulo, artista, duracion, genero, ventana):
        try:
            nueva_duracion = float(duracion)
            if not titulo:
                messagebox.showerror("Error", "El título no puede estar vacío")
                return
            
            cancion.editar(titulo, artista, nueva_duracion, genero)
            self.actualizar_canciones()
            self.actualizar_info_lista()
            ventana.destroy()
        except ValueError:
            messagebox.showerror("Error", "La duración debe ser un número válido")
    
    def eliminar_cancion(self):
        if not self.gestor.lista_activa:
            return
        
        seleccion = self.tree.selection()
        if not seleccion:
            return
        
        titulo = self.tree.item(seleccion[0])["values"][0]
        if self.gestor.lista_activa.eliminar_cancion(titulo):
            self.actualizar_canciones()
            self.actualizar_info_lista()
    
    def reproducir_pausar(self):
        if not self.gestor.lista_activa:
            return
        
        if self.gestor.lista_activa.esta_reproduciendo:
            self.gestor.lista_activa.pausar()
            self.btn_play.config(text="▶")
        else:
            if self.gestor.lista_activa.actual is None and self.gestor.lista_activa.cabeza:
                self.gestor.lista_activa.actual = self.gestor.lista_activa.cabeza
            
            self.gestor.lista_activa.reproducir()
            self.btn_play.config(text="⏸")
            self.tiempo_inicio_reproduccion = time.time()
            
            if self.gestor.lista_activa.actual:
                cancion = self.gestor.lista_activa.actual.cancion
                self.current_song_title.set(cancion.titulo)
                self.current_song_artist.set(cancion.artista)
                self.tiempo_total.set(cancion.obtener_duracion_formateada())
    
    def siguiente_cancion(self):
        if self.gestor.lista_activa:
            self.gestor.lista_activa.siguiente_cancion()
            self.btn_play.config(text="⏸")
            self.tiempo_inicio_reproduccion = time.time()
            
            if self.gestor.lista_activa.actual:
                cancion = self.gestor.lista_activa.actual.cancion
                self.current_song_title.set(cancion.titulo)
                self.current_song_artist.set(cancion.artista)
                self.tiempo_total.set(cancion.obtener_duracion_formateada())
    
    def cancion_anterior(self):
        if self.gestor.lista_activa:
            self.gestor.lista_activa.cancion_anterior()
            self.btn_play.config(text="⏸")
            self.tiempo_inicio_reproduccion = time.time()
            
            if self.gestor.lista_activa.actual:
                cancion = self.gestor.lista_activa.actual.cancion
                self.current_song_title.set(cancion.titulo)
                self.current_song_artist.set(cancion.artista)
                self.tiempo_total.set(cancion.obtener_duracion_formateada())
    
    def seleccionar_cancion(self, event):
        if not self.gestor.lista_activa:
            return
        
        seleccion = self.tree.selection()
        if seleccion:
            valores = self.tree.item(seleccion[0])["values"]
            if valores:
                titulo = valores[0]
                canciones = self.gestor.lista_activa.listar_canciones()
                for cancion in canciones:
                    if cancion.titulo == titulo:
                        self.gestor.lista_activa.seleccionar_cancion(cancion)
                        self.btn_play.config(text="⏸")
                        self.current_song_title.set(cancion.titulo)
                        self.current_song_artist.set(cancion.artista)
                        self.tiempo_total.set(cancion.obtener_duracion_formateada())
                        self.tiempo_inicio_reproduccion = time.time()
                        break
    
    def cambiar_repeticion(self):
        if self.gestor.lista_activa:
            modo = self.gestor.lista_activa.cambiar_modo_repeticion()
            self.btn_repetir.config(text=f"Repetir: {modo}")
    
    def ajustar_volumen(self, valor):
        if self.gestor.lista_activa:
            volumen = float(valor) / 100
            self.gestor.lista_activa.volumen = volumen
            if mixer.get_init() is not None:
                mixer.music.set_volume(volumen)
    
    def saltar_a_tiempo(self, event):
        if self.gestor.lista_activa and self.gestor.lista_activa.actual:
            nueva_posicion = self.progress_bar.get()
            duracion_total = self.gestor.lista_activa.actual.cancion.duracion * 60  # Convertir a segundos
            posicion_segundos = (nueva_posicion / 100) * duracion_total
            
            mixer.music.set_pos(posicion_segundos)
            self.tiempo_inicio_reproduccion = time.time() - posicion_segundos
    
    def actualizar_progreso(self):
        if self.gestor.lista_activa and self.gestor.lista_activa.esta_reproduciendo and self.gestor.lista_activa.actual:
            tiempo_transcurrido = time.time() - self.tiempo_inicio_reproduccion
            duracion_total = self.gestor.lista_activa.actual.cancion.duracion * 60  # Convertir a segundos
            
            if tiempo_transcurrido >= duracion_total:
                self.gestor.lista_activa.manejar_fin_reproduccion()
                if self.gestor.lista_activa.esta_reproduciendo:
                    self.tiempo_inicio_reproduccion = time.time()
                return
            
            porcentaje = (tiempo_transcurrido / duracion_total) * 100
            self.progress_bar.set(porcentaje)
            
            # Actualizar el tiempo actual cada segundo
            if int(tiempo_transcurrido) != self.ultimo_tiempo_actualizado:
                minutos = int(tiempo_transcurrido // 60)
                segundos = int(tiempo_transcurrido % 60)
                self.tiempo_actual.set(f"{minutos}:{segundos:02d}")
                self.ultimo_tiempo_actualizado = int(tiempo_transcurrido)
        
        self.root.after(100, self.actualizar_progreso)
    
    def verificar_eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT:
                if self.gestor.lista_activa:
                    self.gestor.lista_activa.manejar_fin_reproduccion()
                    
                    if self.gestor.lista_activa.esta_reproduciendo and self.gestor.lista_activa.actual:
                        self.tiempo_inicio_reproduccion = time.time()
                        cancion = self.gestor.lista_activa.actual.cancion
                        self.current_song_title.set(cancion.titulo)
                        self.current_song_artist.set(cancion.artista)
                        self.tiempo_total.set(cancion.obtener_duracion_formateada())
                    else:
                        self.btn_play.config(text="▶")
        
        self.root.after(100, self.verificar_eventos)

pygame.init()
mixer.init()

root = tk.Tk()

style = ttk.Style()
style.theme_use("clam")

style.configure("TCombobox", 
    fieldbackground=COLOR_SECUNDARIO, 
    background=COLOR_SECUNDARIO,
    foreground=COLOR_TEXTO,
    selectbackground=COLOR_HOVER,
    selectforeground=COLOR_TEXTO,
    font=("Arial", 10)
)

style.configure("Horizontal.TScale", 
    background=COLOR_SECUNDARIO,
    troughcolor=COLOR_HOVER,
    bordercolor=COLOR_PRIMARIO,
    lightcolor=COLOR_PRIMARIO,
    darkcolor=COLOR_PRIMARIO
)

app = ReproductorApp(root)
app.actualizar_listas()
app.verificar_eventos()
app.actualizar_progreso()

root.mainloop()
pygame.quit()