# main.py
import sys
import os

# Asegurar que el directorio actual esté en el PATH para importaciones relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import load_environment
from src.core.database import DatabaseManager
from src.core.controller import AppController
from src.ui.main_window import MainWindow

def main():
    # 1. Cargar Entorno
    db_uri = load_environment()
    if not db_uri:
        print("Error: No se encontró SUPABASE_DB_URI en el archivo .env")
        sys.exit(1)

    # 2. Inicializar Modelo
    model = DatabaseManager(db_uri)

    # 3. Inicializar Controlador
    controller = AppController(model)

    # 4. Inicializar Vista Principal
    app = MainWindow(controller)
    
    # 5. Ejecutar Aplicación
    app.mainloop()

if __name__ == "__main__":
    main()
