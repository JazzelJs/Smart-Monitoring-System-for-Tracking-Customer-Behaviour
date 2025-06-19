import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import OnboardingPage from './pages/OnboardingPage';
import HomePage from './pages/HomePage';
import AnalyticsPage from './pages/AnalyticsPage';
import PeakHourAnalytics from './pages/PeakHourAnalytics';
import ManageCameras from './pages/ManageCamera';
import CustomerAnalytics from './pages/CustomerAnalytics';
import ActivityLogPage from './pages/ActivityLog';
import HistoricalDataPage from './pages/HistoricalData';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import AnalyticsLayout from './components/AnalyticsContainer'; // ✅ NEW
import ForgotPasswordPage from './pages/ForgotPassword';

import useDetectionStatus from './hooks/UseDetection';

function App() {
  const isDetecting = useDetectionStatus();

  return (
    <Router>
      {isDetecting && (
        <div className="fixed top-0 right-0 bg-green-500 text-white px-4 py-2 rounded-bl-xl z-50">
          Detection Running...
        </div>
      )}
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        {/* Protected pages with standard layout */}
        <Route path="/dashboard" element={<ProtectedRoute><Layout><HomePage /></Layout></ProtectedRoute>} />
        <Route path="/onboarding" element={<ProtectedRoute><Layout><OnboardingPage /></Layout></ProtectedRoute>} />
        <Route path="/activity-log" element={<ProtectedRoute><Layout><ActivityLogPage /></Layout></ProtectedRoute>} />
        <Route path="/historical-data" element={<ProtectedRoute><Layout><HistoricalDataPage /></Layout></ProtectedRoute>} />
        <Route path="/settings/manage-camera" element={<ProtectedRoute><Layout><ManageCameras /></Layout></ProtectedRoute>} />
        {/* 🔁 Analytics Section with persistent video feed */}
        <Route path="/analytics" element={<ProtectedRoute><AnalyticsLayout /></ProtectedRoute>}>
          <Route path="seats" element={<AnalyticsPage />} />
          <Route path="peak-hour" element={<PeakHourAnalytics />} />
          <Route path="customer" element={<CustomerAnalytics />} />
        </Route>
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
