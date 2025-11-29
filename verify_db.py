from src.database.connection import db
from src.config.settings import Config

def verify_database():
    print(f"Conectando a: {Config.DB_SERVER} / {Config.DB_NAME}")
    
    if not db.test_connection():
        print(" Error: No se pudo conectar a la base de datos.")
        return

    print(" Conexión exitosa.")
    
    # Verificar tablas
    tables = [
        "users", "movies", "theaters", "showtimes", "customers", "sales", "tickets"
    ]
    
    print("\nVerificando tablas:")
    all_exist = True
    for table in tables:
        try:
            count = db.execute_scalar(f"SELECT COUNT(*) FROM {table}")
            if count is not None:
                print(f" Tabla '{table}' existe. Registros: {count}")
            else:
                print(f" Tabla '{table}' no encontrada o error de acceso.")
                all_exist = False
        except Exception as e:
            print(f" Error verificando tabla '{table}': {e}")
            all_exist = False
            
    if all_exist:
        print("\n Todas las tablas principales existen.")
    else:
        print("\n Faltan algunas tablas o hubo errores.")

if __name__ == "__main__":
    verify_database()
