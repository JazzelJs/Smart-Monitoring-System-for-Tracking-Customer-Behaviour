import React, { useEffect, useState } from "react";
import api from "../api";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [occupiedSeats, setOccupiedSeats] = useState([]);
  const [status, setStatus] = useState("Loading...");
  const [loading, setLoading] = useState(false);

  const fetchStatus = () => {
    api.get("/analytics/detection-status/")
      .then(res => setStatus(res.data.status))
      .catch(() => setStatus("Error"));
  };

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

  useEffect(() => {
    fetchStatus();
    const stopStatusLoop = setInterval(fetchStatus, 5000);
    const stopAnalyticsLoop = fetchAnalytics();
    return () => {
      clearInterval(stopStatusLoop);
      stopAnalyticsLoop();
    };
  }, []);

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
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <h1 className="text-4xl font-bold mb-6">Analytics</h1>

      {/* Detection Controls */}
      <div className="flex items-center gap-4 mb-8">
        <span className="font-medium text-gray-700">Detection Status:</span>
        <span className={`font-bold ${status === "Running" ? "text-green-600" : "text-red-500"}`}>
          {status}
        </span>
        <button
          onClick={handleStartDetection}
          disabled={loading || status === "Running"}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded flex items-center gap-2"
        >
          ▶ Start Detection
        </button>
        <button
          onClick={handleStopDetection}
          disabled={loading || status !== "Running"}
          className="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded flex items-center gap-2"
        >
          ■ Stop Detection
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 text-lg mb-8">
        <div className="px-4 py-2 border-2 border-dashed border-purple-400 text-purple-600 rounded-lg font-semibold">Seats</div>
        <div className="text-gray-400">Peak Hours</div>
        <div className="text-gray-400">Customer</div>
      </div>

      {/* 2-column main content */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Left: Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-white p-6 rounded-xl shadow">
  {/* Most Popular Seat */}
  <div>
    <p className="text-sm text-gray-500">Most Popular Seat</p>
    <h2 className="text-xl font-bold text-orange-500">{summary?.most_popular_seat || "-"}</h2>
    <p className="text-xs text-gray-400">This Month</p>
  </div>

  {/* Average Seating Time */}
  <div>
    <p className="text-sm text-gray-500">Average Seating Time</p>
    <h2 className="text-xl font-bold text-orange-500">{summary?.average_duration || "-"} H</h2>
    <p className="text-xs text-gray-400">This Month</p>
  </div>

  {/* Longest Current Stay */}
  <div>
    <p className="text-sm text-gray-500">Longest Current Stay</p>
    <h2 className="text-xl font-bold text-orange-500">{summary?.longest_session_table || "-"}</h2>
    <p className="text-xs text-gray-400">{summary?.longest_session_floor || "-"}</p>
  </div>

  {/* Longest Seating Time */}
  <div>
    <p className="text-sm text-gray-500">Longest Seating Time</p>
    <h2 className="text-xl font-bold text-orange-500">{summary?.longest_session_duration || "-"} H</h2>
    <p className="text-xs text-gray-400">{summary?.longest_session_table || "-"}</p>
  </div>
</div>


        {/* Right: Floor Stats */}
        <div className="flex flex-col gap-6">
          {/* First Floor */}
          <div>
            <p className="text-sm font-semibold mb-2 text-gray-700">First Floor</p>
            <div className="bg-white p-6 rounded-xl shadow flex justify-between items-center">
              <div className="flex flex-col items-center">
                <h2 className="text-3xl font-bold text-orange-500">10</h2>
                <p className="text-sm text-gray-400">Empty Seats</p>
              </div>
              <div className="flex flex-col items-center">
                <h2 className="text-3xl font-bold text-gray-800">10</h2>
                <p className="text-sm text-gray-400">Occupied Seats</p>
              </div>
            </div>
          </div>

          {/* Second Floor */}
          <div>
            <p className="text-sm font-semibold mb-2 text-gray-700">Second Floor</p>
            <div className="bg-white p-6 rounded-xl shadow flex justify-between items-center">
              <div className="flex flex-col items-center">
                <h2 className="text-3xl font-bold text-orange-500">13</h2>
                <p className="text-sm text-gray-400">Empty Seats</p>
              </div>
              <div className="flex flex-col items-center">
                <h2 className="text-3xl font-bold text-gray-800">7</h2>
                <p className="text-sm text-gray-400">Occupied Seats</p>
              </div>
            </div>
          </div>
           {/* Add Floor Button */}
      <div className="mb-10">
        <button className="w-full border border-gray-400 rounded-lg py-4 hover:bg-gray-100 transition text-lg font-medium">
          + Add Floors
        </button>
      </div>
        </div>
      </div>

     

      {/* Occupied Seats Table */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-bold mb-4">Currently Occupied Seats</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b">
              <th className="text-left py-2">Seat ID</th>
              <th className="text-left py-2">Floor</th>
              <th className="text-left py-2">Duration</th>
              <th className="text-left py-2">Start Time</th>
              <th className="text-left py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {occupiedSeats.length === 0 ? (
              <tr>
                <td colSpan="5" className="text-center py-4 text-gray-400">No occupied seats</td>
              </tr>
            ) : (
              occupiedSeats.map((seat, index) => (
                <tr key={index} className="border-b">
                  <td className="py-2">{seat.id}</td>
                  <td className="py-2">{seat.floor}</td>
                  <td className="py-2">{seat.duration}</td>
                  <td className="py-2">{seat.start_time}</td>
                  <td className="py-2 text-green-600 font-medium">● Occupied</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
