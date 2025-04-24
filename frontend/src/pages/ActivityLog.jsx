import React, { useState, useEffect } from "react";
import api from "../api";

export default function ActivityLogPage() {
  const [logs, setLogs] = useState([]);
  const [filteredLogs, setFilteredLogs] = useState([]);
  const [filters, setFilters] = useState({ eventType: "", location: "", startDate: "", endDate: "" });
  const [locations, setLocations] = useState([]);

  useEffect(() => {
    fetchLogs();
    fetchLocations();

    const interval = setInterval(() => {
      fetchLogs();  // Auto-refresh every 5 seconds
    }, 5000);

    return () => clearInterval(interval);  // Cleanup on unmount
  }, []);

  const fetchLogs = () => {
    api.get("/analytics/activity-log/").then((res) => {
      setLogs(res.data);
      applyFilters(filters, res.data);
    });
  };

  const fetchLocations = () => {
    api.get("/floors/list/").then((res) => {
      setLocations(res.data);
    });
  };

  const handleFilterChange = (field, value) => {
    const newFilters = { ...filters, [field]: value };
    setFilters(newFilters);
    applyFilters(newFilters);
  };

  const applyFilters = (filters, logsToFilter = logs) => {
    let filtered = logsToFilter;

    if (filters.eventType) {
      filtered = filtered.filter((log) => log.event === filters.eventType);
    }

    if (filters.location) {
      filtered = filtered.filter((log) => log.location === filters.location);
    }

    if (filters.startDate) {
      filtered = filtered.filter((log) => new Date(log.timestamp) >= new Date(filters.startDate));
    }

    if (filters.endDate) {
      filtered = filtered.filter((log) => new Date(log.timestamp) <= new Date(filters.endDate));
    }

    setFilteredLogs(filtered);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="border-b bg-white p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Activity Log</h1>
      </div>

      <div className="flex flex-col md:flex-row p-8 gap-8">
        {/* Filters */}
        <div className="bg-white p-6 rounded-lg shadow w-full md:w-1/4">
          <h2 className="text-lg font-semibold mb-4">Event Options</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium">Event Type</label>
              <select
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                onChange={(e) => handleFilterChange("eventType", e.target.value)}
              >
                <option value="">All</option>
                <option value="Customer Arrives">Customer Arrives</option>
                <option value="Customer Exits">Customer Exits</option>
                <option value="Customer Sitting Down">Customer Sitting Down</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium">Start Date</label>
              <input
                type="date"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                onChange={(e) => handleFilterChange("startDate", e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium">End Date</label>
              <input
                type="date"
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                onChange={(e) => handleFilterChange("endDate", e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium">Location</label>
              <select
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
                onChange={(e) => handleFilterChange("location", e.target.value)}
              >
                <option value="">All</option>
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.name}>{loc.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Logs Table */}
        <div className="flex-1 bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Activity</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{new Date(log.timestamp).toLocaleString()}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.event}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.location}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
