import React from 'react';
import { useNavigate } from 'react-router-dom';
import { clearTokens } from '../utils/auth';

function HomePage() {
  const navigate = useNavigate();

  const handleLogout = () => {
    clearTokens();
    navigate('/login');
  };

  const handleGoToAnalytics = () => {
    navigate('/analytics/seats');
  };

  const handleGoToManageCamera = () => {
    navigate('/settings/manage-camera');
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-white text-[#262626] space-y-6">
      <h1 className="text-3xl font-bold">Welcome 🎉</h1>
      <p className="text-[#494548] text-lg">You're successfully logged in.</p>

      <button
        onClick={handleGoToAnalytics}
        className="bg-blue-600 px-4 py-2 text-white rounded hover:bg-blue-700 font-semibold"
      >
        Go to Seat Analytics
      </button>

      <button
        onClick={handleGoToManageCamera}
        className="bg-blue-600 px-4 py-2 text-white rounded hover:bg-blue-700 font-semibold"
      >
        Go to Camera Management
      </button>


      <button
        onClick={handleLogout}
        className="bg-[#FF9500] px-4 py-2 text-white rounded hover:bg-orange-600 font-semibold"
      >
        Logout
      </button>
    </div>
  );
}

export default HomePage;
