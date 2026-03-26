export const calculateResonance = (input) => {
    return {
        community: input * 0.99,
        node: input * 0.01,
        timestamp: new Date().toISOString()
    };
};
