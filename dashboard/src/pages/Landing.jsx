import { lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import TraceWattLogo from "../components/TraceWattLogo";
const GridScene = lazy(() => import("../components/GridScene"));

export default function Landing() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Link className="brand" to="/" aria-label="TraceWatt Home">
          <TraceWattLogo variant="full" size="lg" theme="auto" showTagline />
        </Link>
        <div>
          <a href="#how-it-works">How it works</a>
          <a href="#why-it-matters">Insights</a>
          <Link className="button primary" to="/console">
            Mission Console ↗
          </Link>
          <Link className="button secondary" to="/lineman" style={{ marginLeft: '10px' }}>
            Lineman Dashboard ↗
          </Link>
        </div>
      </nav>
      <main>
        {/* HERO SECTION */}
        <section className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span className="dot" /> TRACEWATT ENERGY INTELLIGENCE
            </div>
            <h1>
              Find the problem.<br />
              Understand the cause.
            </h1>
            <p>
              TraceWatt helps utilities identify unusual electricity consumption, understand why it happened, and prioritize what needs attention.
            </p>
            <div className="actions">
              <a className="button primary" href="#how-it-works">
                Explore TraceWatt ↓
              </a>
              <Link className="button secondary" to="/console">
                Open Mission Console ↗
              </Link>
            </div>
          </div>
          <div className="hero-visual">
            <div className="visual-top">
              <span>POWER GRID INVESTIGATION</span>
              <span className="badge">LIVE MONITORING</span>
            </div>
            <Suspense fallback={<div className="scene" />}>
              <GridScene conceptual />
            </Suspense>
            <div className="visual-bottom" style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'stretch' }}>
               <div style={{display:'flex', justifyContent:'space-between', color: '#FFCC00'}}>
                 <span>Unusual consumption detected</span>
                 <span>Priority: High</span>
               </div>
               <div style={{color: '#dce6dc'}}>Possible cause: Needs investigation</div>
            </div>
          </div>
        </section>

        {/* 01 THE PROBLEM */}
        <section className="landing-section">
          <div className="section-intro">
            <div className="eyebrow">THE PROBLEM</div>
            <h2>Not every unusual reading means theft.</h2>
            <p>
              The challenge is not simply finding what looks unusual. The challenge is understanding why.
            </p>
          </div>
          <div className="problem-grid">
             <div className="problem-box">
                <h3>UNUSUAL CONSUMPTION</h3>
                <div className="arrow-list">
                  <div>→ Theft?</div>
                  <div>→ Meter issue?</div>
                  <div>→ Communication problem?</div>
                  <div>→ Seasonal change?</div>
                  <div>→ Legitimate behavior?</div>
                </div>
             </div>
             <div className="problem-text">
                <p>Electricity consumption can change because of unusual consumer behavior, meter problems, communication issues, seasonal changes, legitimate reductions, or possible theft and tampering.</p>
             </div>
          </div>
        </section>

        {/* 02 THE IDEA */}
        <section className="landing-section gray-bg">
          <div className="section-intro">
            <div className="eyebrow">THE IDEA</div>
            <h2>From a suspicious signal to a clear investigation.</h2>
            <p>
              TraceWatt brings consumption history, consumer behavior and network information together to help investigators understand unusual electricity patterns.
            </p>
          </div>
          <div className="idea-cards">
            <div className="idea-card">
              <div className="idea-num">01</div>
              <h3>DETECT</h3>
              <p>Find unusual behavior.</p>
            </div>
            <div className="idea-card">
              <div className="idea-num">02</div>
              <h3>UNDERSTAND</h3>
              <p>Look at the context behind it.</p>
            </div>
            <div className="idea-card">
              <div className="idea-num">03</div>
              <h3>ACT</h3>
              <p>Prioritize what deserves attention.</p>
            </div>
          </div>
        </section>

        {/* 03 HOW IT WORKS */}
        <section id="how-it-works" className="landing-section workflow-section">
          <div className="section-intro">
            <div className="eyebrow">HOW IT WORKS</div>
            <h2>A simple, clear path to truth.</h2>
          </div>
          <div className="workflow workflow-new">
             <article><span>01</span><h3>WATCH</h3><p>Monitor consumption patterns.</p></article>
             <article><span>02</span><h3>COMPARE</h3><p>Compare behavior with expected patterns.</p></article>
             <article><span>03</span><h3>UNDERSTAND</h3><p>Look at the surrounding context.</p></article>
             <article><span>04</span><h3>EXPLAIN</h3><p>Show why the case was flagged.</p></article>
             <article><span>05</span><h3>PRIORITIZE</h3><p>Identify what deserves attention first.</p></article>
          </div>
        </section>

        {/* 04 WHAT YOU SEE */}
        <section className="landing-section">
          <div className="section-intro">
            <div className="eyebrow">WHAT YOU SEE</div>
            <h2>Everything you need for an investigation.</h2>
          </div>
          <div className="explain-grid">
            <article>
              <span style={{fontSize: '20px', display: 'block', marginBottom: '10px'}}>🔍</span>
              <h3>WHY WAS THIS FLAGGED?</h3>
              <p>See the signals behind an unusual case.</p>
            </article>
            <article>
              <span style={{fontSize: '20px', display: 'block', marginBottom: '10px'}}>⚖️</span>
              <h3>WHY NOT THEFT?</h3>
              <p>See evidence that may point toward another explanation.</p>
            </article>
            <article>
              <span style={{fontSize: '20px', display: 'block', marginBottom: '10px'}}>📊</span>
              <h3>ESTIMATED IMPACT</h3>
              <p>Understand the potential energy and financial impact.</p>
            </article>
            <article>
              <span style={{fontSize: '20px', display: 'block', marginBottom: '10px'}}>📍</span>
              <h3>WHERE IS THE PROBLEM?</h3>
              <p>See suspicious patterns across feeders and consumers.</p>
            </article>
          </div>
        </section>

        {/* 05 WHY IT MATTERS */}
        <section id="why-it-matters" className="landing-section gray-bg">
          <div className="section-intro">
            <div className="eyebrow">WHY IT MATTERS</div>
            <h2>Less guessing.<br/>Better investigation.<br/>Clearer decisions.</h2>
          </div>
          <div className="before-after">
            <div className="ba-card before">
              <h3>BEFORE TRACEWATT</h3>
              <ul>
                <li>Too many unusual readings</li>
                <li className="arr">↓</li>
                <li>Manual investigation</li>
                <li className="arr">↓</li>
                <li>Unclear cause</li>
                <li className="arr">↓</li>
                <li>Time-consuming prioritization</li>
              </ul>
            </div>
            <div className="ba-card after">
              <h3>WITH TRACEWATT</h3>
              <ul>
                <li>Unusual pattern</li>
                <li className="arr">↓</li>
                <li>Context</li>
                <li className="arr">↓</li>
                <li>Explanation</li>
                <li className="arr">↓</li>
                <li>Priority</li>
                <li className="arr">↓</li>
                <li>Action</li>
              </ul>
            </div>
          </div>
        </section>

        {/* LIVE SCENARIO */}
        <section className="landing-section">
           <div className="section-intro center">
             <div className="eyebrow" style={{justifyContent: 'center'}}>LIVE SIMULATION</div>
             <h2>See TraceWatt respond.</h2>
             <p>Try a situation and see how the system handles different scenarios.</p>
           </div>
           <div className="scenario-cards">
             <Link to="/console/simulation" className="scenario-card">
               <h4>NORMAL</h4>
               <p>Scenario → New reading → Expected behavior → Logged</p>
             </Link>
             <Link to="/console/simulation" className="scenario-card">
               <h4>THEFT / TAMPERING</h4>
               <p>Scenario → New reading → Unusual behavior → Investigation case</p>
             </Link>
             <Link to="/console/simulation" className="scenario-card">
               <h4>METER ISSUE</h4>
               <p>Scenario → New reading → Hardware anomaly → Maintenance flagged</p>
             </Link>
             <Link to="/console/simulation" className="scenario-card">
               <h4>COMMUNICATION ISSUE</h4>
               <p>Scenario → Missing reading → Network anomaly → Status updated</p>
             </Link>
           </div>
        </section>

        {/* 06 READY TO INVESTIGATE */}
        <section className="landing-cta">
          <div className="eyebrow">READY TO INVESTIGATE</div>
          <h2>
            Don't just find what looks wrong.<br/>
            Understand what happened.
          </h2>
          <p>
            Explore TraceWatt and turn unusual electricity patterns into clearer investigation decisions.
          </p>
          <div className="actions justify-center" style={{marginTop: '30px'}}>
            <Link className="button primary" to="/console">
              Open Mission Console ↗
            </Link>
            <a className="button secondary" href="#how-it-works">
              Explore the Platform
            </a>
          </div>
        </section>
      </main>
      <footer>
        <Link className="brand" to="/" aria-label="TraceWatt Home">
          <TraceWattLogo variant="full" size="md" theme="auto" />
        </Link>
        <span>Energy intelligence. Human judgment.</span>
        <Link to="/console/health">System health ↗</Link>
      </footer>
    </div>
  );
}
