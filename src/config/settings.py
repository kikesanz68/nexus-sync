# src/config/settings.py
import os
from dotenv import load_dotenv

# --- CONFIGURACIÓN GLOBAL ---
CONFIG = {
    "app_name": "NexusSync 4.0",
    "version": "4.0",
    "colors": {
        "primary": "#10b981",    # Verde esmeralda
        "secondary": "#3b82f6",  # Azul brillante
        "danger": "#ef4444",     # Rojo vibrante
        "warning": "#f59e0b",
        "bg_input": "#334155",
        "btn_input": "#1e293b",
        "nube": "#a8d0e6",
        "nube_bg": "#1a2b3c",
        "nube_border": "#0066cc"
    },
    "options": {
        "responsables": ["ENRIQUE", "MISSAEL", "GERMAN"],
        "departamentos": ["MANTENIMIENTO", "RECURSOS HUMANOS", "COMPRAS", "SISTEMAS"],
        "unidades": ["PIEZA", "BOLSA", "KILOGRAMO", "METRO", "LITRO", "GALON", "TONELADA", "PAQUETE"]
    }
}

def load_environment():
    """Carga las variables de entorno manejando el caso de ejecutable congelado."""
    import sys
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        load_dotenv(os.path.join(application_path, '.env'))
    else:
        load_dotenv()
    return os.getenv("SUPABASE_DB_URI")
