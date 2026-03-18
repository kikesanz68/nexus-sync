# src/utils/exporter.py
import os
import pandas as pd
from datetime import datetime
from tkinter import filedialog, messagebox

def export_txt(data_list, responsible):
    """Genera reporte en formato de texto."""
    if not data_list: return False
    
    # data_list es lista de records: [cod, prod, uni, resp, fecha, dept]
    folder = filedialog.askdirectory()
    if not folder: return False
    
    try:
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        filepath = os.path.join(folder, f"Altas_{responsible}_{timestamp_str}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"REPORTE NEXUSSYNC - CONTROL DE ALTAS\n")
            f.write(f"Generado el: {current_date_str} a las {datetime.now().strftime('%H:%M:%S')}\n")
            f.write("-" * 80 + "\n\n")
            
            for d in data_list: 
                f.write(f"FECHA: {current_date_str} | HORA: {d[4]} | RESPONSABLE: {d[3]} | DEPTO: {d[5]} | CÓD: {d[0]} | PROD: {d[1]} ({d[2]})\n")
        return True, filepath
    except Exception as e:
        return False, str(e)

def export_excel(data_list, responsible):
    """Genera reporte en Excel usando Pandas."""
    if not data_list: return False
    
    # data_list: [cod, prod, uni, resp, fecha, dept]
    folder = filedialog.askdirectory()
    if not folder: return False
    
    try:
        current_date_str = datetime.now().strftime("%d-%m-%Y")
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        df = pd.DataFrame(data_list, columns=["Código", "Producto", "Unidad", "Responsable", "Hora", "Departamento"])
        df["Fecha"] = datetime.now().strftime("%Y-%m-%d")
        
        # Reordenar para que se vea profesional
        df = df[["Fecha", "Hora", "Responsable", "Departamento", "Código", "Producto", "Unidad"]]
        
        filepath = os.path.join(folder, f"Altas_{responsible}_{timestamp_str}.xlsx")
        df.to_excel(filepath, index=False)
        return True, filepath
    except Exception as e:
        return False, str(e)
