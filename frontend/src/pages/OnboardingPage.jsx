import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import { saveTokens, getAccessToken } from "../utils/auth";

function OnboardingPage() {
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [cafeName, setCafeName] = useState("");
  const [location, setLocation] = useState("");
  const [capacity, setCapacity] = useState(0);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const [floors, setFloors] = useState([
    { name: "Ground Floor", cameras: [] }
  ]);

  const handleAddFloor = () => {
    setFloors([...floors, { name: `Floor ${floors.length + 1}`, cameras: [] }]);
  };

  const handleFloorChange = (index, value) => {
    const updated = [...floors];
    updated[index].name = value;
    setFloors(updated);
  };

  const handleAddCamera = (floorIndex) => {
    const updated = [...floors];
    updated[floorIndex].cameras.push({
      location: "",
      status: "active",
      ip_address: "",
      channel: "",
      admin_name: "",
      admin_password: ""
    });
    setFloors(updated);
  };

  const handleCameraChange = (floorIndex, cameraIndex, field, value) => {
    const updated = [...floors];
    updated[floorIndex].cameras[cameraIndex][field] = value;
    setFloors(updated);
  };

  const handleSubmit = async () => {
    try {
      const cafeRes = await api.post(
        "/cafes/",
        {
          name: cafeName,
          location,
          capacity
        },
        {
          headers: {
            Authorization: `Bearer ${getAccessToken()}`
          }
        }
      );

      const cafeId = cafeRes.data.id;

      for (const floor of floors) {
        const floorRes = await api.post("/floors/", {
          cafe: cafeId,
          name: floor.name,
          floor_number: floors.indexOf(floor) + 1
        });

        const floorId = floorRes.data.id;

        for (const cam of floor.cameras) {
          await api.post("/cameras/", {
            cafe: cafeId,
            floor: floorId,
            status: cam.status,
            ip_address: cam.ip_address,
            channel: cam.channel,
            location: cam.location,
            admin_name: cam.admin_name,
            admin_password: cam.admin_password
          });
        }
      }

      setShowSuccessModal(true); // ✅ Show modal after success
    } catch (err) {
      console.error("Setup error", err);
      alert("Something went wrong during setup.");
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6 relative">
      {step === 1 && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Step 1: Cafe Info</h2>
          <input placeholder="Cafe Name" className="border p-2 w-full" onChange={(e) => setCafeName(e.target.value)} />
          <input placeholder="Location" className="border p-2 w-full" onChange={(e) => setLocation(e.target.value)} />
          <input type="number" placeholder="Capacity" className="border p-2 w-full" onChange={(e) => setCapacity(Number(e.target.value))} />
          <button className="bg-[#FF9500] text-white px-4 py-2 rounded" onClick={() => setStep(2)}>Next</button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <h2 className="text-xl font-bold">Step 2: Add Floors and Cameras</h2>
          {floors.map((floor, i) => (
            <div key={i} className="border p-4 space-y-2">
              <input
                placeholder={`Floor ${i + 1} Name`}
                className="border p-2 w-full"
                value={floor.name}
                onChange={(e) => handleFloorChange(i, e.target.value)}
              />
              {floor.cameras.map((camera, j) => (
                <div key={j} className="pl-4 border-l-4 border-orange-400 space-y-2 mt-2">
                  <p className="font-medium">Camera {j + 1}</p>
                  <input
                    placeholder="IP Address"
                    className="border p-2 w-full"
                    onChange={(e) => handleCameraChange(i, j, "ip_address", e.target.value)}
                  />
                  <input
                    placeholder="Channel"
                    className="border p-2 w-full"
                    onChange={(e) => handleCameraChange(i, j, "channel", e.target.value)}
                  />
                  <input
                    placeholder="Location Description"
                    className="border p-2 w-full"
                    onChange={(e) => handleCameraChange(i, j, "location", e.target.value)}
                  />
                  <input
                    placeholder="Admin Username"
                    className="border p-2 w-full"
                    onChange={(e) => handleCameraChange(i, j, "admin_name", e.target.value)}
                  />
                  <input
                    placeholder="Admin Password"
                    type="password"
                    className="border p-2 w-full"
                    onChange={(e) => handleCameraChange(i, j, "admin_password", e.target.value)}
                  />
                </div>
              ))}
              <button className="text-sm text-blue-500" onClick={() => handleAddCamera(i)}>+ Add Camera</button>
            </div>
          ))}
          <button className="text-sm text-blue-500" onClick={handleAddFloor}>+ Add Floor</button>
          <div className="space-x-2">
            <button className="bg-gray-300 px-4 py-2 rounded" onClick={() => setStep(1)}>Back</button>
            <button className="bg-[#FF9500] text-white px-4 py-2 rounded" onClick={handleSubmit}>Finish</button>
          </div>
        </div>
      )}

      {/* ✅ Success Modal */}
      {showSuccessModal && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg max-w-sm w-full text-center space-y-4">
            <h2 className="text-xl font-bold text-green-600">Success!</h2>
            <p>Your cafe setup is complete.</p>
            <button
              className="bg-[#FF9500] text-white px-4 py-2 rounded hover:bg-orange-600"
              onClick={() => navigate("/dashboard")}
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default OnboardingPage;
