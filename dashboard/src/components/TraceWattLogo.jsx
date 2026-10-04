import React from "react";

/**
 * TraceWatt Unified Brand Logo Component.
 * 
 * Visual Concept:
 * Merges energy grid topology with an analytical trace vector and 
 * an illuminated anomaly focal point.
 * 
 * Props:
 * - variant: "full" | "mark" | "compact" (default: "full")
 * - theme: "auto" | "dark" | "light" | "monochrome" (default: "auto")
 * - size: "sm" | "md" | "lg" | "xl" | number (default: "md")
 * - showTagline: boolean (default: false)
 * - className: string
 */
export default function TraceWattLogo({
  variant = "full",
  theme = "auto",
  size = "md",
  showTagline = false,
  className = "",
  style = {},
  ...props
}) {
  // Height and scale mappings
  const heightMap = {
    sm: 26,
    md: 34,
    lg: 42,
    xl: 52,
  };
  const markSizeMap = {
    sm: 24,
    md: 32,
    lg: 38,
    xl: 48,
  };

  const height = typeof size === "number" ? size : heightMap[size] || 34;
  const markSize = typeof size === "number" ? size : markSizeMap[size] || 32;

  // Color profiles
  const isLight = theme === "light";
  const isMono = theme === "monochrome";

  const primaryTextFill = isMono
    ? "currentColor"
    : isLight
    ? "#0F172A"
    : "var(--text, #F1F5F9)";

  const wattGradientId = `tw_watt_grad_${theme}_${variant}`;
  const traceGradientId = `tw_trace_grad_${theme}_${variant}`;
  const bgGradientId = `tw_bg_grad_${theme}_${variant}`;
  const glowFilterId = `tw_glow_${theme}_${variant}`;

  // Pure Symbol Mark
  const renderMark = (s) => (
    <svg
      width={s}
      height={s}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="tracewatt-mark-svg shrink-0"
      aria-hidden="true"
    >
      <defs>
        <linearGradient
          id={bgGradientId}
          x1="0"
          y1="0"
          x2="48"
          y2="48"
          gradientUnits="userSpaceOnUse"
        >
          <stop
            offset="0%"
            stopColor={isLight ? "#F8FAFC" : "#0F172A"}
          />
          <stop
            offset="100%"
            stopColor={isLight ? "#E2E8F0" : "#020617"}
          />
        </linearGradient>

        <linearGradient
          id={traceGradientId}
          x1="6"
          y1="6"
          x2="42"
          y2="42"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0%" stopColor={isMono ? "currentColor" : "#38BDF8"} />
          <stop offset="50%" stopColor={isMono ? "currentColor" : "#00E5FF"} />
          <stop offset="100%" stopColor={isMono ? "currentColor" : "#10B981"} />
        </linearGradient>

        {!isMono && (
          <filter id={glowFilterId} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="1.5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        )}
      </defs>

      {/* Frame / Tile Container */}
      <rect
        x="2"
        y="2"
        width="44"
        height="44"
        rx="10"
        fill={`url(#${bgGradientId})`}
        stroke={isLight ? "#CBD5E1" : "#1E293B"}
        strokeWidth="1.2"
      />

      {/* Subtle Grid Radar Matrix */}
      <circle
        cx="24"
        cy="24"
        r="14"
        stroke={isLight ? "#94A3B8" : "#334155"}
        strokeWidth="0.8"
        strokeDasharray="1.5 2.5"
        opacity="0.6"
      />

      {/* Grid Network Nodes */}
      <circle cx="14" cy="14" r="2" fill={isMono ? "currentColor" : "#38BDF8"} />
      <circle cx="34" cy="14" r="2" fill={isMono ? "currentColor" : "#00E5FF"} />
      <circle cx="14" cy="34" r="2" fill={isMono ? "currentColor" : "#059669"} />

      {/* Active Diagnostic Trace Line */}
      <path
        d="M14 14 H34 L24 24 V33"
        stroke={`url(#${traceGradientId})`}
        strokeWidth="2.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        filter={isMono ? undefined : `url(#${glowFilterId})`}
      />
      <path
        d="M16 33 L24 25 L32 33"
        stroke={`url(#${traceGradientId})`}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Focal Anomaly Detection Pulse */}
      <circle
        cx="24"
        cy="24"
        r="3.2"
        fill={isLight ? "#0F172A" : "#FFFFFF"}
        filter={isMono ? undefined : `url(#${glowFilterId})`}
      />
      <circle
        cx="24"
        cy="24"
        r="1.6"
        fill={isLight ? "#FFFFFF" : "#00E5FF"}
      />
      <circle
        cx="32"
        cy="33"
        r="2.2"
        fill={isMono ? "currentColor" : "#10B981"}
        filter={isMono ? undefined : `url(#${glowFilterId})`}
      />
    </svg>
  );

  if (variant === "mark") {
    return (
      <span
        className={`tracewatt-logo-mark inline-flex items-center justify-center ${className}`}
        style={{ display: "inline-flex", lineHeight: 0, ...style }}
        role="img"
        aria-label="TraceWatt Mark"
        {...props}
      >
        {renderMark(markSize)}
      </span>
    );
  }

  // Full / Compact Logo with Wordmark
  return (
    <div
      className={`tracewatt-logo-container inline-flex items-center gap-2.5 select-none ${className}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        lineHeight: 1,
        textDecoration: "none",
        ...style,
      }}
      role="img"
      aria-label="TraceWatt"
      {...props}
    >
      <defs style={{ display: "none" }}>
        <linearGradient
          id={wattGradientId}
          x1="0%"
          y1="0%"
          x2="100%"
          y2="100%"
          gradientUnits="userSpaceOnUse"
        >
          <stop
            offset="0%"
            stopColor={isMono ? "currentColor" : isLight ? "#0284C7" : "#00E5FF"}
          />
          <stop
            offset="100%"
            stopColor={isMono ? "currentColor" : isLight ? "#059669" : "#10B981"}
          />
        </linearGradient>
      </defs>

      {renderMark(markSize)}

      <div className="flex flex-col justify-center">
        <div
          style={{
            fontFamily:
              'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            fontSize: `${Math.round(height * 0.58)}px`,
            fontWeight: 700,
            letterSpacing: "-0.035em",
            color: primaryTextFill,
            display: "flex",
            alignItems: "center",
            lineHeight: 1,
          }}
        >
          <span>Trace</span>
          <span
            style={{
              background: isMono
                ? undefined
                : isLight
                ? "linear-gradient(135deg, #0284C7 0%, #059669 100%)"
                : "linear-gradient(135deg, #00E5FF 0%, #10B981 100%)",
              WebkitBackgroundClip: isMono ? undefined : "text",
              WebkitTextFillColor: isMono ? undefined : "transparent",
              color: isMono ? "currentColor" : "#10B981",
              fontWeight: 800,
              marginLeft: "1px",
            }}
          >
            Watt
          </span>
        </div>

        {showTagline && (
          <span
            style={{
              fontFamily:
                'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
              fontSize: `${Math.max(9, Math.round(height * 0.24))}px`,
              fontWeight: 600,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              color: isLight ? "#64748B" : "#94A3B8",
              marginTop: "2px",
            }}
          >
            Energy Intelligence
          </span>
        )}
      </div>
    </div>
  );
}
