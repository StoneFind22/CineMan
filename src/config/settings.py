import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración global del sistema POS Cinema"""
    
    # Configuración de Base de Datos
    # Configuración de Base de Datos
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_NAME = os.getenv("DB_NAME", "POS_CINEMA_DB")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Configuración de la Aplicación
    APP_TITLE = "POS Cinema - Sistema de Ventas"
    APP_VERSION = "1.0.0"
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    
    # Configuración de Roles
    ROLES = {
        "GERENCIAL": {
            "level": 3,
            "permissions": ["all"]
        },
        "ADMINISTRADOR": {
            "level": 2,
            "permissions": ["ventas", "inventario", "horarios", "reportes"]
        },
        "TRABAJADOR": {
            "level": 1,
            "permissions": ["ventas"]
        }
    }
