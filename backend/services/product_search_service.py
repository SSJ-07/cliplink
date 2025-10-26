"""
Product search service with vector embeddings
Combines visual labels with text embeddings for better search
"""
import os
import logging
import json
from typing import List, Dict, Optional
import numpy as np
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class ProductSearchService:
    """Service for searching products using embeddings and vector similarity"""
    
    def __init__(self):
        """Initialize OpenAI client and product database"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.products = self._load_product_database()
        self.product_embeddings = {}
        
        # Pre-compute embeddings for products if not cached
        self._compute_product_embeddings()
    
    def _load_product_database(self) -> List[Dict]:
        """
        Load product database from file or initialize with sample data
        
        In production, this would connect to a real database (Supabase, Pinecone, etc.)
        For now, we'll use a JSON file or return sample products
        """
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.json')
        
        # Check if database file exists
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading product database: {e}")
        
        # Return sample products for demonstration
        return self._get_sample_products()
    
    def _get_sample_products(self) -> List[Dict]:
        """Get sample products for demonstration"""
        return [
            {
                "id": "1",
                "title": "Nike Air Max 270 Running Shoes",
                "description": "Comfortable running shoes with air cushioning, perfect for athletic wear and casual streetwear",
                "tags": ["shoes", "sneakers", "athletic", "nike", "running", "sportswear", "footwear"],
                "price": 150.00,
                "currency": "USD",
                "image_url": "https://static.nike.com/a/images/t_PDP_1728_v1/f_auto,q_auto:eco/99486859-0ff3-46b4-949b-2d16af2ad421/AIR+MAX+270.png",
                "product_url": "https://www.nike.com/t/air-max-270-mens-shoes-KkLcGR"
            },
            {
                "id": "2",
                "title": "Adidas Ultraboost 22 Blue Running Shoes",
                "description": "Premium blue running shoes with boost technology for maximum comfort and energy return",
                "tags": ["shoes", "sneakers", "athletic", "adidas", "running", "blue", "sportswear", "boost"],
                "price": 190.00,
                "currency": "USD",
                "image_url": "https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/fbaf991a78bc4896a3e9ad7800abcec6_9366/Ultraboost_22_Shoes_Blue_GZ0127_01_standard.jpg",
                "product_url": "https://www.adidas.com/us/ultraboost-22-shoes/GZ0127.html"
            },
            {
                "id": "3",
                "title": "Levi's 501 Original Fit Jeans",
                "description": "Classic straight fit denim jeans with button fly, the original blue jean since 1873",
                "tags": ["pants", "jeans", "denim", "levis", "clothing", "casual", "bottoms"],
                "price": 89.50,
                "currency": "USD",
                "image_url": "https://lsco.scene7.com/is/image/lsco/005010101-front-pdp?fmt=jpeg&qlt=70,1&op_sharpen=0&resMode=sharp2&op_usm=0.8,1,10,0&fit=crop,0&wid=750&hei=1000",
                "product_url": "https://www.levi.com/US/en_US/clothing/men/jeans/501-original-fit-mens-jeans/p/005010101"
            },
            {
                "id": "4",
                "title": "Zara Leopard Print Crop Top",
                "description": "Trendy leopard print crop top with round neck, perfect for casual outings",
                "tags": ["top", "shirt", "leopard", "print", "womens", "fashion", "casual", "crop"],
                "price": 39.90,
                "currency": "USD",
                "image_url": "https://static.zara.net/photos///2023/I/0/1/p/4661/144/706/2/w/750/4661144706_1_1_1.jpg",
                "product_url": "https://www.zara.com/us/en/woman/tops-c358002.html"
            },
            {
                "id": "5",
                "title": "H&M Black Slim Fit Pants",
                "description": "Classic black slim fit pants for men, perfect for both casual and formal occasions",
                "tags": ["pants", "trousers", "black", "mens", "slim fit", "formal", "casual"],
                "price": 49.99,
                "currency": "USD",
                "image_url": "https://www2.hm.com/content/dam/hm/productimages/0/82/08/082082082_group_001.jpg",
                "product_url": "https://www2.hm.com/en_us/men/products/pants-trousers.html"
            },
            {
                "id": "6",
                "title": "Urban Outfitters Vintage Cargo Pants",
                "description": "Trendy cargo pants with multiple pockets, perfect for streetwear and casual style",
                "tags": ["pants", "cargo", "streetwear", "casual", "fashion", "pockets", "utility"],
                "price": 69.00,
                "currency": "USD",
                "image_url": "https://images.urbndata.com/is/image/UrbanOutfitters/73289191_001_b",
                "product_url": "https://www.urbanoutfitters.com/mens-pants"
            },
            {
                "id": "7",
                "title": "Uniqlo Oversized Cotton T-Shirt",
                "description": "Comfortable oversized cotton t-shirt, available in multiple colors, perfect for everyday wear",
                "tags": ["shirt", "tshirt", "cotton", "casual", "basic", "oversized", "comfortable"],
                "price": 19.90,
                "currency": "USD",
                "image_url": "https://image.uniqlo.com/UQ/ST3/AsianCommon/imagesgoods/455359/item/goods_09_455359.jpg",
                "product_url": "https://www.uniqlo.com/us/en/men/tops/t-shirts"
            },
            {
                "id": "8",
                "title": "Vans Old Skool Classic Sneakers",
                "description": "Iconic black and white skateboarding shoes with signature side stripe",
                "tags": ["shoes", "sneakers", "vans", "skateboarding", "casual", "classic", "streetwear"],
                "price": 65.00,
                "currency": "USD",
                "image_url": "https://images.vans.com/is/image/Vans/D3HY28-HERO?wid=1600&hei=1984&fmt=jpeg&qlt=90&resMode=sharp2&op_usm=0.9,1.0,8,0",
                "product_url": "https://www.vans.com/shop/old-skool"
            }
        ]
    
    def _compute_product_embeddings(self):
        """Pre-compute embeddings for all products"""
        for product in self.products:
            # Create searchable text from product data
            searchable_text = f"{product['title']} {product['description']} {' '.join(product['tags'])}"
            
            # Get embedding
            embedding = self._get_embedding(searchable_text)
            self.product_embeddings[product['id']] = embedding
        
        logger.info(f"Computed embeddings for {len(self.products)} products")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for text using OpenAI
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return np.array(response.data[0].embedding)
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(1536)
    
    def search_products(
        self,
        query_text: str,
        labels: List[Dict] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for products using text query and optional visual labels
        
        Args:
            query_text: Text search query (can be user description + visual labels)
            labels: Optional visual labels from Vision API
            top_k: Number of results to return
            
        Returns:
            List of top matching products with scores
        """
        # Combine query text with visual labels
        if labels:
            label_text = ' '.join([label['description'] for label in labels[:5]])
            combined_query = f"{query_text} {label_text}"
        else:
            combined_query = query_text
        
        logger.info(f"Searching products with query: {combined_query}")
        
        # Get query embedding
        query_embedding = self._get_embedding(combined_query)
        
        # Calculate similarity with all products
        similarities = []
        for product in self.products:
            product_embedding = self.product_embeddings[product['id']]
            
            # Cosine similarity
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                product_embedding.reshape(1, -1)
            )[0][0]
            
            # Boost score if labels match product tags
            boost = 1.0
            if labels:
                label_descriptions = [l['description'].lower() for l in labels]
                product_tags = [t.lower() for t in product['tags']]
                
                # Count matching tags
                matches = sum(1 for tag in product_tags if any(label in tag or tag in label for label in label_descriptions))
                boost = 1.0 + (matches * 0.1)  # 10% boost per matching tag
            
            final_score = similarity * boost
            similarities.append((product, final_score))
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for product, score in similarities[:top_k]:
            result = product.copy()
            result['similarity_score'] = float(score)
            results.append(result)
        
        logger.info(f"Found {len(results)} products")
        return results
    
    def search_by_labels_only(self, labels: List[Dict], top_k: int = 5) -> List[Dict]:
        """
        Search products using only visual labels (no text query)
        
        Args:
            labels: Visual labels from Vision API
            top_k: Number of results to return
            
        Returns:
            List of top matching products
        """
        query_text = ' '.join([label['description'] for label in labels[:10]])
        return self.search_products(query_text, labels, top_k)


# Singleton instance
_product_search_service = None

def get_product_search_service() -> ProductSearchService:
    """Get or create ProductSearchService singleton"""
    global _product_search_service
    if _product_search_service is None:
        _product_search_service = ProductSearchService()
    return _product_search_service

