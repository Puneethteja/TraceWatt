# TraceWatt UX Audit & Redesign Plan

## 1. Landing Page
### Problem
Very text-heavy, abstract explanations. Lacks a strong visual hook.
### User question
What is TraceWatt and how does it help utility operations?
### Solution
A sleek, dark-themed hero section utilizing glassmorphism and the `GridScene`. Clean cards for features rather than text lists.
### Action
"Launch Mission Console" CTA clearly visible.

## 2. Mission Console Overview
### Problem
Currently a generic stat dump with "ML not connected" warnings scattered around.
### User question
What is the current health of my grid and what needs immediate attention?
### Solution
A dashboard layout:
- Top: KPI cards (Total Consumers, Open Cases, Critical Alerts).
- Middle: A chart showing consumption/anomalies over time or distribution of risk.
- Bottom: Recent Critical Alerts / Highest Priority Cases list.
### Action
Clicking an alert/case goes directly to the Consumer Detail view.

## 3. Consumer Explorer
### Problem
Standard HTML table, lacks visual hierarchy.
### User question
How do I find high-risk consumers quickly?
### Solution
A refined data grid with color-coded badges for Risk (High=Red, Medium=Yellow, Low=Green). Clearer typography.

## 4. Case / Consumer Detail
### Problem
Too much raw text for Evidence and Counter-evidence. Doesn't feel like an "AI Assessment".
### User question
Why was this flagged and what should I do?
### Solution
- Top: Telemetry/Consumption chart.
- Bottom Left: AI Assessment panel (Cause, Risk, Confidence gauge).
- Bottom Right: Evidence list with icons (Check/Cross).
- Action Bar: Update status, Export PDF.

## 5. Visual System (Theme)
- **Palette**: Sleek dark mode (Navy/Charcoal background, glowing accent colors like Cyan/Electric Blue for tech/AI, Red/Amber for alerts).
- **Typography**: Inter / Roboto (modern sans-serif).
- **Components**: Glassmorphism (translucent panels with blur), subtle borders, vibrant gradients for data visualization.

## 6. Integration
- Remove all "ML not connected" fake text. 
- Use the provided backend schemas (`CaseOut`, `Detection`, `ConsumerSummary`).
- Connect directly to the existing APIs without fabricating data.
