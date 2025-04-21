import React, { useEffect, useState } from "react";
import api, { API_BASE_URL } from "../api";

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [chairs, setChairs] = useState({});
  const [isDetecting, setIsDetecting] = useState(false);
  const [statusText, setStatusText] = useState("Detection is stopped.");
  const [entryState, setEntryState] = useState({});
  const [enterCount, setEnterCount] = useState(0);
  const [exitCount, setExitCount] = useState(0);
  const [lastEventSignature, setLastEventSignature] = useState(null);
  const [floors, setFloors] = useState([]);


  const streamUrl = `${API_BASE_URL}/video_feed/`;

  useEffect(() => {
    // Fetch summary once
    api.get('/analytics/seats/summary/')
      .then(res => setSummary(res.data))
      .catch(err => console.error("Failed to fetch summary", err));

    const interval = setInterval(() => {
      // Update chair occupancy
      api.get('/chair-occupancy/')
        .then(res => setChairs(res.data.chairs || {}))
        .catch(err => console.error("Chair error:", err));

      // Update entry state
      api.get('/entry-state/')
        .then(res => {
          const event = res.data;
          const sig = `${event.last_event}-${event.timestamp}`;
          if (sig !== lastEventSignature) {
            if (event.last_event === "enter") setEnterCount(prev => prev + 1);
            else if (event.last_event === "exit") setExitCount(prev => prev + 1);
            setLastEventSignature(sig);
          }
          setEntryState(event);
        })
        .catch(err => console.error("Entry state error:", err));
    }, 2000);

    return () => clearInterval(interval);
  }, [lastEventSignature]);

  const handleStart = () => {
    api.post('/analytics/start-detection/')
      .then(() => {
        setIsDetecting(true);
        setStatusText("Detection is running...");
        setEnterCount(0);
        setExitCount(0);
      })
      .catch(err => {
        console.error("Failed to start detection:", err);
        setStatusText("Failed to start detection.");
      });
  };

  const handleStop = () => {
    api.post('analytics/stop-detection/')
      .then(() => {
        setIsDetecting(false);
        setStatusText("Detection is stopped.");
      })
      .catch(err => {
        console.error("Failed to stop detection:", err);
        setStatusText("Failed to stop detection.");
      });
  };

  const handleResetCache = () => {
    api.post('/detection/reset-chairs/')
      .then(() => alert("Chair cache cleared."))
      .catch(err => {
        console.error("Failed to reset chair cache:", err);
        alert("Failed to reset cached chairs.");
      });
  };

  const occupiedSeats = Object.entries(chairs)
    .filter(([, seat]) => seat.status === "occupied")
    .map(([id, seat]) => ({
      id,
      floor: "-",
      duration: "-",
      start_time: "-",
      ...seat
    }));

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <h1 className="text-4xl font-bold mb-6">Analytics</h1>

      {/* Detection Controls */}
      <div className="flex items-center gap-4 mb-8">
        <span className="font-medium text-gray-700">Status:</span>
        <span className="font-bold text-blue-600">{statusText}</span>
        <button
          onClick={handleStart}
          disabled={isDetecting}
          className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded"
        >
          ▶ Start Detection
        </button>
        <button
          onClick={handleStop}
          disabled={!isDetecting}
          className="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded"
        >
          ■ Stop Detection
        </button>
        <button
          onClick={handleResetCache}
          disabled={isDetecting}
          className="bg-yellow-500 hover:bg-yellow-600 text-white font-semibold px-4 py-2 rounded"
        >
          ↺ Reset Chairs
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 text-lg mb-8">
        <div className="px-4 py-2 border-2 border-dashed border-purple-400 text-purple-600 rounded-lg font-semibold">Seats</div>
        <div className="text-gray-400">Peak Hours</div>
        <div className="text-gray-400">Customer</div>
      </div>

      {/* Live Feed */}
      {isDetecting && (
        <div className="mb-10">
          <h2 className="text-xl font-semibold mb-2">Live Detection Feed</h2>
          <div className="border rounded overflow-hidden w-fit mx-auto">
            <img src={streamUrl} alt="Live Detection Feed" className="w-[640px] h-[480px] object-cover border" />
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-white p-6 rounded-xl shadow">
          <div>
            <p className="text-sm text-gray-500">Most Popular Seat</p>
            <h2 className="text-xl font-bold text-orange-500">{summary?.most_popular_seat || "-"}</h2>
            <p className="text-xs text-gray-400">This Month</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Average Seating Time</p>
            <h2 className="text-xl font-bold text-orange-500">{summary?.average_duration || "-"} H</h2>
            <p className="text-xs text-gray-400">This Month</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Longest Current Stay</p>
            <h2 className="text-xl font-bold text-orange-500">{summary?.longest_session_table || "-"}</h2>
            <p className="text-xs text-gray-400">{summary?.longest_session_floor || "-"}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Longest Seating Time</p>
            <h2 className="text-xl font-bold text-orange-500">{summary?.longest_session_duration || "-"} H</h2>
            <p className="text-xs text-gray-400">{summary?.longest_session_table || "-"}</p>
          </div>
        </div>

        {/* Entry Events Summary */}
        <div className="bg-white p-6 rounded-xl shadow">
          <p className="text-sm font-semibold mb-2 text-gray-700">Entry Stats</p>
          <p>Entered: <strong>{enterCount}</strong></p>
          <p>Exited: <strong>{exitCount}</strong></p>
          {entryState.last_event && (
            <div className={`mt-4 p-3 rounded ${entryState.last_event === 'enter' ? 'bg-green-100' : 'bg-red-100'}`}>
              <p className="font-semibold">Last Event: {entryState.last_event.toUpperCase()}</p>
              <p>Person ID: #{entryState.track_id}</p>
              <p>Time: {entryState.timestamp ? new Date(entryState.timestamp).toLocaleTimeString() : "-"}</p>
            </div>
          )}
        </div>
      </div>

      {/* Occupied Chairs Table */}
      <div className="bg-white p-6 rounded-xl shadow">
        <h2 className="text-xl font-bold mb-4">Currently Occupied Seats</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-gray-500 border-b">
              <th className="text-left py-2">Chair ID</th>
              <th className="text-left py-2">Status</th>
              <th className="text-left py-2">Bounding Box</th>
            </tr>
          </thead>
          <tbody>
            {occupiedSeats.length === 0 ? (
              <tr>
                <td colSpan="3" className="text-center py-4 text-gray-400">No occupied chairs</td>
              </tr>
            ) : (
              occupiedSeats.map((seat, index) => (
                <tr key={index} className="border-b">
                  <td className="py-2">{seat.id}</td>
                  <td className="py-2 text-green-600 font-medium">● Occupied</td>
                  <td className="py-2 text-gray-600 text-xs">{JSON.stringify(seat.box)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
