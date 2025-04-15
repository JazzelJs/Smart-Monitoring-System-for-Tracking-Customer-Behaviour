import React from 'react';
import { Navigate } from 'react-router-dom';
import { getAccessToken } from '../utils/auth';

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = !!getAccessToken();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

export default ProtectedRoute;
