import {useState, useEffect} from "react";
import Select from "react-select";

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

    const actorToOption = (actor) => ({
        value: actor,
        label: `${actor.name} ${actor.surname}`
    });

    const options = availableActors.map(actorToOption);

    const selectValue = value ? value.map(actorToOption) : [];

    const handleChange = (selectedOptions) => {
        const actors = selectedOptions ? selectedOptions.map(opt => opt.value) : [];
        onChange(actors);
    };

    return (
        <Select
            isMulti
            isClearable={false}
            options={options}
            value={selectValue}
            onChange={handleChange}
            placeholder="Select actors..."
            className="actor-select"
            components={{
                DropdownIndicator: () => null,
                IndicatorSeparator: () => null
            }}
        />
    );
}
