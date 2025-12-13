import logging
from typing import List, Dict, Optional, Any
from src.database.connection import DatabaseConnection, DatabaseError
from src.models.models import Movie, MovieStatus

logger = logging.getLogger(__name__)

class MovieService:
    """
    Servicio para gestionar el catálogo de películas (Repositorio).
    Maneja CRUD de películas, etiquetas y metadatos.
    """
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_movies(self, status: Optional[str] = None) -> List[Movie]:
        """
        Obtiene todas las películas y sus etiquetas de forma optimizada, 
        opcionalmente filtradas por estado.
        """
        try:
            # GROUP_CONCAT concatena tags en una sola cadena para optimizar la consulta.
            query = """
                SELECT 
                    m.id, m.title, m.original_title, m.duration_minutes, m.rating, 
                    m.genre, m.synopsis, m.poster_url, m.trailer_url, m.status, m.created_at,
                    GROUP_CONCAT(t.name ORDER BY t.name ASC SEPARATOR ',') AS tags
                FROM 
                    movies m
                LEFT JOIN 
                    movies_tags_association mta ON m.id = mta.movie_id
                LEFT JOIN 
                    movie_tags t ON mta.tag_id = t.id
            """
            params = []
            if status:
                # Se usa alias m.status para evitar ambigüedades.
                query += " WHERE m.status = %s"
                params.append(status)
            
            query += " GROUP BY m.id ORDER BY m.title ASC"
            
            results = self.db.execute_query(query, tuple(params))
            
            movies = []
            for row in results:
                tags_str = row['tags']
                # GROUP_CONCAT devuelve NULL si no hay tags; se convierte a lista vacía.
                tag_list = tags_str.split(',') if tags_str else []
                
                movie = Movie(
                    id=row['id'],
                    title=row['title'],
                    original_title=row['original_title'],
                    duration_minutes=row['duration_minutes'],
                    rating=row['rating'],
                    genre=row['genre'],
                    synopsis=row['synopsis'],
                    poster_url=row['poster_url'],
                    trailer_url=row['trailer_url'],
                    status=row['status'],
                    created_at=row['created_at'],
                    tags=tag_list
                )
                movies.append(movie)
            return movies
        except DatabaseError as e:
            logger.exception(f"Error al obtener películas de forma optimizada: {e}")
            return []

    def get_movie_by_id(self, movie_id: int) -> Optional[Movie]:
        """Obtiene una película por su ID, incluyendo sus etiquetas, de forma optimizada."""
        try:
            query = """
                SELECT 
                    m.id, m.title, m.original_title, m.duration_minutes, m.rating, 
                    m.genre, m.synopsis, m.poster_url, m.trailer_url, m.status, m.created_at,
                    GROUP_CONCAT(t.name ORDER BY t.name ASC SEPARATOR ',') AS tags
                FROM 
                    movies m
                LEFT JOIN 
                    movies_tags_association mta ON m.id = mta.movie_id
                LEFT JOIN 
                    movie_tags t ON mta.tag_id = t.id
                WHERE
                    m.id = %s
                GROUP BY 
                    m.id
            """
            results = self.db.execute_query(query, (movie_id,))
            if not results:
                return None
            
            row = results[0]
            tags_str = row['tags']
            tag_list = tags_str.split(',') if tags_str else []

            return Movie(
                id=row['id'],
                title=row['title'],
                original_title=row['original_title'],
                duration_minutes=row['duration_minutes'],
                rating=row['rating'],
                genre=row['genre'],
                synopsis=row['synopsis'],
                poster_url=row['poster_url'],
                trailer_url=row['trailer_url'],
                status=row['status'],
                created_at=row['created_at'],
                tags=tag_list
            )
        except DatabaseError as e:
            logger.exception(f"Error al obtener película {movie_id} de forma optimizada: {e}")
            return None

    def create_movie(self, movie: Movie) -> Optional[int]:
        """Crea una nueva película en el catálogo."""
        try:
            query = """
                INSERT INTO movies (title, original_title, duration_minutes, rating, genre, 
                                    synopsis, poster_url, trailer_url, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                movie.title, movie.original_title, movie.duration_minutes, movie.rating,
                movie.genre, movie.synopsis, movie.poster_url, movie.trailer_url, movie.status
            )
            movie_id = self.db.execute_insert(query, params)
            
            if movie.tags:
                self.update_movie_tags(movie_id, movie.tags)
                
            return movie_id
        except DatabaseError as e:
            logger.exception(f"Error al crear película: {e}")
            return None

    def update_movie(self, movie: Movie) -> bool:
        """Actualiza una película existente."""
        try:
            query = """
                UPDATE movies 
                SET title=%s, original_title=%s, duration_minutes=%s, rating=%s, genre=%s, 
                    synopsis=%s, poster_url=%s, trailer_url=%s, status=%s
                WHERE id=%s
            """
            params = (
                movie.title, movie.original_title, movie.duration_minutes, movie.rating,
                movie.genre, movie.synopsis, movie.poster_url, movie.trailer_url, movie.status,
                movie.id
            )
            rows_affected = self.db.execute_command(query, params)
            
            if movie.tags is not None: # Si se pasa una lista (incluso vacía), se actualiza
                self.update_movie_tags(movie.id, movie.tags)
                
            return rows_affected > 0 or movie.tags is not None
        except DatabaseError as e:
            logger.exception(f"Error al actualizar película {movie.id}: {e}")
            return False

    def delete_movie(self, movie_id: int) -> bool:
        """Elimina una película del catálogo."""
        try:
            # ON DELETE CASCADE en la FK se encarga de limpiar las asociaciones.
            rows_affected = self.db.execute_command("DELETE FROM movies WHERE id = %s", (movie_id,))
            return rows_affected > 0
        except DatabaseError as e:
            logger.exception(f"Error al eliminar película {movie_id}: {e}")
            return False

    def get_movie_tags(self, movie_id: int) -> List[str]:
        """Obtiene las etiquetas asociadas a una película."""
        try:
            query = """
                SELECT t.name 
                FROM movie_tags t
                JOIN movies_tags_association mta ON t.id = mta.tag_id
                WHERE mta.movie_id = %s
            """
            results = self.db.execute_query(query, (movie_id,))
            return [row['name'] for row in results]
        except DatabaseError:
            return []

    def get_all_tags(self) -> List[str]:
        """Obtiene todas las etiquetas únicas del sistema, ordenadas alfabéticamente."""
        try:
            query = "SELECT name FROM movie_tags ORDER BY name ASC"
            results = self.db.execute_query(query)
            return [row['name'] for row in results] if results else []
        except DatabaseError:
            logger.exception("Error al obtener todas las etiquetas")
            return []

    def update_movie_tags(self, movie_id: int, tags: List[str]):
        """Actualiza las etiquetas de una película (Borra y Recrea)."""
        try:
            tag_ids = []
            for tag_name in tags:
                res = self.db.execute_query("SELECT id FROM movie_tags WHERE name = %s", (tag_name,))
                if res:
                    tag_ids.append(res[0]['id'])
                else:
                    new_id = self.db.execute_insert("INSERT INTO movie_tags (name) VALUES (%s)", (tag_name,))
                    tag_ids.append(new_id)
            
            self.db.execute_command("DELETE FROM movies_tags_association WHERE movie_id = %s", (movie_id,))
            
            if tag_ids:
                # Se usa un loop de inserts por simplicidad en lugar de executemany.
                for tid in tag_ids:
                    self.db.execute_insert(
                        "INSERT INTO movies_tags_association (movie_id, tag_id) VALUES (%s, %s)",
                        (movie_id, tid)
                    )
        except DatabaseError as e:
            logger.exception(f"Error al actualizar tags para película {movie_id}: {e}")
