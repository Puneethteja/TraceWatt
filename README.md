# TraceWatt Dashboard – Feature Overview

## 📖 Overview
TraceWatt is an explainable electricity‑loss investigation platform.  The dashboard provides a **single, coherent UI** that lets utility operators monitor simulations, view alerts, investigate cases, and evaluate system performance without exposing internal developer details.

---

## 🗂️ Main Navigation
| Tab | Description |
|-----|-------------|
| **Dashboard** | Home view showing high‑level KPIs, recent alerts, and quick links to investigations. |
| **Cases** | List of all flagged consumer cases.  Clicking a case opens the **Investigation** view for that consumer. |
| **Simulation** | Run a new simulation; results are automatically pushed to the Cases list and the Alerts panel. |
| **Feeder Analytics** | Visual analytics for feeder‑level loss hotspots, clusters, and consumption patterns. |
| **Evaluation** | New tab (✓ icon) showing model performance metrics (precision, recall, F1, ROC‑AUC, detection latency, throughput, etc.). |
| **Settings** | User‑level configuration (theme, notification preferences). |

---

## 🔔 Alerts Panel
- **Red badge (light mode only)** – Shows the count of unread alerts.  Clicking the badge marks alerts as read and decrements the count.  In dark mode the badge retains the default styling.  Implemented via `Layout.jsx` with classes `alert-sidebar-badge` and `topbar-alerts-btn`.
- **Automatic update** – Every simulation run triggers the ML engine; if an anomaly is detected an alert is created, the badge count updates, and the alert appears in the panel.

---

## 📊 Cases & Investigation Flow
- **Simulation → Cases** – When a simulation finishes it posts readings to `/readings`.  The ingestion pipeline creates or updates a case via the existing `analyze()` flow.  The Cases table now reflects the latest simulation data without manual refresh.
- **Case status sync** – Any status change (e.g., flagged, reviewed, resolved) updates the Cases UI instantly and propagates to the alerts count.
- **Consumer‑ID normalization** – Consumer identifiers are displayed as `CUS_###` (e.g., `CUS_001`).  Internally the helper `normalizeConsumerId` in `client.js` maps these to the original IDs.

---

## 📈 Consumer Detail Page
- Shows **historical vs. current consumption** comparison with deviation % and a plain‑English explanation of the observed pattern (e.g., “Usage spiked by 42 % during the last two weeks, which is atypical for this consumer”).
- Includes **evidence & counter‑evidence** rendered in simple language, avoiding technical jargon.
- Badges indicate risk level (high / medium / low) based on deviation thresholds.

---

## 📦 PDF Export
- The **Export → PDF** endpoint now includes a dedicated section:
  - Consumer & smart‑meter identity.
  - Historical vs. actual consumption chart.
  - Deviation, behavioural pattern, probable cause, confidence score, recommended inspection, and priority.
- The PDF generation (`services/report_pdf.py`) receives the raw readings via `get_consumption` and incorporates them into the report.

---

## ⚡ Feeder Analytics
- Visualizes feeder‑level loss hotspots and clusters.
- Updated to correctly render graphs for consumers `200`, `201`, and `111` that were previously missing.
- Uses real backend data; no mock values are introduced.

---

## 📊 Evaluation Tab
- Provides a static snapshot of model performance:
  - Precision, Recall, F1‑Score, ROC‑AUC, PR‑AUC.
  - False‑positive / false‑negative rates.
  - Detection latency, processing latency, dashboard update latency.
  - Throughput & scalability metrics for different consumer counts and sampling rates.
- Serves as a quick reference for auditors and managers.

---

## 🛠️ Technical Notes (for developers)
- **Consumer ID Helper** – `client.js` now exports `normalizeConsumerId` which pads numeric IDs to `CUS_###` and strips any existing prefix.
- **Alert Badge Styling** – Light‑mode specific CSS located in `src/index.css`; dark mode untouched.
- **Evaluation Endpoint** – Backend route `GET /evaluation` added in `backend/app/routers/dashboard.py` and exposed via FastAPI `main.py`.
- **No UI redesign** – All changes are additive; existing layouts, colors, and navigation remain untouched.

---

## 🚀 Getting Started
```bash
# Backend
uvicorn backend.app.main:app --reload

# Frontend (React)
npm install && npm start
```
Navigate to `http://localhost:3000` to explore the dashboard.

---

*All features were added with the smallest possible code changes, preserving the existing look and feel while fixing the reported bugs.*
