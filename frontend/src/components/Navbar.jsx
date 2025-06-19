import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();
  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };
  return (
    <nav className="flex justify-between items-center bg-black text-white px-6 py-4">
      <div className="flex gap-6">
        <NavItem to="/dashboard" label="Dashboard" />
        <NavItem to="/analytics/seats" label="Live Detections" />
        <NavItem to="/historical-data" label="Historical Data" />
        <NavItem to="/activity-log" label="Activity Log" />
        <NavItem to="/settings/manage-camera" label="Settings" />
      </div>
      <button onClick={handleLogout} className="text-orange-400 hover:text-orange-600">Logout</button>
    </nav>
  );
}
function NavItem({ to, label }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        isActive
          ? "text-orange-400 font-semibold"
          : "hover:underline"
      }
    >
      {label}
    </NavLink>
  );
}
