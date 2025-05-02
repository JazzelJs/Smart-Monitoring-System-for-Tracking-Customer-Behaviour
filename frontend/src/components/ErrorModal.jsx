import React from "react";

export default function ErrorModal({ title = "Error", message, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl max-w-sm w-full px-6 py-8 space-y-4 text-center relative animate-fadeIn">
        <h3 className="text-xl font-semibold text-red-600">{title}</h3>
        <p className="text-gray-600">{message}</p>
        <button
          className="mt-4 bg-[#FF9500] hover:bg-orange-600 text-white font-medium px-6 py-2 rounded-lg transition-all duration-200"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </div>
  );
}
