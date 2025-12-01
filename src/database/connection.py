import mysql.connector
from typing import Optional, List, Tuple, Any
from src.config.settings import Config

class DatabaseConnection:
    """Maneja todas las conexiones y operaciones con MySQL"""
    
    def __init__(self):
        self.config = {
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'database': Config.DB_NAME,
            'raise_on_warnings': True
        }
    
    def get_connection(self):
        """Obtiene una conexión activa a la base de datos"""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Exception as e:
            print(f"Error conectando a BD: {e}")
            return None
    
    def test_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            conn = self.get_connection()
            if conn:
                if conn.is_connected():
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    conn.close()
                    return True
            return False
        except Exception as e:
            print(f"Error en test de conexión: {e}")
            return False
    
    def _prepare_query(self, query: str) -> str:
        """Reemplaza placeholders de ODBC (?) por los de MySQL (%s)"""
        return query.replace('?', '%s')

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Tuple]]:
        """Ejecuta una consulta SELECT y retorna los resultados"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            query = self._prepare_query(query)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            conn.close()
            return results
            
        except Exception as e:
            print(f"Error ejecutando consulta: {e}")
            return None
    
    def execute_command(self, command: str, params: tuple = None) -> bool:
        """Ejecuta un comando INSERT, UPDATE, DELETE"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            command = self._prepare_query(command)
            
            if params:
                cursor.execute(command, params)
            else:
                cursor.execute(command)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error ejecutando comando: {e}")
            return False
    
    def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """Ejecuta una consulta que retorna un solo valor"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            query = self._prepare_query(query)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
            
        except Exception as e:
            print(f"Error ejecutando consulta scalar: {e}")
            return None

# Instancia global de conexión a BD
db = DatabaseConnection()
