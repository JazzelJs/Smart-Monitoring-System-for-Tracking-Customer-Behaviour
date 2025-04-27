import React, { useState, useEffect, useRef } from "react";
import html2canvas from "html2canvas-pro";

import jsPDF from "jspdf";
import api from "../api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, Legend
} from "recharts";

export default function ReportPreview({ year, month, onClose }) {
  const [reportData, setReportData] = useState(null);
  const reportRef = useRef();

  useEffect(() => {
    api.get(`/analytics/monthly-report/${year}/${month}/`).then((res) => {
      setReportData(res.data);
    });
  }, [year, month]);

  const downloadPDF = async () => {
    const input = reportRef.current;
    if (!input) {
      console.error("reportRef is null!");
      return;
    }
  
    const canvas = await html2canvas(input, { scale: 2 }); // Higher scale = better quality
    const imgData = canvas.toDataURL("image/png");
  
    const pdf = new jsPDF("p", "mm", "a4");
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
  
    const imgWidth = pdfWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;
  
    let heightLeft = imgHeight;
    let position = 0;
  
    pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
    heightLeft -= pdfHeight;
  
    while (heightLeft > 0) {
      position -= pdfHeight;
      pdf.addPage();
      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;
    }
  
    pdf.save(`report_${year}_${month}_preview.pdf`);
  };
  
  
  // === Merge Functions for Traffic Comparisons ===
  const mergeDailyTraffic = () => {
    const thisMonth = reportData.daily_visitor_traffic.this_month;
    const lastMonth = reportData.daily_visitor_traffic.last_month;
    return thisMonth.map((day, index) => ({
      day: day.day,
      this_month: day.count,
      last_month: lastMonth[index] ? lastMonth[index].count : 0,
    }));
  };

  const mergeHourlyTraffic = () => {
    const thisMonth = reportData.hourly_visitor_traffic.this_month;
    const lastMonth = reportData.hourly_visitor_traffic.last_month;
    return thisMonth.map((hour, index) => ({
      hour: hour.hour,
      this_month: hour.count,
      last_month: lastMonth[index] ? lastMonth[index].count : 0,
    }));
  };

  const mergeMonthlyTrends = () => {
    return reportData.monthly_visitor_trends.map((item) => {
      const date = new Date(item.month);
      const monthName = date.toLocaleString('default', { month: 'short' }); // e.g., "Feb"

      return {
        month: monthName,
        this_month: (monthName === "Mar") ? item.count : 0,
        last_month: (monthName === "Feb") ? item.count : 0,
      };
    });
  };


  if (!reportData) return <p className="text-center">Loading report...</p>;

  return (
    <div>
      <div className="flex justify-between mb-4">
        <h2 className="text-3xl font-bold">{`March ${year} Reports`}</h2>
        <div className="flex gap-2">
          <button className="bg-red-500 text-white px-4 py-1 rounded" onClick={onClose}>Close</button>
          <button className="bg-blue-600 text-white px-4 py-1 rounded" onClick={downloadPDF}>Download PDF</button>
        </div>
      </div>

      <p className="mb-4 text-gray-600">Generated on: {new Date().toLocaleDateString()}</p>

      <div ref={reportRef} className="bg-gray-50 p-6 rounded-xl shadow space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard title="Total Visitors" value={reportData.total_visitors} color="text-orange-500" />
          <SummaryCard title="Peak Hour" value={reportData.peak_hour} color="text-orange-500" />
          <SummaryCard title="Returning Customers" value={`${reportData.returning_customers_percentage}%`} color="text-orange-500" />
          <SummaryCard title="Avg Visit Duration" value={reportData.average_visit_duration} color="text-orange-500" />
        </div>

        {/* Daily Traffic */}
        <ChartBlock title="Daily Visitor Traffic">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={mergeDailyTraffic()}>
              <XAxis dataKey="day" />
              <YAxis />
              <Tooltip />
              <Legend />

              <Bar dataKey="last_month" fill="#494548" name="February" />
              <Bar dataKey="this_month" fill="#FF9500" name="March" />
            </BarChart>
          </ResponsiveContainer>
        </ChartBlock>

        {/* Hourly Traffic */}
        <ChartBlock title="Hourly Visitor Traffic">
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={mergeHourlyTraffic()}>
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Legend />

              <Line type="monotone" dataKey="last_month" stroke="#494548" strokeWidth={2} name="February" />
              <Line type="monotone" dataKey="this_month" stroke="#FF9500" strokeWidth={2} name="March" />
            </LineChart>
          </ResponsiveContainer>
        </ChartBlock>

        // Monthly Trends Chart
        <ChartBlock title="Monthly Visitor Trends">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={mergeMonthlyTrends()}>
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="this_month" fill="#FF9500" name="March" />
              <Bar dataKey="last_month" fill="#494548" name="February" />
            </BarChart>
          </ResponsiveContainer>
        </ChartBlock>
      </div>
    </div>
  );
}

function SummaryCard({ title, value, color }) {
  return (
    <div className="p-4 rounded-lg shadow bg-white">
      <p className="text-sm text-gray-500">{title}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function ChartBlock({ title, children }) {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {children}
    </div>
  );
}
