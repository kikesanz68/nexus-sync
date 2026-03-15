import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import pyperclip
from datetime import datetime
import os
import psycopg2
import pandas as pd

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NexusSync 3.0 - Control Maestro de Altas")
        self.after(0, lambda: self.state('zoomed'))
        
        # Variables de control
        self.lista_productos_widgets = []
        self.fila_en_edicion = None
        self.codigo_nube_en_edicion = None

        # --- CONFIGURACIÓN DE BASE DE DATOS SUPABASE ---
        # Se elimina el URI con contraseña en el código final por seguridad y se deja preconfigurado.
        self.db_uri = "postgresql://postgres:junior1998TEAMOPAOLA1998@db.rwejnmnbuyzgrlphacah.supabase.co:5432/postgres"
        try:
            self.conn = psycopg2.connect(self.db_uri)
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
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la nube: {e}")

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
        self.entry_cod = ctk.CTkEntry(self.frame_izquierdo, placeholder_text="Solo números", width=300)
        self.entry_cod.pack(pady=5)

        self.crear_label(self.frame_izquierdo, "Descripción:")
        self.entry_prod = ctk.CTkEntry(self.frame_izquierdo, placeholder_text="Nombre del producto...", width=300)
        self.entry_prod.pack(pady=5)
        
        # Etiqueta de retroalimentación en vivo
        self.lbl_feedback = ctk.CTkLabel(self.frame_izquierdo, text="", font=("Roboto", 12, "bold"))
        self.lbl_feedback.pack(pady=(0, 5))
        
        # Eventos para consultar en vivo
        self.entry_cod.bind("<KeyRelease>", self.programar_validacion_vivo)
        self.entry_prod.bind("<KeyRelease>", self.programar_validacion_vivo)

        # Botones de Acción Izquierda
        self.btn_accion_principal = ctk.CTkButton(self.frame_izquierdo, text="AÑADIR A LISTA", fg_color="#28a745", hover_color="#218838", height=45, font=("Roboto", 14, "bold"), command=self.procesar_accion_principal)
        self.btn_accion_principal.pack(pady=20)

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

    def crear_label(self, master, texto):
        lbl = ctk.CTkLabel(master, text=texto, font=("Roboto", 12))
        lbl.pack(pady=(5, 0))

    # --- LÓGICA DE MEJORAS ---

    def programar_validacion_vivo(self, event):
        if hasattr(self, '_val_timer'):
            self.after_cancel(self._val_timer)
        self._val_timer = self.after(500, self.validar_en_vivo)
        
    def validar_en_vivo(self):
        cod = self.entry_cod.get().strip()
        prod = self.entry_prod.get().strip()
        
        if not cod and not prod:
            self.lbl_feedback.configure(text="")
            return
            
        try:
            conn = psycopg2.connect(self.db_uri, connect_timeout=2)
            cur = conn.cursor()
            query = "SELECT codigo, producto FROM historial WHERE "
            conditions = []
            params = []
            if cod:
                conditions.append("codigo = %s")
                params.append(cod)
            if prod:
                conditions.append("producto ILIKE %s")
                params.append(prod)
                
            cur.execute(query + " OR ".join(conditions) + " LIMIT 1", params)
            match = cur.fetchone()
            cur.close()
            conn.close()
            
            if match:
                self.lbl_feedback.configure(text=f"⚠️ Ya registrado: {match[0]} - {match[1]}", text_color="#ffc107")
            else:
                self.lbl_feedback.configure(text="✅ Código/Producto disponible", text_color="#28a745")
                
        except Exception:
            self.lbl_feedback.configure(text="")

    def procesar_accion_principal(self):
        if self.codigo_nube_en_edicion is not None:
            self.actualizar_en_nube()
        elif self.fila_en_edicion is None:
            self.agregar_a_lista()
        else:
            self.finalizar_edicion()

    def agregar_a_lista(self):
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
        self.entry_cod.delete(0, 'end')
        self.entry_prod.delete(0, 'end')
        self.lbl_feedback.configure(text="")

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
        """Filtrado combinado: Local en tiempo real + Búsqueda en Nube programada"""
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
        self.entry_cod.delete(0, 'end'); self.entry_cod.insert(0, d[0])
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
            self.entry_cod.delete(0, 'end'); self.entry_prod.delete(0, 'end')

    def iniciar_edicion_nube(self, fila_nube):
        self.codigo_nube_en_edicion = fila_nube[0]
        if self.fila_en_edicion:
            self.fila_en_edicion["frame"].configure(fg_color="transparent")
            self.fila_en_edicion = None
            
        self.entry_cod.delete(0, 'end'); self.entry_cod.insert(0, fila_nube[0])
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
            self.entry_cod.delete(0, 'end'); self.entry_prod.delete(0, 'end')
            
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