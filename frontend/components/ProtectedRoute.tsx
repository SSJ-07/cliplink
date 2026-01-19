
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-studio-bg">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-[1px] bg-black animate-pulse" />
          <span className="text-[10px] font-bold tracking-[0.3em] uppercase animate-pulse">Studio Init</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;
