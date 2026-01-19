
import React from 'react';
import { Link } from 'react-router-dom';

const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-studio-bg p-6 text-center">
      <h1 className="text-[15vw] font-light tracking-tighter mb-4">404</h1>
      <p className="text-[10px] tracking-[0.3em] font-bold uppercase text-studio-muted mb-12">Path Not Located</p>
      <Link 
        to="/" 
        className="text-xs font-bold tracking-[0.2em] uppercase bg-black text-white px-10 py-5 rounded-full hover:bg-neutral-800 transition-all"
      >
        Return to Home
      </Link>
    </div>
  );
};

export default NotFound;
