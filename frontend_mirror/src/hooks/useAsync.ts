/**
 * Inputs :
 *   - action: (...args: A) => Promise<R>
 * Outputs :
 *   - { run: (...args: A) => Promise<R | undefined>; loading: boolean; error: ApiError | null }
 * File explanation : Wraps a button-triggered API action: sets loading while it runs, stores the error, returns undefined on failure and the result on success. Does not show toasts itself.
 */
