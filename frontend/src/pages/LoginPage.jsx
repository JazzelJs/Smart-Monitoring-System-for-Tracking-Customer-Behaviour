import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { saveTokens } from '../utils/auth';
import ErrorModal from '../components/ErrorModal';

function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [showErrorModal, setShowErrorModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleLogin = async () => {
    try {
      const res = await api.post('/auth/login/', {
        email: form.email,
        password: form.password
      });
      saveTokens(res.data.access, res.data.refresh);
      navigate('/dashboard');
    } catch (error) {
      setErrorMessage('Invalid email or password.');
      setShowErrorModal(true);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <form className="w-full max-w-sm space-y-4" onSubmit={e => e.preventDefault()}>
        <h2 className="text-2xl font-bold text-center text-[#262626]">Login</h2>
        <input name="email" placeholder="Email" className="w-full p-2 border rounded" onChange={handleChange} required />
        <input name="password" type="password" placeholder="Password" className="w-full p-2 border rounded" onChange={handleChange} required />
        <button
          className="w-full bg-[#FF9500] text-white py-2 rounded hover:bg-orange-600"
          onClick={handleLogin}
        >
          Login
        </button>
        <p className="text-sm text-center text-[#494548]">
          Don’t have an account?{" "}
          <span
            onClick={() => navigate("/register")}
            className="text-[#FF9500] font-semibold cursor-pointer hover:underline"
          >
            Sign Up
          </span>
        </p>
      </form>

      {showErrorModal && (
        <ErrorModal
          title="Login Failed"
          message={errorMessage}
          onClose={() => setShowErrorModal(false)}
        />
      )}
    </div>
  );
}

export default LoginPage;
