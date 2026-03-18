# src/core/controller.py
from datetime import datetime
from threading import Thread

class AppController:
    """
    Controlador central (Brains) que gestiona la lógica de negocio, validaciones y sincronización.
    """
    def __init__(self, db_manager):
        self.db = db_manager
        self.local_items = []  # Lista de registros temporales (aún no en la nube)
        
        # Estado de edición
        self.editing_local_item = None
        self.editing_cloud_code = None
        
        # Cache del siguiente código
        self.next_code = None

    def refresh_next_code(self, on_finish_callback=None):
        """Busca el código máximo en la nube de forma asíncrona."""
        def task():
            max_nube = self.db.get_max_code()
            max_nube = max_nube if max_nube is not None else 66056
            
            # También considerar el máximo local
            codigos_locales = [int(i[0]) for i in self.local_items if i[0].isdigit()]
            max_local = max(codigos_locales) if codigos_locales else 0
            
            self.next_code = max(max_nube, max_local) + 1
            
            if on_finish_callback:
                on_finish_callback(self.next_code)
        
        Thread(target=task, daemon=True).start()

    def validate_and_add_local(self, code, product, unit, responsible, dept, on_status_callback=None):
        """Valida un nuevo registro y lo añade a la lista local."""
        if not code.isdigit() or not product:
            return False, "Datos incompletos o código inválido (deben ser solo números)."
            
        # 1. Duplicado local
        for item in self.local_items:
            if item[0] == code: return False, f"El código {code} ya está en la lista temporal."
            if item[1].lower() == product.lower(): return False, f"El producto '{product}' ya existe localmente."

        # 2. Duplicado en la Nube (Asíncrono)
        def check_cloud():
            existente = self.db.check_duplicate(code, product)
            if existente:
                if on_status_callback: 
                    on_status_callback(False, f"Este producto ya fue dado de alta en la Nube.\nCódigo: {existente[0]}\nProducto: {existente[1]}")
                return
            
            # Si cruza ambos, añadirlo
            new_record = [code, product, unit, responsible, datetime.now().strftime("%H:%M"), dept]
            self.local_items.append(new_record)
            if on_status_callback:
                on_status_callback(True, "Añadido exitosamente.", new_record)

        Thread(target=check_cloud, daemon=True).start()
        return True, "Validando en la nube..." # Mensaje temporal

    def sync_to_cloud(self, selected_indices, on_progress_callback=None):
        """Sincroniza los elementos seleccionados de la lista local a la nube."""
        def task():
            items_to_sync = [self.local_items[i] for i in selected_indices if i < len(self.local_items)]
            if not items_to_sync: 
                if on_progress_callback: on_progress_callback("finish", 0, [], "No hay elementos para sincronizar.")
                return

            guardados = 0
            errors = []
            synced_items = []

            for item in items_to_sync:
                success, msg = self.db.insert_record(item)
                if success:
                    guardados += 1
                    synced_items.append(item)
                else:
                    errors.append(f"{item[0]}: {msg}")

            # Limpiar de la lista local lo que sí se guardó
            for item in synced_items:
                if item in self.local_items:
                    self.local_items.remove(item)

            if on_progress_callback:
                self.refresh_next_code() # Recalcular siguiente código después de sync
                on_progress_callback("finish", guardados, errors)

        Thread(target=task, daemon=True).start()

    def search_cloud_async(self, term, on_finish_callback):
        """Realiza búsqueda en la nube sin trabar la interfaz."""
        if not term: 
            on_finish_callback([])
            return
            
        def task():
            results = self.db.search_cloud(term)
            on_finish_callback(results)
        
        Thread(target=task, daemon=True).start()
        
    def delete_cloud_record(self, code, on_finish_callback):
        """Elimina un producto directamente desde la nube."""
        def task():
            success = self.db.delete_record(code)
            if on_finish_callback:
                on_finish_callback(success)
        Thread(target=task, daemon=True).start()
        
    def update_cloud_record(self, new_record, old_code, on_finish_callback):
        """Actualiza un producto directamente desde la nube."""
        def task():
            success, msg = self.db.update_record(new_record, old_code)
            if on_finish_callback:
                on_finish_callback(success, msg)
        Thread(target=task, daemon=True).start()
