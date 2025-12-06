from yoyo import step

def seed_seats(conn):
    cursor = conn.cursor()
    rows = ['A', 'B', 'C', 'D', 'E']
    cols = range(1, 11)
    
    seats_to_insert = []
    for row in rows:
        for col in cols:
            seats_to_insert.append((1, row, col))
            
    cursor.executemany("INSERT INTO seats (`room_id`, `row`, `col`) VALUES (%s, %s, %s)", seats_to_insert)

def rollback_seats(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM seats WHERE room_id = 1")


steps = [
    step(
        """
        INSERT INTO movies (title, director, genre, duration_minutes, release_date, synopsis, poster_url, is_active)
        VALUES 
        ('The Flet Unleashed', 'Dr. Code', 'Action/Comedy', 125, '2025-01-15', 'Un programador debe usar sus habilidades para salvar al mundo.', 'https://via.placeholder.com/200x300.png?text=The+Flet', TRUE),
        ('Attack of the Segfaults', 'Kernel Panic', 'Horror', 95, '2024-10-31', 'Una falla de segmentación cobra vida y aterroriza a una ciudad.', 'https://via.placeholder.com/200x300.png?text=Segfaults', TRUE);
        """,
        "DELETE FROM movies;"
    ),
    step(
        """
        INSERT INTO rooms (name, capacity, `rows`, `cols`)
        VALUES ('Sala 1', 50, 5, 10);
        """,
        "DELETE FROM rooms;"
    ),
    step(seed_seats, rollback_seats),
    step(
        """
        INSERT INTO showtimes (movie_id, room_id, show_time, format)
        VALUES
        (1, 1, CURDATE() + INTERVAL '17:00' HOUR_MINUTE, 'DOB'),
        (1, 1, CURDATE() + INTERVAL '20:00' HOUR_MINUTE, 'SUB');
        """,
        "DELETE FROM showtimes;"
    ),
    step(
        """
        INSERT INTO products (name, category, price, stock, image_url, is_active)
        VALUES
        ('Canchita Gigante', 'CONCESSION', 25.00, 100, 'https://via.placeholder.com/150x150.png?text=Canchita', TRUE),
        ('Gaseosa Grande', 'CONCESSION', 12.50, 200, 'https://via.placeholder.com/150x150.png?text=Gaseosa', TRUE),
        ('Hot-Dog Clásico', 'CONCESSION', 15.00, 150, 'https://via.placeholder.com/150x150.png?text=Hot-Dog', TRUE);
        """,
        "DELETE FROM products;"
    )
]