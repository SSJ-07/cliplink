import React from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, Star, TrendingUp } from 'lucide-react';

export interface Product {
  id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  image_url: string;
  product_url: string;
  similarity_score?: number;
  visual_similarity?: number;  // CLIP visual match score
  tags?: string[];
  source?: string;
}

interface ProductCardProps {
  product: Product;
  rank?: number;
  isPrimary?: boolean;
}

export const ProductCard: React.FC<ProductCardProps> = ({ 
  product, 
  rank, 
  isPrimary = false 
}) => {
  const formatPrice = (price: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(price);
  };

  const getMatchBadge = (score?: number) => {
    if (!score) return null;
    
    const percentage = Math.round(score * 100);
    let variant: "default" | "secondary" | "destructive" | "outline" = "default";
    let label = "Good Match";
    
    if (percentage >= 90) {
      variant = "default";
      label = "Perfect Match";
    } else if (percentage >= 75) {
      variant = "secondary";
      label = "Great Match";
    } else if (percentage >= 60) {
      variant = "outline";
      label = "Good Match";
    }
    
    return (
      <Badge variant={variant} className="flex items-center gap-1">
        <Star className="w-3 h-3" fill="currentColor" />
        {label} ({percentage}%)
      </Badge>
    );
  };

  const getVisualMatchBadge = (score?: number) => {
    if (!score || score === 0) return null;
    
    const percentage = Math.round(score * 100);
    let bgColor = "bg-green-100 text-green-800";
    let label = "Visual Match";
    
    if (percentage >= 80) {
      bgColor = "bg-green-500 text-white";
      label = "Excellent Match";
    } else if (percentage >= 60) {
      bgColor = "bg-blue-500 text-white";
      label = "Good Match";
    } else if (percentage >= 40) {
      bgColor = "bg-yellow-500 text-white";
      label = "Fair Match";
    }
    
    return (
      <Badge className={`${bgColor} font-semibold`}>
        🎯 {percentage}% {label}
      </Badge>
    );
  };

  return (
    <Card className={`overflow-hidden transition-all hover:shadow-lg ${
      isPrimary ? 'ring-2 ring-purple-500' : ''
    }`}>
      <CardHeader className="p-0">
        {/* Product Image */}
        <div className="relative aspect-square bg-gray-100">
          <img
            src={product.image_url}
            alt={product.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 
                'https://via.placeholder.com/400x400?text=Product+Image';
            }}
          />
          {isPrimary && (
            <div className="absolute top-2 left-2">
              <Badge className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                <TrendingUp className="w-3 h-3 mr-1" />
                Top Match
              </Badge>
            </div>
          )}
          {rank && !isPrimary && (
            <div className="absolute top-2 left-2">
              <Badge variant="secondary">#{rank}</Badge>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-4 space-y-3">
        {/* Visual Match Score (CLIP) - Primary indicator */}
        {product.visual_similarity && product.visual_similarity > 0 && (
          <div className="flex flex-wrap gap-2">
            {getVisualMatchBadge(product.visual_similarity)}
          </div>
        )}

        {/* Legacy Match Score */}
        {product.similarity_score && !product.visual_similarity && (
          <div className="flex justify-between items-center">
            {getMatchBadge(product.similarity_score)}
          </div>
        )}

        {/* Product Title */}
        <CardTitle className="text-lg line-clamp-2">
          {product.title}
        </CardTitle>

        {/* Product Description */}
        <p className="text-sm text-gray-600 line-clamp-2">
          {product.description}
        </p>

        {/* Price */}
        <div className="flex items-baseline gap-2">
          {product.price > 0 ? (
            <span className="text-2xl font-bold text-gray-900">
              {formatPrice(product.price, product.currency)}
            </span>
          ) : (
            <span className="text-sm text-gray-500 italic">
              Price available on site
            </span>
          )}
        </div>

        {/* Source */}
        {product.source && (
          <div className="text-xs text-gray-500">
            From {product.source}
          </div>
        )}

        {/* Tags */}
        {product.tags && product.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {product.tags.slice(0, 3).map((tag, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="p-4 pt-0">
        <Button 
          asChild 
          className={`w-full ${
            isPrimary 
              ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600' 
              : ''
          }`}
        >
          <a 
            href={product.product_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2"
          >
            Shop Now
            <ExternalLink className="w-4 h-4" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
};

