import React, { useEffect, useState } from "react";
import api from "../api";
import Navbar from "../components/Navbar"; // ✅ Add Navbar
import AddCameraModal from "../components/AddCameraModal";
import AddFloorModal from "../components/AddFloorModal";
import ConfirmModal from "../components/ConfirmModal"; // ✅ Add ConfirmModal

const ManageCameras = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [floors, setFloors] = useState([]);
  const [dropdownPos, setDropdownPos] = useState({ x: 0, y: 0 });
  const [dropdownOpenId, setDropdownOpenId] = useState(null);

  const [showCameraModal, setShowCameraModal] = useState(false);
  const [cameraForm, setCameraForm] = useState({
    location: "",
    ip_address: "",
    channel: "554",
    floor: null,
    status: "active",
    admin_name: "",
    admin_password: ""
  });
  const [isEditing, setIsEditing] = useState(false);
  const [editId, setEditId] = useState(null);

  const [showFloorModal, setShowFloorModal] = useState(false);
  const [floorForm, setFloorForm] = useState({
    name: "",
    floor_number: null,
    camera_ids: []
  });

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [cameraToDelete, setCameraToDelete] = useState(null);

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

  const resetCameraForm = () => {
    setCameraForm({
      location: "",
      ip_address: "",
      channel: "554",
      floor: null,
      status: "active",
      admin_name: "",
      admin_password: ""
    });
  };

  const handleCreateCamera = async () => {
    try {
      await api.post("/cameras/", cameraForm);
      setShowCameraModal(false);
      resetCameraForm();
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
      resetCameraForm();
      fetchCameras();
    } catch (err) {
      console.error("Error updating camera", err.response?.data || err);
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

  const requestDeleteCamera = (id) => {
    setCameraToDelete(id);
    setShowDeleteModal(true);
  };

  const confirmDeleteCamera = async () => {
    if (!cameraToDelete) return;
    try {
      await api.delete(`/cameras/${cameraToDelete}/`);
      setCameraToDelete(null);
      setShowDeleteModal(false);
      fetchCameras();
    } catch (err) {
      console.error("Failed to delete camera", err);
    }
  };

  const handleCreateFloor = async () => {
    try {
      await api.post("/floors/", floorForm);
      setShowFloorModal(false);
      setFloorForm({ name: "", floor_number: null, camera_ids: [] });
      fetchFloors();
    } catch (err) {
      console.error("Error creating floor", err.response?.data || err);
    }
  };

  useEffect(() => {
    const handleClickOutside = (e) => {
      const isInsideDropdown = e.target.closest(".dropdown-menu");
      const isDropdownBtn = e.target.closest("button");
      if (!isInsideDropdown && !isDropdownBtn) {
        setDropdownOpenId(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <Navbar /> {/* ✅ Add Navbar */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">Manage Cameras</h2>
            <p className="text-gray-500 text-sm">View and manage connected CCTV cameras</p>
          </div>
          <div className="space-x-2">
            <button onClick={() => setShowFloorModal(true)} className="bg-gray-200 px-4 py-2 rounded hover:bg-gray-300">+ Add Floor</button>
            <button onClick={() => {
              setShowCameraModal(true);
              setIsEditing(false);
              resetCameraForm();
            }} className="bg-black text-white px-4 py-2 rounded hover:bg-gray-800">+ Add Camera</button>
          </div>
        </div>

        {loading ? <p>Loading...</p> : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white border rounded-lg text-sm text-left">
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
                    <td className="px-4 py-2 whitespace-nowrap">Cam {cam.id}</td>
                    <td className="px-4 py-2 whitespace-nowrap">{cam.location || "N/A"}</td>
                    <td className="px-4 py-2 whitespace-nowrap">{cam.ip_address}</td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full font-semibold ${cam.status === "active" ? "bg-green-100 text-green-600" : "bg-red-100 text-red-600"}`}>
                        {cam.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap">
                      {cam.last_active ? new Date(cam.last_active).toLocaleTimeString() : "N/A"}
                    </td>
                    <td className="px-4 py-2 relative whitespace-nowrap">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          const rect = e.currentTarget.getBoundingClientRect();
                          setDropdownPos({ x: rect.right - 128, y: rect.bottom + window.scrollY });
                          setDropdownOpenId(dropdownOpenId === cam.id ? null : cam.id);
                        }}
                        className="text-gray-500 hover:text-black"
                      >
                        ⋮
                      </button>
                      {dropdownOpenId === cam.id && (
                        <div
                          className="fixed z-50 w-32 bg-white border border-gray-200 rounded shadow-md dropdown-menu"
                          style={{ top: `${dropdownPos.y}px`, left: `${dropdownPos.x}px` }}
                        >
                          <button onClick={() => handleOpenEdit(cam)} className="block w-full px-4 py-2 text-left hover:bg-gray-100">Edit</button>
                          <button onClick={() => requestDeleteCamera(cam.id)} className="block w-full px-4 py-2 text-left hover:bg-gray-100 text-red-600">Delete</button>
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

        {showDeleteModal && (
          <ConfirmModal
            title="Delete Camera"
            message="Are you sure you want to delete this camera? This action cannot be undone."
            onConfirm={confirmDeleteCamera}
            onCancel={() => {
              setShowDeleteModal(false);
              setCameraToDelete(null);
            }}
          />
        )}
      </div>
    </div>
  );
};

export default ManageCameras;
