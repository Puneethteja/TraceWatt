import { lazy, Suspense, useState } from "react";
import { Link } from "react-router-dom";
const GridScene = lazy(() => import("../components/GridScene"));
const causes = [
  [
    "Communication Failure",
    "Missing or interrupted communication can explain an unusual pattern before consumption itself becomes suspect.",
  ],
  [
    "Meter Malfunction",
    "Meter and electrical signals can help identify possible measurement problems.",
  ],
  [
    "Seasonal Variation",
    "Historical patterns provide context for recurring changes in demand.",
  ],
  [
    "Legitimate Abnormal",
    "A change in activity can be unusual and still have a legitimate explanation.",
  ],
  [
    "Theft / Tampering",
    "Persistent unexplained deviation warrants investigation, supported by evidence and counter-evidence.",
  ],
  [
    "Normal behavior",
    "A signal may be consistent with its available historical context.",
  ],
  [
    "Requires Review",
    "Insufficient or conflicting evidence calls for human review.",
  ],
];
const steps = [
  ["Meter / historical data", "Start with the electricity record."],
  ["Data validation", "Check the incoming measurements."],
  ["Feature engineering", "Organize meaningful signals."],
  ["Baseline comparison", "Compare against available expectations."],
  ["Anomaly detection", "Identify a deviation for review."],
  ["Cause analysis", "Explore competing explanations."],
  ["Evidence + counter-evidence", "Show both sides of the assessment."],
  ["Loss estimation", "Quantify impact where inputs exist."],
  ["Priority", "Focus investigator attention."],
  ["Investigation / action", "Let people make the final call."],
];
export default function Landing() {
  const [selected, setSelected] = useState(0);
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Link className="brand" to="/">
          <span className="brand-mark">ϟ</span>TraceWatt
          <span className="brand-tag">ENERGY INTELLIGENCE</span>
        </Link>
        <div>
          <a href="#approach">Our approach</a>
          <a href="#workflow">How it works</a>
          <Link className="button primary" to="/console">
            Open Mission Console ↗
          </Link>
        </div>
      </nav>
      <main>
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="dot" /> CLARITY BEYOND THE ANOMALY
            </div>
            <h1>
              Find the cause.
              <br />
              <em>Follow the evidence.</em>
            </h1>
            <h2>
              Explainable electricity anomaly detection that finds the cause,
              not just the culprit.
            </h2>
            <p>
              TraceWatt brings consumption patterns, meter signals, and
              communication context into one investigation workspace. Understand
              what changed—and what deserves a closer look.
            </p>
            <div className="actions">
              <Link className="button primary" to="/console">
                Open Mission Console <span>↗</span>
              </Link>
              <a className="button secondary" href="#workflow">
                Explore How It Works ↓
              </a>
            </div>
            <div className="hero-foot">
              <span>CONSUMPTION</span>
              <span>CONTEXT</span>
              <span>EXPLAINABILITY</span>
            </div>
          </div>
          <div className="hero-visual">
            <div className="visual-top">
              <span>THE CONNECTED GRID</span>
              <span className="badge">Concept visualization</span>
            </div>
            <Suspense fallback={<div className="scene" />}>
              <GridScene conceptual />
            </Suspense>
            <div className="visual-bottom">
              <span>Electricity data → Understanding</span>
              <strong>TraceWatt ↗</strong>
            </div>
          </div>
        </section>
        <section className="principle">
          <span>THE PRINCIPLE</span>
          <p>
            An anomaly is a starting point.
            <br />
            <strong>Not a verdict.</strong>
          </p>
          <div>
            A drop in consumption can have many explanations. Good investigation
            asks why before assigning blame.
          </div>
        </section>
        <section id="approach" className="landing-section">
          <div className="section-intro">
            <div className="eyebrow">01 / UNDERSTAND THE SIGNAL</div>
            <h2>
              One unusual reading.
              <br />
              More than one explanation.
            </h2>
            <p>
              Explore possible causes. This is an investigation concept, not an
              implemented ML decision tree.
            </p>
          </div>
          <div className="cause-layout">
            <div
              className="cause-list"
              role="tablist"
              aria-orientation="vertical"
              aria-label="Possible explanations"
            >
              {causes.map(([name], i) => (
                <button
                  role="tab"
                  tabIndex={selected === i ? 0 : -1}
                  onKeyDown={(e) => {
                    if (
                      ["ArrowDown", "ArrowUp", "Home", "End"].includes(e.key)
                    ) {
                      e.preventDefault();
                      const next =
                        e.key === "Home"
                          ? 0
                          : e.key === "End"
                            ? causes.length - 1
                            : (selected +
                                (e.key === "ArrowDown" ? 1 : -1) +
                                causes.length) %
                              causes.length;
                      setSelected(next);
                      document.getElementById("cause-" + next)?.focus();
                    }
                  }}
                  aria-selected={selected === i}
                  aria-controls="cause-description"
                  id={"cause-" + i}
                  key={name}
                  onClick={() => setSelected(i)}
                  className={selected === i ? "selected" : ""}
                >
                  <span>{String(i + 1).padStart(2, "0")}</span>
                  {name}
                  <span>↗</span>
                </button>
              ))}
            </div>
            <div
              className="cause-detail"
              id="cause-description"
              role="tabpanel"
              aria-labelledby={"cause-" + selected}
            >
              <span className="signal-orbit">⌁</span>
              <div className="eyebrow">
                ABNORMAL CONSUMPTION → CONTEXT → REVIEW
              </div>
              <h3>{causes[selected][0]}</h3>
              <p>{causes[selected][1]}</p>
              <div className="notice">
                A possible explanation is not a confirmed finding.
              </div>
            </div>
          </div>
        </section>
        <section id="workflow" className="landing-section workflow-section">
          <div className="section-intro">
            <div className="eyebrow">02 / FROM SIGNAL TO ACTION</div>
            <h2>
              A transparent path
              <br />
              to an informed decision.
            </h2>
            <p>
              The intended TraceWatt workflow. Ingestion and backend records are fully accessible in the
              console, powered by ML anomaly detection.
            </p>
          </div>
          <div className="workflow">
            {steps.map(([name, desc], i) => (
              <article key={name}>
                <span>{String(i + 1).padStart(2, "0")} ↗</span>
                <h3>{name}</h3>
                <p>{desc}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="landing-section">
          <div className="section-intro">
            <div className="eyebrow">03 / BUILT FOR SCRUTINY</div>
            <h2>
              Every conclusion
              <br />
              should show its working.
            </h2>
          </div>
          <div className="explain-grid">
            {[
              ["Evidence", "Signals supporting a possible cause."],
              ["Counter-evidence", "Signals that challenge the explanation."],
              [
                "Confidence",
                "How strongly the available analysis supports a classification.",
              ],
              [
                "Estimated loss",
                "max(Baseline kWh − Actual kWh, 0) × Tariff. Only available backend values are shown.",
              ],
            ].map(([name, text]) => (
              <article key={name}>
                <span>↗</span>
                <h3>{name}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="landing-cta">
          <div className="eyebrow">04 / THE SAME INGESTION PATH</div>
          <h2>
            From a meter signal
            <br />
            to your mission console.
          </h2>
          <p>
            Send an explicit input simulation through the same ingestion API a
            future smart meter or IoT device would use. Watch the
            acknowledgement, then explore the stored consumption record.
          </p>
          <Link className="button primary" to="/console/simulation">
            Explore live ingestion ↗
          </Link>
          <small>Real API. Explicit inputs. No fabricated predictions.</small>
        </section>
      </main>
      <footer>
        <Link className="brand" to="/">
          <span className="brand-mark">ϟ</span>TraceWatt
        </Link>
        <span>Energy intelligence. Human judgment.</span>
        <Link to="/console/health">System health ↗</Link>
      </footer>
    </div>
  );
}
