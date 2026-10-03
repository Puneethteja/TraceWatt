import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';

const NAV_ITEMS = [
  {
    name: 'Dashboard',
    path: '/',
    icon: (
      <svg className="w-4 h-4 mr-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
        />
      </svg>
    ),
  },
  {
    name: 'Consumers',
    path: '/consumers',
    icon: (
      <svg className="w-4 h-4 mr-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
  },
  {
    name: 'Feeders',
    path: '/feeders',
    icon: (
      <svg className="w-4 h-4 mr-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
  },
  {
    name: 'Alerts',
    path: '/alerts',
    icon: (
      <svg className="w-4 h-4 mr-2.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>
    ),
  },
];

export default function Layout({ alerts = [], clearAlerts }) {
  const location = useLocation();
  const alertCount = alerts.length;

  const getPageTitle = () => {
    const item = NAV_ITEMS.find((n) => n.path === location.pathname);
    return item ? item.name : 'TraceWatt';
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-900 overflow-hidden font-sans">
      {/* Clean Flat Sidebar */}
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col shrink-0">
        {/* Brand Header */}
        <div className="h-14 flex items-center px-5 border-b border-gray-200">
          <div className="flex items-center space-x-2.5">
            <div className="h-7 w-7 rounded bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
              TW
            </div>
            <div>
              <span className="text-sm font-semibold tracking-tight text-gray-900 block leading-tight">
                TraceWatt
              </span>
              <span className="text-[11px] text-gray-500 block leading-none">
                Theft Detection
              </span>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-3 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center px-4 py-2 text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? 'bg-gray-100 text-gray-900 border-l-2 border-blue-600'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50 border-l-2 border-transparent'
                }`
              }
            >
              {item.icon}
              <span className="flex-1">{item.name}</span>
              {item.name === 'Alerts' && alertCount > 0 && (
                <span className="bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-2">
                  {alertCount}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* System Status Footer */}
        <div className="p-3.5 border-t border-gray-200 bg-white text-xs">
          <div className="flex items-center justify-between text-gray-500">
            <span>Model Engine</span>
            <span className="text-green-600 flex items-center font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5"></span>
              Active
            </span>
          </div>
          <div className="text-gray-400 text-[11px] mt-0.5 font-mono">v1.0-iot-live</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Simple Flat Topbar */}
        <header className="h-14 bg-white border-b border-gray-200 px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <h1 className="text-sm font-semibold text-gray-900 tracking-tight">{getPageTitle()}</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-gray-100 text-gray-600 border border-gray-200">
              DISCOM Operations
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-xs text-gray-500 font-mono">Region: North Feeder</span>
            <div className="h-7 w-7 rounded bg-gray-100 border border-gray-200 flex items-center justify-center font-semibold text-xs text-gray-700">
              OP
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6 bg-gray-50">
          <Outlet context={{ alerts, clearAlerts }} />
        </main>
      </div>
    </div>
  );
}
