
import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import AppPage from './pages/AppPage';
import NotFound from './pages/NotFound';

// Mock UI components for context (Toaster/Sonner/Tooltip)
const Toaster = () => <div id="toaster" className="fixed top-4 right-4 z-[9999]" />;
const Sonner = () => <div id="sonner" className="fixed bottom-4 right-4 z-[9999]" />;
const TooltipProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => <>{children}</>;

const App: React.FC = () => {
  return (
    <TooltipProvider>
      <AuthProvider>
        <Toaster />
        <Sonner />
        <HashRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route 
              path="/app" 
              element={
                <ProtectedRoute>
                  <AppPage />
                </ProtectedRoute>
              } 
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </HashRouter>
      </AuthProvider>
    </TooltipProvider>
  );
};

export default App;
