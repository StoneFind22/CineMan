import logging
import mysql.connector
from contextlib import contextmanager
from mysql.connector import pooling, Error as DBError, InterfaceError
from typing import Optional, List, Any, Dict

from src.config.settings import Config

logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos, encapsulando detalles."""
    pass

class DatabaseConnection:
    """
    Clase Singleton para gestionar la conexión a la base de datos mediante un pool.
    Centraliza toda la lógica de conexión, ejecución y transacciones para robustez.
    """
    _instance = None
    
    # Se usa Singleton para asegurar una única instancia del pool de conexiones en toda la app.
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self, pool_name: str = 'default_pool', pool_size: int = 5):
        # El constructor solo se ejecuta la primera vez para inicializar el pool.
        if hasattr(self, 'pool') and self.pool:
            return
            
        try:
            if not all([Config.DB_USER, Config.DB_PASSWORD, Config.DB_HOST, Config.DB_NAME]):
                raise DatabaseError("Credenciales de base de datos no configuradas.")

            # Configuración robusta del pool.
            pool_config = {
                'pool_name': pool_name,
                'pool_size': pool_size,
                'user': Config.DB_USER,
                'password': Config.DB_PASSWORD,
                'host': Config.DB_HOST,
                'port': Config.DB_PORT,
                'database': Config.DB_NAME,
                'raise_on_warnings': True,
                'charset': 'utf8mb4',
                'connect_timeout': 5, # Timeout de conexión reducido.
                'pool_reset_session': True, # Resetea la sesión para evitar estado residual.
            }
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info(f"Pool de conexiones '{pool_name}' creado exitosamente.")
        except DBError as e:
            logger.exception("Error de MySQL al crear el pool de conexiones.")
            raise DatabaseError(f"Error de MySQL en la creación del pool: {e}") from e
        except Exception as e:
            logger.exception("Error inesperado al crear el pool de conexiones.")
            raise DatabaseError(f"Error inesperado en la creación del pool: {e}") from e

    def close_pool(self):
        """Cierra el pool de conexiones al terminar la aplicación."""
        logger.info("Cierre de la aplicación. El pool de conexiones se autogestionará.")

    def get_connection(self):
        """Obtiene una conexión del pool, verificando que esté activa."""
        if not self.pool:
            raise DatabaseError("Pool de conexiones no inicializado.")
        try:
            conn = self.pool.get_connection()
            # Asegura que la conexión esté viva para evitar errores con conexiones inactivas.
            conn.ping(reconnect=True, attempts=3, delay=1)
            return conn
        except DBError as e:
            logger.exception("Fallo al obtener una conexión válida del pool.")
            raise DatabaseError(f"Fallo al obtener conexión del pool: {e}") from e

    def _prepare_query(self, query: str) -> str:
        """Reemplaza placeholders de estilo ODBC '?' por el estilo de MySQL '%s'."""
        return query.replace('?', '%s')

    def _execute(self, query: str, params: Optional[tuple] = None, commit: bool = False, fetch: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """Método de ejecución genérico y centralizado para mantener el código DRY."""
        conn = None
        query = self._prepare_query(query)
        # Añade cláusula LIMIT a las consultas de selección si se especifica.
        if limit and fetch:
            query = f"{query} LIMIT {int(limit)}"
            
        try:
            conn = self.get_connection()
            # Usa cursores de diccionario para un acceso a datos más legible y seguro.
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(query, params or ())
                if commit:
                    conn.commit()
                    return cursor.lastrowid or cursor.rowcount
                if fetch == 'one':
                    return cursor.fetchone()
                if fetch == 'all':
                    return cursor.fetchall()
        except (DBError, InterfaceError) as e:
            logger.error(f"Error de BD durante ejecución. Query: {query[:100]}...")
            raise DatabaseError(f"Comando de base de datos falló: {e}") from e
        finally:
            # Devuelve la conexión al pool en un bloque finally para garantizar la liberación.
            if conn and conn.is_connected():
                conn.close() 

    def execute_query(self, query: str, params: Optional[tuple] = None, limit: int = None) -> List[Dict]:
        """Ejecuta una consulta SELECT y retorna todas las filas como una lista de diccionarios."""
        return self._execute(query, params, fetch='all', limit=limit)

    @contextmanager
    def transaction(self):
        """Provee un contexto transaccional seguro con commit y rollback automáticos."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            logger.debug("Transacción iniciada.")
            yield cursor
            conn.commit()
            logger.debug("Transacción completada (commit).")
        except (DBError, InterfaceError) as e:
            if conn:
                conn.rollback()
                logger.exception("Error en transacción, se revirtió (rollback).")
            raise DatabaseError("La transacción falló y fue revertida.") from e
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
                logger.debug("Conexión de transacción devuelta al pool.")
    
    def execute_insert(self, command: str, params: Optional[tuple] = None) -> int:
        """Ejecuta un INSERT y retorna el ID de la nueva fila."""
        return self._execute(command, params, commit=True)

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Ejecuta un UPDATE/DELETE y retorna el número de filas afectadas."""
        return self._execute(command, params, commit=True)

    def execute_scalar(self, query: str, params: Optional[tuple] = None) -> Any:
        """Ejecuta una consulta y retorna el primer valor de la primera fila."""
        result = self._execute(query, params, fetch='one')
        return list(result.values())[0] if result else None
