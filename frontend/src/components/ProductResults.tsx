import React from 'react';
import { ProductCard, Product } from './ProductCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Tag } from 'lucide-react';

interface DetectedLabel {
  label: string;
  confidence: number;
}

interface ProductResultsProps {
  products: Product[];
  detectedLabels?: DetectedLabel[];
  detectedBrand?: string;
}

export const ProductResults: React.FC<ProductResultsProps> = ({ 
  products, 
  detectedLabels,
  detectedBrand
}) => {
  if (!products || products.length === 0) {
    return null;
  }

  const primaryProduct = products[0];
  const alternativeProducts = products.slice(1);

  return (
    <div className="space-y-8">
      {/* Detected Brand Section */}
      {detectedBrand && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-blue-50 to-purple-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Sparkles className="w-6 h-6 text-blue-600" />
              <div>
                <div className="text-sm text-gray-600">Brand Detected</div>
                <div className="text-xl font-bold text-gray-900 capitalize">
                  {detectedBrand}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detected Labels Section */}
      {detectedLabels && detectedLabels.length > 0 && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-purple-50 to-pink-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Tag className="w-5 h-5 text-purple-600" />
              <span>What We Found in Your Reel</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {detectedLabels.slice(0, 8).map((label, index) => (
                <Badge 
                  key={index} 
                  variant="secondary" 
                  className="text-sm py-1 px-3"
                >
                  {label.label}
                  <span className="ml-2 text-xs opacity-70">
                    {Math.round(label.confidence * 100)}%
                  </span>
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Primary Product - Featured */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-6 h-6 text-purple-600" />
          <h2 className="text-2xl font-bold text-gray-900">
            Best Match
          </h2>
        </div>
        <div className="max-w-xl mx-auto shadow-md rounded-2xl overflow-hidden border border-purple-300">
          <ProductCard product={primaryProduct} isPrimary={true} />
        </div>
      </div>

      {/* Alternative Products */}
      {alternativeProducts.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            More Options
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {alternativeProducts.map((product, index) => (
              <ProductCard 
                key={product.product_url || product.title || index} 
                product={product}
                rank={index + 2}
              />
            ))}
          </div>
        </div>
      )}

      {/* CLIP Visual Verification Info */}
      {products.some(p => p.visual_similarity && p.visual_similarity > 0) && (
        <Card className="border-0 shadow-lg bg-gradient-to-r from-green-50 to-blue-50">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="text-3xl">🎯</div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  AI Visual Verification
                </h3>
                <p className="text-sm text-gray-600">
                  Products are verified using CLIP AI to ensure they visually match your reel. 
                  Higher percentages mean stronger visual similarity to what you saw in the video.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results Summary */}
      <Card className="border-0 shadow-lg bg-white/80">
        <CardContent className="p-4">
          <p className="text-sm text-gray-600 text-center">
            Found <span className="font-semibold text-purple-600">{products.length}</span> products 
            that match your reel. All prices and availability are subject to change.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

