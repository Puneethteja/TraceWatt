# TraceWatt dashboard

React 19 + Vite + React Router + Recharts. Three.js powers the lazy-loaded conceptual network. Fonts are bundled locally. All frontend implementation is inside this directory.

## Run

```powershell
cd dashboard
npm install
npm run dev
```

Open http://127.0.0.1:5173. Landing: `/`; operations: `/console`.

Development uses `VITE_API_URL=/api` and Vite's proxy to `API_PROXY_TARGET=http://127.0.0.1:8000`. No backend CORS edits are needed for this same-origin proxy. Production needs either a real `VITE_API_URL` configured at build time with an allowed backend origin, or a host-provided `/api` reverse proxy. Vite's development proxy is not part of the production bundle. The Vercel SPA rewrite alone does not proxy the API.

The backend is managed separately. Do not start it casually against an empty database: the incoming backend merge automatically seeds synthetic records at startup. This frontend does not seed data, create a database, generate predictions, or bypass HTTP.

## Implemented

- Landing page with interactive cause explanations, conceptual workflow, explainability, and console CTA.
- Overview with API-derived counts (consumer sample capped and labeled), composition, alerts, case statuses, and consumption.
- Consumer explorer with server filters and pagination; search is explicitly limited to the loaded page.
- Consumer investigation with actual/baseline chart, case details, evidence, counter-evidence, confidence, loss, priority, status updates, notes, and PDF export.
- Case register and JSON export. Original backend's `Open` status is preserved for display; update options are the six requested statuses.
- Feeder summaries and average-loss visualization, with unsupported measurements explicitly unavailable.
- Alert center, consumption/baseline pages, health and pipeline pages.
- Input simulation with real consumer selection, nullable ReadingIn fields, timestamp conversion, 5–300 second interval, start/pause/stop, and real POST acknowledgement.
- Responsive light/dark console, keyboard-accessible navigation and cause tabs, reduced-motion support, loading/empty/error/unavailable states.
- Sequential polling (15 or 30 seconds), hidden-tab cancellation, timer cleanup, and charts capped to the latest 1,500 returned points.

## Existing endpoints used

| Method | Path                                 | Purpose                                                                           |
| ------ | ------------------------------------ | --------------------------------------------------------------------------------- |
| GET    | /health                              | API reachability; not a database connectivity test                                |
| GET    | /consumers                           | Identity list; risk, feeder, transformer, category, limit, offset                 |
| GET    | /cases                               | Paginated case list in the incoming backend version                               |
| GET    | /export/cases                        | Original case-list fallback, export, and verification of stored consumer analysis |
| GET    | /cases/{consumer_id}                 | Stored case assessment                                                            |
| PATCH  | /cases/{consumer_id}/status          | Status and note update                                                            |
| GET    | /consumers/{consumer_id}/consumption | Actual consumption                                                                |
| GET    | /consumers/{consumer_id}/baseline    | Stored baseline points                                                            |
| GET    | /feeders                             | Feeder identities                                                                 |
| GET    | /feeders/summary                     | Stored feeder summaries with optional feeder_id                                   |
| GET    | /alerts                              | Latest 1,000 persisted alerts                                                     |
| POST   | /readings                            | Exact ReadingIn input; ReadingAck stored/queued flags                             |
| GET    | /export/cases/{consumer_id}/pdf      | Case report                                                                       |

No GET /readings, fabricated WebSocket, direct SQLite connection, or substitute backend is used. The original repository had no mounted WebSocket route.

## Data integrity and ML

ML model is not implemented/integrated by this frontend. The dashboard is prepared for the existing Detection contract and displays an explicit unavailable state instead of fabricated predictions.

Case records are displayed only when returned by a case API. ReadingAck does not establish processing completion or detection. Existing cases are not presented as analysis of the latest simulated reading.

A concurrent backend merge added model files and API defaults during this work; that engine was neither implemented nor validated here. Its health endpoint has fixed `database` and `fuzzy_engine` strings, which are not treated as live telemetry.

The incoming consumer endpoints synthesize risk/status/anomaly values for consumers without cases. The frontend verifies these fields against persisted case exports. The incoming dashboard trend/risk and feeder-loss functions also contain generated fallbacks, so those endpoints are deliberately unused. Baseline overlays use only the dedicated baseline endpoint, not the consumption response's fallback baseline. The consumption API converts null kWh to zero; the chart discloses this upstream limitation.

## Verification

```powershell
npm run build
npm run lint
npm test
npm run test:browser
npm run test:integration
```

Browser tests require Chrome, the Vite server on port 5173, and the existing backend on port 8000. They use live endpoints and abort real network requests for the unavailable-state check; they do not fabricate API responses. Component tests exercise empty/loading/unavailable states without creating database records.

- Production build passed; Three.js is lazy-loaded, with a ~134 KB gzip chunk (Vite reports a >500 KB uncompressed warning).
- Lint passed with no warnings.
- 11 contract/component tests passed.
- Browser tests cover landing interaction, all console routes, mobile layout/navigation, connection failures, polling, and invalid ReadingIn validation.
- Invalid POST /readings returned HTTP 422.
- Normal backend startup could not be validated without changing the database: startup attempted missing-table creation. Read-only diagnostics used `--lifespan off`, which intentionally does not test queue processing.
- Both original database files were compared byte-for-byte to Git and remained unchanged by this work.

## Integration blockers

The supplied database does not have the tables expected by the API (`consumers`, `feeders`, `cases`, `alerts`, etc.). Read-only diagnostics returned HTTP 200 for /health and HTTP 500 for data endpoints in both the original and merged backend versions.

Therefore populated consumer/detail charts, baseline charts, case updates/PDF, feeder summaries, stored reading success, duplicate-reading acknowledgements, and end-to-end refreshed ingestion could not be verified against real records. No records, schema, fixtures, or alternate database were created to hide this blocker.

Full case event history, queue depth, processing completion, and reliable live database/model health are not exposed. Transformer input/metered measurements are not exposed through a trustworthy measurement endpoint. Production API URL/proxy configuration is deployment-specific.

The inherited Tailwind 3 dependency tree reports five high-severity development dependency advisories. No forced major-version upgrade was performed.

## Scope and concurrent work

The initial Git status was clean. This task changed only dashboard files. During testing, an external merge committed the frontend work and brought in backend/model changes; those incoming changes were preserved. Later backend source edits, bytecode changes, and test artifacts appeared externally and were not cleaned up or overwritten. A final repository-wide diff therefore includes unrelated work and must not be described as dashboard-only.

See [FILES.md](FILES.md) for the frontend file manifest.
