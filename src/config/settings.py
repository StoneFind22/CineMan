import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración global del sistema POS Cinema"""
    
    # Configuración de Base de Datos
    DB_SERVER = os.getenv("DB_SERVER", "localhost")
    DB_NAME = os.getenv("DB_NAME", "POS_CINEMA_DB")
    DB_DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_TRUSTED_CONNECTION = os.getenv("DB_TRUSTED_CONNECTION", "yes")
    
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
