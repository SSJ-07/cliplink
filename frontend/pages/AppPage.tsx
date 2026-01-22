
import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { Product } from '@/types';
import { transformProduct, formatPrice, formatSimilarity } from '@/utils/transform';
import { analyzeReel as callAnalyzeReelApi } from '@/services/api';

const AppPage: React.FC = () => {
  const [url, setUrl] = useState('');
  const [prompt, setPrompt] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisSubStep, setAnalysisSubStep] = useState(0);
  const [products, setProducts] = useState<Product[]>([]);

  const hasStarted = isAnalyzing || products.length > 0;
  const analysisTexts = ["Extracting frames", "Understanding frame", "Searching products"];

  // Cycle through analysis steps when loading
  useEffect(() => {
    let interval: number;
    if (isAnalyzing) {
      setAnalysisSubStep(0);
      interval = window.setInterval(() => {
        setAnalysisSubStep(prev => (prev < 2 ? prev + 1 : prev));
      }, 1200);
    }
    return () => {
      clearInterval(interval);
    };
  }, [isAnalyzing]);

  const handleAnalyzeReel = async () => {
    if (!url.trim()) return;
    
    setIsAnalyzing(true);
    setProducts([]); // Clear existing results for new search
    
    try {
      // Use the API service which handles relative URLs correctly
      const data = await callAnalyzeReelApi(
        url,
        prompt || '',
        3 // num_frames
      );
      
      // Transform products to display format
      const transformedProducts = data.products.map(transformProduct);
      setProducts(transformedProducts);
    } catch (error: any) {
      console.error("Discovery failed", error);
      alert(`Error: ${error.message || 'Failed to analyze reel. Please try again.'}`);
      setProducts([]);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-studio-bg text-studio-text">
      <Navbar />
      
      <style>{`
        @keyframes custom-ripple {
          0% { transform: scale(0.6); opacity: 0; }
          40% { opacity: 0.1; }
          100% { transform: scale(2); opacity: 0; }
        }
        .animate-ripple {
          animation: custom-ripple 4s cubic-bezier(0.22, 1, 0.36, 1) infinite;
        }
      `}</style>

      <main className="pt-32 pb-32 px-6 overflow-x-hidden">
        <div className="max-w-6xl mx-auto">
          
          <div className={`relative w-full transition-all duration-[1200ms] ease-[cubic-bezier(0.22,1,0.36,1)] ${hasStarted ? 'h-32 mb-16' : 'h-[400px] mb-20'}`}>
            
            <div className={`absolute left-1/2 -translate-x-1/2 transition-all duration-[1200ms] ease-[cubic-bezier(0.22,1,0.36,1)] text-center w-full ${hasStarted ? 'top-1/2 -translate-y-1/2' : 'top-12'}`}>
              <span className="text-[10px] font-bold tracking-[0.4em] uppercase text-studio-muted block">Studio Workspace</span>
              <h2 className={`font-cinzel font-bold tracking-tight transition-all duration-[1200ms] ease-[cubic-bezier(0.22,1,0.36,1)] ${hasStarted ? 'text-2xl' : 'text-5xl'}`}>
                Product Discovery
              </h2>
            </div>

            <div className={`
              absolute transition-all duration-[1200ms] ease-[cubic-bezier(0.22,1,0.36,1)] 
              bg-white rounded-[24px] border border-studio-border pill-shadow overflow-hidden z-20 flex flex-col
              ${hasStarted 
                ? 'left-0 top-1/2 -translate-y-1/2 w-[340px] p-5 gap-4 opacity-100' 
                : 'left-1/2 top-[65%] -translate-x-1/2 -translate-y-1/2 w-full max-w-xl p-6 gap-4'
              }
            `}>
              
              <div className="relative">
                <input 
                  type="text" 
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste Instagram/TikTok URL..."
                  className={`w-full bg-neutral-50/50 border border-studio-border rounded-xl transition-all outline-none font-mono focus:bg-white focus:border-black ${hasStarted ? 'py-3 px-4 text-[10px]' : 'py-4 px-5 text-xs'}`}
                />
              </div>

              <div className="relative">
                <input 
                  type="text" 
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="What are we looking for?"
                  className={`w-full bg-white border border-studio-border rounded-xl transition-all outline-none shadow-sm focus:border-black ${hasStarted ? 'py-3.5 px-4 pr-12 text-xs' : 'py-5 px-5 pr-16 text-sm'}`}
                />
                <button 
                  onClick={handleAnalyzeReel}
                  disabled={isAnalyzing || !url}
                  className={`absolute right-1.5 top-1/2 -translate-y-1/2 bg-black text-white rounded-lg flex items-center justify-center hover:bg-neutral-800 transition-all disabled:opacity-20 shadow-lg ${hasStarted ? 'w-10 h-10' : 'w-12 h-12'}`}
                >
                  {isAnalyzing ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <span className={hasStarted ? 'text-lg' : 'text-xl'}>→</span>
                  )}
                </button>
              </div>
            </div>
          </div>

          <div className="relative">
            {isAnalyzing ? (
              <div className="fixed inset-0 z-50 flex items-center justify-center animate-in fade-in duration-700 pointer-events-none">
                <div className="relative flex items-center justify-center w-[600px] h-[600px]">
                  {/* Layered, light, consistent ripples */}
                  <div className="absolute inset-0 border border-black/10 rounded-full animate-ripple" />
                  <div className="absolute inset-0 border border-black/10 rounded-full animate-ripple [animation-delay:1s]" />
                  <div className="absolute inset-0 border border-black/10 rounded-full animate-ripple [animation-delay:2s]" />
                  <div className="absolute inset-0 border border-black/10 rounded-full animate-ripple [animation-delay:3s]" />
                  
                  {/* Center Status Indicator */}
                  <div className="relative z-10 bg-white/95 backdrop-blur-xl px-12 py-6 rounded-full border border-studio-border shadow-2xl flex items-center gap-6">
                    <span className="w-3 h-3 bg-black rounded-full animate-pulse" />
                    <span className="text-sm font-bold tracking-[0.3em] uppercase whitespace-nowrap min-w-[180px]">
                      {analysisTexts[analysisSubStep]}
                    </span>
                  </div>
                </div>
              </div>
            ) : products.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-12 gap-y-20 animate-in fade-in slide-in-from-bottom-12 duration-[1500ms] ease-[cubic-bezier(0.22,1,0.36,1)]">
                {products.map((product) => {
                  const imageUrl = product.image_url || product.imageUrl || '';
                  const productUrl = product.product_url || product.buyUrl || '#';
                  const productTitle = product.title || product.name || 'Product';
                  const productPrice = formatPrice(product.price, product.currency);
                  const brand = product.source || product.brand || 'Unknown';
                  const similarity = product.visual_similarity || product.similarity_score;
                  
                  return (
                    <div key={product.id} className="group cursor-crosshair">
                      <div className="relative aspect-[3/4] overflow-hidden bg-white border border-studio-border mb-8 shadow-sm">
                        <img 
                          src={imageUrl} 
                          alt={productTitle}
                          className="w-full h-full object-cover transition-transform duration-[2000ms] group-hover:scale-105"
                          onError={(e) => {
                            // Fallback image on error
                            (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x600?text=No+Image';
                          }}
                        />
                        {similarity && (
                          <div className="absolute top-4 right-4 bg-white/90 backdrop-blur px-3 py-1.5 rounded-full border border-studio-border">
                            <span className="text-[9px] font-bold tracking-wider uppercase">
                              {formatSimilarity(similarity)} Match
                            </span>
                          </div>
                        )}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-700" />
                        <div className="absolute bottom-6 left-6 right-6 opacity-0 group-hover:opacity-100 transform translate-y-6 group-hover:translate-y-0 transition-all duration-700 delay-100">
                          <a 
                            href={productUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block w-full bg-white/95 backdrop-blur text-center py-4 text-[10px] font-bold tracking-[0.2em] uppercase border border-studio-border hover:bg-black hover:text-white transition-colors"
                          >
                            Source Product
                          </a>
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-start gap-4 transition-all duration-700 group-hover:translate-x-1">
                        <div className="space-y-1">
                          <p className="text-[10px] font-bold tracking-widest text-studio-muted uppercase">{brand}</p>
                          <h3 className="text-sm font-medium tracking-tight group-hover:underline underline-offset-4 decoration-1">
                            {productTitle}
                          </h3>
                        </div>
                        <span className="text-xs font-bold">{productPrice}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-40 border-t border-studio-border space-y-4 opacity-40">
                <div className="w-16 h-[1px] bg-studio-border" />
                <p className="text-[10px] font-bold tracking-[0.5em] uppercase text-studio-muted">Ready for Curation</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default AppPage;
