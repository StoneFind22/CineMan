from yoyo import step

steps = [
    step(
        """CREATE TABLE movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            director VARCHAR(255),
            genre VARCHAR(100),
            duration_minutes INT,
            release_date DATE,
            synopsis TEXT,
            poster_url VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE
        )""",
        "DROP TABLE IF EXISTS movies"
    ),
    step(
        """CREATE TABLE rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            capacity INT,
            `rows` INT,
            `cols` INT
        )""",
        "DROP TABLE IF EXISTS rooms"
    ),
    step(
        """CREATE TABLE seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_id INT NOT NULL,
            `row` VARCHAR(2) NOT NULL,
            `col` INT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )""",
        "DROP TABLE IF EXISTS seats"
    ),
    step(
        """CREATE TABLE showtimes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT NOT NULL,
            room_id INT NOT NULL,
            show_time DATETIME NOT NULL,
            format VARCHAR(50),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )""",
        "DROP TABLE IF EXISTS showtimes"
    ),
    step(
        """CREATE TABLE products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            price DECIMAL(10, 2) NOT NULL,
            stock INT,
            image_url VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE
        )""",
        "DROP TABLE IF EXISTS products"
    ),
    step(
        """CREATE TABLE sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            sale_date DATETIME NOT NULL,
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
            ticket_type VARCHAR(50),
            price DECIMAL(10, 2),
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
            price_at_sale DECIMAL(10, 2),
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )""",
        "DROP TABLE IF EXISTS sale_items"
    )
]