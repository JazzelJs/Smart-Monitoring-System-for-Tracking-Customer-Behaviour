import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { saveTokens } from '../utils/auth';

function LoginPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });

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
      console.error(error);
      alert('Login failed');
    }
  };
  return (
    <div className="min-h-screen flex items-center justify-center bg-white px-4">
      <form className="w-full max-w-sm space-y-4" onSubmit={e => e.preventDefault()}>
        <h2 className="text-2xl font-bold text-center text-[#262626]">Login</h2>
        <input name="email" placeholder="Email" className="w-full p-2 border rounded" onChange={handleChange} required />
        <input name="password" type="password" placeholder="Password" className="w-full p-2 border rounded" onChange={handleChange} required />
        <button className="w-full bg-[#FF9500] text-white py-2 rounded hover:bg-orange-600" onClick={handleLogin}>
          Login
        </button>
      </form>
    </div>
  );
}

export default LoginPage;
