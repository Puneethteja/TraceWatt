import { useState, useEffect } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useResource } from "../hooks/useResource";
import { api } from "../api/client";
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
      ["evaluation", "Evaluation", "✓"],
    ],
  ],
  [
    "DATA",
    [
      ["consumption", "Consumption", "⌁"],
      ["baselines", "Baselines", "≋"],
    ],
  ],
];
export default function Layout({ alerts = [], clearAlerts }) {
  const [open, setOpen] = useState(false),
    [dark, setDark] = useState(() => localStorage.getItem("theme") !== "light");
  const location = useLocation();
  const alertsResource = useResource(api.alerts, 5000);
  const alertsList = Array.isArray(alertsResource.data) ? alertsResource.data : (Array.isArray(alerts) ? alerts : []);
  const unreadAlertsCount = alertsList.filter((a) => !a.is_read).length;
  const displayAlertCount = unreadAlertsCount;

  useEffect(() => {
    function handleAlertUpdate() {
      alertsResource.refresh();
    }
    window.addEventListener("tracewatt-alert-updated", handleAlertUpdate);
    return () => window.removeEventListener("tracewatt-alert-updated", handleAlertUpdate);
  }, [alertsResource]);

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
                {title === "Alerts" && displayAlertCount > 0 && (
                  <span
                    className="badge warning alert-sidebar-badge"
                    style={{
                      marginLeft: "auto",
                      padding: "1px 6px",
                      fontSize: "0.72rem",
                      borderRadius: "10px",
                      fontWeight: 600,
                    }}
                  >
                    {displayAlertCount}
                  </span>
                )}
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
            {displayAlertCount > 0 && (
              <NavLink
                to="/console/alerts"
                className="topbar-alerts-btn"
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.35rem",
                  textDecoration: "none",
                  marginRight: "0.5rem",
                  padding: "4px 8px",
                  borderRadius: "6px",
                  fontSize: "0.82rem",
                  color: "inherit",
                  border: "1px solid var(--border)",
                  background: "var(--card-bg, rgba(255,255,255,0.05))",
                }}
                title={`${displayAlertCount} Active Alerts`}
              >
                <span aria-hidden="true">🔔</span>
                <span style={{ fontWeight: 600 }}>{displayAlertCount}</span>
              </NavLink>
            )}
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
