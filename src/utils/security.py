import bcrypt
from datetime import datetime
from typing import Dict
from src.config.settings import Config

class SecurityUtils:
    """Utilidades para manejo seguro de contraseñas y sesiones"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera hash seguro de contraseña"""
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            print(f"Error hasheando contraseña: {e}")
            return None
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verifica contraseña contra hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            print(f"Error verificando contraseña: {e}")
            return False
    
    @staticmethod
    def validate_user_role(role: str) -> bool:
        """Valida que el rol de usuario sea válido"""
        return role.upper() in Config.ROLES
    
    @staticmethod
    def check_permission(user_role: str, required_permission: str) -> bool:
        """Verifica si un usuario tiene permisos para una acción"""
        try:
            role_info = Config.ROLES.get(user_role.upper())
            if not role_info:
                return False
            
            permissions = role_info.get("permissions", [])
            return "all" in permissions or required_permission in permissions
        except Exception as e:
            print(f"Error verificando permisos: {e}")
            return False

class UserSession:
    """Maneja la sesión del usuario actual"""
    
    def __init__(self):
        self.user_id = None
        self.username = None
        self.role = None
        self.login_time = None
        self.is_active = False
    
    def login(self, user_id: int, username: str, role: str):
        """Inicia sesión de usuario"""
        self.user_id = user_id
        self.username = username
        self.role = role.upper()
        self.login_time = datetime.now()
        self.is_active = True
    
    def logout(self):
        """Cierra sesión de usuario"""
        self.user_id = None
        self.username = None
        self.role = None
        self.login_time = None
        self.is_active = False
    
    def has_permission(self, permission: str) -> bool:
        """Verifica si el usuario actual tiene un permiso específico"""
        if not self.is_active:
            return False
        return SecurityUtils.check_permission(self.role, permission)
    
    def get_session_info(self) -> Dict:
        """Retorna información de la sesión actual"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "is_active": self.is_active
        }

# Instancia global de sesión de usuario
current_session = UserSession()
