// src/components/Layout.jsx
import React, { useEffect } from 'react';
import { ToastContainer } from 'react-toastify';
import { checkAndNotify } from '../utils/notifications';
import api from '../api';
import 'react-toastify/dist/ReactToastify.css';

export default function Layout({ children }) {
  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const res = await api.get('/analytics/peak-hours/');
        const { occupancy_percent, peak_hour } = res.data;

        checkAndNotify({
          occupancyPercent: occupancy_percent,
          peakHour: peak_hour, // e.g., "12:00 - 13:00"
        });
      } catch (error) {
        console.error("Notification check failed", error);
      }
    }

    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <ToastContainer position="top-right" autoClose={5000} />
      {children}
    </>
  );
}
