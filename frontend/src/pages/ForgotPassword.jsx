import React, { useState } from "react";
import api from "../api";
import OTPModal from "../components/OTPModal";
import ErrorModal from "../components/ErrorModal";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpStatus, setOtpStatus] = useState("");
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [showResetForm, setShowResetForm] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");

  const handleSendOTP = async () => {
    try {
      await api.post("/auth/reset-password/", { email });
      setShowOTPModal(true);
    } catch {
      setError("Failed to send OTP. Please check your email.");
    }
  };

  const handleValidateOTP = async (otp) => {
    try {
      await api.post("/auth/validate-otp/", { email, otp });
      setOtpStatus("success");
      setShowOTPModal(false);
      setShowResetForm(true);
    } catch {
      setOtpStatus("error");
      setError("Invalid or expired OTP.");
    }
  };

  const handleResetPassword = async () => {
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      await api.post("/auth/set-new-password/", { email, new_password: password });
      alert("Password reset successful! Please login.");
      window.location.href = "/login";
    } catch {
      setError("Failed to reset password.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <div className="w-full max-w-md space-y-6">
        <h2 className="text-2xl font-bold text-center text-[#262626]">Forgot Password</h2>
        {!otpSent && (
          <>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 border rounded"
              required
            />
            <button className="w-full bg-[#FF9500] text-white py-2 rounded" onClick={handleSendOTP}>
              Send OTP
            </button>
          </>
        )}

        {showResetForm && (
          <>
            <input
              type="password"
              placeholder="New Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 border rounded"
              required
            />
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full p-2 border rounded"
              required
            />
            <button className="w-full bg-[#FF9500] text-white py-2 rounded" onClick={handleResetPassword}>
              Reset Password
            </button>
          </>
        )}

        {error && <p className="text-red-600 text-sm">{error}</p>}

        {showOTPModal && (
          <OTPModal
            email={email}
            onSubmit={handleValidateOTP}
            onClose={() => setShowOTPModal(false)}
            otpStatus={otpStatus}
          />
        )}
      </div>
    </div>
  );
}
