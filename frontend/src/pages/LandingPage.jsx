import React from 'react';
import { useNavigate } from 'react-router-dom';

function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center space-y-6">
        <h1 className="text-3xl font-bold text-[#262626]">Welcome to Our Platform</h1>
        <p className="text-md text-[#494548]">Please choose an option to continue</p>

        <div className="space-y-3">
          <button
            onClick={() => navigate('/login')}
            className="w-64 py-2 px-4 bg-[#FF9500] hover:bg-orange-600 text-white font-semibold rounded"
          >
            Log In
          </button>
          <button
            onClick={() => navigate('/register')}
            className="w-64 py-2 px-4 border border-[#FF9500] text-[#FF9500] font-semibold rounded hover:bg-orange-50"
          >
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;
