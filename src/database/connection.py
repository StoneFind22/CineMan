import pyodbc
from typing import Optional, List, Tuple, Any
from src.config.settings import Config

class DatabaseConnection:
    """Maneja todas las conexiones y operaciones con SQL Server"""
    
    def __init__(self):
        self.connection_string = None
        self.setup_connection_string()
    
    def setup_connection_string(self):
        """Configura la cadena de conexión a SQL Server"""
        try:
            if Config.DB_TRUSTED_CONNECTION.lower() == 'yes':
                self.connection_string = (
                    f"DRIVER={Config.DB_DRIVER};"
                    f"SERVER={Config.DB_SERVER};"
                    f"DATABASE={Config.DB_NAME};"
                    "Trusted_Connection=yes;"
                    "TrustServerCertificate=yes;"
                )
            else:
                self.connection_string = (
                    f"DRIVER={Config.DB_DRIVER};"
                    f"SERVER={Config.DB_SERVER};"
                    f"DATABASE={Config.DB_NAME};"
                    f"UID={Config.DB_USER};"
                    f"PWD={Config.DB_PASSWORD};"
                    "TrustServerCertificate=yes;"
                )
        except Exception as e:
            print(f"Error configurando conexión: {e}")
    
    def get_connection(self):
        """Obtiene una conexión activa a la base de datos"""
        try:
            connection = pyodbc.connect(self.connection_string)
            return connection
        except Exception as e:
            print(f"Error conectando a BD: {e}")
            return None
    
    def test_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            conn = self.get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                conn.close()
                return True
            return False
        except Exception as e:
            print(f"Error en test de conexión: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> Optional[List[Tuple]]:
        """Ejecuta una consulta SELECT y retorna los resultados"""
        try:
            conn = self.get_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
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
