import {useState, useEffect} from "react";

export default function ActorSelect({value, onChange}) {
    const [availableActors, setAvailableActors] = useState([]);

    useEffect(() => {
        const fetchActors = async () => {
            const response = await fetch(`/actors`);
            if (response.ok) {
                const actors = await response.json();
                setAvailableActors(actors);
            }
        };
        fetchActors();
    }, []);

    return (
        <div>
        </div>
    );
}
