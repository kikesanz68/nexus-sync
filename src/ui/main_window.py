# src/ui/main_window.py
import customtkinter as ctk
from tkinter import messagebox
from src.config.settings import CONFIG
from src.ui.sidebar_frame import SidebarFrame
from src.ui.history_frame import HistoryFrame
from src.utils.exporter import export_txt, export_excel
import pyperclip

class MainWindow(ctk.CTk):
    """
    Ventana principal que ensambla los componentes y se comunica con el Controller.
    """
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        # Configuración Ventana
        self.title(f"{CONFIG['app_name']} - Control Maestro de Altas")
        self.after(0, lambda: self.state('zoomed'))
        
        # UI State
        self.local_widgets = []
        self.cloud_widgets = []

        # Setup Layout
        self._setup_ui()
        
        # Iniciar datos
        self.after(500, self._init_data)

    def _setup_ui(self):
        # Sidebar
        self.sidebar = SidebarFrame(self, self.controller)
        self.sidebar.pack(side="left", fill="y")
        
        # History
        self.history = HistoryFrame(self)
        self.history.pack(side="right", fill="both", expand=True)

    def _init_data(self):
        self.controller.refresh_next_code(self._update_next_code_callback)

    def _update_next_code_callback(self, next_code):
        self.sidebar.update_next_code_ui(next_code)

    # --- EVENTOS DESDE COMPONENTES ---

    def _on_add_to_list(self):
        data = self.sidebar.get_form_data()
        
        # Llamada al controller para validar
        success, msg = self.controller.validate_and_add_local(
            data['code'], data['product'], data['unit'], 
            data['responsible'], data['dept'],
            on_status_callback=self._on_add_status
        )
        if not success: 
            messagebox.showwarning("Error", msg)
        else:
            self.sidebar.lbl_feedback.configure(text=msg, text_color="yellow")

    def _on_add_status(self, success, msg, record=None):
        if success and record:
            self.sidebar.lbl_feedback.configure(text="Producto añadido.", text_color=CONFIG["colors"]["primary"])
            self._render_local_row(record)
            self.sidebar.entry_prod.delete(0, 'end')
        else:
            messagebox.showerror("Error", msg)
            self.sidebar.lbl_feedback.configure(text="")

    def _render_local_row(self, record):
        w = self.history.add_row(
            record, is_cloud=False,
            on_edit=lambda: self._edit_local(record),
            on_delete=lambda: self._delete_local(record)
        )
        self.local_widgets.append(w)

    def _on_sync_now(self):
        # Obtener índices seleccionados
        selected = [i for i, w in enumerate(self.local_widgets) if w['var'].get()]
        if not selected:
            messagebox.showinfo("INFO", "No hay elementos seleccionados para guardar.")
            return
            
        self.sidebar.btn_nube.configure(state="disabled", text="Sincronizando...")
        self.controller.sync_to_cloud(selected, self._on_sync_finish)

    def _on_sync_finish(self, status, count, errors):
        self.sidebar.btn_nube.configure(state="normal", text="GUARDAR EN NUBE ☁️")
        if status == "finish":
            # Limpiar widgets locales procesados
            # (En el controlador ya se borraron de la lista de datos)
            self._refresh_history_view()
            if count > 0:
                messagebox.showinfo("Éxito", f"Se guardaron {count} productos en la Nube.")
            if errors:
                messagebox.showwarning("Errores", "\n".join(errors))

    def _refresh_history_view(self):
        self.history.clear_list()
        self.local_widgets.clear()
        for r in self.controller.local_items:
            self._render_local_row(r)
        self.controller.refresh_next_code(self._update_next_code_callback)

    def _on_search_change(self, term):
        # Primero filtrar localmente (esto es rápido)
        for w in self.local_widgets:
            if not term or term.lower() in w['data'][0].lower() or term.lower() in w['data'][1].lower():
                w['frame'].pack(fill="x", pady=2)
            else:
                w['frame'].pack_forget()
        
        # Luego buscar en la nube (asíncrono con debounce simulado en el controlador)
        if hasattr(self, '_search_timer'): self.after_cancel(self._search_timer)
        self._search_timer = self.after(600, lambda: self.controller.search_cloud_async(term, self._render_cloud_results))

    def _render_cloud_results(self, results):
        # Limpiar resultados anteriores de nube
        for w in self.cloud_widgets: w['frame'].destroy()
        self.cloud_widgets.clear()
        
        # Evitar mostrar si ya están en locales
        locales = [r[0] for r in self.controller.local_items]
        
        for r in results:
            if r[0] not in locales:
                w = self.history.add_row(
                    r, is_cloud=True,
                    on_edit=lambda rec=r: self._edit_cloud(rec),
                    on_delete=lambda rec=r: self._delete_cloud(rec)
                )
                self.cloud_widgets.append(w)

    # --- ACCIONES DE FILA ---
    def _delete_local(self, record):
        if record in self.controller.local_items:
            self.controller.local_items.remove(record)
            self._refresh_history_view()

    def _edit_local(self, record):
        self.sidebar.set_form_data(record)
        self._delete_local(record) # Lo quitamos para re-insertarlo al editar

    def _delete_cloud(self, record):
        if messagebox.askyesno("Eliminar", f"¿Seguro que quieres borrar {record[0]} de la nube permanentemente?"):
            self.controller.delete_cloud_record(record[0], lambda success: self._on_search_change(self.history.entry_search.get()))

    def _edit_cloud(self, record):
        # Para editar en nube, simplemente lo cargamos al form y 
        # el botón debería cambiar a "Actualizar en Nube" - (Omitido por brevedad en este MVP)
        self.sidebar.set_form_data(record)
        messagebox.showinfo("Edición", "Datos cargados. Usa 'Añadir' para intentar guardar cambios (validará duplicados).")

    # --- EXPORTACIÓN ---
    def _on_export_txt(self):
        data = [w['data'] for w in self.local_widgets if w['var'].get()]
        success, path = export_txt(data, self.sidebar.user_menu.get())
        if success: messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _on_export_excel(self):
        data = [w['data'] for w in self.local_widgets if w['var'].get()]
        success, path = export_excel(data, self.sidebar.user_menu.get())
        if success: messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")

    def _on_clear_list(self):
        if messagebox.askyesno("Limpiar", "¿Borrar toda la lista local?"):
            self.controller.local_items.clear()
            self._refresh_history_view()

    def _on_copy_all(self):
        sel = [f"• {w['data'][0]} - {w['data'][1]} ({w['data'][2]}) [{w['data'][5]}]" for w in self.local_widgets if w['var'].get()]
        if sel: pyperclip.copy("Buen día, sus códigos son:\n" + "\n".join(sel))

    def _on_copy_index(self, idx):
        sel = [w['data'][idx] for w in self.local_widgets if w['var'].get()]
        if sel: pyperclip.copy("\n".join(sel))
