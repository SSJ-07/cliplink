
import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Instagram, Music, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Home = () => {
  const { user, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  React.useEffect(() => {
    if (user) {
      navigate('/app');
    }
  }, [user, navigate]);

  const handleGetStarted = async () => {
    await signInWithGoogle();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 flex flex-col">
      {/* Header */}
      <header className="p-6 flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
            <Zap className="w-5 h-5 text-purple-600" />
          </div>
          <span className="text-white font-bold text-xl">ClipLink</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-8 flex justify-center space-x-4">
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl">
              <Instagram className="w-8 h-8 text-white" />
            </div>
            <div className="p-3 bg-white/20 backdrop-blur-sm rounded-2xl">
              <Music className="w-8 h-8 text-white" />
            </div>
          </div>

          <h1 className="text-5xl md:text-7xl font-black text-white mb-6 leading-tight">
            From Reel to
            <span className="block bg-gradient-to-r from-yellow-300 to-pink-300 bg-clip-text text-transparent">
              Real Deal
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-white/90 mb-8 max-w-2xl mx-auto leading-relaxed">
            Share any Instagram or TikTok reel, tell us what caught your eye, and get instant product links. 
            Shopping just got a major glow-up ✨
          </p>

          <div className="space-y-4">
            <Button
              onClick={handleGetStarted}
              size="lg"
              className="bg-white text-purple-600 hover:bg-gray-100 font-bold px-8 py-4 text-lg rounded-2xl shadow-xl hover:shadow-2xl transform hover:-translate-y-1 transition-all duration-200"
            >
              <Sparkles className="w-5 h-5 mr-2" />
              Get Started with Google
            </Button>
            
            <p className="text-white/70 text-sm">
              No cap, it's totally free and takes 2 seconds
            </p>
          </div>

          {/* Feature Highlights */}
          <div className="mt-16 grid md:grid-cols-3 gap-8">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
              <div className="w-12 h-12 bg-gradient-to-r from-pink-400 to-purple-400 rounded-xl flex items-center justify-center mb-4 mx-auto">
                <span className="text-2xl">🔗</span>
              </div>
              <h3 className="text-white font-bold text-lg mb-2">Drop That Link</h3>
              <p className="text-white/80 text-sm">Paste any IG or TikTok reel URL and we'll do the magic</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
              <div className="w-12 h-12 bg-gradient-to-r from-cyan-400 to-blue-400 rounded-xl flex items-center justify-center mb-4 mx-auto">
                <span className="text-2xl">💬</span>
              </div>
              <h3 className="text-white font-bold text-lg mb-2">Spill the Tea</h3>
              <p className="text-white/80 text-sm">Tell us what you're vibing with - the fit, the vibe, whatever!</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6">
              <div className="w-12 h-12 bg-gradient-to-r from-yellow-400 to-orange-400 rounded-xl flex items-center justify-center mb-4 mx-auto">
                <span className="text-2xl">🛍️</span>
              </div>
              <h3 className="text-white font-bold text-lg mb-2">Shop It Now</h3>
              <p className="text-white/80 text-sm">Get direct links to buy exactly what you saw - no more endless scrolling</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center">
        <p className="text-white/60 text-sm">
          Made for the culture, by the culture 💅
        </p>
      </footer>
    </div>
  );
};

export default Home;
