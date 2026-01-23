
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import Navbar from '@/components/Navbar';

const Home: React.FC = () => {
  const { user, login, isLoading } = useAuth();
  const navigate = useNavigate();
  const [demoStep, setDemoStep] = useState(0); // 0: Paste/Type, 1: Analyzing, 2: Result
  const [analysisSubStep, setAnalysisSubStep] = useState(0);
  const [typingText, setTypingText] = useState('');
  const [isSendClicked, setIsSendClicked] = useState(false);
  const fullPromptText = "i want that brown jacket";

  // Sequential Animation Controller
  useEffect(() => {
    let timeoutId: number;

    const runSequence = () => {
      // Step 0: Typing
      setDemoStep(0);
      setTypingText('');
      setIsSendClicked(false);
      
      let charIndex = 0;
      const typingInterval = setInterval(() => {
        if (charIndex < fullPromptText.length) {
          setTypingText(fullPromptText.slice(0, charIndex + 1));
          charIndex++;
        } else {
          clearInterval(typingInterval);
          // 1. Shorter pause after typing (800ms)
          timeoutId = window.setTimeout(() => {
            // 2. Animate send button
            setIsSendClicked(true);
            timeoutId = window.setTimeout(() => {
              startAnalysis();
            }, 400); // Duration of send click animation
          }, 800);
        }
      }, 70);
    };

    const startAnalysis = () => {
      setDemoStep(1);
      setAnalysisSubStep(0);
      
      // Sequence the analysis texts strictly
      timeoutId = window.setTimeout(() => {
        setAnalysisSubStep(1);
        timeoutId = window.setTimeout(() => {
          setAnalysisSubStep(2);
          timeoutId = window.setTimeout(() => {
            showResult();
          }, 1500);
        }, 1200);
      }, 1200);
    };

    const showResult = () => {
      setDemoStep(2);
      timeoutId = window.setTimeout(() => {
        runSequence(); // Loop back to start after showing result
      }, 4000);
    };

    runSequence();
    return () => clearTimeout(timeoutId);
  }, []);

  const analysisTexts = ["Analyzing reel", "Visual processing", "Finding Product"];

  const handleStart = async () => {
    if (user) {
      navigate('/app');
    } else {
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
    }
  };

  return (
    <div className="min-h-screen bg-studio-bg selection:bg-black selection:text-white">
      <style>{`
        @keyframes ripple {
          0% {
            transform: translate(-50%, -50%) scale(0.9);
            opacity: 0.5;
          }
          100% {
            transform: translate(-50%, -50%) scale(1.5);
            opacity: 0;
          }
        }
        /* Hide scrollbar */
        body {
          overflow-y: scroll;
        }
        body::-webkit-scrollbar {
          display: none;
        }
        body {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
      <Navbar />
      
      <main className="px-6">
        <div className="max-w-7xl mx-auto">
          <div className="min-h-[calc(100vh-80px)] flex items-center pt-24 mb-16">
            <div className="relative grid grid-cols-1 lg:grid-cols-12 gap-16 items-center w-full">
              {/* Vertical Editorial Divider */}
              <div className="hidden lg:block absolute left-[calc(58.33%+1rem)] top-1/2 -translate-y-1/2 w-[1.5px] h-[70%] bg-neutral-400/20 pointer-events-none" />
              
              {/* Left Content */}
              <div className="lg:col-span-7">
                <h1 className="text-7xl md:text-[8vw] font-cinzel font-bold leading-[0.9] tracking-tighter mb-12 uppercase">
                  REEL <span className="font-light italic text-studio-muted lowercase">to</span> <br />
                  REALITY<span className="inline-block w-4 h-4 bg-black rounded-full ml-4" />
                </h1>
                <p className="text-xl md:text-2xl font-light leading-relaxed text-studio-text mb-12 max-w-xl">
                  A digital bridge between social discovery and personal curation. Instantly identify products from any Instagram or TikTok reel.
                </p>
                <button 
                  onClick={handleStart}
                  disabled={isLoading}
                  className="group relative flex items-center gap-6 bg-black text-white px-10 py-6 rounded-full overflow-hidden hover:pr-14 transition-all duration-500 disabled:opacity-50"
                >
                  <span className="text-xs font-bold tracking-[0.2em] uppercase">
                    {isLoading ? 'Accessing Studio...' : 'Start Discovery'}
                  </span>
                  <span className="absolute right-6 opacity-0 group-hover:opacity-100 transition-all duration-500 transform translate-x-4 group-hover:translate-x-0 text-xl">
                    →
                  </span>
                </button>
              </div>

              {/* Right: Studio Demo Animation Box */}
              <div className="lg:col-span-5 flex justify-center lg:justify-end">
                <div className="relative w-full max-w-[360px] scale-90 origin-center lg:origin-right aspect-[9/16] bg-white rounded-[2.5rem] p-3 border border-studio-border pill-shadow overflow-hidden group">
                  <div className="relative h-full w-full rounded-[2rem] overflow-hidden bg-neutral-100">
                    <video 
                      autoPlay 
                      muted 
                      loop 
                      playsInline 
                      className={`absolute inset-0 w-full h-full object-cover grayscale brightness-75 transition-all duration-1000 ${demoStep === 0 ? 'blur-md opacity-20' : 'blur-0 opacity-100'}`}
                      onError={(e) => {
                        // Silently handle video load errors (404, network issues, etc.)
                        (e.target as HTMLVideoElement).style.display = 'none';
                      }}
                    >
                      <source src="https://cdn.pixabay.com/video/2023/11/02/187494-880097103_large.mp4" type="video/mp4" />
                    </video>

                    <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                      
                      {/* STEP 0: PASTE URL & TYPING PROMPT */}
                      <div className={`absolute inset-0 flex flex-col items-center justify-center transition-all duration-700 px-6 ${demoStep === 0 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                        <div className="w-11/12 bg-white p-4 rounded-2xl border border-studio-border shadow-lg space-y-3">
                           <div className="flex items-center gap-2 mb-1">
                              <div className="w-3 h-3 bg-neutral-200 rounded-full" />
                              <div className="w-20 h-2 bg-neutral-100 rounded-full" />
                           </div>
                           <div className="h-9 bg-neutral-50 rounded-lg flex items-center px-3 overflow-hidden border border-neutral-100">
                              <span className="text-[9px] text-neutral-400 font-mono truncate italic">instagram.com/reel/C8x2...</span>
                           </div>
                           
                           {/* Typing Prompt Box */}
                           <div className="relative h-10 bg-white border border-neutral-100 rounded-lg flex items-center px-3 pr-10 shadow-inner">
                              <span className="text-[10px] text-black font-medium">
                                {typingText}
                                <span className={`animate-pulse ${typingText.length === fullPromptText.length ? 'hidden' : ''}`}>|</span>
                              </span>
                              <div className={`absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 bg-black rounded-md flex items-center justify-center transition-all duration-300 ${isSendClicked ? 'scale-90 bg-neutral-700' : 'scale-100 opacity-80'}`}>
                                 <span className="text-white text-[10px]">→</span>
                              </div>
                           </div>
                        </div>
                      </div>

                      {/* STEP 1: ANALYZING */}
                      <div className={`absolute inset-0 flex flex-col items-center justify-center transition-all duration-700 ${demoStep === 1 ? 'opacity-100 scale-100' : 'opacity-0 scale-90'}`}>
                        <div className="w-48 h-48 border border-white/40 rounded-full animate-[ping_3s_infinite] flex items-center justify-center">
                           <div className="w-32 h-32 border border-white/60 rounded-full animate-[ping_2s_infinite]" />
                        </div>
                        
                        {/* Subtle ripple effect behind loading text */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 rounded-full border-[2.5px] border-white/50 animate-[ripple_2s_ease-out_infinite]" />
                          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 rounded-full bg-white/50 animate-[ripple_2s_ease-out_infinite] [animation-delay:0.5s]" />
                          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 rounded-full border-[2.5px] border-white/40 animate-[ripple_2s_ease-out_infinite] [animation-delay:1s]" />
                        </div>
                        
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white/90 backdrop-blur-md px-5 py-2.5 rounded-full border border-studio-border shadow-xl z-10">
                          <span className="text-[10px] font-bold tracking-[0.2em] uppercase flex items-center gap-2 whitespace-nowrap">
                            <span className="w-1.5 h-1.5 bg-black rounded-full animate-pulse" />
                            {analysisTexts[analysisSubStep]}
                          </span>
                        </div>
                      </div>

                      {/* STEP 2: RESULT */}
                      <div className={`absolute bottom-6 left-6 right-6 transition-all duration-700 ${demoStep === 2 ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-12'}`}>
                        <div className="bg-white p-4 flex gap-4 items-center rounded-2xl border border-studio-border shadow-2xl">
                          <div className="w-12 h-16 bg-neutral-200 rounded-lg overflow-hidden shrink-0">
                            <img src="https://images.unsplash.com/photo-1591047139829-d91aecb6caea?q=80&w=200&auto=format&fit=crop" className="w-full h-full object-cover" alt="Product" />
                          </div>
                          <div className="space-y-1 flex-1">
                            <div className="flex justify-between items-start">
                              <p className="text-[8px] font-bold tracking-widest text-studio-muted uppercase">Jil Sander</p>
                              <span className="text-[10px] font-bold text-black">$2,450</span>
                            </div>
                            <p className="text-[10px] font-medium leading-tight">Tailored Wool Blend Blazer</p>
                            <div className="pt-1">
                               <div className="h-6 bg-black rounded flex items-center justify-center">
                                  <span className="text-[8px] font-bold text-white uppercase tracking-tighter">Shop Now</span>
                               </div>
                            </div>
                          </div>
                        </div>
                      </div>

                    </div>

                    <div className="absolute inset-0 bg-gradient-to-t from-black/20 via-transparent to-transparent pointer-events-none" />
                    <div className="absolute top-6 left-6 pointer-events-none">
                       <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-studio-border pt-20 pb-32 grid grid-cols-1 md:grid-cols-2 gap-16">
            {[
              { title: "Visual AI", desc: "Proprietary recognition of textures, brands, and silhouettes." },
              { title: "Direct Links", desc: "Automated routing to verified luxury and high-street retailers." }
            ].map((feature, i) => (
              <div key={i} className="space-y-4">
                <span className="text-[10px] font-bold text-studio-muted">0{i+1}</span>
                <h3 className="text-lg font-bold tracking-tight uppercase">{feature.title}</h3>
                <p className="text-sm font-light leading-relaxed text-studio-muted">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-studio-border py-20 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start gap-12">
          <div className="space-y-6">
            <h2 className="text-xl font-bold tracking-tighter uppercase">ClipLink.</h2>
            <p className="text-xs text-studio-muted max-w-xs leading-relaxed">
              Curating the future of social commerce through advanced visual intelligence.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-20">
            <div className="space-y-4">
              <span className="text-[10px] font-bold uppercase tracking-widest text-studio-muted">Contact</span>
              <div className="flex flex-col text-xs font-medium space-y-2">
                <a href="#" className="hover:underline">Press</a>
                <a href="#" className="hover:underline">Studio</a>
              </div>
            </div>
            <div className="space-y-4">
              <span className="text-[10px] font-bold uppercase tracking-widest text-studio-muted">Social</span>
              <div className="flex flex-col text-xs font-medium space-y-2">
                <a href="#" className="hover:underline">Instagram</a>
                <a href="#" className="hover:underline">Twitter</a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
