
import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Loader2, LogOut, Send, ExternalLink, Sparkles, Instagram, Music } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ApiResponse {
  primarySku: string;
  primaryLink: string;
  altLinks: string[];
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
          note: note
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setResult(data);
      toast({
        title: "Found it! 🎉",
        description: "We found some fire products for you!",
      });
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
        {result && (
          <Card className="border-0 shadow-xl bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-green-600">
                <Sparkles className="w-5 h-5" />
                <span>Found It! 🎉</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Primary Product */}
              <div className="p-6 bg-gradient-to-r from-purple-50 to-pink-50 rounded-2xl">
                <h3 className="font-bold text-lg text-gray-900 mb-2">Primary Match</h3>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-800">{result.primarySku}</p>
                    <p className="text-sm text-gray-600">This looks like the closest match!</p>
                  </div>
                  <Button asChild className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600">
                    <a href={result.primaryLink} target="_blank" rel="noopener noreferrer">
                      Shop Now <ExternalLink className="w-4 h-4 ml-2" />
                    </a>
                  </Button>
                </div>
              </div>

              {/* Alternative Products */}
              <div>
                <h3 className="font-bold text-lg text-gray-900 mb-4">Similar Vibes</h3>
                <div className="grid gap-4">
                  {result.altLinks.map((link, index) => (
                    <div key={index} className="p-4 bg-gray-50 rounded-xl flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-800">Alternative #{index + 1}</p>
                        <p className="text-sm text-gray-600">Another great option to consider</p>
                      </div>
                      <Button variant="outline" asChild>
                        <a href={link} target="_blank" rel="noopener noreferrer">
                          Check It Out <ExternalLink className="w-4 h-4 ml-2" />
                        </a>
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
};

export default App;
