import React from "react";

const AddFloorModal = ({ form, setForm, onSubmit, onCancel, cameraList }) => {
  const toggleCamera = (cameraId) => {
    const updated = form.camera_ids.includes(cameraId)
      ? form.camera_ids.filter((id) => id !== cameraId)
      : [...form.camera_ids, cameraId];
    setForm({ ...form, camera_ids: updated });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-md w-full max-w-md shadow-lg relative">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-lg font-semibold">Add New Floor</h3>
          <button
            onClick={onCancel}
            className="text-xl font-bold text-gray-500 hover:text-black"
          >
            &times;
          </button>
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Enter the details for the new floor and optionally select cameras connected to it.
        </p>

        <div>
            <label className="block text-sm font-medium mb-1">Floor Number</label>
            <input
              type="number"
              placeholder="e.g., 1"
              value={form.floor_number || ""}
              onChange={(e) =>
                setForm({ ...form, floor_number: parseInt(e.target.value) || null })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-orange-400"
            />
          </div>



        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Floor Name</label>
            <input
              type="text"
              placeholder="e.g., Ground Floor"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring focus:ring-orange-400"
            />
          </div>

          

          <div>
            <label className="block text-sm font-medium mb-2">Cameras</label>
            <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
              {cameraList && cameraList.length > 0 ? (
                cameraList.map((cam) => (
                  <label key={cam.id} className="flex items-center space-x-2 text-sm">
                    <input
                      type="checkbox"
                      checked={form.camera_ids.includes(cam.id)}
                      onChange={() => toggleCamera(cam.id)}
                      className="accent-orange-500"
                    />
                    <span>{cam.location || `Camera ${cam.id}`}</span>
                  </label>
                ))
              ) : (
                <p className="text-sm text-gray-400">No available cameras</p>
              )}
            </div>
            <p className="text-xs text-gray-400 italic mt-1">
              * You can skip camera selection
            </p>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onSubmit}
            className="bg-orange-500 hover:bg-orange-600 text-white px-5 py-2 rounded"
          >
            Add Floor
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddFloorModal;
