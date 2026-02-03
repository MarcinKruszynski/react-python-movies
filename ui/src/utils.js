export const COULD_NOT_CONNECT_TO_SERVER = "Could not connect to server";

export const getErrorMessage = (contextMessage, errorDetail) => {
    return errorDetail
        ? `${contextMessage}: ${errorDetail}`
        : contextMessage;
};