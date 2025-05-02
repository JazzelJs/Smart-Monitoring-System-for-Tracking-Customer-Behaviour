import React, { useEffect, useState } from "react";
import api from "../api";
import AnalyticsTabs from '../components/AnalyticsTabs';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

export default function PeakHourAnalytics() {
  const [stats, setStats] = useState(null);
  const [trafficData, setTrafficData] = useState([]);
  const [mode, setMode] = useState("daily");

  useEffect(() => {
    api.get("/analytics/peak-hours/")
      .then(res => setStats(res.data))
      .catch(err => {
        console.error("Failed to fetch peak hour stats", err);
        setStats(null);
      });
  }, []);

  useEffect(() => {
    api.get(`/analytics/visitor-traffic/?mode=${mode}`)
      .then(res => setTrafficData(res.data))
      .catch(err => {
        console.error("Failed to fetch visitor traffic", err);
        setTrafficData([]);
      });
  }, [mode]);

  const allZero = trafficData.every(d => d.count === 0);

  return (
    <div className="bg-gray-50 font-sans">
      {/* Tabs */}
      <AnalyticsTabs activeTab="PeakHour" />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-10">
        <Card label="Peak Time" value={stats?.peak_hour || "-"} sub={`${stats?.peak_hour_visitors || 0} Visitors`} />
        <Card label="Peak Day" value={stats?.peak_day || "-"} sub={`${stats?.peak_day_visitors || 0} Visitors`} />
        <Card label="Average Daily Visitors" value={stats?.avg_daily_visitors || 0} sub="Last 7 Days" />
        <Card
          label="Current Occupancy"
          value={stats ? `${stats.occupancy_percent}%` : "-"}
          sub={stats ? `${stats.occupied_seats}/${stats.total_seats} seats occupied` : "-"}
        />
      </div>

      {/* Visitor Chart */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-lg font-semibold mb-4">Visitor Traffic</h2>
        <div className="flex gap-4 mb-4">
          {["daily", "weekly", "monthly"].map((item) => (
            <button
              key={item}
              onClick={() => setMode(item)}
              className={`${mode === item ? "bg-black text-white" : "bg-gray-100 text-gray-600"} px-3 py-1 rounded`}
            >
              {item.charAt(0).toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>

        {/* Chart or fallback */}
        {trafficData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-gray-400 italic">Loading...</div>
        ) : allZero ? (
          <div className="h-64 flex items-center justify-center text-gray-400 italic">No visitors recorded yet.</div>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trafficData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

function Card({ label, value, sub }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow">
      <p className="text-sm text-gray-500 mb-2">{label}</p>
      <h2 className="text-2xl font-bold text-orange-500">{value}</h2>
      <p className="text-xs text-gray-400">{sub}</p>
    </div>
  );
}
