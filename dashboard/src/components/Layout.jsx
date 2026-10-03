import { useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
const groups = [
  [
    "WORKSPACE",
    [
      ["", "Overview", "◫"],
      ["consumers", "Consumers", "◉"],
      ["cases", "Cases", "▤"],
      ["feeders", "Feeders", "⑂"],
      ["alerts", "Alerts", "◷"],
      ["simulation", "Simulation", "⌁"],
    ],
  ],
  [
    "DATA",
    [
      ["consumption", "Consumption", "⌁"],
      ["baselines", "Baselines", "≋"],
    ],
  ],
  [
    "SYSTEM",
    [
      ["pipeline", "Pipeline", "⇢"],
      ["health", "Health", "♡"],
    ],
  ],
];
export default function Layout({ alerts = [], clearAlerts }) {
  const [open, setOpen] = useState(false),
    [dark, setDark] = useState(() => localStorage.getItem("theme") !== "light");
  const health = useResource(api.health, 30000),
    location = useLocation();
  function theme() {
    setDark(!dark);
    localStorage.setItem("theme", dark ? "light" : "dark");
  }
  return (
    <div className={`app ${dark ? "dark-theme" : ""}`}>
      <a className="skip" href="#content">
        Skip to content
      </a>
      <aside className={`sidebar ${open ? "is-open" : ""}`}>
        <Link className="brand" to="/">
          <span className="brand-mark">ϟ</span>TraceWatt
        </Link>
        <div className="workspace-label">
          UTILITY OPERATIONS <span>↗</span>
        </div>
        {groups.map(([name, items]) => (
          <div className="nav-group" key={name}>
            <span>{name}</span>
            {items.map(([path, title, icon]) => (
              <NavLink
                end={path === ""}
                key={title}
                to={"/console" + (path ? "/" + path : "")}
                onClick={() => setOpen(false)}
              >
                <i aria-hidden="true">{icon}</i>
                {title}
                {title === "Simulation" && <small>LIVE</small>}
              </NavLink>
            ))}
          </div>
        ))}
        <div className="sidebar-bottom">
          <span className="dot" /> Evidence before action
          <Link to="/">About TraceWatt ↗</Link>
        </div>
      </aside>
      {open && (
        <button
          className="nav-backdrop"
          aria-label="Close navigation"
          onClick={() => setOpen(false)}
        />
      )}
      <div className="app-main">
        <header className="topbar">
          <div>
            <button
              className="mobile-menu"
              aria-label="Toggle navigation"
              aria-expanded={open}
              onClick={() => setOpen(!open)}
            >
              ☰
            </button>
            <span>Mission Console</span>
            <span className="muted">
              {" "}
              / {location.pathname.split("/")[2] || "Overview"}
            </span>
          </div>
          <div className="actions">
            <span
              className={`connection ${health.data && !health.error ? "connected" : ""}`}
            >
              <span className="dot" />
              {health.loading
                ? "Connecting"
                : health.error
                  ? "Backend unavailable"
                  : health.data?.status === "ok"
                    ? "API connected"
                    : "Check API status"}
            </span>
            <button
              aria-label={dark ? "Use light appearance" : "Use dark appearance"}
              onClick={theme}
            >
              {dark ? "☀" : "◐"}
            </button>
          </div>
        </header>
        <main id="content" className="content">
          <Outlet context={{ alerts, clearAlerts }} />
        </main>
        <div className="console-footer">
          TRACEWATT / OPERATIONS WORKSPACE
          <span>Live records · polling pauses in background</span>
        </div>
      </div>
    </div>
  );
}
