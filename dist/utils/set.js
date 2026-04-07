/**
 * Note: this code is hot, so is optimized for speed.
 */
export function difference(a, b) {
    const result = new Set();
    for (const item of a) {
        if (!b.has(item)) {
            result.add(item);
        }
    }
    return result;
}
/**
 * Note: this code is hot, so is optimized for speed.
 */
export function intersects(a, b) {
    if (a.size === 0 || b.size === 0) {
        return false;
    }
    for (const item of a) {
        if (b.has(item)) {
            return true;
        }
    }
    return false;
}
/**
 * Note: this code is hot, so is optimized for speed.
 */
export function every(a, b) {
    for (const item of a) {
        if (!b.has(item)) {
            return false;
        }
    }
    return true;
}
/**
 * Note: this code is hot, so is optimized for speed.
 */
export function union(a, b) {
    const result = new Set();
    for (const item of a) {
        result.add(item);
    }
    for (const item of b) {
        result.add(item);
    }
    return result;
}
