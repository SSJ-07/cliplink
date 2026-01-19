import { Product } from '@/types';

/**
 * Transform backend product to display format
 * Handles both new backend format and legacy format for compatibility
 */
export function transformProduct(backendProduct: Product): Product {
  // If already in correct format, return as-is
  if (backendProduct.image_url && backendProduct.product_url) {
    return backendProduct;
  }

  // Transform from legacy format if needed
  return {
    ...backendProduct,
    title: backendProduct.title || backendProduct.name || 'Product',
    image_url: backendProduct.image_url || backendProduct.imageUrl || '',
    product_url: backendProduct.product_url || backendProduct.buyUrl || '#',
    price: typeof backendProduct.price === 'number' 
      ? backendProduct.price 
      : parseFloat(backendProduct.price?.toString().replace(/[^0-9.]/g, '') || '0'),
    currency: backendProduct.currency || 'USD',
  };
}

/**
 * Format price with currency symbol
 */
export function formatPrice(price: number, currency: string = 'USD'): string {
  if (price === 0 || isNaN(price)) {
    return 'Price not available';
  }

  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(price);
  } catch {
    // Fallback if currency code is invalid
    return `$${price.toFixed(2)}`;
  }
}

/**
 * Format similarity score as percentage
 */
export function formatSimilarity(score: number): string {
  if (score === undefined || score === null || isNaN(score)) {
    return 'N/A';
  }
  
  const percentage = Math.round(score * 100);
  return `${percentage}%`;
}

/**
 * Get similarity badge label based on score
 */
export function getSimilarityLabel(score: number): string {
  if (score === undefined || score === null || isNaN(score)) {
    return 'Unknown';
  }
  
  const percentage = Math.round(score * 100);
  
  if (percentage >= 90) {
    return 'Perfect Match';
  } else if (percentage >= 75) {
    return 'Excellent Match';
  } else if (percentage >= 60) {
    return 'Good Match';
  } else if (percentage >= 40) {
    return 'Fair Match';
  } else {
    return 'Low Match';
  }
}
