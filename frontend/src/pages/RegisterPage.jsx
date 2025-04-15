import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { saveTokens } from '../utils/auth';
import OTPModal from '../components/OTPModal';

function RegisterPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: '',
    phone_number: '',
    email: '',
    password: '',
    passwordConfirm: '',
  });

  const [showOTPModal, setShowOTPModal] = useState(false);
  const [otpStatus, setOtpStatus] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // ✅ Register + send OTP (unified endpoint)
  const handleRegisterWithOTP = async () => {
    try {
      await api.post('auth/register/', form);
      setShowOTPModal(true);
    } catch (err) {
      if (err.response?.data?.error === 'Email already exists') {
        alert('Email already exists. Try logging in.');
      } else {
        alert('Failed to register.');
        console.error('Register error:', err.response?.data || err.message);
      }
    }
  };

  // ✅ OTP verification, password confirmation, login
  const handleVerifyAndRegister = async (otp) => {
    try {
      const res = await api.post('auth/verify-otp/', { email: form.email, otp });
  
      if (res.status === 200) {
        setOtpStatus('success');
  
        setTimeout(async () => {
          try {
            await api.post('auth/set-new-password/', {
              email: form.email,
              new_password: form.password,
            });
  
            const loginRes = await api.post('auth/login/', {
              email: form.email,
              password: form.password,
            });
  
            saveTokens(loginRes.data.access, loginRes.data.refresh);
            setShowOTPModal(false);
            navigate('/onboarding');
          } catch (error) {
            console.error('Error during post-OTP steps:', error);
            setOtpStatus('error');
          }
        }, 2000);
      } else {
        // In case server returns non-200 but no error thrown
        setOtpStatus('error');
      }
    } catch (err) {
      console.error("OTP verification failed:", err);
      setOtpStatus('error');
    }
  };
  

  return (
    <div className="min-h-screen bg-white flex items-center justify-center px-4 relative">
      <button
        onClick={() => navigate('/login')}
        className="absolute top-6 right-6 text-[#FF9500] font-medium text-sm"
      >
        Login
      </button>

      <form
        className="w-full max-w-md space-y-5"
        onSubmit={(e) => e.preventDefault()}
      >
        <h2 className="text-2xl font-bold text-center text-[#262626]">
          Create an account
        </h2>
        <p className="text-sm text-center text-[#494548]">
          Enter your details below to create your account
        </p>

        <div>
          <label className="text-sm text-[#494548] block mb-1">Full Name</label>
          <input
            name="name"
            placeholder="John Doe"
            className="w-full p-2 border border-gray-300 rounded"
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label className="text-sm text-[#494548] block mb-1">Handphone</label>
          <input
            name="phone_number"
            placeholder="+62 812 3456 7890"
            className="w-full p-2 border border-gray-300 rounded"
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label className="text-sm text-[#494548] block mb-1">Email</label>
          <input
            name="email"
            type="email"
            placeholder="name@example.com"
            className="w-full p-2 border border-gray-300 rounded"
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label className="text-sm text-[#494548] block mb-1">Password</label>
          <input
            name="password"
            type="password"
            placeholder="Password"
            className="w-full p-2 border border-gray-300 rounded"
            onChange={handleChange}
            required
          />
        </div>

        <div>
          <label className="text-sm text-[#494548] block mb-1">
            Password Confirmation
          </label>
          <input
            name="passwordConfirm"
            type="password"
            placeholder="Confirm Password"
            className="w-full p-2 border border-gray-300 rounded"
            onChange={handleChange}
            required
          />
        </div>

        <button
          className="w-full bg-[#FF9500] text-white py-2 font-semibold rounded hover:bg-orange-600"
          onClick={handleRegisterWithOTP}
        >
          Sign Up
        </button>

        <p className="text-xs text-center text-[#494548] pt-2">
          By clicking continue, you agree to our{' '}
          <span className="underline cursor-pointer">Terms of Service</span> and{' '}
          <span className="underline cursor-pointer">Privacy Policy</span>.
        </p>
      </form>

      {showOTPModal && (
        <OTPModal
          email={form.email}
          onSubmit={handleVerifyAndRegister}
          onClose={() => setShowOTPModal(false)}
          otpStatus={otpStatus}
        />
      )}
    </div>
  );
}

export default RegisterPage;
