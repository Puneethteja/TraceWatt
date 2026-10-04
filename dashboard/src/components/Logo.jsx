import React from 'react';
import { Link } from 'react-router-dom';

/**
 * TraceWatt Logo Component
 * 
 * @param {string} variant - "full" | "mark"
 * @param {string} theme - "dark" | "light" | "auto" 
 * @param {string} className - Additional CSS classes
 */
export default function Logo({ variant = "full", theme = "auto", className = "", ...props }) {
  const isDark = theme === "dark";
  const textColor = isDark ? "text-white" : "text-gray-900";
  const markColor = isDark ? "text-white" : "text-slate-800";
  
  const mark = (
    <svg 
      viewBox="0 0 32 32" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg" 
      className={`w-8 h-8 ${markColor} shrink-0`}
      {...props}
    >
      {/* Outer Trace Arc */}
      <path 
        d="M16 4 A12 12 0 1 1 4 16" 
        stroke="currentColor" 
        strokeWidth="3.5" 
        strokeLinecap="round" 
      />
      {/* Watt Energy Spark */}
      <path 
        d="M18 8 L11 17 L16 17 L14 25 L23 14 L17 14 Z" 
        fill="#2563EB" 
      />
      {/* Anomaly/Detection Node */}
      <circle 
        cx="7.5" 
        cy="7.5" 
        r="3" 
        fill="#10B981" 
      />
    </svg>
  );

  if (variant === "mark") {
    return mark;
  }

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {mark}
      <span className={`font-bold tracking-tight text-xl ${textColor}`}>
        Trace<span className="text-blue-600">Watt</span>
      </span>
    </div>
  );
}
