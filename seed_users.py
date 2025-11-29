"""
Script para crear usuarios de prueba en la base de datos
Ejecutar: python seed_users.py
"""

import sys
sys.path.insert(0, 'c:/!PROYECTOS/TKINTER/CINE')

from src.database.connection import db
from src.utils.security import SecurityUtils
from datetime import datetime

def create_test_users():
    """Crea usuarios de prueba para cada rol del sistema"""
    
    print("Creando usuarios de prueba...")
    
    # Lista de usuarios de prueba
    test_users = [
        {
            'username': 'admin',
            'password': 'admin123',
            'role': 'ADMINISTRADOR',
            'full_name': 'Administrador del Sistema',
            'email': 'admin@poscine.com'
        },
        {
            'username': 'gerente',
            'password': 'gerente123',
            'role': 'GERENCIAL',
            'full_name': 'Juan Pérez García',
            'email': 'gerente@poscine.com'
        },
        {
            'username': 'trabajador1',
            'password': 'trabajador123',
            'role': 'TRABAJADOR',
            'full_name': 'María López Rodríguez',
            'email': 'maria.lopez@poscine.com'
        },
        {
            'username': 'trabajador2',
            'password': 'trabajador123',
            'role': 'TRABAJADOR',
            'full_name': 'Carlos Sánchez Martínez',
            'email': 'carlos.sanchez@poscine.com'
        },
        {
            'username': 'cajero',
            'password': 'cajero123',
            'role': 'TRABAJADOR',
            'full_name': 'Ana Torres Fernández',
            'email': 'ana.torres@poscine.com'
        }
    ]
    
    created_count = 0
    skipped_count = 0
    
    for user_data in test_users:
        try:
            # Verificar si el usuario ya existe
            check_query = "SELECT COUNT(*) FROM users WHERE username = ?"
            result = db.execute_scalar(check_query, (user_data['username'],))
            
            if result and result > 0:
                print(f"Usuario '{user_data['username']}' ya existe, omitiendo...")
                skipped_count += 1
                continue
            
            # Hashear la contraseña
            password_hash = SecurityUtils.hash_password(user_data['password'])
            
            # Insertar el usuario
            insert_query = """
            INSERT INTO users (username, password_hash, role, full_name, email, is_active, created_date)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """
            
            success = db.execute_command(
                insert_query,
                (
                    user_data['username'],
                    password_hash,
                    user_data['role'],
                    user_data['full_name'],
                    user_data['email'],
                    datetime.now()
                )
            )
            
            if success:
                print(f" Usuario '{user_data['username']}' creado exitosamente")
                print(f"   - Rol: {user_data['role']}")
                print(f"   - Nombre: {user_data['full_name']}")
                print(f"   - Contraseña: {user_data['password']}")
                created_count += 1
            else:
                print(f"Error creando usuario '{user_data['username']}'")
                
        except Exception as e:
            print(f"Error procesando usuario '{user_data['username']}': {e}")
    
    print("\n" + "="*60)
    print(f"Resumen:")
    print(f"  - Usuarios creados: {created_count}")
    print(f"  - Usuarios omitidos (ya existían): {skipped_count}")
    print(f"  - Total procesados: {len(test_users)}")
    print("="*60)
    
    if created_count > 0:
        print("\n Credenciales de acceso:")
        print("-" * 60)
        for user_data in test_users:
            print(f"Usuario: {user_data['username']:15} | Contraseña: {user_data['password']:15} | Rol: {user_data['role']}")
        print("-" * 60)

if __name__ == "__main__":
    print("="*60)
    print("SEED DE USUARIOS DE PRUEBA - POS CINEMA")
    print("="*60)
    print()
    
    # Verificar conexión a la base de datos
    if not db.test_connection():
        print("Error: No se pudo conectar a la base de datos")
        print("   Verifica la configuración en .env")
        sys.exit(1)
    
    print("Conexión a base de datos exitosa")
    print()
    
    create_test_users()
    
    print("\n Proceso completado")
