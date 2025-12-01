from typing import Optional, Dict
from src.utils.security import SecurityUtils

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
            
            # Verificar contraseña
            if SecurityUtils.verify_password(password, stored_hash):
                # Actualizar último login
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
            
        except Exception as e:
            print(f"Error autenticando usuario: {e}")
            return None
    
    def update_last_login(self, user_id: int):
        """Actualiza la fecha de último login"""
        try:
            query = "UPDATE users SET last_login = NOW() WHERE id = ?"
            self.db.execute_command(query, (user_id,))
        except Exception as e:
            print(f"Error actualizando último login: {e}")
    
    def create_user(self, username: str, password: str, role: str, 
                   full_name: str, email: str = None) -> bool:
        """Crea un nuevo usuario"""
        try:
            # Validar que el usuario no exista
            existing = self.db.execute_scalar(
                "SELECT COUNT(*) FROM users WHERE username = ?", 
                (username,)
            )
            
            if existing > 0:
                return False
            
            # Hashear contraseña
            password_hash = SecurityUtils.hash_password(password)
            if not password_hash:
                return False
            
            # Insertar usuario
            query = """
            INSERT INTO users (username, password_hash, role, full_name, email, 
                             is_active, created_date)
            VALUES (?, ?, ?, ?, ?, 1, NOW())
            """
            
            return self.db.execute_command(
                query, 
                (username, password_hash, role.upper(), full_name, email)
            )
            
        except Exception as e:
            print(f"Error creando usuario: {e}")
            return False
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Cambia la contraseña de un usuario"""
        try:
            # Verificar contraseña actual
            current_hash = self.db.execute_scalar(
                "SELECT password_hash FROM users WHERE id = ?", 
                (user_id,)
            )
            
            if not SecurityUtils.verify_password(old_password, current_hash):
                return False
            
            # Hashear nueva contraseña
            new_hash = SecurityUtils.hash_password(new_password)
            if not new_hash:
                return False
            
            # Actualizar contraseña
            query = "UPDATE users SET password_hash = ? WHERE id = ?"
            return self.db.execute_command(query, (new_hash, user_id))
            
        except Exception as e:
            print(f"Error cambiando contraseña: {e}")
            return False
