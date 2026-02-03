import {useState, useEffect} from "react";
import Select from "react-select";
import { toast } from 'react-toastify';
import {COULD_NOT_CONNECT_TO_SERVER, getErrorMessage} from "./utils";

export default function ActorSelect({value, onChange}) {
    const [availableActors, setAvailableActors] = useState([]);

    useEffect(() => {
        const controller = new AbortController();

        const fetchActors = async () => {
            const contextErrorMessage = 'Failed to load actors';
            try {
                const response = await fetch(`/actors`, {signal: controller.signal});
                if (response.ok) {
                    const actors = await response.json();
                    setAvailableActors(actors);
                } else {
                    const errorData = await response.json();
                    toast.error(getErrorMessage(contextErrorMessage, errorData.detail));
                }
            } catch (error) {
                if (error.name === 'AbortError') return;
                toast.error(getErrorMessage(contextErrorMessage, COULD_NOT_CONNECT_TO_SERVER));
            }
        };

        fetchActors();

        return () => controller.abort();
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
