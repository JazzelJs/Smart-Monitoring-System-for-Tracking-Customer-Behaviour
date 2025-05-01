import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import api from '../api';
import Navbar from '../components/Navbar';

export default function HomePage() {
  const navigate = useNavigate();
  const [seatSummary, setSeatSummary] = useState(null);
  const [customerStats, setCustomerStats] = useState(null);
  const [chairs, setChairs] = useState({});
  const [peakStats, setPeakStats] = useState(null);

  useEffect(() => {
    api.get('/analytics/seats/summary/').then(res => setSeatSummary(res.data));
    api.get('/analytics/customers/').then(res => setCustomerStats(res.data));
    api.get('/chair-occupancy/').then(res => setChairs(res.data.chairs || {}));
    api.get('/analytics/peak-hours/').then(res => setPeakStats(res.data));
  }, []);

  const occupiedCount = Object.values(chairs).filter(seat => seat.status === 'occupied').length;
  const totalCount = Object.values(chairs).length;

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Navbar */}
      <Navbar/>

      {/* Main Content */}
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-8">Overview - Ngopi Pintar</h1>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <Card 
            title="Occupied Seats" 
            value={`${occupiedCount} / ${totalCount}`} 
            subtitle="Currently" 
            onArrowClick={() => navigate('/analytics/seats')} 
          />
          <Card 
            title="Average Seating Time" 
            value={seatSummary?.average_duration ? `${Math.floor(seatSummary.average_duration / 60)} H ${seatSummary.average_duration % 60} M` : '-'} 
            subtitle="During the last month" 
            onArrowClick={() => navigate('/analytics/seats')} 
          />
          <Card 
            title="Peak Hours" 
            value={peakStats?.peak_hour || '-'} 
            subtitle="This Month" 
            onArrowClick={() => navigate('/analytics/peak-hour')} 
          />
          <Card 
            title="Returning Customers" 
            value={`${customerStats?.returning_customers_percentage || 0}%`} 
            subtitle="This Month" 
            onArrowClick={() => navigate('/analytics/customer')} 
          />
        </div>

        {/* Live Video Feeds */}
        <div>
          <h2 className="text-xl font-bold mb-4">Live Video Feeds</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((_, i) => (
              <div key={i} className="bg-gray-300 h-48 rounded flex items-center justify-center">
                <button className="text-white bg-black rounded-full p-2">▶</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function Card({ title, value, subtitle, onArrowClick }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow flex flex-col justify-between">
      <div>
        <p className="text-sm text-gray-500">{title}</p>
        <h2 className="text-3xl font-bold text-orange-500">{value}</h2>
        <p className="text-xs text-gray-400">{subtitle}</p>
      </div>
      <div className="flex justify-end mt-4">
        <button onClick={onArrowClick} className="text-orange-500 text-sm hover:underline">↗</button>
      </div>
    </div>
  );
}
