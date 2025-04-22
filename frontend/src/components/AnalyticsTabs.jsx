// src/components/AnalyticsTabs.jsx

import { Link, useLocation } from 'react-router-dom';

export default function AnalyticsTabs() {
  const location = useLocation();

  const tabs = [
    { name: 'Seats', path: '/analytics/seats' },
    { name: 'Peak Hours', path: '/analytics/peak-hour' },
    { name: 'Customers', path: '/analytics/customers' },
  ];

  return (
    <div className="flex gap-6 text-lg mb-8">
      {tabs.map((tab) => {
        const isActive = location.pathname === tab.path;
        return (
          <Link
            key={tab.name}
            to={tab.path}
            className={`${
              isActive
                ? 'font-bold text-black bg-white px-2 py-1 rounded'
                : 'text-gray-400'
            }`}
          >
            {tab.name}
          </Link>
        );
      })}
    </div>
  );
}
