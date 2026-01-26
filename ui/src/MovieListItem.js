export default function MovieListItem(props) {
    return (
        <div>
            <div>
                <strong>{props.movie.title}</strong>
                {' '}
                <span>({props.movie.year})</span>
                {' '}
                directed by {props.movie.director}
                {props.movie.actors && props.movie.actors.length > 0 && (
                    <>
                        {' '}
                        <span>
                            and starring {props.movie.actors.map(actor => `${actor.name} ${actor.surname}`).join(', ')}
                        </span>
                    </>
                )}
                {' '}
                <a onClick={props.onDelete}>Delete</a>
            </div>
            {props.movie.description}
        </div>
    );
}
