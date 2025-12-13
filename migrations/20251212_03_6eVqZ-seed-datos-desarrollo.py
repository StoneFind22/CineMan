"""
seed_datos_desarrollo
"""

from yoyo import step

__depends__ = {'20251212_02_PcF75-seed-datos-esenciales'}

steps = [
    # -- Pelicula de Prueba 1
    step(
        """
        INSERT INTO movies (id, title, original_title, duration_minutes, rating, genre, synopsis, status)
        VALUES (1, 'La Venganza del Código', 'Code''s Revenge', 135, 'PG-13', 'Acción/Sci-Fi', 
                'Un programador retirado vuelve a la acción cuando un virus amenaza con destruir el mundo digital.', 'ACTIVE');
        """,
        "DELETE FROM movies WHERE id = 1;"
    ),
    # -- Pelicula de Prueba 2
    step(
        """
        INSERT INTO movies (id, title, original_title, duration_minutes, rating, genre, synopsis, status)
        VALUES (2, 'El Bucle Infinito', 'The Infinite Loop', 98, 'R', 'Misterio/Thriller', 
                'Dos detectives quedan atrapados en un bucle temporal mientras investigan una extraña desaparición.', 'ACTIVE');
        """,
        "DELETE FROM movies WHERE id = 2;"
    ),
    # -- Tags de prueba
    step(
        """
        INSERT INTO movie_tags (id, name) VALUES (1, 'Estreno'), (2, 'Recomendada'), (3, 'Sci-Fi');
        """,
        "DELETE FROM movie_tags WHERE id IN (1, 2, 3);"
    ),
    # -- Asociar tags a pelicula 1
    step(
        """
        INSERT INTO movies_tags_association (movie_id, tag_id) VALUES (1, 1), (1, 3);
        """,
        "DELETE FROM movies_tags_association WHERE movie_id = 1;"
    ),
    # -- Sala de prueba
    step(
        """
        INSERT INTO theaters (id, name, total_capacity, is_active) 
        VALUES (1, 'Sala Digital A', 120, TRUE);
        """,
        "DELETE FROM theaters WHERE id = 1;"
    ),
    # -- Perfil de precios de prueba
    step(
        """
        INSERT INTO price_profiles (id, name, base_price_general, base_price_child, base_price_senior, is_active)
        VALUES (1, 'Precio General 2025', 25.50, 15.00, 18.00, TRUE);
        """,
        "DELETE FROM price_profiles WHERE id = 1;"
    ),
    # -- Funciones de prueba
    step(
        """
        INSERT INTO showtimes (movie_id, theater_id, price_profile_id, start_time, end_time, projection_type, audio_type, status)
        VALUES (1, 1, 1, '2025-12-25 17:00:00', '2025-12-25 19:15:00', '2D', 'DUB', 'OPEN'),
               (1, 1, 1, '2025-12-25 20:00:00', '2025-12-25 22:15:00', '2D', 'SUB', 'OPEN');
        """,
        "DELETE FROM showtimes WHERE movie_id = 1 AND theater_id = 1;"
    )
]
