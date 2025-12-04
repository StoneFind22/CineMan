import logging
from typing import Optional, Dict
from src.utils.security import SecurityUtils
from src.database.connection import DatabaseError

logger = logging.getLogger(__name__)

class UserManager:
    """Maneja todas las operaciones relacionadas con usuarios"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Autentica usuario y retorna información si es válido"""
        try:
            query = """
            SELECT id, username, password_hash, role, full_name, email, 
                   is_active, created_date, last_login
            FROM users 
            WHERE username = ? AND is_active = 1
            """
            
            result = self.db.execute_query(query, (username,))
            
            if not result:
                return None
            
            user_data = result[0]
            stored_hash = user_data[2]
            
            if SecurityUtils.verify_password(password, stored_hash):
                self.update_last_login(user_data[0])
                
                return {
                    "id": user_data[0],
                    "username": user_data[1],
                    "role": user_data[3],
                    "full_name": user_data[4],
                    "email": user_data[5],
                    "last_login": user_data[8]
                }
            
            return None
            
        except DatabaseError as e:
            logger.exception(f"Error de base de datos al autenticar a {username}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Error inesperado al autenticar a {username}: {e}")
            return None
    
    def update_last_login(self, user_id: int):
        """Actualiza la fecha de último login"""
        try:
            query = "UPDATE users SET last_login = NOW() WHERE id = ?"
            self.db.execute_command(query, (user_id,))
        except DatabaseError as e:
            logger.error(f"Error de BD al actualizar último login para user_id {user_id}: {e}")

    def create_user(self, username: str, password: str, role: str, 
                   full_name: str, email: str = None) -> bool:
        """Crea un nuevo usuario y retorna True si fue exitoso."""
        try:
            existing = self.db.execute_scalar(
                "SELECT COUNT(*) FROM users WHERE username = ?", 
                (username,)
            )
            
            if existing > 0:
                logger.warning(f"Intento de crear usuario duplicado: {username}")
                return False
            
            password_hash = SecurityUtils.hash_password(password)
            if not password_hash:
                return False
            
            query = """
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
            """
            
            new_id = self.db.execute_insert(
                query, 
                (username, password_hash, role.upper(), full_name, email)
            )
            
            return new_id is not None and new_id > 0
            
        except DatabaseError as e:
            logger.exception(f"Error de BD al crear usuario {username}: {e}")
            return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Cambia la contraseña de un usuario."""
        try:
            current_hash = self.db.execute_scalar(
                "SELECT password_hash FROM users WHERE id = ?", 
                (user_id,)
            )
            
            if not current_hash or not SecurityUtils.verify_password(old_password, current_hash):
                logger.warning(f"Intento de cambio de contraseña fallido (antigua no coincide) para user_id: {user_id}")
                return False
            
            new_hash = SecurityUtils.hash_password(new_password)
            if not new_hash:
                return False
            
            query = "UPDATE users SET password_hash = ? WHERE id = ?"
            rows_affected = self.db.execute_command(query, (new_hash, user_id))
            return rows_affected > 0
            
        except DatabaseError as e:
            logger.exception(f"Error de BD al cambiar contraseña para user_id {user_id}: {e}")
            return False
