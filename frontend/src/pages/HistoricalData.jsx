import React, { useState, useEffect } from "react";
import api, { API_BASE_URL } from "../api";
import { Download, Eye } from "lucide-react";
import ReportPreview from "../components/ReportPreview";

export default function HistoricalDataPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedReport, setSelectedReport] = useState(null); // For Report Preview Modal

  const currentDate = new Date();
  const [generateYear, setGenerateYear] = useState(currentDate.getFullYear());
  const [generateMonth, setGenerateMonth] = useState(currentDate.getMonth() - 1 < 0 ? 11 : currentDate.getMonth() - 1);

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
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download PDF:", error);
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-6">Historical Data</h1>
      <p className="text-gray-500 mb-8">View and generate historical analytics reports</p>

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
                {report.file_url && (
                  <button 
                    className="border rounded px-4 py-2 text-sm hover:bg-gray-200"
                    onClick={() => setSelectedReport({ year: report.year, month: report.month })}
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                )}
                {report.file_url && (
                  <button 
                    className="border rounded px-4 py-2 text-sm hover:bg-gray-200"
                    onClick={() => downloadFile(fullFileUrl, filename)}
                  >
                    <Download className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {selectedReport && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
          <div className="bg-white w-11/12 max-w-6xl h-[90%] overflow-auto rounded-xl p-6">
            <ReportPreview 
              year={selectedReport.year} 
              month={selectedReport.month} 
              onClose={() => setSelectedReport(null)} 
            />
          </div>
        </div>
      )}
    </div>
  );
}
