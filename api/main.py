import logging
from fastapi import FastAPI, Path, HTTPException, Request, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from typing import Annotated, List, Final, Optional
import sqlite3
from pydantic import BaseModel, Field

DB_FILE_NAME: Final[str] = "movies-extended.db"
MOVIE_TABLE_NAME: Final[str] = "movie"
ACTOR_TABLE_NAME: Final[str] = "actor"
MOVIE_ACTOR_TABLE_NAME: Final[str] = "movie_actor_through"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.mount("/static", StaticFiles(directory="../ui/build/static", check_dir=False), name="static")


class MovieBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    year: int = Field(..., ge=1888, le=2100)
    director: str = Field(..., max_length=255)
    description: str


class Movie(MovieBase):
    id: int = Field(..., gt=0)


class ActorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    surname: str = Field(..., min_length=2, max_length=255)


class Actor(ActorBase):
    id: int = Field(..., gt=0)


class MovieWithActors(Movie):
    actors: List[Actor] = []


def get_db():
    connection = sqlite3.connect(DB_FILE_NAME)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
    finally:
        connection.close()


def db_fetch_all(db: sqlite3.Connection, table: str) -> List[dict]:
    cursor = db.cursor()
    query = f"SELECT * FROM {table}"
    cursor.execute(query)
    return [dict(row) for row in cursor]


def db_fetch_one(db: sqlite3.Connection, table: str, item_id: int) -> Optional[dict]:
    cursor = db.cursor()
    query = f"SELECT * FROM {table} WHERE id=?"
    row = cursor.execute(query, (item_id,)).fetchone()
    if row:
        return dict(row)
    return None


def db_insert(db: sqlite3.Connection, table: str, data: dict) -> int:
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    values = tuple(data.values())
    with db:
        cursor = db.cursor()
        cursor.execute(query, values)
        return cursor.lastrowid


def db_update(db: sqlite3.Connection, table: str, item_id: int, data: dict) -> bool:
    set_clause = ", ".join([f"{key}=?" for key in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE id=?"
    values = list(data.values()) + [item_id]
    with db:
        cursor = db.cursor()
        cursor.execute(query, values)
        return cursor.rowcount > 0


def db_delete(db: sqlite3.Connection, table: str, item_id: int, junction_table: str = None,
              junction_column: str = None) -> bool:
    with db:
        cursor = db.cursor()
        if junction_table and junction_column:
            cursor.execute(f"DELETE FROM {junction_table} WHERE {junction_column}=?", (item_id,))
        cursor.execute(f"DELETE FROM {table} WHERE id=?", (item_id,))
        return cursor.rowcount > 0


def db_delete_all(db: sqlite3.Connection, table: str, junction_table: str = None) -> int:
    with db:
        cursor = db.cursor()
        if junction_table:
            cursor.execute(f"DELETE FROM {junction_table}")
        cursor.execute(f"DELETE FROM {table}")
        return cursor.rowcount


def db_fetch_movie_actors(db: sqlite3.Connection, movie_id: int) -> List[dict]:
    cursor = db.cursor()
    query = '''
            SELECT a.id, a.name, a.surname
            FROM actor a
            JOIN movie_actor_through mat ON a.id = mat.actor_id
            WHERE mat.movie_id = ? 
            '''
    cursor.execute(query, (movie_id,))
    return [dict(row) for row in cursor]


def db_search_actors(db: sqlite3.Connection, search_string: str) -> List[dict]:
    cursor = db.cursor()
    query = f"SELECT * FROM {ACTOR_TABLE_NAME} WHERE name LIKE ? OR surname LIKE ?"
    wildcard_search = f"%{search_string}%"
    cursor.execute(query, (wildcard_search, wildcard_search))
    return [dict(row) for row in cursor]


def db_fetch_all_movies_with_actors(db: sqlite3.Connection) -> List[dict]:
    cursor = db.cursor()
    query = '''
        SELECT 
            m.id as movie_id, m.title, m.year, m.director, m.description,
            a.id as actor_id, a.name, a.surname
        FROM movie m
        LEFT JOIN movie_actor_through mat ON m.id = mat.movie_id
        LEFT JOIN actor a ON mat.actor_id = a.id
    '''
    cursor.execute(query)
    rows = cursor.fetchall()

    movies_map = {}

    for row in rows:
        m_id = row['movie_id']
        
        if m_id not in movies_map:
            movies_map[m_id] = {
                "id": m_id,
                "title": row['title'],
                "year": row['year'],
                "director": row['director'],
                "description": row['description'],
                "actors": []
            }
        
        if row['actor_id'] is not None:
            actor = {
                "id": row['actor_id'],
                "name": row['name'],
                "surname": row['surname']
            }
            movies_map[m_id]['actors'].append(actor)

    return list(movies_map.values())


@app.exception_handler(sqlite3.IntegrityError)
async def sqlite_integrity_exception_handler(request: Request, exc: sqlite3.IntegrityError):
    logger.exception("Database integrity error occurred")
    return JSONResponse(
        status_code=409,
        content={"detail": "Database integrity error"}
    )


@app.exception_handler(sqlite3.OperationalError)
async def sqlite_operational_exception_handler(request: Request, exc: sqlite3.OperationalError):
    logger.exception("Database operational error occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database operational error"}
    )


@app.exception_handler(sqlite3.Error)
async def sqlite_exception_handler(request: Request, exc: sqlite3.Error):
    logger.exception("Database error occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()}
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
    logger.exception("Response validation error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


@app.get("/")
def serve_react_app():
    return FileResponse("../ui/build/index.html")


@app.get('/movies', response_model=List[MovieWithActors])
def get_movies(db: sqlite3.Connection = Depends(get_db)):
    return db_fetch_all_movies_with_actors(db)


@app.get('/movies/{movie_id}', response_model=Movie)
def get_movie(movie_id: Annotated[int, Path(gt=0)], db: sqlite3.Connection = Depends(get_db)):
    movie = db_fetch_one(db, MOVIE_TABLE_NAME, movie_id)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    return movie


@app.post('/movies')
def add_movie(movie: MovieBase, db: sqlite3.Connection = Depends(get_db)):
    new_id = db_insert(db, MOVIE_TABLE_NAME, movie.model_dump())
    return {
        "id": new_id,
        "message": "Movie added successfully"
    }


@app.delete('/movies/{movie_id}')
def delete_movie(movie_id: Annotated[int, Path(gt=0)], db: sqlite3.Connection = Depends(get_db)):
    deleted = db_delete(db, MOVIE_TABLE_NAME, movie_id, junction_table=MOVIE_ACTOR_TABLE_NAME,
                        junction_column='movie_id')
    if not deleted:
        raise HTTPException(404, "Movie not found")
    return {"message": "Movie deleted successfully"}


@app.put('/movies/{movie_id}')
def update_movie(movie_id: Annotated[int, Path(gt=0)], movie: MovieBase, db: sqlite3.Connection = Depends(get_db)):
    updated = db_update(db, MOVIE_TABLE_NAME, movie_id, movie.model_dump())
    if not updated:
        raise HTTPException(404, "Movie not found")
    return {"message": "Movie updated successfully"}


@app.delete('/movies')
def delete_movies(db: sqlite3.Connection = Depends(get_db)):
    deleted_count = db_delete_all(db, MOVIE_TABLE_NAME, junction_table=MOVIE_ACTOR_TABLE_NAME)
    return {
        "deleted": deleted_count,
        "message": "Movies deleted successfully"
    }


@app.get('/actors', response_model=List[Actor])
def get_actors(db: sqlite3.Connection = Depends(get_db),
               q: Annotated[Optional[str], Query(min_length=3, description="Search by name or surname")] = None):
    if q:
        return db_search_actors(db, q)
    return db_fetch_all(db, ACTOR_TABLE_NAME)


@app.get('/actors/{actor_id}', response_model=Actor)
def get_actor(actor_id: Annotated[int, Path(gt=0)], db: sqlite3.Connection = Depends(get_db)):
    actor = db_fetch_one(db, ACTOR_TABLE_NAME, actor_id)
    if actor is None:
        raise HTTPException(404, "Actor not found")
    return actor


@app.post('/actors')
def add_actor(actor: ActorBase, db: sqlite3.Connection = Depends(get_db)):
    new_id = db_insert(db, ACTOR_TABLE_NAME, actor.model_dump())
    return {
        "id": new_id,
        "message": "Actor added successfully"
    }


@app.delete('/actors/{actor_id}')
def delete_actor(actor_id: Annotated[int, Path(gt=0)], db: sqlite3.Connection = Depends(get_db)):
    deleted = db_delete(db, ACTOR_TABLE_NAME, actor_id, junction_table=MOVIE_ACTOR_TABLE_NAME,
                        junction_column='actor_id')
    if not deleted:
        raise HTTPException(404, "Actor not found")
    return {"message": "Actor deleted successfully"}


@app.put('/actors/{actor_id}')
def update_actor(actor_id: Annotated[int, Path(gt=0)], actor: ActorBase, db: sqlite3.Connection = Depends(get_db)):
    updated = db_update(db, ACTOR_TABLE_NAME, actor_id, actor.model_dump())
    if not updated:
        raise HTTPException(404, "Actor not found")
    return {"message": "Actor updated successfully"}


@app.get('/movies/{movie_id}/actors', response_model=List[Actor])
def get_movie_actors(movie_id: Annotated[int, Path(gt=0)], db: sqlite3.Connection = Depends(get_db)):
    movie = db_fetch_one(db, MOVIE_TABLE_NAME, movie_id)
    if movie is None:
        raise HTTPException(404, "Movie not found")
    return db_fetch_movie_actors(db, movie_id)
