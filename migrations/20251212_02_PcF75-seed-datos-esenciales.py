"""
seed_datos_esenciales
"""

from yoyo import step

__depends__ = {'20251212_01_10msb-schema-base-completa'}

# Contraseña para todos los usuarios de prueba: 'admin'
# Hash generado con bcrypt
password_hash = "$2b$12$VFO3taPdHi7YRjBuVT/zFejAyGErFAdMkymElCtfiKZ7uQ2U72.ye"

steps = [
    step(
        f"""
        INSERT INTO users (username, password_hash, role, full_name, is_active)
        VALUES 
            ('admin', '{password_hash}', 'ADMINISTRADOR', 'Usuario Administrador', 1),
            ('gerencial', '{password_hash}', 'GERENCIAL', 'Usuario Gerencial', 1),
            ('trabajador', '{password_hash}', 'TRABAJADOR', 'Usuario Trabajador', 1)
        """,
        """
        DELETE FROM users WHERE username IN ('admin', 'gerencial', 'trabajador')
        """
    ),
    step(
        """INSERT INTO seat_types (name, price_modifier) VALUES 
           ('General', 1.00), ('VIP', 1.50), ('Discapacitados', 1.00)""",
        "DELETE FROM seat_types WHERE name IN ('General', 'VIP', 'Discapacitados')"
    )
]
