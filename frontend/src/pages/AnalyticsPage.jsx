import React, { useEffect, useState } from "react";
import api, { API_BASE_URL } from "../api";
import AnalyticsTabs from '../components/AnalyticsTabs';
import Navbar from '../components/Navbar';

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null);
  const [chairs, setChairs] = useState({});
  const [isDetecting, setIsDetecting] = useState(false);
  const [statusText, setStatusText] = useState("Detection is stopped.");
  const [entryState, setEntryState] = useState({});
  const [enterCount, setEnterCount] = useState(0);
  const [exitCount, setExitCount] = useState(0);
  const [lastEventSignature, setLastEventSignature] = useState(null);
  const [floorsWithStats, setFloorsWithStats] = useState([]);

  const streamUrl = `${API_BASE_URL}/video_feed/`;

  // ⬇️ Fetch floor and camera list once and initialize with 0 stats
  useEffect(() => {
    api.get('/floors/list/')
      .then(res => {
        const floors = res.data.map(floor => ({
          ...floor,
          cameras: (floor.cameras  || []).map(cam => ({ ...cam, occupied: 0, empty: 0 }))
        }));
        setFloorsWithStats(floors);
      })
      .catch(err => console.error("Failed to load floors:", err));
  }, []);

  // ⬇️ Update chair occupancy stats dynamically when chairs change
  useEffect(() => {
    setFloorsWithStats(prevFloors =>
      prevFloors.map(floor => ({
        ...floor,
        cameras: floor.cameras.map(cam => {
          const seatList = Object.values(chairs).filter(seat => seat.camera_id === cam.id);
          const occupied = seatList.filter(seat => seat.status === "occupied").length;
          const empty = seatList.filter(seat => seat.status === "empty").length;
          return { ...cam, occupied, empty };
        })
      }))
    );
  }, [chairs]);

  // ⬇️ Fetch summary and polling data every 2 seconds
  useEffect(() => {
    api.get('/analytics/seats/summary/')
  .then(res => setSummary(res.data))
  .catch(err => {
    console.error("Failed to fetch summary", err);
    setSummary(null); // fallback
  });

    const interval = setInterval(() => {
      api.get('/chair-occupancy/')
        .then(res => setChairs(res.data.chairs || {}))
        .catch(err => console.error("Chair error:", err));

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
  .map(([id, seat]) => {
    const start = seat.start_time;
    const floor = "Video";

    let duration = "-";
    let startTime = "-";

    if (start) {
      const now = isDetecting ? Date.now() / 1000 : start;
      const minutes = Math.floor((now - start) / 60);
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      duration = hours > 0 ? `${hours}h ${remainingMinutes}m` : `${minutes}m`;

      const startDate = new Date(start * 1000);
      startTime = startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    return {
      id,
      floor,
      duration,
      start_time: startTime
    };
  });



  return (

    <div className="min-h-screen bg-gray-50 font-sans">
          {/* Navbar */}
          <Navbar/>
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
        <AnalyticsTabs />
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

      {/* Summary & Floor Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Monthly Summary */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 bg-white p-6 rounded-xl shadow">
        <div>
  <p className="text-sm text-gray-500">Most Popular Seat</p>
  <h2 className="text-xl font-bold text-orange-500">{summary?.most_popular_seat || "-"}</h2>
  <p className="text-xs text-gray-400">This Month</p>
</div>
<div>
  <p className="text-sm text-gray-500">Average Seating Time</p>
  <h2 className="text-xl font-bold text-orange-500">{summary?.average_duration || "-"} min</h2>
  <p className="text-xs text-gray-400">This Month</p>
</div>
<div>
  <p className="text-sm text-gray-500">Longest Current Stay</p>
  <h2 className="text-xl font-bold text-orange-500">{summary?.longest_current_stay || "-"}</h2>
  <p className="text-xs text-gray-400">Live</p>
</div>
<div>
  <p className="text-sm text-gray-500">Longest Seating Time</p>
  <h2 className="text-xl font-bold text-orange-500">{summary?.longest_session_duration || "-"} min</h2>
  <p className="text-xs text-gray-400">{summary?.longest_session_table || "-"}</p>
</div>

        </div>

        {/* Floor Stats Summary */}
        <div className="flex flex-col gap-6">
          {floorsWithStats.map((floor) => {
            const totalOccupied = floor.cameras.reduce((sum, cam) => sum + cam.occupied, 0);
            const totalEmpty = floor.cameras.reduce((sum, cam) => sum + cam.empty, 0);
            return (
              <div key={floor.id}>
                <p className="text-sm font-semibold mb-2 text-gray-700">{floor.name}</p>
                <div className="bg-white p-6 rounded-xl shadow flex justify-between items-center">
                  <div className="flex flex-col items-center">
                    <h2 className="text-3xl font-bold text-orange-500">{totalEmpty}</h2>
                    <p className="text-sm text-gray-400">Empty Seats</p>
                  </div>
                  <div className="flex flex-col items-center">
                    <h2 className="text-3xl font-bold text-gray-800">{totalOccupied}</h2>
                    <p className="text-sm text-gray-400">Occupied Seats</p>
                  </div>
                </div>
              </div>
            );
          })}
 {/* ⬇ New: Live Video Total Count */}
 <div className="mt-6">
    <p className="text-sm font-semibold mb-2 text-gray-700">Video-Based Chair Summary</p>
    <div className="bg-white p-6 rounded-xl shadow flex justify-between items-center">
      <div className="flex flex-col items-center">
        <h2 className="text-3xl font-bold text-orange-500">
          {Object.values(chairs).filter(seat => seat.status === "available").length}
        </h2>
        <p className="text-sm text-gray-400">Available Seats</p>
      </div>
      <div className="flex flex-col items-center">
        <h2 className="text-3xl font-bold text-gray-800">
          {Object.values(chairs).filter(seat => seat.status === "occupied").length}
        </h2>
        <p className="text-sm text-gray-400">Occupied Seats</p>
      </div>
    </div>
  </div>

        </div>
      </div>

      {/* Occupied Chairs Table */}
<div className="bg-white p-6 rounded-xl shadow">
  <h2 className="text-xl font-bold mb-4">Currently Occupied Seats</h2>
  <table className="w-full text-sm table-fixed">
    <thead>
      <tr className="text-gray-500 border-b">
        <th className="text-left py-2 w-1/6">Seat ID</th>
        <th className="text-left py-2 w-1/6">Floor</th>
        <th className="text-left py-2 w-1/4">Duration</th>
        <th className="text-left py-2 w-1/4">Start Time</th>
        <th className="text-left py-2 w-1/6">Status</th>
      </tr>
    </thead>
    <tbody>
      {occupiedSeats.length === 0 ? (
        <tr>
          <td colSpan="5" className="text-center py-4 text-gray-400">No occupied chairs</td>
        </tr>
      ) : (
        occupiedSeats.map((seat, index) => (
          <tr key={index} className="border-b">
            <td className="py-2">{seat.id}</td>
            <td className="py-2">{seat.floor}</td>
            <td className="py-2 flex items-center gap-1">
              <span>🕒</span>{seat.duration}
            </td>
            <td className="py-2">{seat.start_time}</td>
            <td className="py-2">
              <span className="inline-flex items-center gap-1 text-green-600 font-medium">
                <span className="h-2 w-2 rounded-full bg-green-500 inline-block"></span>Occupied
              </span>
            </td>
          </tr>
        ))
      )}
    </tbody>
  </table>
</div>

    </div>
  </div>
  );
}
