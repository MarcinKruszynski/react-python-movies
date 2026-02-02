import './App.css';
import {useEffect, useState} from "react";
import "milligram";
import MovieForm from "./MovieForm";
import MoviesList from "./MoviesList";
import {ToastContainer, toast} from 'react-toastify';
import {COULD_NOT_CONNECT_TO_SERVER, getErrorMessage} from "./utils";

function App() {
    const [movies, setMovies] = useState([]);
    const [addingMovie, setAddingMovie] = useState(false);

    useEffect(() => {
        const controller = new AbortController();

        const fetchMovies = async () => {
            const contextErrorMessage = 'Failed to load movies';
            try {
                const response = await fetch(`/movies`, {signal: controller.signal});
                if (response.ok) {
                    const movies = await response.json();
                    setMovies(movies);
                } else {
                    const errorData = await response.json();
                    toast.error(getErrorMessage(contextErrorMessage, errorData.detail));
                }
            } catch (error) {
                if (error.name === 'AbortError') return;
                toast.error(getErrorMessage(contextErrorMessage, COULD_NOT_CONNECT_TO_SERVER));
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
        const contextErrorMessage = 'Failed to add movie';
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
                toast.error(getErrorMessage(contextErrorMessage, errorData.detail));
            }
        } catch (error) {
            toast.error(getErrorMessage(contextErrorMessage, COULD_NOT_CONNECT_TO_SERVER));
        }
    }

    async function handleDeleteMovie(movie) {
        const url = `/movies/${movie.id}`;
        const contextErrorMessage = 'Failed to delete movie';
        try {
            const response = await fetch(url, {method: 'DELETE'});
            if (response.ok) {
                setMovies(movies.filter(m => m !== movie));
                toast.success('Movie deleted successfully');
            } else {
                const errorData = await response.json();
                toast.error(getErrorMessage(contextErrorMessage, errorData.detail));
            }
        } catch (error) {
            toast.error(getErrorMessage(contextErrorMessage, COULD_NOT_CONNECT_TO_SERVER));
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
