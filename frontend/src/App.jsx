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
import ProtectedRoute from './components/ProtectedRoute';
import useDetectionStatus from './hooks/UseDetection';
import ActivityLogPage from './pages/ActivityLog';
import HistoricalDataPage from './pages/HistoricalData';

function App() {
  const isDetecting = useDetectionStatus();  // ⬅️ Add the hook here

  return (
    <Router>
      {/* Optional: Global UI based on detection */}
      {isDetecting && (
        <div className="fixed top-0 right-0 bg-green-500 text-white px-4 py-2 rounded-bl-xl z-50">
          Detection Running...
        </div>
      )}

      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* After Login */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          }
        />

        {/* After Signup */}
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <OnboardingPage />
            </ProtectedRoute>
          }
        />

        {/* Analytics */}
        <Route
          path="/analytics/seats"
          element={
            <ProtectedRoute>
              <AnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics/peak-hour"
          element={
            <ProtectedRoute>
              <PeakHourAnalytics />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics/customer"
          element={
            <ProtectedRoute>
              <CustomerAnalytics />
            </ProtectedRoute>
          }
        />
        {/* Activity Log */}
        <Route
          path="/activity-log"
          element={
            <ProtectedRoute>
              <ActivityLogPage />
            </ProtectedRoute>
          }
        />

      {/* Historical Data */}
      <Route
          path="/historical-data"
          element={
            <ProtectedRoute>
              <HistoricalDataPage/>
            </ProtectedRoute>
          }
        />

        {/* Manage Camera */}
        <Route
          path="/settings/manage-camera"
          element={
            <ProtectedRoute>
              <ManageCameras />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
