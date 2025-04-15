import React, { useState, useEffect } from 'react';
import api from '../api'; // ✅ Axios instance

function OTPModal({ email, onSubmit, onClose, otpStatus }) {
  const [otp, setOtp] = useState('');
  const [secondsLeft, setSecondsLeft] = useState(30);
  const [isResending, setIsResending] = useState(false);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setSecondsLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setVerifying(true);
    await onSubmit(otp); // from parent
    setVerifying(false);
  };

  const handleResend = async () => {
    setIsResending(true);
    try {
      await api.post('/reset-password/', { email }); // ✅ using your axios instance
      setSecondsLeft(30);
    } catch (err) {
      alert('Failed to resend OTP');
      console.error(err);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-sm">
        <h2 className="text-lg font-semibold text-[#262626]">OTP Required</h2>
        <p className="text-sm text-[#494548] mb-4">
          Enter the 6-digit code sent to <strong>{email}</strong>
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded"
            placeholder="Enter OTP"
            required
          />

          {otpStatus === 'success' && (
            <div className="text-green-600 text-sm font-medium flex items-center gap-1">
              ✅ OTP Verified! Redirecting...
            </div>
          )}

          {otpStatus === 'error' && (
            <div className="text-red-600 text-sm font-medium">
              ❌ Invalid OTP. Please try again.
            </div>
          )}

          <button
            type="submit"
            disabled={verifying}
            className={`w-full text-white py-2 font-semibold rounded ${
              verifying ? 'bg-orange-800' : 'bg-[#FF9500] hover:bg-orange-600'
            }`}
          >
            {verifying ? 'Verifying...' : 'Submit'}
          </button>
        </form>

        <div className="flex justify-between items-center text-sm text-[#494548] mt-4">
          {secondsLeft > 0 ? (
            <span className="text-gray-500">Resend OTP in ({secondsLeft})</span>
          ) : (
            <button
              onClick={handleResend}
              disabled={isResending}
              className="text-[#FF9500] hover:underline"
            >
              {isResending ? 'Resending...' : 'Resend OTP'}
            </button>
          )}
          <button onClick={onClose} className="text-gray-400 hover:text-black">
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default OTPModal;
