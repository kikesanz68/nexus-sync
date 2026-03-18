# src/ui/history_frame.py
import customtkinter as ctk
import tkinter as tk
from src.config.settings import CONFIG

class HistoryFrame(ctk.CTkFrame):
    """
    Componente derecho: Buscador e Historial con scroll.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, corner_radius=0, fg_color="transparent", **kwargs)
        self._setup_ui()

    def _setup_ui(self):
        # Buscador superior
        self.search_container = ctk.CTkFrame(self, fg_color="transparent")
        self.search_container.pack(pady=(30, 10), padx=30, fill="x")
        
        self.entry_search = ctk.CTkEntry(self.search_container, placeholder_text="Buscar por código o producto...", height=45, font=("Inter", 13), corner_radius=10)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_search.bind("<KeyRelease>", self._on_search_key)

        self.btn_buscar = ctk.CTkButton(self.search_container, text="🔍 Buscar", width=100, height=45, fg_color="#64748b", hover_color="#475569", font=("Inter", 12, "bold"), corner_radius=10, command=self._on_search_manual)
        self.btn_buscar.pack(side="right")

        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text="HISTORIAL DE ACTIVIDAD")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Panel de botones de copiado rápido
        self.button_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.button_grid.pack(pady=20, padx=30, fill="x")

        ctk.CTkButton(self.button_grid, text="COPIAR PARA ENVÍO 📋", fg_color=CONFIG["colors"]["secondary"], hover_color="#2563eb", height=40, font=("Inter", 12, "bold"), command=lambda: self.master._on_copy_all()).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="SOLO CÓDIGOS 🔢", fg_color="#f59e0b", hover_color="#d97706", height=40, font=("Inter", 12, "bold"), command=lambda: self.master._on_copy_index(0)).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="SOLO PRODUCTOS 📦", fg_color="#06b6d4", hover_color="#0891b2", height=40, font=("Inter", 12, "bold"), command=lambda: self.master._on_copy_index(1)).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ctk.CTkButton(self.button_grid, text="SOLO UNIDADES 📏", fg_color="#8b5cf6", hover_color="#7c3aed", height=40, font=("Inter", 12, "bold"), command=lambda: self.master._on_copy_index(2)).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        self.button_grid.grid_columnconfigure((0, 1), weight=1)

    def _on_search_key(self, event):
        self.master._on_search_change(self.entry_search.get())

    def _on_search_manual(self):
        self.master._on_search_change(self.entry_search.get())

    def clear_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

    def add_row(self, data, is_cloud=False, on_edit=None, on_delete=None):
        """Añade una fila visual al scrollable frame."""
        # data: [cod, prod, uni, resp, fecha, dept]
        bg = CONFIG["colors"]["nube_bg"] if is_cloud else "transparent"
        border = CONFIG["colors"]["nube_border"] if is_cloud else "transparent"
        
        row = ctk.CTkFrame(self.scroll_frame, fg_color=bg, border_width=1 if is_cloud else 0, border_color=border)
        row.pack(fill="x", pady=2)
        
        text = f"[{data[4]}] [{data[5]}] {data[0]} | {data[1]}"
        if is_cloud: text = f"☁️ NUBE | " + text
        
        check_var = ctk.BooleanVar(value=True)
        if is_cloud:
            lbl = ctk.CTkLabel(row, text=text, font=("Roboto", 12, "bold"), text_color=CONFIG["colors"]["nube"])
            lbl.pack(side="left", padx=10, pady=5, expand=True, fill="x", anchor="w")
        else:
            chk = ctk.CTkCheckBox(row, text=text, variable=check_var, font=("Roboto", 12))
            chk.pack(side="left", padx=5, expand=True, fill="x")

        # Botones de Acción
        btn_edit = ctk.CTkButton(row, text="✏️", width=30, fg_color="#ffc107", text_color="black", command=on_edit)
        btn_edit.pack(side="right", padx=2)
        
        btn_del = ctk.CTkButton(row, text="🗑️", width=30, fg_color="#dc3545", command=on_delete)
        btn_del.pack(side="right", padx=2)
        
        return {"frame": row, "var": check_var, "data": data}
