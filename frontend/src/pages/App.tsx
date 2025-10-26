
import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Loader2, LogOut, Send, Sparkles, Instagram, Music } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { ProductResults } from '@/components/ProductResults';
import { Product } from '@/components/ProductCard';

interface DetectedLabel {
  label: string;
  confidence: number;
}

interface ApiResponse {
  products: Product[];
  count: number;
  detected_labels?: DetectedLabel[];
  detected_brand?: string;
  // Legacy support
  primarySku?: string;
  primaryLink?: string;
  altLinks?: string[];
}

const App = () => {
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const [url, setUrl] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ApiResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      toast({
        title: "Hold up! 🤚",
        description: "You gotta drop that reel URL first!",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
      const response = await fetch(`${apiUrl}/api/analyze-reel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          note: note,
          num_frames: 3  // Extract 3 frames for better analysis
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setResult(data);
      
      const productCount = data.products?.length || 0;
      toast({
        title: "Found it! 🎉",
        description: `We found ${productCount} amazing product${productCount !== 1 ? 's' : ''} for you!`,
      });

      // Scroll to results
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    } catch (error) {
      console.error('Error:', error);
      toast({
        title: "Oops! Something went wrong 😅",
        description: error instanceof Error ? error.message : "Try again in a sec - our servers might be taking a little nap",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const isValidUrl = (url: string) => {
    return url.includes('instagram.com') || url.includes('tiktok.com');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-purple-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
              ClipLink
            </h1>
          </div>
          
          <div className="flex items-center space-x-3">
            <Avatar className="w-8 h-8">
              <AvatarImage src={user?.photoURL || ''} />
              <AvatarFallback className="bg-gradient-to-r from-purple-400 to-pink-400 text-white text-sm">
                {user?.displayName?.charAt(0) || 'U'}
              </AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium text-gray-700 hidden sm:block">
              {user?.displayName?.split(' ')[0] || 'Hey there!'}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={logout}
              className="text-gray-600 hover:text-purple-600"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-4">
            What's got you
            <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent"> obsessed</span>?
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Drop that reel URL and spill what caught your eye. We'll find you the exact products to recreate the look! 
          </p>
        </div>

        {/* Main Form */}
        <Card className="mb-8 border-0 shadow-xl bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center space-x-2 text-xl">
              <div className="flex space-x-2">
                <Instagram className="w-5 h-5 text-pink-500" />
                <Music className="w-5 h-5 text-purple-500" />
              </div>
              <span>Share Your Reel</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Reel URL <span className="text-red-500">*</span>
                </label>
                <Input
                  type="url"
                  placeholder="https://instagram.com/reel/... or https://tiktok.com/@..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className={`h-12 text-base ${
                    url && !isValidUrl(url) 
                      ? 'border-red-300 focus:border-red-500' 
                      : 'border-purple-200 focus:border-purple-500'
                  }`}
                />
                {url && !isValidUrl(url) && (
                  <p className="text-red-500 text-sm mt-1">
                    Please use an Instagram or TikTok URL
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  What caught your eye? (Optional)
                </label>
                <Textarea
                  placeholder="The pink cargo pants are everything! Also loving that top... 💅"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="min-h-[100px] text-base border-purple-200 focus:border-purple-500"
                />
                <p className="text-gray-500 text-sm mt-1">
                  Be specific! The more details, the better we can help you find it.
                </p>
              </div>

              <Button
                type="submit"
                disabled={loading || !url.trim() || !isValidUrl(url)}
                className="w-full h-12 text-base font-semibold bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Finding your products...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Find My Products
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Results */}
        {result && result.products && result.products.length > 0 && (
          <div id="results" className="scroll-mt-8">
            <ProductResults 
              products={result.products}
              detectedLabels={result.detected_labels}
              detectedBrand={result.detected_brand}
            />
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
