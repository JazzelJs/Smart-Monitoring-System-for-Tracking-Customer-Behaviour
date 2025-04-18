// ManageCameras.jsx
import React, { useEffect, useState } from 'react';
import api from '../api'; // adjust the path based on your structure

const ManageCameras = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/cameras/list/')
      .then(res => {
        console.log("Camera response:", res.data);
        const data = res.data;
        if (Array.isArray(data)) {
          setCameras(data);
        } else if (Array.isArray(data.results)) {
          setCameras(data.results);
        } else {
          console.warn("Unexpected camera data format", data);
          setCameras([]);
        }
      })
      .catch(err => {
        console.error("Error fetching cameras:", err.response || err);
        setCameras([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);
  
  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-1">Manage Cameras</h2>
      <p className="text-gray-500 mb-4">View and manage connected CCTV cameras</p>

      {loading ? <p>Loading...</p> : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border rounded-lg">
            <thead>
              <tr className="bg-gray-100 text-left text-sm font-medium">
                <th className="px-4 py-2">Camera ID</th>
                <th className="px-4 py-2">Location</th>
                <th className="px-4 py-2">IP Address</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Last Seen</th>
                <th className="px-4 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {cameras.map(cam => (
                <tr key={cam.id} className="border-t text-sm">
                  <td className="px-4 py-2">Cam {cam.id}</td>
                  <td className="px-4 py-2">{cam.location || 'N/A'}</td>
                  <td className="px-4 py-2">{cam.ip_address}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${cam.status === 'active' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                      {cam.status === 'active' ? 'Online' : 'Offline'}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {cam.last_active ? new Date(cam.last_active).toLocaleTimeString() : 'N/A'}
                  </td>
                  <td className="px-4 py-2">
                    <button className="text-gray-500 hover:text-black">⋮</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4">
        <button className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">
          + Add Camera
        </button>
      </div>
    </div>
  );
};

export default ManageCameras;
