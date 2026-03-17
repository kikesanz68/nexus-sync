import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import pyperclip
from datetime import datetime
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

# Cargamos las variables secretas (contraseñas/tokens)
load_dotenv()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    """
    Clase principal de la aplicación.
    Contiene toda la estructura visual y la lógica de negocio para gestionar el historial.
    """
    def __init__(self):
        super().__init__()

        self.title("NexusSync 3.0 - Control Maestro de Altas")
        self.after(0, lambda: self.state('zoomed'))
        
        # Variables de control
        self.lista_productos_widgets = []
        self.fila_en_edicion = None
        self.codigo_nube_en_edicion = None
        self.codigo_siguiente = None  # Código que se va a dar de alta automáticamente

        # --- CONFIGURACIÓN DE BASE DE DATOS SUPABASE ---
        # Aseguramos que cargamos el .env incluso si está al lado del ejecutable
        import sys
        if getattr(sys, 'frozen', False):
            # Si es un EXE, buscamos el .env en la misma carpeta que el EXE
            application_path = os.path.dirname(sys.executable)
            load_dotenv(os.path.join(application_path, '.env'))
        else:
            load_dotenv()

        self.db_uri = os.getenv("SUPABASE_DB_URI")
        
        if not self.db_uri:
            # No podemos destruir aquí inmediatamente porque el mainloop no ha empezado
            # y CustomTkinter puede colapsar. Usamos un flag o lo programamos para después.
            self.after(100, lambda: self._show_error_and_exit("No se encontró el archivo .env o la variable SUPABASE_DB_URI."))
            return
            
        try:
            self.conn = psycopg2.connect(self.db_uri, connect_timeout=5)
            self.cursor = self.conn.cursor()
            
            # Crear la tabla si no existe
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
            self.conn.commit()
        except Exception as e:
            self.after(100, lambda ex=e: messagebox.showerror("Error de Conexión", f"No se pudo conectar a la nube: {ex}"))

        # --- COLUMNA IZQUIERDA (FORMULARIO) ---
        self.frame_izquierdo = ctk.CTkFrame(self, corner_radius=0)
        self.frame_izquierdo.place(relx=0, rely=0, relwidth=0.4, relheight=1)

        self.label_titulo = ctk.CTkLabel(self.frame_izquierdo, text="REGISTRO DE PRODUCTO", font=("Roboto", 28, "bold"))
        self.label_titulo.pack(pady=(40, 20))

        # Inputs con etiquetas
        self.crear_label(self.frame_izquierdo, "Responsable:")
        self.user_menu = ctk.CTkOptionMenu(self.frame_izquierdo, values=["ENRIQUE", "MISSAEL", "GERMAN"], width=300)
        self.user_menu.pack(pady=5)

        self.crear_label(self.frame_izquierdo, "Departamento:")
        self.dept_menu = ctk.CTkOptionMenu(self.frame_izquierdo, values=["MANTENIMIENTO", "RECURSOS HUMANOS", "COMPRAS", "SISTEMAS"], width=300)
        self.dept_menu.set("MANTENIMIENTO")
        self.dept_menu.pack(pady=5)

        self.crear_label(self.frame_izquierdo, "Unidad:")
        self.unit_menu = ctk.CTkOptionMenu(self.frame_izquierdo, values=["PIEZA", "BOLSA", "KILOGRAMO", "METRO", "LITRO", "GALON", "TONELADA", "PAQUETE"], width=300)
        self.unit_menu.pack(pady=5)

        self.crear_label(self.frame_izquierdo, "Código:")
        self.entry_cod = ctk.CTkEntry(
            self.frame_izquierdo,
            placeholder_text="Auto-generado",
            width=300,
            state="disabled",          # Bloqueado: el sistema lo rellena
            text_color="#00ff88",
            fg_color="#1a2b1a",
            border_color="#28a745"
        )
        self.entry_cod.pack(pady=5)

        self.crear_label(self.frame_izquierdo, "Descripción:")
        self.entry_prod = ctk.CTkEntry(self.frame_izquierdo, placeholder_text="Nombre del producto...", width=300)
        self.entry_prod.pack(pady=5)
        
        # Menú contextual de Copiar/Pegar para el campo Descripción
        self.menu_contextual_prod = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white",
                                            activebackground="#28a745", activeforeground="white")
        self.menu_contextual_prod.add_command(label="📋  Copiar", command=self.copiar_descripcion)
        self.menu_contextual_prod.add_command(label="📎  Pegar",  command=self.pegar_descripcion)
        self.entry_prod.bind("<Button-3>", self.mostrar_menu_contextual_prod)  # Click derecho
        
        # Label de feedback (oculto — ya no se valida descripción en vivo)
        self.lbl_feedback = ctk.CTkLabel(self.frame_izquierdo, text="", font=("Roboto", 12, "bold"))
        self.lbl_feedback.pack(pady=(0, 5))
        # Sin bind KeyRelease en entry_prod: el campo es solo de captura, sin buscar en BD

        # Botones de Acción Izquierda
        self.btn_accion_principal = ctk.CTkButton(self.frame_izquierdo, text="AÑADIR A LISTA", fg_color="#28a745", hover_color="#218838", height=45, font=("Roboto", 14, "bold"), command=self.procesar_accion_principal)
        self.btn_accion_principal.pack(pady=(20, 8))

        # --- PANEL DE CÓDIGO SIGUIENTE ---
        self.frame_codigo_sig = ctk.CTkFrame(self.frame_izquierdo, fg_color="#1a2b1a", border_width=2, border_color="#28a745", corner_radius=12)
        self.frame_codigo_sig.pack(pady=(0, 10), padx=30, fill="x")

        ctk.CTkLabel(self.frame_codigo_sig, text="📋 CÓDIGO SIGUIENTE A DAR DE ALTA",
                     font=("Roboto", 10, "bold"), text_color="#7dcf7d").pack(pady=(8, 0))

        self.lbl_codigo_sig = ctk.CTkLabel(self.frame_codigo_sig, text="Cargando...",
                                           font=("Roboto", 32, "bold"), text_color="#00ff88")
        self.lbl_codigo_sig.pack(pady=(2, 4))

        self.lbl_aviso_sig = ctk.CTkLabel(self.frame_codigo_sig, text="",
                                          font=("Roboto", 10), text_color="#aaaaaa")
        self.lbl_aviso_sig.pack(pady=(0, 8))

        self.btn_nube = ctk.CTkButton(self.frame_izquierdo, text="GUARDAR EN NUBE ☁️", fg_color="#0066cc", hover_color="#0052a3", height=45, font=("Roboto", 14, "bold"), command=self.guardar_en_nube)
        self.btn_nube.pack(pady=(0, 20))

        # Contenedor para botones de guardado local
        self.frame_guardado_local = ctk.CTkFrame(self.frame_izquierdo, fg_color="transparent")
        self.frame_guardado_local.pack(pady=10)

        self.btn_save = ctk.CTkButton(self.frame_guardado_local, text="REPORTE (.txt) 📄", fg_color="#dc3545", width=140, command=self.guardar_archivo)
        self.btn_save.grid(row=0, column=0, padx=5)

        self.btn_excel = ctk.CTkButton(self.frame_guardado_local, text="REPORTE (.xlsx) 📊", fg_color="#20c997", width=140, command=self.exportar_excel)
        self.btn_excel.grid(row=0, column=1, padx=5)

        self.btn_reset = ctk.CTkButton(self.frame_izquierdo, text="LIMPIAR TODO EL HISTORIAL 🧹", fg_color="#6c757d", command=self.limpiar_historial_completo)
        self.btn_reset.pack(pady=10)

        # --- COLUMNA DERECHA (HISTORIAL Y BUSCADOR) ---
        self.frame_derecho = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.frame_derecho.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)

        # Buscador en tiempo real
        self.search_frame = ctk.CTkFrame(self.frame_derecho, fg_color="transparent")
        self.search_frame.pack(pady=(20, 0), padx=20, fill="x")
        
        self.entry_search = ctk.CTkEntry(self.search_frame, placeholder_text="Escriba código o descripción...", height=35)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(20, 5))
        self.entry_search.bind("<KeyRelease>", self.filtrar_busqueda)

        self.btn_buscar = ctk.CTkButton(self.search_frame, text="🔍 Buscar", width=80, height=35, fg_color="#4b5563", hover_color="#374151", command=lambda: self.filtrar_busqueda(None))
        self.btn_buscar.pack(side="right", padx=(0, 20))

        # Menú contextual de Copiar y Pegar para el buscador
        self.menu_contextual = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", activebackground="#0066cc", activeforeground="white")
        self.menu_contextual.add_command(label="Copiar", command=self.copiar_buscador)
        self.menu_contextual.add_command(label="Pegar", command=self.pegar_buscador)
        self.entry_search.bind("<Button-3>", self.mostrar_menu_contextual) # Click derecho

        self.scroll_frame = ctk.CTkScrollableFrame(self.frame_derecho, label_text="HISTORIAL DE ACTIVIDAD")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Panel de botones de copiado
        self.button_grid = ctk.CTkFrame(self.frame_derecho, fg_color="transparent")
        self.button_grid.pack(pady=20, padx=20, fill="x")

        ctk.CTkButton(self.button_grid, text="Copiar para Envío 📋", fg_color="#007bff", command=self.copiar_seleccionados).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="Solo Códigos 🔢", fg_color="#fd7e14", command=lambda: self.copiar_especifico(0)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="Solo Productos 📦", fg_color="#17a2b8", command=lambda: self.copiar_especifico(1)).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="Solo Unidades 📏", fg_color="#6f42c1", command=lambda: self.copiar_especifico(2)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.button_grid.grid_columnconfigure((0, 1), weight=1)

        # Evento de cierre
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Calcular y mostrar el código siguiente al iniciar
        self.after(300, self.actualizar_codigo_siguiente)

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
        # El panel siempre muestra el que viene DESPUÉS del que está en el campo
        try:
            siguiente_display = int(valor) + 1
            self.lbl_codigo_sig.configure(text=str(siguiente_display), text_color="#00ff88")
            self.lbl_aviso_sig.configure(text=f"(En campo: {valor})", text_color="#888888")
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
                    self.lbl_codigo_sig.configure(text=str(val_actual + 1), text_color="#00ff88")
                    self.lbl_aviso_sig.configure(text=f"(En campo: {val_actual})", text_color="#888888")
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

        self.crear_fila_historial(cod, prod, self.unit_menu.get(), self.user_menu.get(), datetime.now().strftime("%H:%M"), self.dept_menu.get())
        self.entry_prod.delete(0, 'end')
        self.lbl_feedback.configure(text="")
        # El código NO cambia aquí — solo cambia cuando se guarda en la nube

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
        self.lbl_codigo_sig.configure(text=str(self.codigo_siguiente), text_color="#00ff88")
        ultimo_referencia = maximo_total
        self.lbl_aviso_sig.configure(
            text=f"(Último registrado/pendiente: {ultimo_referencia})",
            text_color="#888888"
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
                    
                    lbl = ctk.CTkLabel(row, text=f"☁️ NUBE   |   [{fila[4]}] [{fila[5]}]   {cod}   |   {fila[1]} ({fila[2]})", 
                                       font=("Roboto", 12, "bold"), text_color="#a8d0e6")
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
        self.unit_menu.set(d[2]); self.user_menu.set(d[3]); self.dept_menu.set(d[5])
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
            d[0], d[1], d[2], d[3], d[5] = cod, prod, self.unit_menu.get(), self.user_menu.get(), self.dept_menu.get()

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
        self.unit_menu.set(fila_nube[2]); self.user_menu.set(fila_nube[3]); self.dept_menu.set(fila_nube[5])
        
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
            """, (cod, prod, self.unit_menu.get(), self.user_menu.get(), self.dept_menu.get(), self.codigo_nube_en_edicion))
            
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
        
        ruta = os.path.join(carpeta, f"Altas_{self.user_menu.get()}_{fecha_hora_re}.txt")
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
        Toma todos los elementos con 'palomita' de la lista, les asigna las columnas (Hora, Responsable, etc.)
        y las convierte en un archivo de Microsoft Excel usando la librería openpyxl/pandas.
        """
        elementos_a_guardar = [i for i in self.lista_productos_widgets if i['var'].get()]
        if not elementos_a_guardar:
            messagebox.showinfo("Sin selección", "No hay elementos en la lista para exportar.")
            return
            
        carpeta = filedialog.askdirectory()
        if not carpeta: return
        
        datos = [i['datos'] for i in elementos_a_guardar]
        
        # Convertimos los datos a un formato que pandas entienda, asignando nombres de columnas
        df = pd.DataFrame(datos, columns=['Código', 'Producto', 'Unidad', 'Responsable', 'Hora', 'Departamento'])
        
        # Reordenamos columnas para una mejor presentación en Excel
        df = df[['Hora', 'Responsable', 'Departamento', 'Código', 'Producto', 'Unidad']]
        
        ruta = os.path.join(carpeta, f"Reporte_Altas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        
        try:
            df.to_excel(ruta, index=False, engine='openpyxl')
            
            for item in elementos_a_guardar:
                self.eliminar_producto(item)
                
            messagebox.showinfo("Éxito", f"Reporte Excel guardado correctamente en:\n{ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo Excel.\nDetalle: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()