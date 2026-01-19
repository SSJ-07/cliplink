
export interface Product {
  id: string;
  title: string;           // Changed from 'name'
  description?: string;
  price: number;            // Changed from string
  currency: string;
  image_url: string;        // Changed from 'imageUrl'
  product_url: string;      // Changed from 'buyUrl'
  similarity_score?: number;
  visual_similarity?: number;
  tags?: string[];
  source?: string;
  // Legacy fields for backward compatibility
  name?: string;
  brand?: string;
  imageUrl?: string;
  buyUrl?: string;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

export interface AuthContextType {
  user: AuthUser | null;
  login: () => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

// Backend API Response Types
export interface DetectedLabel {
  label: string;
  confidence: number;
}

export interface AnalyzeReelResponse {
  products: Product[];
  count: number;
  primary?: Product;
  alternatives?: Product[];
  detected_labels?: DetectedLabel[];
  detected_brand?: string;
  used_clip?: boolean;
  frames_extracted?: number;
}

export interface HealthResponse {
  status: string;
  message: string;
  version?: string;
  features?: {
    openai?: boolean;
    vision_api?: boolean;
  };
}

export interface SearchProductsResponse {
  products: Product[];
  count: number;
}
