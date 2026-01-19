import { AnalyzeReelResponse, HealthResponse, SearchProductsResponse } from '../types';

// Get API base URL - use proxy in dev, or env var in production
const getApiUrl = (): string => {
  // In development, use proxy (no base URL needed)
  if (import.meta.env.DEV) {
    return '';
  }
  // In production, use env var
  return import.meta.env.VITE_API_URL || 'http://localhost:5001';
};

const apiUrl = getApiUrl();

/**
 * Health check endpoint
 */
export async function checkHealth(): Promise<HealthResponse> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

  try {
    const response = await fetch(`${apiUrl}/api/health`, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return await response.json();
  } catch (error: any) {
    clearTimeout(timeoutId);
    if (error.name === 'AbortError') {
      throw new Error('Health check timeout');
    }
    throw error;
  }
}

/**
 * Analyze Instagram/TikTok reel and find matching products
 * 
 * @param url - Reel URL
 * @param note - User description/note (optional)
 * @param numFrames - Number of frames to extract (default: 3)
 * @param signal - Optional AbortSignal for cancellation
 * @returns Promise with product results
 */
export async function analyzeReel(
  url: string,
  note?: string,
  numFrames: number = 3,
  signal?: AbortSignal
): Promise<AnalyzeReelResponse> {
  // Create controller if signal not provided
  const controller = signal ? undefined : new AbortController();
  const timeoutId = setTimeout(() => {
    controller?.abort();
  }, 300000); // 5 minute timeout for analyze-reel (video processing can take time)

  try {
    const response = await fetch(`${apiUrl}/api/analyze-reel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url,
        note: note || '',
        num_frames: numFrames,
      }),
      signal: signal || controller?.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error || errorData.message || `HTTP error! status: ${response.status}`;
      
      if (response.status === 400) {
        throw new Error(errorMessage);
      } else if (response.status === 404) {
        throw new Error('No products found');
      } else if (response.status === 500) {
        throw new Error('Server error, please try again');
      } else {
        throw new Error(errorMessage);
      }
    }

    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }

    return data;
  } catch (error: any) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Request timeout or cancelled');
    }
    
    // Re-throw if already a proper Error
    if (error instanceof Error) {
      throw error;
    }
    
    // Handle network errors
    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      throw new Error('Unable to connect to server. Please check your connection.');
    }
    
    throw new Error(error.message || 'An unexpected error occurred');
  }
}

/**
 * Search products by text query only (no video)
 * 
 * @param query - Search query
 * @param signal - Optional AbortSignal for cancellation
 * @returns Promise with product results
 */
export async function searchProducts(
  query: string,
  signal?: AbortSignal
): Promise<SearchProductsResponse> {
  const controller = signal ? undefined : new AbortController();
  const timeoutId = setTimeout(() => {
    controller?.abort();
  }, 10000); // 10 second timeout

  try {
    const response = await fetch(`${apiUrl}/api/search-products`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        num_results: 5,
      }),
      signal: signal || controller?.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }

    return data;
  } catch (error: any) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error('Request timeout or cancelled');
    }
    
    if (error instanceof Error) {
      throw error;
    }
    
    throw new Error(error.message || 'An unexpected error occurred');
  }
}
