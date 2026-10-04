import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
const ConsolePage = lazy(() => import("./pages/Console"));
const Simulation = lazy(() => import("./pages/Simulation"));
function ConsoleRoute({ name, ...props }) {
  return <ConsolePage name={name} {...props} />;
}
export default function App() {
  return (
    <BrowserRouter>
      <Suspense
        fallback={
          <div className="app-loading" role="status">
            ϟ TraceWatt · Loading workspace…
          </div>
        }
      >
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/console" element={<Layout />}>
            <Route index element={<ConsoleRoute name="Overview" />} />
            <Route
              path="consumers"
              element={<ConsoleRoute name="Consumers" />}
            />
            <Route
              path="consumers/:id"
              element={<ConsoleRoute name="ConsumerDetail" />}
            />
            <Route path="cases" element={<ConsoleRoute name="Cases" />} />
            <Route path="feeders" element={<ConsoleRoute name="Feeders" />} />
            <Route path="alerts" element={<ConsoleRoute name="Alerts" />} />
            <Route
              path="consumption"
              element={<ConsoleRoute name="DataView" />}
            />
            <Route
              path="baselines"
              element={<ConsoleRoute name="DataView" baseline />}
            />
            <Route
              path="pipeline"
              element={<ConsoleRoute name="System" pipeline />}
            />
            <Route path="health" element={<ConsoleRoute name="System" />} />
            <Route path="simulation" element={<Simulation />} />
            <Route path="evaluation" element={<ConsoleRoute name="Evaluation" />} />
          </Route>
          {["consumers", "cases", "feeders", "alerts", "consumption"].map(
            (path) => (
              <Route
                key={path}
                path={"/" + path}
                element={<Navigate to={"/console/" + path} replace />}
              />
            ),
          )}
          <Route
            path="/simulator"
            element={<Navigate to="/console/simulation" replace />}
          />
          <Route
            path="*"
            element={
              <div className="empty">
                <h1>Page not found</h1>
                <a href="/console">Return to Mission Console →</a>
              </div>
            }
          />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
