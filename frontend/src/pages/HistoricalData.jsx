import React, { useState, useEffect } from "react";
import api, { API_BASE_URL } from "../api";
import { Download, Eye } from "lucide-react";
import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';

export default function HistoricalDataPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedReportUrl, setSelectedReportUrl] = useState(null);  // For PDF Viewer modal

  const currentDate = new Date();
  const [generateYear, setGenerateYear] = useState(currentDate.getFullYear());
  const [generateMonth, setGenerateMonth] = useState(currentDate.getMonth() - 1 < 0 ? 11 : currentDate.getMonth() - 1);

  const defaultLayoutPluginInstance = defaultLayoutPlugin();

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = () => {
    setLoading(true);
    setError("");
    api.get("/reports/")
      .then(res => setReports(res.data))
      .catch(() => setError("Failed to fetch reports"))
      .finally(() => setLoading(false));
  };

  const handleGenerateReport = () => {
    api.post("/reports/generate/", { year: generateYear, month: generateMonth + 1 })
      .then(() => fetchReports())
      .catch(err => {
        console.error(err);
        alert("Failed to generate report (maybe it already exists)");
      });
  };

  // 🔥 Updated Download logic with blob
  const downloadFile = async (fileUrl, filename) => {
    try {
      const response = await api.get(fileUrl, { responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);  // Cleanup
    } catch (error) {
      console.error("Failed to download PDF:", error);
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-6">Historical Data</h1>
      <p className="text-gray-500 mb-8">View and generate historical analytics reports</p>

      {/* Generate Report Form */}
      <div className="flex gap-4 mb-8">
        <select className="border rounded p-2" value={generateYear} onChange={(e) => setGenerateYear(Number(e.target.value))}>
          {[2025, 2024, 2023].map(year => (
            <option key={year} value={year}>{year}</option>
          ))}
        </select>
        <select className="border rounded p-2" value={generateMonth} onChange={(e) => setGenerateMonth(Number(e.target.value))}>
          {Array.from({ length: 12 }, (_, i) => (
            <option key={i} value={i}>{new Date(0, i).toLocaleString('default', { month: 'long' })}</option>
          ))}
        </select>
        <button onClick={handleGenerateReport} className="px-4 py-2 bg-blue-500 text-white rounded">Generate Report</button>
      </div>

      {/* Loading/Error/Reports */}
      {loading && <p>Loading reports...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && reports.length === 0 && <p className="text-gray-500">No reports found.</p>}

      <div className="grid grid-cols-1 gap-4">
        {reports.map((report, idx) => {
          const fullFileUrl = `${API_BASE_URL}${report.file_url}`;
          const filename = `report_${report.year}_${report.month}.pdf`;
          return (
            <div key={idx} className="flex justify-between items-center p-4 border rounded-lg shadow-md bg-white">
              <div className="flex flex-col">
                <span className="font-semibold text-lg">{`Report for ${report.year}-${report.month}`}</span>
                <span className="text-gray-500 text-sm">{new Date(report.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex gap-2">
                {/* View PDF */}
                {report.file_url && (
                  <button 
                    className="border rounded px-4 py-2 text-sm hover:bg-gray-200"
                    onClick={() => setSelectedReportUrl(fullFileUrl)}  // Open modal
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
                {/* Download PDF */}
                {report.file_url && (
                  <button 
                    className="border rounded px-4 py-2 text-sm hover:bg-gray-200"
                    onClick={() => downloadFile(fullFileUrl, filename)}  // Use blob-based download
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* PDF Viewer Modal */}
      {selectedReportUrl && (
        <PDFViewerModal fileUrl={selectedReportUrl} onClose={() => setSelectedReportUrl(null)} />
      )}
    </div>
  );
}

// === PDF Viewer Modal Component ===
function PDFViewerModal({ fileUrl, onClose }) {
  const [blobUrl, setBlobUrl] = useState(null);
  const defaultLayoutPluginInstance = defaultLayoutPlugin();

  useEffect(() => {
    api.get(fileUrl, { responseType: 'blob' })
      .then(response => {
        const url = URL.createObjectURL(response.data);
        setBlobUrl(url);
      })
      .catch(err => {
        console.error("Failed to load PDF:", err);
      });

    return () => {
      if (blobUrl) URL.revokeObjectURL(blobUrl);
    };
  }, [fileUrl]);

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
      onClick={onClose} // Close when clicking outside the modal
    >
      <div 
        className="bg-white w-4/5 h-4/5 rounded-xl shadow-lg relative"
        onClick={(e) => e.stopPropagation()}  // Prevent close when clicking inside
      >
        <button onClick={onClose} className="absolute top-2 right-2 bg-red-500 text-white rounded px-3 py-1">Close</button>
        {blobUrl ? (
          <Worker workerUrl={`https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js`}>
            <Viewer fileUrl={blobUrl} plugins={[defaultLayoutPluginInstance]} />
          </Worker>
        ) : (
          <div className="flex justify-center items-center h-full">Loading PDF...</div>
        )}
      </div>
    </div>
  );
}
