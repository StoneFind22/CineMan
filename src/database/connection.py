import logging
import mysql.connector
from contextlib import contextmanager
from mysql.connector import pooling, Error as DBError
from typing import Optional, List, Tuple, Any, Dict
from src.config.settings import Config

# Configuración del logger
logger = logging.getLogger(__name__)

class DatabaseError(Exception):
    """Excepción base para errores relacionados con la base de datos."""
    pass

class DatabaseConnection:
    """Maneja todas las conexiones y operaciones con MySQL usando un pool."""
    
    def __init__(self, pool_name: str = 'default_pool', pool_size: int = 5):
        self.pool = None
        try:
            if not all([Config.DB_USER, Config.DB_PASSWORD, Config.DB_HOST, Config.DB_NAME]):
                raise DatabaseError("Faltan credenciales de base de datos en la configuración.")

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
                'connect_timeout': 10
            }
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info(f"Pool de conexiones '{pool_name}' creado exitosamente.")
        except DBError as e:
            logger.exception("Error de MySQL al crear el pool de conexiones.")
            raise DatabaseError(f"Error de MySQL al crear el pool: {e}") from e
        except Exception as e:
            logger.exception("Error inesperado al crear el pool de conexiones.")
            raise DatabaseError(f"Error inesperado al crear el pool: {e}") from e

    def close(self):
        """Cierra el pool de conexiones."""
        if self.pool:
            try:
                logger.info(f"El cierre explícito del pool '{self.pool.pool_name}' no es necesario, se manejará automáticamente.")
            except Exception as e:
                 logger.error(f"Error durante el cierre del pool de conexiones: {e}")

    def get_pool_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas básicas del pool."""
        if not self.pool:
            return {"error": "Pool no inicializado."}
        return {
            "pool_name": self.pool.pool_name,
            "pool_size": self.pool.pool_size
        }

    def get_connection(self):
        """Obtiene una conexión activa del pool. Usar con 'with'."""
        if not self.pool:
            raise DatabaseError("El pool de conexiones no ha sido inicializado.")
        try:
            return self.pool.get_connection()
        except DBError as e:
            logger.exception("No se pudo obtener una conexión del pool.")
            raise DatabaseError("No se pudo obtener una conexión del pool.") from e
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos obteniendo una del pool."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchall()
            return True
        except (DBError, DatabaseError) as e:
            logger.error(f"Fallo el test de conexión a la base de datos: {e}")
            return False
    
    def _prepare_query(self, query: str) -> str:
        """Reemplaza placeholders de ODBC (?) por los de MySQL (%s)"""
        return query.replace('?', '%s')

    def execute_query(self, query: str, params: tuple = None) -> List[Tuple]:
        """Ejecuta una consulta SELECT y retorna los resultados."""
        query = self._prepare_query(query)
        try:
            with self.get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params or ())
                    return cursor.fetchall()
        except DBError as e:
            logger.exception(f"Error al ejecutar la consulta: {query}")
            raise DatabaseError("Error al ejecutar la consulta.") from e

    @contextmanager
    def transaction(self):
        """Un context manager para ejecutar operaciones dentro de una transacción."""
        conn = self.get_connection()
        try:
            conn.start_transaction()
            logger.debug("Transacción iniciada.")
            with conn.cursor() as cursor:
                yield cursor
            conn.commit()
            logger.debug("Transacción completada con éxito (commit).")
        except DBError as e:
            logger.exception("Error durante la transacción. Se hará rollback.")
            conn.rollback()
            logger.debug("Rollback de la transacción realizado.")
            raise DatabaseError("Error durante la transacción.") from e
        finally:
            conn.close()
            logger.debug("Conexión devuelta al pool.")

    def execute_insert(self, command: str, params: tuple = None) -> int:
        """Ejecuta un comando INSERT y retorna el ID de la fila nueva."""
        command = self._prepare_query(command)
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(command, params or ())
                    conn.commit()
                    return cursor.lastrowid
        except DBError as e:
            logger.exception(f"Error al ejecutar el comando de inserción: {command}")
            raise DatabaseError("Error al ejecutar el comando de inserción.") from e

    def execute_command(self, command: str, params: tuple = None) -> int:
        """Ejecuta un comando INSERT, UPDATE, DELETE y retorna el número de filas afectadas."""
        command = self._prepare_query(command)
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(command, params or ())
                    conn.commit()
                    return cursor.rowcount
        except DBError as e:
            logger.exception(f"Error al ejecutar el comando: {command}")
            raise DatabaseError("Error al ejecutar el comando.") from e

    def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """Ejecuta una consulta que retorna un solo valor."""
        query = self._prepare_query(query)
        try:
            with self.get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    cursor.execute(query, params or ())
                    result = cursor.fetchone()
                    return list(result.values())[0] if result else None
        except DBError as e:
            logger.exception(f"Error al ejecutar la consulta escalar: {query}")
            raise DatabaseError("Error al ejecutar la consulta escalar.") from e
