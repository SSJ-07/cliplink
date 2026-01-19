
import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar: React.FC = () => {
  const { user, login, logout, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      await login();
      navigate('/app');
    } catch (error: any) {
      // User cancelled or error occurred
      if (error.code !== 'auth/popup-closed-by-user' && error.code !== 'auth/cancelled-popup-request') {
        console.error('Login error:', error);
        alert('Failed to sign in. Please try again.');
      }
    }
  };

  return (
    <div className="fixed top-8 left-0 right-0 z-[100] flex justify-center px-6">
      <nav className="bg-white/80 backdrop-blur-xl border border-studio-border/50 h-16 px-8 flex items-center justify-between gap-12 rounded-full w-full max-w-4xl pill-shadow">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-2 h-2 bg-black rounded-full group-hover:scale-150 transition-transform duration-500" />
          <span className="text-sm font-bold tracking-[0.2em] uppercase">ClipLink</span>
        </Link>
        
        <div className="flex items-center gap-10">
          <div className="hidden md:flex items-center gap-8 text-[11px] font-bold tracking-[0.15em] uppercase text-studio-muted">
            {user && (
              <Link 
                to="/app" 
                className={`transition-colors hover:text-black ${location.pathname === '/app' ? 'text-black' : ''}`}
              >
                Studio
              </Link>
            )}
          </div>

          <div className="h-4 w-[1px] bg-studio-border hidden md:block" />

          <div className="flex items-center gap-6">
            {user ? (
              <button 
                onClick={logout}
                className="text-[11px] font-bold tracking-[0.15em] uppercase hover:opacity-50 transition-opacity"
              >
                Sign Out
              </button>
            ) : (
              <button 
                onClick={handleLogin}
                disabled={isLoading}
                className="text-[11px] font-bold tracking-[0.15em] uppercase hover:opacity-50 transition-opacity disabled:opacity-50"
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </button>
            )}
          </div>
        </div>
      </nav>
    </div>
  );
};

export default Navbar;
