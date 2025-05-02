// HomePage.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { API_BASE_URL } from '../api';
import Navbar from '../components/Navbar';

export default function HomePage() {
  const navigate = useNavigate();
  const [seatSummary, setSeatSummary] = useState(null);
  const [customerStats, setCustomerStats] = useState(null);
  const [chairs, setChairs] = useState({});
  const [peakStats, setPeakStats] = useState(null);
  const [cameras, setCameras] = useState([]);
  const [selectedCameraIds, setSelectedCameraIds] = useState([]);
  const [statusMap, setStatusMap] = useState({});
  const [cafe, setCafe] = useState(null);
  const [sourceType, setSourceType] = useState("camera");
  const [selectedVideoPath, setSelectedVideoPath] = useState("D:/sample_vids/demo1.mp4");

  useEffect(() => {
    api.get('/analytics/seats/summary/').then(res => setSeatSummary(res.data));
    api.get('/analytics/customers/').then(res => setCustomerStats(res.data));
    api.get('/chair-occupancy/').then(res => setChairs(res.data.chairs || {}));
    api.get('/analytics/peak-hours/').then(res => setPeakStats(res.data));
    api.get('/cameras/list/').then(res => {
      const camList = res.data || [];
      setCameras(camList);
      const statusInit = {};
      camList.forEach(cam => statusInit[cam.id] = cam.status);
      setStatusMap(statusInit);
    });
    api.get('/cafes/user/').then(res => setCafe(res.data)).catch(() => setCafe(null));
  }, []);

  const toggleCamera = (id) => {
    setSelectedCameraIds(prev =>
      prev.includes(id) ? prev.filter(cid => cid !== id) : [...prev, id]
    );
  };

  const handleCameraError = (id) => {
    setStatusMap(prev => ({ ...prev, [id]: 'inactive' }));
  };

  const handleCameraLoad = (id) => {
    setStatusMap(prev => ({ ...prev, [id]: 'active' }));
  };

  const occupiedCount = Object.values(chairs).filter(seat => seat.status === 'occupied').length;
  const totalCount = Object.values(chairs).length;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <Navbar />

      <div className="p-8">
        <h1 className="text-3xl font-bold mb-8">
          Overview - {cafe?.name || 'Cafe'}
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
          <Card title="Occupied Seats" value={`${occupiedCount} / ${totalCount}`} subtitle="Currently" onArrowClick={() => navigate('/analytics/seats')} />
          <Card title="Average Seating Time" value={seatSummary?.average_duration ? `${Math.floor(seatSummary.average_duration / 60)} H ${seatSummary.average_duration % 60} M` : '-'} subtitle="During the last month" onArrowClick={() => navigate('/analytics/seats')} />
          <Card title="Peak Hours" value={peakStats?.peak_hour || '-'} subtitle="This Month" onArrowClick={() => navigate('/analytics/seats')} />
          <Card title="Returning Customers" value={`${customerStats?.retention_rate || 0}%`} subtitle="This Month" onArrowClick={() => navigate('/analytics/seats')} />
        </div>

        <div className="mb-4 flex gap-4">
          <button className={`px-4 py-2 rounded ${sourceType === 'camera' ? 'bg-black text-white' : 'bg-white border'}`} onClick={() => setSourceType('camera')}>Use Live Cameras</button>
          <button className={`px-4 py-2 rounded ${sourceType === 'sample' ? 'bg-black text-white' : 'bg-white border'}`} onClick={() => setSourceType('sample')}>Use Sample Video</button>
        </div>

        {sourceType === 'sample' && (
          <div className="mb-4">
            <label className="text-sm font-medium">Select Sample Video</label>
            <select
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm"
              value={selectedVideoPath}
              onChange={(e) => setSelectedVideoPath(e.target.value)}
            >
              <option value="D:/sample_vids/demo1.mp4">Demo 1</option>
              <option value="D:/sample_vids/demo2.mp4">Demo 2</option>
            </select>
          </div>
        )}

        {sourceType === 'camera' && (
          <>
            <div className="mb-6">
              <h2 className="text-lg font-semibold mb-2">Select Cameras to View</h2>
              <div className="flex flex-wrap gap-4">
                {cameras.map((cam) => {
                  const isSelected = selectedCameraIds.includes(cam.id);
                  return (
                    <button
                      key={cam.id}
                      onClick={() => toggleCamera(cam.id)}
                      className={`rounded-xl px-6 py-2 min-w-[120px] text-sm font-semibold border shadow transition ${
                        isSelected ? 'bg-black text-white border-black' : 'bg-white text-gray-800 border-gray-300 hover:bg-gray-100'
                      }`}
                    >
                      {cam.location || `Camera ${cam.id}`}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {(selectedCameraIds.length > 0 || sourceType === 'sample') && (
          <div className="mt-6">
            <button
              className="bg-orange-500 text-white px-6 py-2 rounded hover:bg-orange-600"
              onClick={() => navigate("/analytics/seats", {
                state: { sourceType, selectedCameraIds, videoPath: selectedVideoPath }
              })}
            >
              ▶ Start Analytics
            </button>
          </div>
        )}
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
