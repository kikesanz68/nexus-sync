import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import pyperclip
from datetime import datetime
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from tkcalendar import Calendar
from fpdf import FPDF

# --- CONFIGURACIÓN GLOBAL ---
CONFIG = {
    "colors": {
        "primary": "#10b981",    # Verde esmeralda
        "secondary": "#3b82f6",  # Azul brillante
        "danger": "#ef4444",     # Rojo vibrante
        "bg_input": "#334155",
        "btn_input": "#1e293b"
    },
    "options": {
        "responsables": ["ENRIQUE", "MISSAEL", "GERMAN"],
        "usuarios": {
            "ENRIQUE": "123",
            "MISSAEL": "123",
            "GERMAN": "123"
        },
        "departamentos": ["MANTENIMIENTO", "RECURSOS HUMANOS", "COMPRAS", "SISTEMAS"],
        "unidades": ["PIEZA", "BOLSA", "KILOGRAMO", "METRO", "LITRO", "GALON", "TONELADA", "PAQUETE"]
    }
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VentanaLogin(ctk.CTkToplevel):
    """Ventana emergente para autenticación de usuarios."""
    def __init__(self, master, callback_exito):
        super().__init__(master)
        self.title("Acceso NexusSync")
        self.geometry("400x450")
        self.resizable(False, False)
        self.callback_exito = callback_exito
        
        # Centrar ventana
        self.after(10, self._centrar)
        self.grab_set()  # Hacer ventana modal
        
        # UI
        ctk.CTkLabel(self, text="BIENVENIDO", font=("Inter", 28, "bold"), text_color=CONFIG["colors"]["primary"]).pack(pady=(40, 5))
        ctk.CTkLabel(self, text="Por favor inicia sesión para continuar", font=("Inter", 12), text_color="#64748b").pack(pady=(0, 30))
        
        self.user_menu = ctk.CTkOptionMenu(self, values=CONFIG["options"]["responsables"], width=280, height=40)
        self.user_menu.pack(pady=10)
        
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=280, height=40)
        self.pass_entry.pack(pady=10)
        self.pass_entry.bind("<Return>", lambda e: self.intentar_login())
        
        self.btn_login = ctk.CTkButton(self, text="ENTRAR", font=("Inter", 14, "bold"), 
                                       fg_color=CONFIG["colors"]["primary"], height=45, width=280,
                                       command=self.intentar_login)
        self.btn_login.pack(pady=(30, 10))

    def _centrar(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def intentar_login(self):
        usuario = self.user_menu.get()
        password = self.pass_entry.get()
        
        # Primero intentamos contra la Nube si hay conexión
        login_exitoso = False
        try:
            if hasattr(self.master, 'conn') and self.master.conn:
                cursor = self.master.conn.cursor()
                cursor.execute("SELECT password FROM usuarios WHERE usuario = %s", (usuario,))
                resultado = cursor.fetchone()
                if resultado and resultado[0] == password:
                    login_exitoso = True
                cursor.close()
        except Exception as e:
            print("Error verificando en nube, usando respaldo local:", e)
            
        # Si no hubo éxito o falló la conexión, usamos el CONFIG local como respaldo
        if not login_exitoso:
            if CONFIG["options"]["usuarios"].get(usuario) == password:
                login_exitoso = True
                
        if login_exitoso:
            self.callback_exito(usuario)
            self.destroy()
        else:
            messagebox.showerror("Acceso Denegado", "Contraseña incorrecta. Inténtalo de nuevo.")
            self.pass_entry.delete(0, 'end')

class VentanaCambiarPassword(ctk.CTkToplevel):
    """Ventana para que el usuario logueado cambie su contraseña."""
    def __init__(self, master, usuario_actual):
        super().__init__(master)
        self.title("Cambiar Contraseña")
        self.geometry("400x480")
        self.resizable(False, False)
        self.usuario_actual = usuario_actual
        self.master = master
        
        # Centrar ventana y hacerla modal
        self.after(10, self._centrar)
        self.grab_set()
        
        ctk.CTkLabel(self, text="🔑 ACTUALIZAR ACCESO", font=("Inter", 22, "bold"), text_color=CONFIG["colors"]["primary"]).pack(pady=(30, 10))
        ctk.CTkLabel(self, text=f"Estás cambiando la clave de: {usuario_actual}", font=("Inter", 12), text_color="#64748b").pack(pady=(0, 30))
        
        # Campos
        self.pass_actual = ctk.CTkEntry(self, placeholder_text="Contraseña Actual", show="*", width=280, height=45)
        self.pass_actual.pack(pady=10)
        
        self.pass_nueva = ctk.CTkEntry(self, placeholder_text="Nueva Contraseña", show="*", width=280, height=45)
        self.pass_nueva.pack(pady=10)
        
        self.pass_confirmar = ctk.CTkEntry(self, placeholder_text="Confirmar Nueva Contraseña", show="*", width=280, height=45)
        self.pass_confirmar.pack(pady=10)
        
        self.btn_guardar = ctk.CTkButton(self, text="GUARDAR CAMBIO", font=("Inter", 14, "bold"), 
                                         fg_color=CONFIG["colors"]["primary"], height=45, width=280,
                                         command=self.ejecutar_cambio)
        self.btn_guardar.pack(pady=(30, 10))

    def _centrar(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def ejecutar_cambio(self):
        actual = self.pass_actual.get()
        nueva = self.pass_nueva.get()
        confirmar = self.pass_confirmar.get()
        
        if not actual or not nueva or not confirmar:
            messagebox.showwarning("Incompleto", "Por favor llena todos los campos.")
            return
            
        if nueva != confirmar:
            messagebox.showerror("Error", "Las contraseñas nuevas no coinciden.")
            return
            
        if len(nueva) < 3:
            messagebox.showerror("Error", "La nueva contraseña debe tener al menos 3 caracteres.")
            return

        # Verificar contraseña actual
        verificado = False
        try:
            if hasattr(self.master, 'conn') and self.master.conn:
                cursor = self.master.conn.cursor()
                cursor.execute("SELECT password FROM usuarios WHERE usuario = %s", (self.usuario_actual,))
                res = cursor.fetchone()
                if res and res[0] == actual:
                    # Proceder al cambio en Nube
                    cursor.execute("UPDATE usuarios SET password = %s WHERE usuario = %s", (nueva, self.usuario_actual))
                    self.master.conn.commit()
                    verificado = True
                cursor.close()
            else:
                # Fallback local (no recomendado pero útil para debug/offline)
                if CONFIG["options"]["usuarios"].get(self.usuario_actual) == actual:
                    CONFIG["options"]["usuarios"][self.usuario_actual] = nueva
                    verificado = True
        except Exception as e:
            messagebox.showerror("Error Nube", f"No se pudo completar el cambio en la base de datos:\n{e}")
            return

        if verificado:
            messagebox.showinfo("Éxito", "Contraseña actualizada exitosamente.\nPor favor, usa tu nueva clave la próxima vez que ingreses.")
            self.destroy()
        else:
            messagebox.showerror("Error", "La contraseña actual es incorrecta.")


class App(ctk.CTk):
    """
    Clase principal de la aplicación.
    Contiene toda la estructura visual y la lógica de negocio para gestionar el historial.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()  # Ocultar ventana principal hasta el login
        
        self.title("NexusSync 3.0 - Control Maestro de Altas")
        self.after(0, lambda: self.state('zoomed'))
        
        # Estado de la Aplicación
        self.responsable_sesion = None
        self.lista_productos_widgets = []
        self.fila_en_edicion = None
        self.codigo_nube_en_edicion = None
        self.codigo_siguiente = None
        
        # Cargar variables de entorno
        self._cargar_env()
              # Inicializar Base de Datos
        if not self.db_uri:
            self.after(100, lambda: self._show_error_and_exit("No se encontró la variable SUPABASE_DB_URI en el archivo .env"))
            return
            
        self._inicializar_db()

        # Iniciar proceso de Login
        self.after(100, lambda: VentanaLogin(self, self._finalizar_login))

    def cerrar_sesion(self):
        """Lógica para salir y volver al login."""
        if messagebox.askyesno("Cerrar Sesión", "¿Deseas cerrar la sesión de " + self.responsable_sesion + "?"):
            self.withdraw()
            self.responsable_sesion = None
            # Destruir frames actuales para que se reconstruyan limpios al re-ingresar
            if hasattr(self, 'frame_izquierdo'): self.frame_izquierdo.destroy()
            if hasattr(self, 'frame_derecho'): self.frame_derecho.destroy()
            self.after(100, lambda: VentanaLogin(self, self._finalizar_login))

    def mostrar_menu_principal(self):
        """Pantalla intermedia para elegir entre Productos o Clientes."""
        # Limpiar cualquier frame existente en la ventana principal
        for widget in ["frame_izquierdo", "frame_derecho"]:
            if hasattr(self, widget):
                getattr(self, widget).destroy()
        
        # También limpiar cualquier otro widget suelto que no sea la ventana misma
        for child in self.winfo_children():
            if isinstance(child, (ctk.CTkFrame, ctk.CTkCanvas)):
                child.destroy()

        self.title(f"NexusSync 3.0 - Menú Principal | Sesión: {self.responsable_sesion}")

        menu_frame = ctk.CTkFrame(self, fg_color="transparent")
        menu_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(menu_frame, text="CENTRO DE OPERACIONES", font=("Inter", 32, "bold"), text_color=CONFIG["colors"]["primary"]).pack(pady=(0, 10))
        ctk.CTkLabel(menu_frame, text="Selecciona el módulo con el que deseas trabajar hoy", font=("Inter", 14), text_color="#64748b").pack(pady=(0, 40))

        buttons_container = ctk.CTkFrame(menu_frame, fg_color="transparent")
        buttons_container.pack()

        # Botón Productos
        btn_prod = ctk.CTkButton(buttons_container, text="📦\n\nALTA DE PRODUCTOS", 
                                 width=250, height=250, font=("Inter", 16, "bold"),
                                 fg_color=CONFIG["colors"]["bg_input"], hover_color=CONFIG["colors"]["primary"],
                                 command=self._mostrar_alta_productos)
        btn_prod.pack(side="left", padx=20)

        # Botón Clientes
        btn_cli = ctk.CTkButton(buttons_container, text="👤\n\nALTA DE CLIENTES", 
                                width=250, height=250, font=("Inter", 16, "bold"),
                                fg_color=CONFIG["colors"]["bg_input"], hover_color=CONFIG["colors"]["secondary"],
                                command=self._mostrar_alta_clientes)
        btn_cli.pack(side="left", padx=20)

        ctk.CTkButton(menu_frame, text="Cambiar Contraseña 🔐", fg_color="transparent", text_color=CONFIG["colors"]["secondary"], 
                       hover_color="#1e293b", command=self.abrir_ventana_cambio_password).pack(pady=(20, 0))

        ctk.CTkButton(menu_frame, text="Cerrar Sesión", fg_color="transparent", text_color="#ef4444", 
                       hover_color="#1e293b", command=self.cerrar_sesion).pack(pady=(10, 0))
        
        # Botón de Salida Definitiva
        ctk.CTkButton(menu_frame, text="SALIR DEL SISTEMA ⛔", fg_color=CONFIG["colors"]["danger"], 
                       hover_color="#991b1b", font=("Inter", 12, "bold"), height=40,
                       command=self.salir_definitivo).pack(pady=(30, 0))

    def salir_definitivo(self):
        """Lógica para cerrar todo el programa tras confirmación."""
        if messagebox.askyesno("Confirmar Salida", "¿Estás seguro que deseas salir completamente del sistema?"):
            self.on_closing() # Llama al limpiador de conexiones y destruye la ventana principal

    def abrir_ventana_cambio_password(self):
        """Abre el diálogo para cambiar contraseña."""
        VentanaCambiarPassword(self, self.responsable_sesion)

    def _mostrar_alta_productos(self):
        """Construye la interfaz de productos."""
        for child in self.winfo_children(): child.destroy()
        self.title("NexusSync 3.0 - Gestión de Productos")
        self._setup_ui_sidebar()
        self._setup_ui_history()
        self.after(300, self.actualizar_codigo_siguiente)

    def _mostrar_alta_clientes(self):
        """Construye la nueva interfaz de alta de clientes."""
        for child in self.winfo_children(): child.destroy()
        self.title("NexusSync 3.0 - Registro de Clientes")

        # Sidebar Clientes
        sidebar = ctk.CTkFrame(self, width=400, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkButton(sidebar, text="← VOLVER AL MENÚ", fg_color="transparent", text_color="#64748b", font=("Inter", 10, "bold"), 
                      command=self.mostrar_menu_principal).pack(pady=(20, 10), padx=20, anchor="w")

        ctk.CTkLabel(sidebar, text="ALTA DE CLIENTES", font=("Inter", 24, "bold"), text_color=CONFIG["colors"]["secondary"]).pack(pady=(20, 30))

        form = ctk.CTkFrame(sidebar, fg_color="transparent")
        form.pack(fill="x", padx=40)

        fields = [
            ("RFC:", "ej. ABC123456XYZ"),
            ("NOMBRE O DENOMINACIÓN SOCIAL:", "Nombre completo o empresa..."),
            ("CÓDIGO POSTAL:", "5 dígitos..."),
            ("RÉGIMEN:", "ej. Personas Físicas..."),
            ("DIRECCIÓN:", "Calle y colonia..."),
            ("NÚMERO EXTERIOR:", "ej. 123"),
            ("NÚMERO INTERIOR (OPCIONAL):", "ej. Depto 4")
        ]

        self.client_entries = {}
        for label_text, placeholder in fields:
            self.crear_label(form, label_text)
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, width=300)
            entry.pack(pady=2)
            self.client_entries[label_text] = entry

        # --- ÁREA DE DOCUMENTOS ---
        ctk.CTkLabel(sidebar, text="DOCUMENTACIÓN", font=("Inter", 12, "bold"), text_color="#64748b").pack(pady=(20, 5))
        
        self.btn_adjuntar = ctk.CTkButton(sidebar, text="ADJUNTAR ARCHIVO 📎\n(PDF, JPG, PNG)", 
                                          fg_color=CONFIG["colors"]["btn_input"], 
                                          hover_color=CONFIG["colors"]["secondary"], 
                                          height=60, font=("Inter", 12, "bold"),
                                          command=self._adjuntar_documento_cliente)
        self.btn_adjuntar.pack(pady=10, padx=40, fill="x")

        self.lbl_info_adjunto = ctk.CTkLabel(sidebar, text="Sin documentos seleccionados", font=("Inter", 10, "italic"), text_color="#ef4444")
        self.lbl_info_adjunto.pack(pady=(0, 10))

        self.archivo_seleccionado_path = None
        self.archivo_seleccionado_bin = None

        ctk.CTkButton(sidebar, text="GUARDAR CLIENTE ✔️", fg_color=CONFIG["colors"]["secondary"], 
                      height=45, font=("Inter", 14, "bold"),
                      command=self._guardar_cliente_nube).pack(pady=20, padx=40, fill="x")

        # Panel Derecho (Resumen y Listado de Clientes)
        self.derecho_clientes = ctk.CTkFrame(self, fg_color="transparent")
        self.derecho_clientes.pack(side="right", fill="both", expand=True)
        
        # Split vertical en el panel derecho: Arriba Pre-visualización, Abajo tabla de clientes (opcional)
        self.preview_frame = ctk.CTkFrame(self.derecho_clientes, fg_color=CONFIG["colors"]["bg_input"], corner_radius=15)
        self.preview_frame.pack(fill="x", padx=30, pady=30, ipady=40)
        
        self.lbl_preview_title = ctk.CTkLabel(self.preview_frame, text="VISTA PREVIA DEL DOCUMENTO", font=("Inter", 16, "bold"), text_color="#94a3b8")
        self.lbl_preview_title.pack(pady=20)
        
        self.lbl_preview_icon = ctk.CTkLabel(self.preview_frame, text="📄", font=("Inter", 80))
        self.lbl_preview_icon.pack(pady=10)
        
        self.lbl_preview_name = ctk.CTkLabel(self.preview_frame, text="Selecciona un archivo para previsualizarlo aquí", font=("Inter", 13, "italic"), text_color="#64748b")
        self.lbl_preview_name.pack(pady=10)

        # Botón para limpiar selección
        self.btn_quitar_adjunto = ctk.CTkButton(self.preview_frame, text="Quitar Archivo ❌", fg_color="#ef4444", 
                                                width=120, command=self._quitar_adjunto, state="disabled")
        self.btn_quitar_adjunto.pack(pady=10)

    def _adjuntar_documento_cliente(self):
        """Abre el diálogo para seleccionar archivos y los prepara para subir."""
        filetypes = [
            ("Documentos e Imágenes", "*.pdf;*.png;*.jpg;*.jpeg"),
            ("PDF", "*.pdf"),
            ("Imágenes", "*.png;*.jpg;*.jpeg"),
            ("Todos los archivos", "*.*")
        ]
        
        path = filedialog.askopenfilename(title="Seleccionar documento del cliente", filetypes=filetypes)
        
        if path:
            self.archivo_seleccionado_path = path
            nombre_archivo = os.path.basename(path)
            
            # Cargar a binario
            try:
                with open(path, "rb") as f:
                    self.archivo_seleccionado_bin = f.read()
                
                # Actualizar UI
                self.lbl_info_adjunto.configure(text=f"✓ {nombre_archivo}", text_color=CONFIG["colors"]["primary"])
                self.lbl_preview_name.configure(text=f"Nombre: {nombre_archivo}\nExtensión: {nombre_archivo.split('.')[-1].upper()}\nTamaño estimado: {len(self.archivo_seleccionado_bin)//1024} KB", text_color="white")
                self.btn_quitar_adjunto.configure(state="normal")
                
                # Cambiar ícono según tipo
                ext = nombre_archivo.lower().split('.')[-1]
                icon = "🖼️" if ext in ['png', 'jpg', 'jpeg'] else "📑"
                self.lbl_preview_icon.configure(text=icon)
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")

    def _quitar_adjunto(self):
        self.archivo_seleccionado_path = None
        self.archivo_seleccionado_bin = None
        self.lbl_info_adjunto.configure(text="Sin documentos seleccionados", text_color="#ef4444")
        self.lbl_preview_name.configure(text="Selecciona un archivo para previsualizarlo aquí", text_color="#64748b")
        self.lbl_preview_icon.configure(text="📄")
        self.btn_quitar_adjunto.configure(state="disabled")

    def _guardar_cliente_nube(self):
        """Extrae los campos del formulario y los guarda en la tabla 'clientes' de Supabase."""
        # Extraer datos dinámicamente de los campos de texto
        datos = {label.replace(":", ""): entry.get().strip() for label, entry in self.client_entries.items()}
        
        # Validaciones mínimas
        if not datos.get("RFC") or not datos.get("NOMBRE O DENOMINACIÓN SOCIAL"):
            messagebox.showwarning("Incompleto", "RFC y Nombre son campos obligatorios.")
            return

        try:
            conn = psycopg2.connect(self.db_uri)
            cursor = conn.cursor()
            
            sql = """
                INSERT INTO clientes (rfc, nombre, cp, regimen, direccion, num_ext, num_int, archivo_nombre, archivo_data, fecha_registro, responsable)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (rfc) DO UPDATE 
                SET nombre=EXCLUDED.nombre, cp=EXCLUDED.cp, regimen=EXCLUDED.regimen, 
                    direccion=EXCLUDED.direccion, num_ext=EXCLUDED.num_ext, 
                    num_int=EXCLUDED.num_int, archivo_nombre=EXCLUDED.archivo_nombre, 
                    archivo_data=EXCLUDED.archivo_data, fecha_registro=EXCLUDED.fecha_registro,
                    responsable=EXCLUDED.responsable
            """
            
            nombre_archivo = os.path.basename(self.archivo_seleccionado_path) if self.archivo_seleccionado_path else None
            fecha_ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            valores = (
                datos.get("RFC"),
                datos.get("NOMBRE O DENOMINACIÓN SOCIAL"),
                datos.get("CÓDIGO POSTAL"),
                datos.get("RÉGIMEN"),
                datos.get("DIRECCIÓN"),
                datos.get("NÚMERO EXTERIOR"),
                datos.get("NÚMERO INTERIOR (OPCIONAL)"),
                nombre_archivo,
                psycopg2.Binary(self.archivo_seleccionado_bin) if self.archivo_seleccionado_bin else None,
                fecha_ahora,
                self.responsable_sesion
            )
            
            cursor.execute(sql, valores)
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Éxito", f"El cliente {datos.get('RFC')} se ha guardado correctamente en la nube.")
            
            # Limpiar formulario tras éxito
            for entry in self.client_entries.values(): entry.delete(0, 'end')
            self._quitar_adjunto()
            
        except Exception as e:
            messagebox.showerror("Error de Guardado", f"No se pudo guardar la información del cliente:\n{e}")


    def _finalizar_login(self, usuario):
        """Callback tras login exitoso."""
        self.responsable_sesion = usuario
        self.deiconify()  # Mostrar ventana principal
        self.mostrar_menu_principal()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_ui_sidebar(self):
        """Configura la columna izquierda: Formulario y Dashboard de control."""
        self.frame_izquierdo = ctk.CTkFrame(self, corner_radius=0, width=400)
        self.frame_izquierdo.pack(side="left", fill="y")
        self.frame_izquierdo.pack_propagate(False)

        ctk.CTkButton(self.frame_izquierdo, text="← VOLVER AL MENÚ", fg_color="transparent", text_color="#64748b", font=("Inter", 10, "bold"), 
                      command=self.mostrar_menu_principal).pack(pady=(15, 0), padx=20, anchor="w")

        # Header con Switch de Tema (Compacto)
        self.header_left = ctk.CTkFrame(self.frame_izquierdo, fg_color="transparent")
        self.header_left.pack(pady=(10, 5), padx=20, fill="x")
        
        self.theme_switch = ctk.CTkSwitch(self.header_left, text="Modo Oscuro", command=self.cambiar_tema)
        self.theme_switch.select()
        self.theme_switch.pack(side="right")

        self.label_titulo = ctk.CTkLabel(self.frame_izquierdo, text="NEXUSSYNC 3.0", font=("Inter", 24, "bold"), text_color=CONFIG["colors"]["primary"])
        self.label_titulo.pack(pady=(5, 10))

        # Contenedor del Formulario (Más compacto)
        self.form_container = ctk.CTkFrame(self.frame_izquierdo, fg_color="transparent")
        self.form_container.pack(pady=5, padx=40, fill="x")

        # Info del Usuario logueado
        self.lbl_session = ctk.CTkLabel(self.form_container, text=f"SESIÓN: {self.responsable_sesion}", 
                                        font=("Inter", 12, "bold"), text_color=CONFIG["colors"]["secondary"])
        self.lbl_session.pack(pady=(0, 5))
        
        self.btn_logout = ctk.CTkButton(self.form_container, text="Cerrar Sesión 🔑", height=24, width=120, 
                                        font=("Inter", 10), fg_color="#475569", hover_color="#dc2626",
                                        command=self.cerrar_sesion)
        self.btn_logout.pack(pady=(0, 5))

        self.btn_seguridad = ctk.CTkButton(self.form_container, text="Seguridad 🔒", height=24, width=120, 
                                           font=("Inter", 10), fg_color="transparent", text_color="#64748b",
                                           hover_color="#1e293b", command=self.abrir_ventana_cambio_password)
        self.btn_seguridad.pack(pady=(0, 15))

        # Inputs con etiquetas (pady reducido)
        self.crear_label(self.form_container, "Departamento:")
        self.dept_menu = ctk.CTkOptionMenu(self.form_container, values=CONFIG["options"]["departamentos"], width=300, fg_color=CONFIG["colors"]["bg_input"], button_color=CONFIG["colors"]["btn_input"])
        self.dept_menu.set("MANTENIMIENTO")
        self.dept_menu.pack(pady=2)

        self.crear_label(self.form_container, "Unidad:")
        self.unit_menu = ctk.CTkOptionMenu(self.form_container, values=CONFIG["options"]["unidades"], width=300, fg_color=CONFIG["colors"]["bg_input"], button_color=CONFIG["colors"]["btn_input"])
        self.unit_menu.pack(pady=2)

        self.crear_label(self.form_container, "Código:")
        self.entry_cod = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Auto-generado",
            width=300,
            state="disabled",
            text_color=CONFIG["colors"]["primary"],
            fg_color=("white", "#1e293b"),
            border_color=CONFIG["colors"]["primary"]
        )
        self.entry_cod.pack(pady=2)

        self.crear_label(self.form_container, "Descripción:")
        self.entry_prod = ctk.CTkEntry(self.form_container, placeholder_text="Nombre del producto...", width=300)
        self.entry_prod.pack(pady=2)
        
        # Menú contextual de Copiar/Pegar para el campo Descripción
        self.menu_contextual_prod = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#28a745", activeforeground="white")
        self.menu_contextual_prod.add_command(label="📋  Copiar", command=self.copiar_descripcion)
        self.menu_contextual_prod.add_command(label="📎  Pegar",  command=self.pegar_descripcion)
        self.entry_prod.bind("<Button-3>", self.mostrar_menu_contextual_prod)

        self.lbl_feedback = ctk.CTkLabel(self.frame_izquierdo, text="", font=("Roboto", 12, "bold"))
        self.lbl_feedback.pack(pady=(0, 5))

        # Botones de Acción (Altura reducida)
        self.btn_accion_principal = ctk.CTkButton(self.frame_izquierdo, text="AÑADIR A LISTA", fg_color=CONFIG["colors"]["primary"], hover_color="#059669", height=40, font=("Inter", 14, "bold"), command=self.procesar_accion_principal)
        self.btn_accion_principal.pack(pady=(15, 8), padx=40, fill="x")

        self.btn_nube = ctk.CTkButton(self.frame_izquierdo, text="GUARDAR EN NUBE ☁️", fg_color=CONFIG["colors"]["secondary"], hover_color="#2563eb", height=40, font=("Inter", 14, "bold"), command=self.guardar_en_nube)
        self.btn_nube.pack(pady=(0, 8), padx=40, fill="x")

        # Reportes y Limpieza
        self.frame_extra = ctk.CTkFrame(self.frame_izquierdo, fg_color="transparent")
        self.frame_extra.pack(pady=5, padx=40, fill="x")
        
        self.btn_save = ctk.CTkButton(self.frame_extra, text="TXT 📄", fg_color=CONFIG["colors"]["danger"], hover_color="#dc2626", width=80, height=35, command=self.guardar_archivo)
        self.btn_save.pack(side="left", padx=5)

        self.btn_excel = ctk.CTkButton(self.frame_extra, text="Excel 📊", fg_color="#10b981", hover_color="#059669", width=80, height=35, command=self.exportar_excel)
        self.btn_excel.pack(side="left", padx=5)

        self.btn_reset = ctk.CTkButton(self.frame_extra, text="Limpiar 🧹", fg_color="#6b7280", hover_color="#4b5563", width=80, height=35, command=self.limpiar_historial_completo)
        self.btn_reset.pack(side="left", padx=5)

        self.btn_reporte_historial = ctk.CTkButton(self.frame_izquierdo, text="HISTORIAL DE ALTAS 📅", fg_color="#6366f1", hover_color="#4f46e5", height=40, font=("Inter", 14, "bold"), command=self.mostrar_historico_ventana)
        self.btn_reporte_historial.pack(pady=(0, 15), padx=40, fill="x")

        # Panel de Código Siguiente (Más ajustado)
        self.frame_codigo_sig = ctk.CTkFrame(self.frame_izquierdo, fg_color=("#f1f5f9", "#1e293b"), border_width=1, border_color=CONFIG["colors"]["primary"], corner_radius=15)
        self.frame_codigo_sig.pack(side="bottom", pady=(10, 20), padx=30, fill="x")

        ctk.CTkLabel(self.frame_codigo_sig, text="CÓDIGO SIGUIENTE", font=("Inter", 10, "bold"), text_color=CONFIG["colors"]["primary"]).pack(pady=(8, 0))
        self.lbl_codigo_sig = ctk.CTkLabel(self.frame_codigo_sig, text="---", font=("Inter", 32, "bold"), text_color=CONFIG["colors"]["primary"])
        self.lbl_codigo_sig.pack(pady=(0, 0))
        self.lbl_aviso_sig = ctk.CTkLabel(self.frame_codigo_sig, text="", font=("Inter", 9), text_color="#64748b")
        self.lbl_aviso_sig.pack(pady=(0, 8))



    def _setup_ui_history(self):
        """Configura la columna derecha: Historial y Herramientas de búsqueda."""
        self.frame_derecho = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_derecho.pack(side="right", fill="both", expand=True)

        # Buscador superior
        self.search_container = ctk.CTkFrame(self.frame_derecho, fg_color="transparent")
        self.search_container.pack(pady=(30, 10), padx=30, fill="x")
        
        self.entry_search = ctk.CTkEntry(self.search_container, placeholder_text="Buscar por código o producto...", height=45, font=("Inter", 13), corner_radius=10)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", self.filtrar_busqueda)

        self.btn_buscar = ctk.CTkButton(self.search_container, text="🔍 Buscar", width=100, height=45, fg_color="#64748b", hover_color="#475569", font=("Inter", 12, "bold"), corner_radius=10, command=lambda: self.filtrar_busqueda(None))
        self.btn_buscar.pack(side="right")

        # Menú contextual Buscador
        self.menu_contextual = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#0066cc", activeforeground="white")
        self.menu_contextual.add_command(label="Copiar", command=self.copiar_buscador)
        self.menu_contextual.add_command(label="Pegar", command=self.pegar_buscador)
        self.entry_search.bind("<Button-3>", self.mostrar_menu_contextual)

        self.scroll_frame = ctk.CTkScrollableFrame(self.frame_derecho, label_text="HISTORIAL DE ACTIVIDAD")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Panel de botones de copiado
        self.button_grid = ctk.CTkFrame(self.frame_derecho, fg_color="transparent")
        self.button_grid.pack(pady=20, padx=30, fill="x")

        ctk.CTkButton(self.button_grid, text="COPIAR PARA ENVÍO 📋", fg_color=CONFIG["colors"]["secondary"], hover_color="#2563eb", height=40, font=("Inter", 12, "bold"), command=self.copiar_seleccionados).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="SOLO CÓDIGOS 🔢", fg_color="#f59e0b", hover_color="#d97706", height=40, font=("Inter", 12, "bold"), command=lambda: self.copiar_especifico(0)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="SOLO PRODUCTOS 📦", fg_color="#06b6d4", hover_color="#0891b2", height=40, font=("Inter", 12, "bold"), command=lambda: self.copiar_especifico(1)).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="SOLO UNIDADES 📏", fg_color="#8b5cf6", hover_color="#7c3aed", height=40, font=("Inter", 12, "bold"), command=lambda: self.copiar_especifico(2)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.button_grid.grid_columnconfigure((0, 1), weight=1)
        self.after(300, self.actualizar_codigo_siguiente)

    def cambiar_tema(self):
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _cargar_env(self):
        """Carga las variables de entorno soportando empaquetado PyInstaller."""
        import sys
        if getattr(sys, 'frozen', False):
            # Ruta donde PyInstaller extrae los archivos temporales
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
            env_path = os.path.join(base_path, '.env')
            # Si no está empaquetado pero sí congelado, buscar junto al exe
            if not os.path.exists(env_path):
                env_path = os.path.join(os.path.dirname(sys.executable), '.env')
            load_dotenv(env_path)
        else:
            load_dotenv()
        self.db_uri = os.getenv("SUPABASE_DB_URI")

    def _inicializar_db(self):
        """Prepara la conexión inicial y crea la tabla si no existe."""
        try:
            self.conn = psycopg2.connect(self.db_uri, connect_timeout=5)
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS historial (
                    codigo TEXT PRIMARY KEY,
                    producto TEXT,
                    unidad TEXT,
                    responsable TEXT,
                    fecha TEXT,
                    departamento TEXT
                )
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    usuario TEXT PRIMARY KEY,
                    password TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    rfc TEXT PRIMARY KEY,
                    nombre TEXT,
                    cp TEXT,
                    regimen TEXT,
                    direccion TEXT,
                    num_ext TEXT,
                    num_int TEXT,
                    archivo_nombre TEXT,
                    archivo_data BYTEA,
                    fecha_registro TEXT,
                    responsable TEXT
                )
            ''')
            
            # Poblar usuarios iniciales si la tabla está vacía
            self.cursor.execute("SELECT COUNT(*) FROM usuarios")
            if self.cursor.fetchone()[0] == 0:
                for user, pwd in CONFIG["options"]["usuarios"].items():
                    self.cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (%s, %s)", (user, pwd))
                    
            self.conn.commit()
        except Exception as e:
            self.after(100, lambda ex=e: messagebox.showerror("Error de Conexión", f"No se pudo conectar a la nube: {ex}"))

    def _show_error_and_exit(self, mensaje):
        messagebox.showerror("Error Crítico", mensaje)
        self.destroy()

    def on_closing(self):

        if hasattr(self, 'conn'):
            self.conn.close()
        self.destroy()

    def mostrar_menu_contextual(self, event):
        self.menu_contextual.tk_popup(event.x_root, event.y_root)

    def copiar_buscador(self):
        try:
            texto = self.entry_search.selection_get()
        except tk.TclError:
            texto = self.entry_search.get() # Si no hay selección, copia todo el texto
        if texto:
            pyperclip.copy(texto)

    def pegar_buscador(self):
        texto = pyperclip.paste()
        if texto:
            try:
                self.entry_search.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            self.entry_search.insert(tk.INSERT, texto)
            self.filtrar_busqueda(None)

    def mostrar_menu_contextual_prod(self, event):
        """Menú contextual click derecho para el campo Descripción."""
        self.menu_contextual_prod.tk_popup(event.x_root, event.y_root)

    def copiar_descripcion(self):
        try:
            texto = self.entry_prod.selection_get()
        except tk.TclError:
            texto = self.entry_prod.get()  # Si no hay selección, copia todo
        if texto:
            pyperclip.copy(texto)

    def pegar_descripcion(self):
        texto = pyperclip.paste()
        if texto:
            try:
                self.entry_prod.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            self.entry_prod.insert(tk.INSERT, texto)
            self.programar_validacion_vivo(None)

    def crear_label(self, master, texto):
        lbl = ctk.CTkLabel(master, text=texto, font=("Roboto", 12))
        lbl.pack(pady=(5, 0))

    def _set_cod(self, valor):
        """Helper: habilita el campo código (bloqueado), escribe el valor, lo bloquea
        y actualiza el panel de 'Código Siguiente' para mostrar valor+1."""
        self.entry_cod.configure(state="normal")
        self.entry_cod.delete(0, 'end')
        self.entry_cod.insert(0, str(valor))
        self.entry_cod.configure(state="disabled")
        
        # El panel de abajo muestra el que viene DESPUÉS del que está en el campo
        try:
            siguiente_display = int(valor) + 1
            self.lbl_codigo_sig.configure(text=str(siguiente_display))
            self.lbl_aviso_sig.configure(text=f"(Código actual en campo: {valor})")
        except (ValueError, AttributeError):
            pass


    # --- LÓGICA DE CÓDIGO SIGUIENTE ---

    def obtener_maximo_codigo_nube(self):
        """
        Consulta la base de datos y retorna el mayor código numérico registrado.
        Si no hay registros numéricos, retorna 66056 como base.
        """
        try:
            conn = psycopg2.connect(self.db_uri, connect_timeout=4)
            cur = conn.cursor()
            # Obtenemos el máximo código numérico de la tabla
            cur.execute("""
                SELECT MAX(CAST(codigo AS BIGINT))
                FROM historial
                WHERE codigo ~ '^[0-9]+$'
            """)
            resultado = cur.fetchone()
            cur.close()
            conn.close()
            if resultado and resultado[0] is not None:
                return int(resultado[0])
            else:
                return 66057  # Base si la tabla está vacía o sin códigos numéricos
        except Exception as e:
            print("No se pudo obtener el máximo código:", e)
            return None

    def actualizar_codigo_siguiente(self):
        """
        Calcula el siguiente código disponible (máximo + 1), lo pone en el campo
        y el panel muestra automáticamente ese valor + 1 (via _set_cod).
        """
        maximo = self.obtener_maximo_codigo_nube()
        if maximo is not None:
            self.codigo_siguiente = maximo + 1
            # Solo rellenar el campo si no hay edición activa
            if not self.entry_cod.get().strip() and self.fila_en_edicion is None and self.codigo_nube_en_edicion is None:
                self._set_cod(self.codigo_siguiente)
            else:
                # Aunque no rellene el campo, actualiza el panel con el valor actual del campo
                try:
                    val_actual = int(self.entry_cod.get().strip())
                    self.lbl_codigo_sig.configure(text=str(val_actual + 1), text_color=CONFIG["colors"]["primary"])
                    self.lbl_aviso_sig.configure(text=f"(Sigue al que está en campo: {val_actual})", text_color="#64748b")
                except ValueError:
                    pass
        else:
            self.lbl_codigo_sig.configure(text="Sin conexión", text_color="#ff6666")
            self.lbl_aviso_sig.configure(text="Verifique la conexión a la nube", text_color="#ff6666")


    # --- LÓGICA DE MEJORAS ---

    def programar_validacion_vivo(self, event):
        """Reservado — ya no se usa para búsqueda en BD."""
        pass

    def validar_en_vivo(self):
        """Reservado — ya no busca en BD desde el campo descripción."""
        pass

    def procesar_accion_principal(self):
        """
        [MÓDULO DE ACCIÓN DE BOTÓN AÑADIR/ACTUALIZAR]
        Decide el comportamiento del botón verde basándose en el contexto actual:
        - Si edita un producto de la nube -> Llama a actualizar_en_nube()
        - Si edita un producto de la lista temporal -> Llama a finalizar_edicion()
        - Si es un producto nuevo -> Llama a agregar_a_lista()
        """
        if self.codigo_nube_en_edicion is not None:
            self.actualizar_en_nube()
        elif self.fila_en_edicion is None:
            self.agregar_a_lista()
        else:
            self.finalizar_edicion()

    def agregar_a_lista(self):
        """
        [MÓDULO DE INSERCIÓN TEMPORAL]
        Valida que los campos estén completos, que el código sea numérico y 
        que el registro no exista ya localmente o en Supabase (la BD). 
        Si todo está bien, lo enlista visualmente sin mandarlo a la BD aún.
        """
        cod = self.entry_cod.get().strip()
        prod = self.entry_prod.get().strip()
        
        if not cod.isdigit() or not prod:
            messagebox.showwarning("Error", "Datos incompletos o código inválido (deben ser solo números).")
            return
            
        # Validación de duplicados locales
        codigos_actuales = [i['datos'][0] for i in self.lista_productos_widgets]
        productos_actuales = [i['datos'][1].lower() for i in self.lista_productos_widgets]
        
        if cod in codigos_actuales:
            messagebox.showwarning("Código Duplicado", f"El código {cod} ya está en tu lista actual.\nEvita capturarlo dos veces.")
            return
        if prod.lower() in productos_actuales:
            messagebox.showwarning("Producto Duplicado", f"El nombre del producto '{prod}' ya está en tu lista actual.")
            return

        # Validación estricta con Supabase para códigos o productos duplicados
        try:
            conn_nube = psycopg2.connect(self.db_uri, connect_timeout=3)
            cursor_nube = conn_nube.cursor()
            
            # Busca ignorando mayúsculas y minúsculas (ILIKE)
            cursor_nube.execute("SELECT codigo, producto FROM historial WHERE codigo = %s OR producto ILIKE %s LIMIT 1", (cod, prod))
            existente = cursor_nube.fetchone()
            
            cursor_nube.close()
            conn_nube.close()
            
            if existente:
                cod_existente, prod_existente = existente
                messagebox.showerror("No autorizado", f"Este producto ya fue dado de alta en la Base de Datos.\n\nCoincidencia encontrada:\nCódigo: {cod_existente}\nProducto: {prod_existente}")
                return
        except Exception as e:
            print("No se pudo validar duplicados en la nube:", e) # Permite fallo silencioso si se corta el internet

        # ✅ ALMACENAR FECHA COMPLETA (Fecha + Hora) para reportes históricos
        fecha_full = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.crear_fila_historial(cod, prod, self.unit_menu.get(), self.responsable_sesion, fecha_full, self.dept_menu.get())
        self.entry_prod.delete(0, 'end')
        self.lbl_feedback.configure(text="")
        
        # ✅ CAMBIO SOLICITADO: Incrementar automáticamente al añadir a la lista
        self._refrescar_codigo_y_rellenar()

    def _refrescar_codigo_y_rellenar(self):
        """
        Recalcula el siguiente código desde la nube y pre-rellena el campo.
        Se llama después de agregar un producto a la lista local.
        El siguiente código es el máximo en nube+1 o bien el mayor entre lista local y nube+1.
        """
        maximo_nube = self.obtener_maximo_codigo_nube()
        # También considera los códigos ya en la lista local (aún no guardados en nube)
        codigos_locales = []
        for item in self.lista_productos_widgets:
            try:
                codigos_locales.append(int(item['datos'][0]))
            except ValueError:
                pass
        maximo_local = max(codigos_locales) if codigos_locales else 0
        maximo_base = maximo_nube if maximo_nube is not None else 66057
        maximo_total = max(maximo_base, maximo_local)
        self.codigo_siguiente = maximo_total + 1
        
        self.lbl_codigo_sig.configure(text=str(self.codigo_siguiente + 1), text_color=CONFIG["colors"]["primary"])
        self.lbl_aviso_sig.configure(
            text=f"(Último ocupado: {maximo_total} | En campo: {self.codigo_siguiente})",
            text_color="#64748b"
        )
        self._set_cod(self.codigo_siguiente)

    def crear_fila_historial(self, cod, prod, uni, resp, fecha, dept):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)

        check_var = ctk.BooleanVar(value=True)
        chk = ctk.CTkCheckBox(row, text=f"[{fecha}] [{dept}] {cod} | {prod}", variable=check_var, font=("Roboto", 12))
        chk.pack(side="left", padx=5, expand=True, fill="x")

        item_data = {
            "var": check_var,
            "datos": [cod, prod, uni, resp, fecha, dept],
            "frame": row,
            "chk_widget": chk
        }

        ctk.CTkButton(row, text="✏️", width=30, fg_color="#ffc107", text_color="black", command=lambda: self.iniciar_edicion(item_data)).pack(side="right", padx=2)
        ctk.CTkButton(row, text="🗑️", width=30, fg_color="#dc3545", command=lambda: self.eliminar_producto(item_data)).pack(side="right", padx=2)

        self.lista_productos_widgets.append(item_data)

    def filtrar_busqueda(self, event):
        """
        [MÓDULO DE BÚSQUEDA]
        Filtrado combinado: 
        1. Oculta/Muestra en tiempo real los registros guardados en la lista local temporal.
        2. Inicia un temporizador para buscar indirectamente en Supabase si encuentra algo.
        """
        termino = self.entry_search.get().lower().strip()
        
        # 1. Filtrado de la lista local en tiempo real
        for item in self.lista_productos_widgets:
            if not termino or termino in item['datos'][0].lower() or termino in item['datos'][1].lower():
                item['frame'].pack(fill="x", pady=2)
            else:
                item['frame'].pack_forget()
                
        # 2. Gestión de la búsqueda en Supabase (Debounce de 600ms para evitar sobrecarga)
        if hasattr(self, '_search_timer'):
            self.after_cancel(self._search_timer)
            
        if termino:
            self._search_timer = self.after(600, self.buscar_en_nube, termino)
        else:
            self.limpiar_resultados_nube()

    def limpiar_resultados_nube(self):
        if hasattr(self, 'resultados_nube_widgets'):
            for widget in self.resultados_nube_widgets:
                widget.destroy()
        self.resultados_nube_widgets = []

    def buscar_en_nube(self, termino):
        """
        [MÓDULO DE CONSULTA A BASE DE DATOS]
        Se conecta a Supabase y trae hasta 15 resultados que coincidan en el nombre o código.
        Los pinta en la tabla visual para que puedas verlos (o editarlos/borrarlos).
        """
        self.limpiar_resultados_nube()
        
        # Códigos locales para no mostrar duplicados
        codigos_locales = [item['datos'][0] for item in self.lista_productos_widgets]
        
        try:
            # connect_timeout=3 previene que la interfaz se congele mucho tiempo si no hay internet
            conn_nube = psycopg2.connect(self.db_uri, connect_timeout=3)
            cursor_nube = conn_nube.cursor()
            
            # ILIKE hace búsqueda insensible a mayúsculas/minúsculas en PostgreSQL
            cursor_nube.execute("""
                SELECT codigo, producto, unidad, responsable, fecha, departamento 
                FROM historial 
                WHERE codigo ILIKE %s OR producto ILIKE %s 
                LIMIT 15
            """, (f"%{termino}%", f"%{termino}%"))
            filas_nube = cursor_nube.fetchall()
            
            for fila in filas_nube:
                cod = fila[0]
                if cod not in codigos_locales:
                    # Crear fila visual estática para mostrar el resultado resguardado en la nube
                    row = ctk.CTkFrame(self.scroll_frame, fg_color="#1a2b3c", border_width=1, border_color="#0066cc")
                    row.pack(fill="x", pady=2)
                    
                    lbl = ctk.CTkLabel(row, text=f"☁️ NUBE   |   {fila[4]} | [{fila[5]}]   {cod}   |   {fila[1]} ({fila[2]})", 
                                       font=("Roboto", 11, "bold"), text_color="#a8d0e6")
                    lbl.pack(side="left", padx=10, pady=5, expand=True, fill="x", anchor="w")
                    
                    btn_editar = ctk.CTkButton(row, text="✏️", width=30, fg_color="#ffc107", text_color="black", hover_color="#e0a800", command=lambda f=fila: self.iniciar_edicion_nube(f))
                    btn_editar.pack(side="right", padx=2)
                    
                    btn_eliminar = ctk.CTkButton(row, text="🗑️", width=30, fg_color="#dc3545", hover_color="#c82333", command=lambda c=cod: self.eliminar_en_nube(c))
                    btn_eliminar.pack(side="right", padx=10)
                    
                    self.resultados_nube_widgets.append(row)
                    
            cursor_nube.close()
            conn_nube.close()
        except Exception as e:
            print("Búsqueda en la nube no disponible:", e)

    def limpiar_historial_completo(self):
        """MEJORA: Limpiar todo"""
        if not self.lista_productos_widgets: return
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar TODA la lista actual?"):
            for item in self.lista_productos_widgets:
                item['frame'].destroy()
            self.lista_productos_widgets.clear()
            self.fila_en_edicion = None
            self.btn_accion_principal.configure(text="AÑADIR A LISTA", fg_color="#28a745")
            self.entry_search.delete(0, 'end')
            self.limpiar_resultados_nube()

    # --- LÓGICA DE EDICIÓN ---

    def iniciar_edicion(self, item_data):
        self.fila_en_edicion = item_data
        d = item_data["datos"]
        self._set_cod(d[0])
        self.entry_prod.delete(0, 'end'); self.entry_prod.insert(0, d[1])
        self.unit_menu.set(d[2]); self.dept_menu.set(d[5])
        self.btn_accion_principal.configure(text="ACTUALIZAR FILA", fg_color="#fd7e14")
        item_data["frame"].configure(fg_color="#3b3b3b")

    def finalizar_edicion(self):
        cod = self.entry_cod.get().strip()
        prod = self.entry_prod.get().strip()
        if cod.isdigit() and prod:
            d = self.fila_en_edicion["datos"]
            codigo_anterior = d[0]
            
            # Validar localmente si el código o el producto que acaban de escribir choca 
            # con OTRO registro que ya esté listado
            for item in self.lista_productos_widgets:
                if item == self.fila_en_edicion:
                    continue
                if item['datos'][0] == cod:
                    messagebox.showerror("Error", "Este código ya está en otro producto de la lista.")
                    return
                if item['datos'][1].lower() == prod.lower():
                    messagebox.showerror("Error", "Este nombre de producto ya está en otro producto de la lista.")
                    return
            
            # Actualizamos los datos visuales
            d[0], d[1], d[2], d[3], d[5] = cod, prod, self.unit_menu.get(), self.responsable_sesion, self.dept_menu.get()

            self.fila_en_edicion["chk_widget"].configure(text=f"[{d[4]}] [{d[5]}] {d[0]} | {d[1]}")
            self.fila_en_edicion["frame"].configure(fg_color="transparent")
            self.fila_en_edicion = None
            self.btn_accion_principal.configure(text="AÑADIR A LISTA", fg_color="#28a745")
            # El código NO se recalcula aquí — se mantiene hasta GUARDAR EN NUBE
            self.entry_prod.delete(0, 'end')

    def iniciar_edicion_nube(self, fila_nube):
        self.codigo_nube_en_edicion = fila_nube[0]
        if self.fila_en_edicion:
            self.fila_en_edicion["frame"].configure(fg_color="transparent")
            self.fila_en_edicion = None
            
        self._set_cod(fila_nube[0])
        self.entry_prod.delete(0, 'end'); self.entry_prod.insert(0, fila_nube[1])
        self.unit_menu.set(fila_nube[2]); self.dept_menu.set(fila_nube[5])
        
        self.btn_accion_principal.configure(text="ACTUALIZAR EN NUBE ☁️", fg_color="#fd7e14", hover_color="#e06200")

    def actualizar_en_nube(self):
        cod = self.entry_cod.get().strip()
        prod = self.entry_prod.get().strip()
        
        if not cod.isdigit() or not prod:
            messagebox.showwarning("Error", "Datos incompletos o código inválido.")
            return

        try:
            conn_nube = psycopg2.connect(self.db_uri)
            cursor_nube = conn_nube.cursor()
            
            cursor_nube.execute("SELECT codigo FROM historial WHERE (codigo = %s OR producto ILIKE %s) AND codigo != %s", 
                                (cod, prod, self.codigo_nube_en_edicion))
            if cursor_nube.fetchone():
                messagebox.showerror("Duplicado en la Nube", "Error al actualizar.\nYa existe otro registro con ese MISMO CÓDIGO o ese MISMO NOMBRE.")
                cursor_nube.close()
                conn_nube.close()
                return

            cursor_nube.execute("""
                UPDATE historial 
                SET codigo = %s, producto = %s, unidad = %s, responsable = %s, departamento = %s
                WHERE codigo = %s
            """, (cod, prod, self.unit_menu.get(), self.responsable_sesion, self.dept_menu.get(), self.codigo_nube_en_edicion))
            
            conn_nube.commit()
            cursor_nube.close()
            conn_nube.close()
            
            messagebox.showinfo("Éxito", "El producto se modificó correctamente en Supabase.")
            
            self.codigo_nube_en_edicion = None
            self.btn_accion_principal.configure(text="AÑADIR A LISTA", fg_color="#28a745", hover_color="#218838")
            self._set_cod(self.codigo_siguiente)
            self.entry_prod.delete(0, 'end')
            
            self.filtrar_busqueda(None) # Refrescar búsqueda visual
            
        except psycopg2.IntegrityError:
            messagebox.showerror("Código ya existe", "No se puede actualizar. El nuevo código ya le pertenece a otro producto en la Nube.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al actualizar en la nube:\n{e}")

    def eliminar_producto(self, item_data):
        item_data["frame"].destroy()
        self.lista_productos_widgets.remove(item_data)
        # ✅ CAMBIO SOLICITADO: Refrescar código al borrar (lo "regresa" si era el último)
        self._refrescar_codigo_y_rellenar()

    def eliminar_en_nube(self, codigo):
        if not messagebox.askyesno("Confirmar Eliminación", f"¿Estás completamente seguro de borrar el producto con código {codigo} de la base de datos en nube?\n\nEsta acción eliminará el registro de forma permanente para todos los usuarios y no se puede deshacer."):
            return
            
        try:
            conn_nube = psycopg2.connect(self.db_uri)
            cursor_nube = conn_nube.cursor()
            
            cursor_nube.execute("DELETE FROM historial WHERE codigo = %s", (codigo,))
            
            conn_nube.commit()
            cursor_nube.close()
            conn_nube.close()
            
            messagebox.showinfo("Eliminado", f"El producto {codigo} fue eliminado desde la Nube exitosamente.")
            self.filtrar_busqueda(None) # Refrescar la búsqueda
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el código desde la nube.\n{e}")

    # --- COPIADO Y GUARDADO ---
    
    def guardar_en_nube(self):
        """
        [MÓDULO DE SINCRONIZACIÓN]
        Toma todos los productos que tengan el checkbox ✓ marcado en tu lista de 'HISTORIAL DE ACTIVIDAD',
        y los intenta insertar uno por uno en la tabla de Supabase. Te advierte de duplicados.
        """
        elementos_a_guardar = [i['datos'] for i in self.lista_productos_widgets if i['var'].get()]
        if not elementos_a_guardar:
            messagebox.showinfo("Sin selección", "No hay elementos en la lista para guardar.")
            return

        # Intentar conectar fresco para evitar problemas de conexión perdida
        try:
            conn_nube = psycopg2.connect(self.db_uri)
            cursor_nube = conn_nube.cursor()
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo contactar con Supabase:\n{e}")
            return

        duplicados = []
        guardados = 0
        ultimo_error = ""
        elementos_a_eliminar = []

        for item in self.lista_productos_widgets:
            if not item['var'].get():
                continue
                
            d = item['datos']
            try:
                # Comprobar si ya existe con el mismo código O con el mismo producto estrictamente (para evitar nombres tontamente duplicados)
                cursor_nube.execute("SELECT codigo, producto FROM historial WHERE codigo = %s OR producto ILIKE %s LIMIT 1", (d[0], d[1]))
                existente = cursor_nube.fetchone()
                
                if existente:
                    duplicados.append(f"{d[0]} ({d[1]})")
                    continue

                cursor_nube.execute("INSERT INTO historial (codigo, producto, unidad, responsable, fecha, departamento) VALUES (%s, %s, %s, %s, %s, %s)", 
                                    (d[0], d[1], d[2], d[3], d[4], d[5]))
                conn_nube.commit()
                guardados += 1
                elementos_a_eliminar.append(item)
            except psycopg2.IntegrityError:
                conn_nube.rollback()
                duplicados.append(f"{d[0]} ({d[1]})")
            except Exception as e:
                conn_nube.rollback()
                ultimo_error = str(e)
                print(f"Error insertando {d[0]}:", e)
                
        cursor_nube.close()
        conn_nube.close()

        # Limpiar los guardados exitosamente
        for item in elementos_a_eliminar:
            self.eliminar_producto(item)

        if guardados > 0:
            mensaje = f"Se guardaron {guardados} productos exitosamente en la Nube."
            if duplicados:
                mensaje += f"\n\nATENCIÓN: Los siguientes productos NO se guardaron porque el código o el nombre ya existían:\n{', '.join(duplicados)}"
                messagebox.showwarning("Proceso Completado con Observaciones", mensaje)
            else:
                messagebox.showinfo("Éxito", mensaje)
            # ✅ Solo aquí se recalcula y actualiza el código — al confirmar que fue a la nube
            self.after(200, self._refrescar_codigo_y_rellenar)
        else:
            if duplicados:
                messagebox.showwarning("Sin cambios", f"Todos los productos seleccionados ya están dados de alta o tienen un nombre repetido:\n{', '.join(duplicados)}")
            else:
                messagebox.showerror("Error", f"Ocurrió un problema y no se guardaron los productos.\nDetalle: {ultimo_error}")

    def copiar_seleccionados(self):
        seleccionados = [f"• {i['datos'][0]} - {i['datos'][1]} ({i['datos'][2]}) [{i['datos'][5]}]" for i in self.lista_productos_widgets if i['var'].get()]
        if seleccionados:
            pyperclip.copy("Buen día, sus códigos son:\n" + "\n".join(seleccionados))
            messagebox.showinfo("Copiado", "Formato para envío listo.")

    def copiar_especifico(self, idx):
        sel = [i['datos'][idx] for i in self.lista_productos_widgets if i['var'].get()]
        if sel: pyperclip.copy("\n".join(sel)); messagebox.showinfo("Copiado", "Datos copiados.")

    def guardar_archivo(self):
        elementos_a_guardar = [i for i in self.lista_productos_widgets if i['var'].get()]
        if not elementos_a_guardar: return
        carpeta = filedialog.askdirectory()
        if not carpeta: return
        
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        fecha_hora_re = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        ruta = os.path.join(carpeta, f"Altas_{self.responsable_sesion}_{fecha_hora_re}.txt")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(f"REPORTE NEXUSSYNC - CONTROL DE ALTAS\n")
            f.write(f"Generado el: {fecha_actual} a las {datetime.now().strftime('%H:%M:%S')}\n")
            f.write("-" * 80 + "\n\n")
            
            for item in elementos_a_guardar: 
                d = item['datos']
                # d[0]=codigo, d[1]=producto, d[2]=unidad, d[3]=responsable, d[4]=hora, d[5]=departamento
                f.write(f"FECHA: {fecha_actual} | HORA: {d[4]} | RESPONSABLE: {d[3]} | DEPTO: {d[5]} | CÓD: {d[0]} | PROD: {d[1]} ({d[2]})\n")
                
        for item in elementos_a_guardar:
            self.eliminar_producto(item)
            
        messagebox.showinfo("Éxito", "Reporte TXT guardado exitosamente con fecha y responsables.")

    def exportar_excel(self):
        """
        [MÓDULO DE EXPORTACIÓN PANDAS]
        Toma todos los elementos con 'palomita' de la lista y genera un Excel.
        """
        elementos_a_guardar = [i for i in self.lista_productos_widgets if i['var'].get()]
        if not elementos_a_guardar:
            messagebox.showinfo("Sin selección", "No hay elementos en la lista para exportar.")
            return

        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Archivos Excel", "*.xlsx")],
                                             initialfile=f"Reporte_Altas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        if not ruta: return

        try:
            datos = [i['datos'] for i in elementos_a_guardar]
            df = pd.DataFrame(datos, columns=['Código', 'Producto', 'Unidad', 'Responsable', 'Fecha/Hora', 'Departamento'])
            df.to_excel(ruta, index=False, engine='openpyxl')
            
            for item in elementos_a_guardar:
                self.eliminar_producto(item)
                
            messagebox.showinfo("Éxito", f"Reporte Excel guardado correctamente en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo Excel.\nDetalle: {e}")

    # --- NUEVAS FUNCIONES DE REPORTE HISTÓRICO ---
    def mostrar_historico_ventana(self):
        """Abre la ventana de búsqueda histórica por fecha."""
        win = ctk.CTkToplevel(self)
        win.title("Reporte de Altas por Fecha")
        win.geometry("900x650")
        win.grab_set()
        
        # Header
        top_frame = ctk.CTkFrame(win, fg_color="transparent")
        top_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(top_frame, text="CONSULTA HISTÓRICA", font=("Inter", 22, "bold"), text_color=CONFIG["colors"]["primary"]).pack(side="left")
        
        # Layout principal de la ventana
        main_layout = ctk.CTkFrame(win, fg_color="transparent")
        main_layout.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Panel Izquierdo: Calendario y Acciones
        left_panel = ctk.CTkFrame(main_layout, width=320)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        ctk.CTkLabel(left_panel, text="ELIGE UNA FECHA", font=("Inter", 12, "bold")).pack(pady=(15, 5))
        
        self.cal = Calendar(left_panel, selectmode='day', 
                           background=CONFIG["colors"]["btn_input"], 
                           foreground='white', selectbackground=CONFIG["colors"]["primary"])
        self.cal.pack(padx=10, pady=10, fill="x")
        
        self.btn_consulta_dia = ctk.CTkButton(left_panel, text="🔎 CONSULTAR DÍA", fg_color=CONFIG["colors"]["primary"], height=45, font=("Inter", 13, "bold"),
                                              command=lambda: self.buscar_folios_por_fecha(self.cal.get_date(), scroll_resultados))
        self.btn_consulta_dia.pack(fill="x", padx=20, pady=15)
        
        self.btn_descargar_pdf = ctk.CTkButton(left_panel, text="📥 DESCARGAR PDF", fg_color="#ef4444", height=45, font=("Inter", 13, "bold"),
                                               state="disabled")
        self.btn_descargar_pdf.pack(fill="x", padx=20, pady=5)
        
        # Panel Derecho: Resultados
        right_panel = ctk.CTkFrame(main_layout)
        right_panel.pack(side="right", fill="both", expand=True)
        
        self.lbl_status_reporte = ctk.CTkLabel(right_panel, text="Selecciona una fecha para ver los folios registrados", font=("Inter", 11), text_color="#64748b")
        self.lbl_status_reporte.pack(pady=10)
        
        scroll_resultados = ctk.CTkScrollableFrame(right_panel, label_text="Altas encontradas")
        scroll_resultados.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.data_reporte_actual = [] 

    def buscar_folios_por_fecha(self, fecha_cal, container):
        """Consulta folios en Supabase por la fecha seleccionada."""
        for widget in container.winfo_children():
            widget.destroy()
        
        try:
            # Parsear fecha del calendario (tkcalendar suele devolver 'MM/DD/YY' o similar según OS locale)
            from datetime import datetime
            try:
                # Intentar varios formatos comunes
                for fmt in ('%m/%d/%y', '%d/%m/%y', '%Y-%m-%d', '%y-%m-%d'):
                    try:
                        d_obj = datetime.strptime(fecha_cal, fmt)
                        break
                    except: continue
                prefijo_fecha = d_obj.strftime("%Y-%m-%d")
            except:
                prefijo_fecha = fecha_cal # Fallback si ya viene formateada
            
            conn = psycopg2.connect(self.db_uri)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT codigo, producto, responsable, fecha, departamento, unidad
                FROM historial 
                WHERE fecha LIKE %s
                ORDER BY fecha ASC
            """, (f"{prefijo_fecha}%",))
            
            resultados = cursor.fetchall()
            cursor.close()
            conn.close()
            
            self.data_reporte_actual = resultados
            self.fecha_seleccionada_str = prefijo_fecha
            
            if not resultados:
                ctk.CTkLabel(container, text="No se encontraron registros para este día.", font=("Inter", 13)).pack(pady=50)
                self.btn_descargar_pdf.configure(state="disabled")
                self.lbl_status_reporte.configure(text=f"Sin resultados para {prefijo_fecha}")
            else:
                self.lbl_status_reporte.configure(text=f"Se encontraron {len(resultados)} registros para {prefijo_fecha}")
                for res in resultados:
                    # res: 0=cod, 1=prod, 2=resp, 3=fecha, 4=depto, 5=uni
                    row = ctk.CTkFrame(container, fg_color="transparent")
                    row.pack(fill="x", pady=3, padx=5)
                    
                    hora = res[3].split(' ')[1] if ' ' in res[3] else "--:--"
                    ctk.CTkLabel(row, text=f"🕒 {hora}", font=("Inter", 10, "bold"), width=60).pack(side="left")
                    ctk.CTkLabel(row, text=f"• Folio: {res[0]}", font=("Inter", 11, "bold"), text_color=CONFIG["colors"]["primary"]).pack(side="left", padx=5)
                    ctk.CTkLabel(row, text=f"| {res[1]}", font=("Inter", 11), anchor="w").pack(side="left", padx=5, fill="x", expand=True)
                    ctk.CTkLabel(row, text=f"👤 {res[2]}", font=("Inter", 10), text_color="#64748b").pack(side="right", padx=10)
                
                self.btn_descargar_pdf.configure(state="normal", command=lambda: self.exportar_pdf_historico(prefijo_fecha))
                
        except Exception as e:
            messagebox.showerror("Error de Búsqueda", f"No se pudo consultar la base de datos:\n{e}")

    def exportar_pdf_historico(self, fecha_str):
        if not self.data_reporte_actual: return
        
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("Archivos PDF", "*.pdf")],
                                             initialfile=f"Reporte_Altas_{fecha_str}.pdf")
        if not ruta: return
        
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Encabezado con estética
            pdf.set_fill_color(16, 185, 129) # Color Esmeralda
            pdf.rect(0, 0, 210, 40, 'F')
            
            pdf.set_font("Arial", 'B', 22)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 20, txt="NEXUSSYNC 3.0", ln=True, align='C')
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(190, 5, txt="REPORTE HISTÓRICO DE ALTAS", ln=True, align='C')
            pdf.ln(15)
            
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, txt=f"FECHA CONSULTADA: {fecha_str}", ln=True, align='L')
            pdf.ln(2)
            
            # Tabla Header
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(20, 10, "Hora", 1, 0, 'C', 1)
            pdf.cell(25, 10, "Folio", 1, 0, 'C', 1)
            pdf.cell(75, 10, "Descripción del Producto", 1, 0, 'C', 1)
            pdf.cell(35, 10, "Responsable", 1, 0, 'C', 1)
            pdf.cell(35, 10, "Departamento", 1, 1, 'C', 1)
            
            # Filas
            pdf.set_font("Arial", '', 9)
            for res in self.data_reporte_actual:
                hora = res[3].split(' ')[1] if ' ' in res[3] else "--:--"
                pdf.cell(20, 8, hora, 1, 0, 'C')
                pdf.cell(25, 8, str(res[0]), 1, 0, 'C')
                # Truncar producto si es muy largo para la celda
                prod_txt = str(res[1])[:40] + ("..." if len(str(res[1])) > 40 else "")
                pdf.cell(75, 8, prod_txt, 1, 0, 'L')
                pdf.cell(35, 8, str(res[2]), 1, 0, 'C')
                pdf.cell(35, 8, str(res[4]), 1, 1, 'C')
                
            pdf.ln(10)
            pdf.set_font("Arial", 'I', 8)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(190, 5, txt=f"Este reporte fue generado automáticamente por NexusSync el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='R')
            
            pdf.output(ruta)
            messagebox.showinfo("Éxito", f"Reporte PDF generado correctamente:\n{ruta}")
            
        except Exception as e:
            messagebox.showerror("Error PDF", f"No se pudo generar el archivo PDF:\n{e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()