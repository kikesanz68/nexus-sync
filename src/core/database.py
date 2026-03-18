# src/core/database.py
import psycopg2
from psycopg2 import pool
from datetime import datetime

class DatabaseManager:
    """
    Gestiona la conexión y operaciones CRUD con la base de datos de la nube (PostgreSQL).
    """
    def __init__(self, db_uri):
        self.db_uri = db_uri
        self.conn_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Prepara el pool de conexiones."""
        try:
            if not self.db_uri:
                return False
            # Pool simple para evitar bloqueos constantes
            self.conn_pool = psycopg2.pool.SimpleConnectionPool(1, 5, self.db_uri)
            self._ensure_table_exists()
            return True
        except Exception as e:
            print(f"Error al inicializar el pool: {e}")
            return False

    def _ensure_table_exists(self):
        """Crea la tabla si no existe."""
        conn = self.get_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS historial (
                        codigo TEXT PRIMARY KEY,
                        producto TEXT,
                        unidad TEXT,
                        responsable TEXT,
                        fecha TEXT,
                        departamento TEXT
                    )
                ''')
            conn.commit()
        except Exception as e:
            print(f"Error al crear tabla: {e}")
        finally:
            self.release_connection(conn)

    def get_connection(self):
        """Obtiene una conexión del pool."""
        try:
            if not self.conn_pool:
                self._initialize_pool()
            return self.conn_pool.getconn()
        except Exception:
            # Fallback simple si el pool falló
            try:
                return psycopg2.connect(self.db_uri, connect_timeout=5)
            except:
                return None

    def release_connection(self, conn):
        """Libera la conexión de vuelta al pool."""
        if self.conn_pool and conn:
            self.conn_pool.putconn(conn)
        elif conn:
            conn.close()

    def get_max_code(self):
        """Busca el mayor código numérico registrado."""
        conn = self.get_connection()
        if not conn: return None
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(CAST(codigo AS BIGINT))
                    FROM historial
                    WHERE codigo ~ '^[0-9]+$'
                """)
                resultado = cur.fetchone()
                return int(resultado[0]) if resultado and resultado[0] is not None else 66056
        except Exception as e:
            print(f"Error en get_max_code: {e}")
            return None
        finally:
            self.release_connection(conn)

    def search_cloud(self, term, limit=15):
        """Busca registros por código o producto en la nube."""
        conn = self.get_connection()
        if not conn: return []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT codigo, producto, unidad, responsable, fecha, departamento 
                    FROM historial 
                    WHERE codigo ILIKE %s OR producto ILIKE %s 
                    LIMIT %s
                """, (f"%{term}%", f"%{term}%", limit))
                return cur.fetchall()
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            return []
        finally:
            self.release_connection(conn)

    def check_duplicate(self, code, product):
        """Verifica si ya existe un código o producto (ILIKE)."""
        conn = self.get_connection()
        if not conn: return None
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT codigo, producto FROM historial WHERE codigo = %s OR producto ILIKE %s LIMIT 1", (code, product))
                return cur.fetchone()
        except Exception as e:
            print(f"Error en validación duplicados: {e}")
            return None
        finally:
            self.release_connection(conn)

    def insert_record(self, record):
        """Inserta un nuevo registro."""
        # record: [cod, prod, uni, resp, fecha, dept]
        conn = self.get_connection()
        if not conn: return False, "Sin conexión a base de datos"
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO historial (codigo, producto, unidad, responsable, fecha, departamento) VALUES (%s, %s, %s, %s, %s, %s)", 
                            (record[0], record[1], record[2], record[3], record[4], record[5]))
            conn.commit()
            return True, "Guardado exitosamente"
        except psycopg2.IntegrityError:
            conn.rollback()
            return False, "Conflict: El código ya existe"
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            self.release_connection(conn)

    def update_record(self, new_record, old_code):
        """Actualiza un registro existente."""
        conn = self.get_connection()
        if not conn: return False, "Sin conexión"
        try:
            with conn.cursor() as cur:
                # Verificar otros duplicados antes de actualizar
                cur.execute("SELECT codigo FROM historial WHERE (codigo = %s OR producto ILIKE %s) AND codigo != %s", 
                                    (new_record[0], new_record[1], old_code))
                if cur.fetchone():
                    return False, "Ya existe otro registro con ese código o nombre"
                
                cur.execute("""
                    UPDATE historial 
                    SET codigo = %s, producto = %s, unidad = %s, responsable = %s, departamento = %s
                    WHERE codigo = %s
                """, (new_record[0], new_record[1], new_record[2], new_record[3], new_record[5], old_code))
            conn.commit()
            return True, "Actualizado exitosamente"
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            self.release_connection(conn)

    def delete_record(self, code):
        """Elimina un producto de la nube."""
        conn = self.get_connection()
        if not conn: return False
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM historial WHERE codigo = %s", (code,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error al eliminar: {e}")
            return False
        finally:
            self.release_connection(conn)
