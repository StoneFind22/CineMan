"""
seed_user_roles
"""

from yoyo import step

__depends__ = {'20251126_01_wGjzL-initial-schema'}

# Contraseña para todos los usuarios: 'admin'
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
    )
]