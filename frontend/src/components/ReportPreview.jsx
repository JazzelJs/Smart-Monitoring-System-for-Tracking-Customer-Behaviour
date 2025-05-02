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

  const monthName = (y, m) => new Date(y, m - 1).toLocaleString('default', { month: 'long' });
  const currentMonthName = monthName(year, month);
  const previousMonthName = monthName(year, month - 1);

  const downloadPDF = async () => {
    const input = reportRef.current;
    if (!input) {
      console.error("reportRef is null!");
      return;
    }

    const canvas = await html2canvas(input, { scale: 2 });
    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF("p", "mm", "a4");
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = pdfWidth;
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    // === Header Info ===
    const generatedDate = new Date().toLocaleDateString();
    const cafeName = reportData?.cafe_name || "N/A";

    pdf.setFont("helvetica", "bold");
    pdf.setFontSize(16);
    pdf.text(`${currentMonthName} ${year} Report`, 14, 18);

    pdf.setFontSize(11);
    pdf.setFont("helvetica", "normal");
    pdf.text(`Café: ${cafeName}`, 14, 26);
    pdf.text(`Generated on: ${generatedDate}`, 14, 32);

    // === Image of Report Content ===
    let position = 40;
    pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
    let heightLeft = imgHeight - (pdfHeight - position);

    while (heightLeft > 0) {
      position -= pdfHeight;
      pdf.addPage();
      pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
      heightLeft -= pdfHeight;
    }

    pdf.save(`report_${year}_${month}_preview.pdf`);
  };

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
    const currentMonthShort = currentMonthName.slice(0, 3);
    const previousMonthShort = previousMonthName.slice(0, 3);

    return reportData.monthly_visitor_trends
      .filter(item => {
        const label = new Date(item.month).toLocaleString('default', { month: 'short' });
        return label === currentMonthShort || label === previousMonthShort;
      })
      .map(item => {
        const label = new Date(item.month).toLocaleString('default', { month: 'short' });
        return {
          month: label,
          [label === currentMonthShort ? "this_month" : "last_month"]: item.count
        };
      });
  };

  if (!reportData) return <p className="text-center">Loading report...</p>;

  return (
    <div>
      <div className="flex justify-between mb-4">
        <div>
          <h2 className="text-3xl font-bold">{`${currentMonthName} ${year} Reports`}</h2>
          <p className="text-gray-600">{`Café: ${reportData.cafe_name || "N/A"}`}</p>
          <p className="text-gray-500">Generated on: {new Date().toLocaleDateString()}</p>
        </div>
        <div className="flex gap-2">
          <button className="bg-red-500 text-white px-4 py-1 rounded" onClick={onClose}>Close</button>
          <button className="bg-blue-600 text-white px-4 py-1 rounded" onClick={downloadPDF}>Download PDF</button>
        </div>
      </div>

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
              <Bar dataKey="last_month" fill="#494548" name={previousMonthName} />
              <Bar dataKey="this_month" fill="#FF9500" name={currentMonthName} />
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
              <Line type="monotone" dataKey="last_month" stroke="#494548" strokeWidth={2} name={previousMonthName} />
              <Line type="monotone" dataKey="this_month" stroke="#FF9500" strokeWidth={2} name={currentMonthName} />
            </LineChart>
          </ResponsiveContainer>
        </ChartBlock>

        {/* Monthly Trends */}
        <ChartBlock title="Monthly Visitor Trends">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={mergeMonthlyTrends()}>
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="this_month" fill="#FF9500" name={currentMonthName} />
              <Bar dataKey="last_month" fill="#494548" name={previousMonthName} />
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
