import React, { useEffect, useState } from 'react';
import api from '../api';
import AnalyticsTabs from '../components/AnalyticsTabs';

export default function CustomerAnalytics() {
  const [stats, setStats] = useState(null);
  const [customers, setCustomers] = useState([]);

  useEffect(() => {
    api.get('/analytics/customers/').then(res => {
      setStats(res.data);
    });

    api.get('/entry-events/?event_type=enter').then(res => {
      setCustomers(res.data);
    });
  }, []);

  

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-6">Analytics</h1>

      {/* Tabs */}
      <AnalyticsTabs activeTab="Customers" />

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 my-10">
        <Card title="First Time Customers" value={stats?.first_time_customers || 0} />
        <Card title="Returning Customers" value={stats?.returning_customers || 0} />
        <Card title="Retention Rate" value={`${stats?.retention_rate || 0}%`} />
        <Card title="Average Visits" value={stats?.average_visits || 0} />
      </div>

      {/* Customer Table */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-semibold mb-4">Recent Visitors</h2>
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="text-gray-500 border-b">
              <th className="py-2">Visitor</th>
              <th>First Seen</th>
              <th>Last Seen</th>
              <th>Visit Count</th>
              <th>Average Stay</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c, i) => (
              <tr key={i} className="border-b">
                <td className="py-2">{c.customer?.face_id || 'Unknown'}</td>
                <td>{c.customer?.first_visit || '-'}</td>
                <td>{c.customer?.last_visit || '-'}</td>
                <td>{c.customer?.visit_count || 0}</td>
                <td>{c.customer?.average_stay || 0}m</td>
                <td>
                  <span className={`px-2 py-1 rounded text-white ${c.customer?.status === 'returning' ? 'bg-orange-500' : 'bg-black'}`}>
                    {c.customer?.status || 'Unknown'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Card({ title, value }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <p className="text-sm text-gray-500 mb-2">{title}</p>
      <h2 className="text-3xl font-bold text-orange-500">{value}</h2>
      <p className="text-xs text-gray-400">This Month</p>
    </div>
  );
}
