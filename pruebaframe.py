import customtkinter as ctk

# Configuración inicial de apariencia
ctk.set_appearance_mode("dark") 
ctk.set_default_color_theme("blue")

class MiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Gestor de Texto Pro")
        self.geometry("1920x1080")
        
        # Variables de estado
        self.lista_textos = []
        self.indice_edicion = None

        # Configuración de columnas (Izquierda para entrada, Derecha para lista)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- FRAME IZQUIERDO (Entrada de datos) ---
        self.frame_izq = ctk.CTkFrame(self)
        self.frame_izq.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.label_titulo = ctk.CTkLabel(self.frame_izq, text="Panel de Control", font=("Roboto", 24, "bold"))
        self.label_titulo.pack(pady=20)

        self.entrada_texto = ctk.CTkEntry(self.frame_izq, placeholder_text="Escribe algo aquí...", width=400, height=40)
        self.entrada_texto.pack(pady=10)

        self.btn_añadir = ctk.CTkButton(self.frame_izq, text="Añadir Texto", command=self.añadir_texto, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_añadir.pack(pady=10)

        self.btn_modo = ctk.CTkButton(self.frame_izq, text="Cambiar Modo Claro/Oscuro", command=self.cambiar_tema)
        self.btn_modo.pack(pady=10)

        # --- FRAME DERECHO (Visualización y Gestión) ---
        self.frame_der = ctk.CTkFrame(self)
        self.frame_der.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.label_lista = ctk.CTkLabel(self.frame_der, text="Textos Guardados", font=("Roboto", 20))
        self.label_lista.pack(pady=10)

        # Caja de lista (Scrollable Frame)
        self.scroll_frame = ctk.CTkScrollableFrame(self.frame_der, width=500, height=600)
        self.scroll_frame.pack(pady=10, fill="both", expand=True)

        self.actualizar_vista()

    def añadir_texto(self):
        texto = self.entrada_texto.get()
        if texto:
            if self.indice_edicion is not None:
                self.lista_textos[self.indice_edicion] = texto
                self.indice_edicion = None
                self.btn_añadir.configure(text="Añadir Texto", fg_color="#2ecc71")
            else:
                self.lista_textos.append(texto)
            
            self.entrada_texto.delete(0, 'end')
            self.actualizar_vista()

    def eliminar_texto(self, indice):
        self.lista_textos.pop(indice)
        self.actualizar_vista()

    def preparar_editar(self, indice):
        self.entrada_texto.delete(0, 'end')
        self.entrada_texto.insert(0, self.lista_textos[indice])
        self.indice_edicion = indice
        self.btn_añadir.configure(text="Guardar Cambios", fg_color="#f39c12")

    def actualizar_vista(self):
        # Limpiar frame de scroll
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Reconstruir lista
        for i, t in enumerate(self.lista_textos):
            f = ctk.CTkFrame(self.scroll_frame)
            f.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(f, text=t, anchor="w").pack(side="left", padx=10, expand=True, fill="x")
            
            ctk.CTkButton(f, text="Editar", width=60, fg_color="#3498db", 
                          command=lambda i=i: self.preparar_editar(i)).pack(side="left", padx=2)
            
            ctk.CTkButton(f, text="Eliminar", width=60, fg_color="#e74c3c", 
                          command=lambda i=i: self.eliminar_texto(i)).pack(side="left", padx=2)

    def cambiar_tema(self):
        if ctk.get_appearance_mode() == "Dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

if __name__ == "__main__":
    app = MiApp()
    app.mainloop()