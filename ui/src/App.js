import './App.css';
import {useEffect, useState} from "react";
import "milligram";
import MovieForm from "./MovieForm";
import MoviesList from "./MoviesList";
import {ToastContainer, toast} from 'react-toastify';

function App() {
    const [movies, setMovies] = useState([]);
    const [addingMovie, setAddingMovie] = useState(false);

    useEffect(() => {
        const controller = new AbortController();

        const fetchMovies = async () => {
            try {
                const response = await fetch(`/movies`, {signal: controller.signal});
                if (response.ok) {
                    const movies = await response.json();
                    setMovies(movies);
                } else {
                    const errorData = await response.json();
                    toast.error(errorData.detail || 'Failed to load movies');
                }
            } catch (error) {
                if (error.name === 'AbortError') return;
                toast.error('Network error: Could not connect to server');
            }
        };

        fetchMovies();

        return () => controller.abort();
    }, []);

    async function handleAddMovie(movie) {
        const payload = {
            title: movie.title,
            year: movie.year,
            director: movie.director,
            description: movie.description,
            actor_ids: movie.actors ? movie.actors.map(actor => actor.id) : []
        };

        try {
            const response = await fetch('/movies', {
                method: 'POST',
                body: JSON.stringify(payload),
                headers: {'Content-Type': 'application/json'}
            });
            if (response.ok) {
                const movieWithId = await response.json();
                movie.id = movieWithId.id;
                setMovies([...movies, movie]);
                setAddingMovie(false);
                toast.success('Movie added successfully');
            } else {
                const errorData = await response.json();
                toast.error(errorData.detail || 'Failed to add movie');
            }
        } catch (error) {
            toast.error('Network error: Could not connect to server');
        }
    }

    async function handleDeleteMovie(movie) {
        const url = `/movies/${movie.id}`;
        try {
            const response = await fetch(url, {method: 'DELETE'});
            if (response.ok) {
                setMovies(movies.filter(m => m !== movie));
                toast.success('Movie deleted successfully');
            } else {
                const errorData = await response.json();
                toast.error(errorData.detail || 'Failed to delete movie');
            }
        } catch (error) {
            toast.error('Network error: Could not connect to server');
        }
    }

    return (
        <div className="container">
            <h1>My favourite movies to watch</h1>
            {movies.length === 0
                ? <p>No movies yet. Maybe add something?</p>
                : <MoviesList movies={movies}
                              onDeleteMovie={handleDeleteMovie}
                />}
            {addingMovie
                ? <MovieForm onMovieSubmit={handleAddMovie}
                             buttonLabel="Add a movie"
                />
                : <button onClick={() => setAddingMovie(true)}>Add a movie</button>}
            <ToastContainer/>
        </div>
    );
}

export default App;
