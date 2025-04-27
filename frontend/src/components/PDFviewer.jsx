import React from 'react';
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';

export default function PdfViewer({ fileUrl, onClose }) {
  const defaultLayoutPluginInstance = defaultLayoutPlugin();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white w-4/5 h-4/5 rounded-xl shadow-lg relative">
        {/* Close Button */}
        <button onClick={onClose} className="absolute top-2 right-2 bg-red-500 text-white rounded px-3 py-1">
          Close
        </button>

        {/* PDF Viewer */}
        <Worker workerUrl={`https://unpkg.com/pdfjs-dist@${pdfjsVersion}/build/pdf.worker.min.js`}>
          <Viewer fileUrl={fileUrl} plugins={[defaultLayoutPluginInstance]} />
        </Worker>
      </div>
    </div>
  );
}

const pdfjsVersion = '3.11.174';  // or check your installed pdfjs-dist version
