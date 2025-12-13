"""
schema_base_completa
"""
from yoyo import step

__depends__ = {}

steps = [
    # ==========================================
    # 1. USERS & AUTH
    # ==========================================
    step(
        """
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100),
            is_active BOOLEAN DEFAULT TRUE,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        """,
        "DROP TABLE IF EXISTS users"
    ),
    # ==========================================
    # 2. CATALOGO DE PELICULAS (Movie Repository)
    # ==========================================
    step(
        """CREATE TABLE movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            original_title VARCHAR(255),
            duration_minutes INT NOT NULL,
            rating VARCHAR(50),
            genre VARCHAR(100),
            synopsis TEXT,
            poster_url VARCHAR(500),
            trailer_url VARCHAR(500),
            status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, ARCHIVED, COMING_SOON
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        "DROP TABLE IF EXISTS movies"
    ),
    step(
        """CREATE TABLE movie_tags (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE
        )""",
        "DROP TABLE IF EXISTS movie_tags"
    ),
    step(
        """CREATE TABLE movies_tags_association (
            movie_id INT NOT NULL,
            tag_id INT NOT NULL,
            PRIMARY KEY (movie_id, tag_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES movie_tags(id) ON DELETE CASCADE
        )""",
        "DROP TABLE IF EXISTS movies_tags_association"
    ),
    # ==========================================
    # 3. SALAS Y ASIENTOS (Physical Layout)
    # ==========================================
    step(
        """CREATE TABLE theaters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            total_capacity INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        "DROP TABLE IF EXISTS theaters"
    ),
    step(
        """CREATE TABLE seat_types (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL, -- General, VIP, Wheelchair
            price_modifier DECIMAL(5, 2) DEFAULT 1.00 -- Multiplicador (ej: 1.5 para VIP)
        )""",
        "DROP TABLE IF EXISTS seat_types"
    ),
    step(
        """CREATE TABLE seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            theater_id INT NOT NULL,
            row_label VARCHAR(5) NOT NULL, -- A, B, AA
            number INT NOT NULL, -- 1, 2, 3
            seat_type_id INT NOT NULL,
            status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, BROKEN, MAINTENANCE
            x_position INT, -- Para editor visual
            y_position INT, -- Para editor visual
            FOREIGN KEY (theater_id) REFERENCES theaters(id) ON DELETE CASCADE,
            FOREIGN KEY (seat_type_id) REFERENCES seat_types(id)
        )""",
        "DROP TABLE IF EXISTS seats"
    ),
    # ==========================================
    # 4. PROGRAMACION Y PRECIOS (Scheduling)
    # ==========================================
    step(
        """CREATE TABLE price_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL, -- Matinee, Estreno, Lunes Loco
            base_price_general DECIMAL(10, 2) NOT NULL,
            base_price_child DECIMAL(10, 2) NOT NULL,
            base_price_senior DECIMAL(10, 2) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )""",
        "DROP TABLE IF EXISTS price_profiles"
    ),
    step(
        """CREATE TABLE showtimes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT NOT NULL,
            theater_id INT NOT NULL,
            price_profile_id INT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL, -- Calculado (start + duration + cleaning)
            projection_type VARCHAR(20) DEFAULT '2D', -- 2D, 3D, IMAX
            audio_type VARCHAR(20) DEFAULT 'DUB', -- SUB, DUB, ORIGINAL
            status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, CLOSED, CANCELLED
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (theater_id) REFERENCES theaters(id),
            FOREIGN KEY (price_profile_id) REFERENCES price_profiles(id)
        )""",
        "DROP TABLE IF EXISTS showtimes"
    ),
    # ==========================================
    # 5. INVENTARIO AVANZADO (Inventory Theory)
    # ==========================================
    step(
        """CREATE TABLE product_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL, -- Bebidas, Popcorn, Combos
            is_active BOOLEAN DEFAULT TRUE
        )""",
        "DROP TABLE IF EXISTS product_categories"
    ),
    step(
        """CREATE TABLE inventory_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL, -- Maiz, Vaso Grande, Jarabe Coca
            unit VARCHAR(20) NOT NULL, -- kg, lt, unit
            current_stock DECIMAL(10, 3) DEFAULT 0.000,
            reorder_point DECIMAL(10, 3) DEFAULT 10.000,
            cost_per_unit DECIMAL(10, 2) DEFAULT 0.00
        )""",
        "DROP TABLE IF EXISTS inventory_items"
    ),
    step(
        """CREATE TABLE products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_id INT NOT NULL,
            name VARCHAR(255) NOT NULL, -- Palomitas Grandes, Combo 1
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            product_type VARCHAR(20) NOT NULL DEFAULT 'SIMPLE', -- SIMPLE, COMBO, SERVICE
            track_stock BOOLEAN DEFAULT TRUE,
            image_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (category_id) REFERENCES product_categories(id)
        )""",
        "DROP TABLE IF EXISTS products"
    ),
    step(
        """CREATE TABLE product_recipes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            parent_product_id INT NOT NULL,
            -- Puede estar compuesto de un InventoryItem (ingrediente) O de otro Product (sub-producto para combos)
            inventory_item_id INT, 
            child_product_id INT,
            quantity DECIMAL(10, 3) NOT NULL, -- Cuanto descuenta
            FOREIGN KEY (parent_product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
            FOREIGN KEY (child_product_id) REFERENCES products(id)
        )""",
        "DROP TABLE IF EXISTS product_recipes"
    ),
    step(
        """CREATE TABLE stock_movements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            inventory_item_id INT NOT NULL,
            quantity DECIMAL(10, 3) NOT NULL, -- Positivo (Entrada) o Negativo (Salida)
            movement_type VARCHAR(50) NOT NULL, -- SALE, RESTOCK, ADJUSTMENT, LOSS
            reference_id INT, -- ID de Venta o ID de Orden de Compra
            user_id INT, -- Quien hizo el movimiento
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""",
        "DROP TABLE IF EXISTS stock_movements"
    ),

    # ==========================================
    # 5. VENTAS (Sales Core)
    # ==========================================
    step(
        """CREATE TABLE sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL, -- Vendedor
            customer_id INT, -- Opcional (Cliente registrado)
            total_amount DECIMAL(10, 2) NOT NULL,
            tax_amount DECIMAL(10, 2) DEFAULT 0.00,
            discount_amount DECIMAL(10, 2) DEFAULT 0.00,
            payment_method VARCHAR(50), -- CASH, CARD, MIXED
            status VARCHAR(20) DEFAULT 'COMPLETED', -- COMPLETED, REFUNDED, CANCELLED
            sale_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )""",
        "DROP TABLE IF EXISTS sales"
    ),
    step(
        """CREATE TABLE tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT NOT NULL,
            showtime_id INT NOT NULL,
            seat_id INT NOT NULL,
            price_sold DECIMAL(10, 2) NOT NULL,
            ticket_type VARCHAR(50), -- General, Student, VIP (Snapshot del momento)
            status VARCHAR(20) DEFAULT 'VALID', -- VALID, USED, REFUNDED
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (showtime_id) REFERENCES showtimes(id),
            FOREIGN KEY (seat_id) REFERENCES seats(id)
        )""",
        "DROP TABLE IF EXISTS tickets"
    ),
    step(
        """CREATE TABLE sale_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            subtotal DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""",
        "DROP TABLE IF EXISTS sale_items"
    )
]
