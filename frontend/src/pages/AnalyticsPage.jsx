import React, { useEffect, useState } from "react";
import api from "../api";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [occupiedSeats, setOccupiedSeats] = useState([]);
  const [status, setStatus] = useState("Loading...");
  const [loading, setLoading] = useState(false);

  // 🔁 Fetch detection status
  const fetchStatus = () => {
    api.get("/analytics/detection-status/")
      .then(res => setStatus(res.data.status))
      .catch(() => setStatus("Error"));
  };

  // 📊 Fetch seat summary and current seats
  const fetchAnalytics = () => {
    api.get("/analytics/seats/summary/")
      .then(res => setSummary(res.data))
      .catch(err => console.error("Failed to load summary", err));

    const fetchSeats = () => {
      api.get("/analytics/seats/current/")
        .then(res => setOccupiedSeats(res.data.seats || []))
        .catch(err => console.error("Failed to load seats", err));
    };

    fetchSeats();
    const interval = setInterval(fetchSeats, 5000);
    return () => clearInterval(interval);
  };

  // ⏱️ Initialize on mount
  useEffect(() => {
    fetchStatus();
    const stopStatusLoop = setInterval(fetchStatus, 5000);
    const stopAnalyticsLoop = fetchAnalytics();
    return () => {
      clearInterval(stopStatusLoop);
      stopAnalyticsLoop();
    };
  }, []);

  // ▶ Start YOLO detection
  const handleStartDetection = async () => {
    setLoading(true);
    try {
      await api.post("/analytics/start-detection/");
      fetchStatus();
    } catch (err) {
      console.error("Start error:", err);
    }
    setLoading(false);
  };

  // ■ Stop YOLO detection
  const handleStopDetection = async () => {
    setLoading(true);
    try {
      await api.post("/analytics/stop-detection/");
      fetchStatus();
    } catch (err) {
      console.error("Stop error:", err);
    }
    setLoading(false);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans">
      <h1 className="text-3xl font-bold mb-4">Analytics</h1>

      {/* Detection Controls */}
      <div className="mb-6 flex gap-4 items-center">
        <span className="font-medium text-gray-700">Detection Status:</span>
        <span className={`font-bold ${status === "Running" ? "text-green-600" : "text-red-500"}`}>
          {status}
        </span>
        <button
          onClick={handleStartDetection}
          disabled={loading || status === "Running"}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded"
        >
          ▶ Start Detection
        </button>
        <button
          onClick={handleStopDetection}
          disabled={loading || status !== "Running"}
          className="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded"
        >
          ■ Stop Detection
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <div className="border-2 border-purple-400 px-4 py-2 rounded-lg bg-white text-purple-600 font-semibold">Seats</div>
        <div className="text-gray-400">Peak Hours</div>
        <div className="text-gray-400">Customer</div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-6 mb-6">
        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500">Most Popular Seat</p>
          <h2 className="text-xl font-bold">{summary?.most_popular_seat || '-'}</h2>
        </div>
        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500">Average Seating Time</p>
          <h2 className="text-xl font-bold">{summary ? `${summary.average_duration} min` : '-'}</h2>
        </div>
        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm text-gray-500">Longest Seating Time</p>
          <h2 className="text-xl font-bold">{summary?.longest_session_duration || 0} min</h2>
          <p className="text-xs text-gray-400">{summary?.longest_session_table || '-'}</p>
        </div>
      </div>

      {/* Occupied Seats Table */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-bold mb-4">Currently Occupied Seats</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500 border-b">
              <th className="pb-2">Seat ID</th>
              <th className="pb-2">Floor</th>
              <th className="pb-2">Duration</th>
              <th className="pb-2">Start Time</th>
              <th className="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {occupiedSeats.map((seat, index) => (
              <tr key={index} className="border-b hover:bg-gray-100">
                <td className="py-2">{seat.id}</td>
                <td className="py-2">{seat.floor}</td>
                <td className="py-2">{seat.duration}</td>
                <td className="py-2">{seat.start_time}</td>
                <td className="py-2">
                  <span className="text-green-500 font-semibold">● Occupied</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
