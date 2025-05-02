import React, { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import api, { API_BASE_URL } from "../api";

export default function AnalyticsContainer() {
  const [isDetecting, setIsDetecting] = useState(false);
  const [cameraList, setCameraList] = useState([]);
  const [selectedSource, setSelectedSource] = useState({ sourceType: "camera", selectedCameraIds: [], videoPath: "" });
  const [statusText, setStatusText] = useState("Stopped");

  const streamUrl = `${API_BASE_URL}/video_feed/`;

  useEffect(() => {
    api.get("/analytics/detection-status/")
      .then(res => {
        setIsDetecting(res.data.is_detecting);
        setStatusText(res.data.is_detecting ? "Running" : "Stopped");
      })
      .catch(() => setIsDetecting(false));

    api.get("/cameras/list/")
      .then(res => setCameraList(res.data || []))
      .catch(err => console.error("Failed to fetch cameras", err));
  }, []);

  const handleSourceChange = (e) => {
    const val = e.target.value;
    if (val.startsWith("camera-")) {
      const camId = parseInt(val.split("-")[1]);
      setSelectedSource({ sourceType: "camera", selectedCameraIds: [camId], videoPath: "" });
    } else {
      setSelectedSource({ sourceType: "sample", selectedCameraIds: [], videoPath: val });
    }
  };

  const handleStart = () => {
    const payload = {
      source_type: selectedSource.sourceType,
      video_path: selectedSource.videoPath,
      selected_camera_ids: selectedSource.selectedCameraIds,
    };
    api.post("/analytics/start-detection/", payload)
      .then(() => {
        setIsDetecting(true);
        setStatusText("Running");
      })
      .catch(err => console.error("Start error:", err));
  };

  const handleStop = () => {
    api.post("/analytics/stop-detection/")
      .then(() => {
        setIsDetecting(false);
        setStatusText("Stopped");
      })
      .catch(err => console.error("Stop error:", err));
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <Navbar />
      <div className="p-8">
        <h1 className="text-3xl font-bold mb-6">Analytics</h1>

        {/* Source Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Select Source:</label>
          <select
            className="w-full max-w-md p-2 border rounded"
            value={selectedSource.sourceType === "sample" ? selectedSource.videoPath : `camera-${selectedSource.selectedCameraIds[0] || ""}`}
            onChange={handleSourceChange}
          >
            <option value="">-- Select --</option>
            {cameraList.map(cam => (
              <option key={cam.id} value={`camera-${cam.id}`}>Camera {cam.id}: {cam.location}</option>
            ))}
            <option value="D:/Kuliah/Tugas Akhir/Coding Udemy/Testing Faces/cctv_vids/vid1.mp4">Sample: Demo 1</option>
            <option value="D:/Kuliah/Tugas Akhir/Coding Udemy/Testing Faces/cctv_vids/vid5.mp4">Sample: Demo 2</option>
          </select>
        </div>

        {/* Status & Control */}
        <div className="flex gap-4 items-center mb-6">
          <span className="text-gray-700 font-medium">Status:</span>
          <span className="text-blue-600 font-semibold">{statusText}</span>
          {isDetecting ? (
            <button
              onClick={handleStop}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded"
            >
              ■ Stop Detection
            </button>
          ) : (
            <button
              onClick={handleStart}
              className="bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded"
              disabled={!selectedSource.sourceType || (selectedSource.sourceType === "camera" && selectedSource.selectedCameraIds.length === 0)}
            >
              ▶ Start Detection
            </button>
          )}
        </div>

        {/* Live Feed */}
        {isDetecting && (
          <div className="mb-10">
            <h2 className="text-xl font-semibold mb-2">Live Detection Feed</h2>
            <div className="relative border rounded w-[640px] mx-auto h-[480px] bg-black">
              <img
                src={streamUrl}
                alt="Live Detection Feed"
                className="w-full h-full object-cover border"
              />
            </div>
          </div>
        )}

        {/* Analytics Tabs + Page */}
        <Outlet />
      </div>
    </div>
  );
}