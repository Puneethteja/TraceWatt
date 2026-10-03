import { useCallback, useEffect, useState } from "react";
export function useResource(loader, interval = 15000, version = 0) {
  const [state, setState] = useState({
    data: null,
    loading: true,
    error: null,
    updated: null,
  });
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((n) => n + 1), []);
  useEffect(() => {
    let stopped = false,
      timer,
      controller,
      generation = 0;
    async function run() {
      if (stopped || document.hidden) return;
      const token = ++generation;
      const request = new AbortController();
      controller = request;
      try {
        const data = await loader(request.signal);
        if (!stopped && !request.signal.aborted)
          setState({
            data,
            loading: false,
            error: null,
            updated: new Date(),
            loader,
            revision,
            version,
          });
      } catch (error) {
        if (!stopped && !request.signal.aborted)
          setState({
            data: null,
            loading: false,
            error,
            updated: null,
            loader,
            revision,
            version,
          });
      } finally {
        if (!stopped && token === generation && !document.hidden && interval)
          timer = setTimeout(run, interval);
      }
    }
    function visibility() {
      ++generation;
      clearTimeout(timer);
      controller?.abort();
      if (!document.hidden) run();
    }
    run();
    document.addEventListener("visibilitychange", visibility);
    return () => {
      stopped = true;
      clearTimeout(timer);
      controller?.abort();
      document.removeEventListener("visibilitychange", visibility);
    };
  }, [loader, interval, revision, version]);
  return state.loader === loader &&
    state.revision === revision &&
    state.version === version
    ? { ...state, refresh }
    : { data: null, loading: true, error: null, updated: null, refresh };
}
