import React, { useEffect, useState } from "react";
import api from "../api";
import AddCameraModal from "../components/AddCameraModal";
import AddFloorModal from "../components/AddFloorModal";

const ManageCameras = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [floors, setFloors] = useState([]);

  const [showCameraModal, setShowCameraModal] = useState(false);
  const [cameraForm, setCameraForm] = useState({
    location: "",
    ip_address: "",
    channel: "554",
    floor: "",
    status: "active",
    admin_name: "",
    admin_password: ""
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editId, setEditId] = useState(null);
  const [dropdownOpenId, setDropdownOpenId] = useState(null);

  const [showFloorModal, setShowFloorModal] = useState(false);
  const [floorForm, setFloorForm] = useState({
    name: "",
    camera_ids: []
  });

  useEffect(() => {
    fetchCameras();
    fetchFloors();
  }, []);

  const fetchCameras = async () => {
    try {
      const res = await api.get("/cameras/list/");
      setCameras(res.data);
    } catch (err) {
      console.error("Failed to fetch cameras", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFloors = async () => {
    try {
      const res = await api.get("/floors/list/");
      setFloors(res.data);
    } catch (err) {
      console.error("Failed to fetch floors", err);
    }
  };

  const handleCreateCamera = async () => {
    try {
      await api.post("/cameras/", cameraForm);
      setShowCameraModal(false);
      setCameraForm({ location: "", ip_address: "", channel: "554", floor: "", status: "active", admin_name: "", admin_password: "" });
      fetchCameras();
    } catch (err) {
      console.error("Error creating camera", err.response?.data || err);
    }
  };

  const handleUpdateCamera = async () => {
    try {
      await api.put(`/cameras/${editId}/`, cameraForm);
      setShowCameraModal(false);
      setIsEditing(false);
      setEditId(null);
      setCameraForm({ location: "", ip_address: "", channel: "554", floor: "", status: "active", admin_name: "", admin_password: "" });
      fetchCameras();
    } catch (err) {
      console.error("Error updating camera", err.response?.data || err);
    }
  };

  const handleDeleteCamera = async (id) => {
    if (!window.confirm("Are you sure to delete this camera?")) return;
    try {
      await api.delete(`/cameras/${id}/`);
      fetchCameras();
    } catch (err) {
      console.error("Failed to delete camera", err);
    }
  };

  const handleOpenEdit = (camera) => {
    setCameraForm({
      location: camera.location || "",
      ip_address: camera.ip_address,
      channel: camera.channel,
      floor: camera.floor,
      status: camera.status,
      admin_name: camera.admin_name,
      admin_password: camera.admin_password
    });
    setEditId(camera.id);
    setIsEditing(true);
    setShowCameraModal(true);
  };

  const handleCreateFloor = async () => {
    try {
      await api.post("/floors/", floorForm);
      setShowFloorModal(false);
      setFloorForm({ name: "", camera_ids: [] });
      fetchFloors();
    } catch (err) {
      console.error("Error creating floor", err.response?.data || err);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">Manage Cameras</h2>
          <p className="text-gray-500 text-sm">View and manage connected CCTV cameras</p>
        </div>
        <div className="space-x-2">
          <button onClick={() => setShowFloorModal(true)} className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300">+ Add Floor</button>
          <button onClick={() => { setShowCameraModal(true); setIsEditing(false); setCameraForm({ location: "", ip_address: "", channel: "554", floor: "", status: "active", admin_name: "", admin_password: "" }); }} className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">+ Add Camera</button>
        </div>
      </div>

      {loading ? <p>Loading...</p> : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border rounded-lg text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-4 py-2">Camera ID</th>
                <th className="px-4 py-2">Location</th>
                <th className="px-4 py-2">IP Address</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Last Seen</th>
                <th className="px-4 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {cameras.map((cam) => (
                <tr key={cam.id} className="border-t">
                  <td className="px-4 py-2">Cam {cam.id}</td>
                  <td className="px-4 py-2">{cam.location || "N/A"}</td>
                  <td className="px-4 py-2">{cam.ip_address}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-1 text-xs rounded-full font-semibold ${cam.status === "active" ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"}`}>
                      {cam.status}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {cam.last_active ? new Date(cam.last_active).toLocaleTimeString() : "N/A"}
                  </td>
                  <td className="px-4 py-2 relative">
                    <button onClick={() => setDropdownOpenId(dropdownOpenId === cam.id ? null : cam.id)} className="text-gray-500 hover:text-black">⋮</button>
                    {dropdownOpenId === cam.id && (
                      <div className="absolute z-10 right-0 mt-2 bg-white border shadow-md rounded w-28">
                        <button onClick={() => handleOpenEdit(cam)} className="block w-full px-4 py-2 text-left hover:bg-gray-100">Edit</button>
                        <button onClick={() => handleDeleteCamera(cam.id)} className="block w-full px-4 py-2 text-left hover:bg-gray-100 text-red-600">Delete</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCameraModal && (
        <AddCameraModal
          form={cameraForm}
          setForm={setCameraForm}
          onSubmit={isEditing ? handleUpdateCamera : handleCreateCamera}
          onCancel={() => { setShowCameraModal(false); setIsEditing(false); }}
          floors={floors}
          isEdit={isEditing}
        />
      )}

      {showFloorModal && (
        <AddFloorModal
          form={floorForm}
          setForm={setFloorForm}
          onSubmit={handleCreateFloor}
          onCancel={() => setShowFloorModal(false)}
          cameraList={cameras}
        />
      )}
    </div>
  );
};

export default ManageCameras;
