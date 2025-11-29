"""
initial_schema
"""

from yoyo import step

__depends__ = {}

steps = [
    step(
        """
        -- Crear tabla de usuarios
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
        BEGIN
            CREATE TABLE users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100),
                is_active BIT DEFAULT 1,
                created_date DATETIME DEFAULT GETDATE(),
                last_login DATETIME
            );
            
            -- Usuario administrador por defecto (password: admin123)
            INSERT INTO users (username, password_hash, role, full_name, is_active)
            VALUES ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6IymVFt7H.8.X/M.S.V.m.i', 'ADMINISTRADOR', 'Administrador del Sistema', 1);
        END
        """,
        "DROP TABLE IF EXISTS users"
    )
]
