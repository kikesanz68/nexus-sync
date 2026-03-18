# src/ui/sidebar_frame.py
import customtkinter as ctk
import tkinter as tk
from src.config.settings import CONFIG

class SidebarFrame(ctk.CTkFrame):
    """
    Componente de la barra lateral que contiene el formulario de captura.
    """
    def __init__(self, master, controller, **kwargs):
        super().__init__(master, corner_radius=0, width=400, **kwargs)
        self.controller = controller
        self.pack_propagate(False)
        self._setup_ui()

    def _setup_ui(self):
        # Header y Título
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(pady=(20, 10), padx=20, fill="x")
        
        self.label_titulo = ctk.CTkLabel(self, text="NEXUSSYNC 3.0", font=("Inter", 28, "bold"), text_color=CONFIG["colors"]["primary"])
        self.label_titulo.pack(pady=(10, 20))

        # Contenedor del Formulario
        self.form_container = ctk.CTkFrame(self, fg_color="transparent")
        self.form_container.pack(pady=10, padx=40, fill="x")

        # Inputs
        self._crear_label("Responsable:")
        self.user_menu = ctk.CTkOptionMenu(self.form_container, values=CONFIG["options"]["responsables"], width=300, fg_color=CONFIG["colors"]["bg_input"], button_color=CONFIG["colors"]["btn_input"])
        self.user_menu.pack(pady=5)

        self._crear_label("Departamento:")
        self.dept_menu = ctk.CTkOptionMenu(self.form_container, values=CONFIG["options"]["departamentos"], width=300, fg_color=CONFIG["colors"]["bg_input"], button_color=CONFIG["colors"]["btn_input"])
        self.dept_menu.set("MANTENIMIENTO")
        self.dept_menu.pack(pady=5)

        self._crear_label("Unidad:")
        self.unit_menu = ctk.CTkOptionMenu(self.form_container, values=CONFIG["options"]["unidades"], width=300, fg_color=CONFIG["colors"]["bg_input"], button_color=CONFIG["colors"]["btn_input"])
        self.unit_menu.pack(pady=5)

        self._crear_label("Código:")
        self.entry_cod = ctk.CTkEntry(self.form_container, placeholder_text="Auto-generado", width=300, state="disabled", text_color=CONFIG["colors"]["primary"], fg_color=("white", "#1e293b"), border_color=CONFIG["colors"]["primary"])
        self.entry_cod.pack(pady=5)

        self._crear_label("Descripción:")
        self.entry_prod = ctk.CTkEntry(self.form_container, placeholder_text="Nombre del producto...", width=300)
        self.entry_prod.pack(pady=5)
        
        # Feedback visual ligero
        self.lbl_feedback = ctk.CTkLabel(self, text="", font=("Roboto", 12, "bold"))
        self.lbl_feedback.pack(pady=(0, 5))

        # Botones de Acción
        self.btn_accion_principal = ctk.CTkButton(self, text="AÑADIR A LISTA", fg_color=CONFIG["colors"]["primary"], hover_color="#059669", height=45, font=("Inter", 14, "bold"), command=self._on_add_click)
        self.btn_accion_principal.pack(pady=(20, 10), padx=40, fill="x")

        self.btn_nube = ctk.CTkButton(self, text="GUARDAR EN NUBE ☁️", fg_color=CONFIG["colors"]["secondary"], hover_color="#2563eb", height=45, font=("Inter", 14, "bold"), command=self._on_sync_click)
        self.btn_nube.pack(pady=(0, 10), padx=40, fill="x")

        # Reportes y Limpieza
        self.frame_extra = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_extra.pack(pady=10, padx=40, fill="x")
        
        self.btn_save = ctk.CTkButton(self.frame_extra, text="TXT 📄", fg_color=CONFIG["colors"]["danger"], hover_color="#dc2626", width=80, command=self._on_export_txt)
        self.btn_save.pack(side="left", padx=5)

        self.btn_excel = ctk.CTkButton(self.frame_extra, text="Excel 📊", fg_color="#10b981", hover_color="#059669", width=80, command=self._on_export_excel)
        self.btn_excel.pack(side="left", padx=5)

        self.btn_reset = ctk.CTkButton(self.frame_extra, text="Limpiar 🧹", fg_color="#6b7280", hover_color="#4b5563", width=80, command=self._on_clear_click)
        self.btn_reset.pack(side="left", padx=5)

        # Panel de Código Siguiente
        self.frame_codigo_sig = ctk.CTkFrame(self, fg_color=("#f1f5f9", "#1e293b"), border_width=1, border_color=CONFIG["colors"]["primary"], corner_radius=15)
        self.frame_codigo_sig.pack(side="bottom", pady=30, padx=30, fill="x")

        ctk.CTkLabel(self.frame_codigo_sig, text="PRÓXIMO CÓDIGO", font=("Inter", 11, "bold"), text_color=CONFIG["colors"]["primary"]).pack(pady=(12, 0))
        self.lbl_codigo_sig = ctk.CTkLabel(self.frame_codigo_sig, text="---", font=("Inter", 38, "bold"), text_color=CONFIG["colors"]["primary"])
        self.lbl_codigo_sig.pack(pady=(2, 2))
        self.lbl_aviso_sig = ctk.CTkLabel(self.frame_codigo_sig, text="", font=("Inter", 10), text_color="#64748b")
        self.lbl_aviso_sig.pack(pady=(0, 12))

    def _crear_label(self, texto):
        lbl = ctk.CTkLabel(self.form_container, text=texto, font=("Roboto", 12))
        lbl.pack(pady=(5, 0))

    def update_next_code_ui(self, next_code, current_in_field=None):
        """Actualiza visualmente el código siguiente."""
        self.lbl_codigo_sig.configure(text=str(next_code))
        if current_in_field:
            self.lbl_aviso_sig.configure(text=f"(En campo: {current_in_field})")
        else:
            self.entry_cod.configure(state="normal")
            self.entry_cod.delete(0, 'end')
            self.entry_cod.insert(0, str(next_code))
            self.entry_cod.configure(state="disabled")
            self.lbl_aviso_sig.configure(text=f"(Código actual asignado)")

    # Eventos (Callback a la ventana principal o controlador)
    def _on_add_click(self):
        # La lógica de validación la hará el Controller via MainWindow
        self.master._on_add_to_list()

    def _on_sync_click(self):
        self.master._on_sync_now()

    def _on_export_txt(self):
        self.master._on_export_txt()

    def _on_export_excel(self):
        self.master._on_export_excel()

    def _on_clear_click(self):
        self.master._on_clear_list()

    def get_form_data(self):
        return {
            "code": self.entry_cod.get().strip(),
            "product": self.entry_prod.get().strip(),
            "unit": self.unit_menu.get(),
            "responsible": self.user_menu.get(),
            "dept": self.dept_menu.get()
        }
        
    def set_form_data(self, data):
        # data: [cod, prod, uni, resp, fecha, dept]
        self.entry_cod.configure(state="normal")
        self.entry_cod.delete(0, 'end'); self.entry_cod.insert(0, data[0])
        self.entry_cod.configure(state="disabled")
        self.entry_prod.delete(0, 'end'); self.entry_prod.insert(0, data[1])
        self.unit_menu.set(data[2]); self.user_menu.set(data[3]); self.dept_menu.set(data[5])
