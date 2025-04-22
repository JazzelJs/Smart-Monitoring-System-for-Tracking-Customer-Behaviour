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

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <h1 className="text-4xl font-bold mb-6">Analytics</h1>

      {/* Tabs */}
      <div className="flex gap-6 text-lg mb-8">
        <AnalyticsTabs />
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 mb-10">
        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500 mb-2">Peak Time</p>
          <h2 className="text-2xl font-bold text-orange-500">{stats?.peak_hour || "-"}</h2>
          <p className="text-xs text-gray-400">{stats?.peak_hour_visitors || 0} Visitors</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500 mb-2">Peak Day</p>
          <h2 className="text-2xl font-bold text-orange-500">{stats?.peak_day || "-"}</h2>
          <p className="text-xs text-gray-400">{stats?.peak_day_visitors || 0} Visitors</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500 mb-2">Average Daily Visitors</p>
          <h2 className="text-2xl font-bold text-orange-500">{stats?.avg_daily_visitors || 0}</h2>
          <p className="text-xs text-gray-400">Last 7 Days</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500 mb-2">Current Occupancy</p>
          <h2 className="text-2xl font-bold text-orange-500">
            {stats ? `${stats.occupancy_percent}%` : "-"}
          </h2>
          <p className="text-xs text-gray-400">
            {stats ? `${stats.occupied_seats}/${stats.total_seats} seats occupied` : "-"}
          </p>
        </div>
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
      </div>
    </div>
  );
}
