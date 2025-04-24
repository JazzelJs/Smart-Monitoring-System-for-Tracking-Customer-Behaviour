import React, { useState, useEffect } from "react";
import api from "../api";
import { Download, Eye } from "lucide-react";

export default function HistoricalDataPage() {
  const [reports, setReports] = useState([]);
  const [filters, setFilters] = useState({ year: "2024", startDate: "", endDate: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchReports();
  }, [filters]);

  const fetchReports = () => {
    setLoading(true);
    setError("");
    api.get("/historical-data/reports/", { params: filters })
      .then(res => setReports(res.data))
      .catch(() => setError("Failed to fetch reports"))
      .finally(() => setLoading(false));
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-6">Historical Data</h1>
      <p className="text-gray-500 mb-8">View and download historical analytics reports</p>

      {/* Filters */}
      <div className="flex gap-4 mb-8">
        <select className="border rounded p-2" value={filters.year} onChange={(e) => handleFilterChange("year", e.target.value)}>
          <option value="2024">2024</option>
          <option value="2023">2023</option>
          <option value="2022">2022</option>
        </select>

        <input type="date" className="border rounded p-2" value={filters.startDate} onChange={(e) => handleFilterChange("startDate", e.target.value)} />
        <input type="date" className="border rounded p-2" value={filters.endDate} onChange={(e) => handleFilterChange("endDate", e.target.value)} />
      </div>

      {/* Loading/Error/Reports */}
      {loading && <p>Loading reports...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && reports.length === 0 && <p className="text-gray-500">No reports found for the selected filters.</p>}

      <div className="grid grid-cols-1 gap-4">
        {reports.map((report, idx) => (
          <div key={idx} className="flex justify-between items-center p-4 border rounded-lg shadow-md bg-white">
            <div className="flex flex-col">
              <span className="font-semibold text-lg">{report.name}</span>
              <span className="text-gray-500 text-sm">{report.date_range}</span>
            </div>
            <div className="flex gap-2">
              {/* View Button */}
              <button 
                className="border rounded px-4 py-2 text-sm hover:bg-gray-200"
                onClick={() => window.open(report.url_view, "_blank")}
              >
                <Eye className="w-4 h-4" />
              </button>

              {/* Download Button */}
              <button 
                className="border rounded px-4 py-2 text-sm hover:bg-gray-200"
                onClick={() => window.open(report.url_download, "_blank")}
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
