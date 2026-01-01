"""
AI-Powered Data Accessor
Demonstrates intelligent data retrieval using unique IDs with ML-based recommendations.
"""

import sqlite3
import numpy as np
from datetime import datetime
from collections import defaultdict

class AIDataAccessor:
    def __init__(self, db_name='optimized_database.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.user_profiles = {}
        self.product_similarity = {}
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        print("✓ Connected to database")
    
    # ==================== Core Data Access by Unique ID ====================
    
    def get_user_by_id(self, user_id):
        """Retrieve user data by unique ID"""
        query = "SELECT * FROM users WHERE user_id = ?"
        self.cursor.execute(query, (user_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_product_by_id(self, product_id):
        """Retrieve product data by unique ID"""
        query = "SELECT * FROM products WHERE product_id = ?"
        self.cursor.execute(query, (product_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_order_by_id(self, order_id):
        """Retrieve order data by unique ID with related information"""
        query = """
            SELECT 
                o.*,
                u.username,
                u.email,
                p.product_name,
                p.category
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN products p ON o.product_id = p.product_id
            WHERE o.order_id = ?
        """
        self.cursor.execute(query, (order_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None
    
    def get_multiple_records(self, table, ids):
        """Batch retrieve multiple records by IDs"""
        placeholders = ','.join('?' * len(ids))
        query = f"SELECT * FROM {table} WHERE {table[:-1]}_id IN ({placeholders})"
        self.cursor.execute(query, ids)
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ==================== AI-Powered Features ====================
    
    def build_user_profile(self, user_id):
        """Build AI-enhanced user profile based on purchase history"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Get user's order history
        query = """
            SELECT 
                o.order_id,
                o.product_id,
                o.quantity,
                o.total_price,
                o.order_date,
                p.product_name,
                p.category,
                p.price
            FROM orders o
            JOIN products p ON o.product_id = p.product_id
            WHERE o.user_id = ?
            ORDER BY o.order_date DESC
        """
        self.cursor.execute(query, (user_id,))
        orders = [dict(row) for row in self.cursor.fetchall()]
        
        # Calculate user statistics
        total_spent = sum(order['total_price'] for order in orders)
        total_orders = len(orders)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Category preferences
        category_counts = defaultdict(int)
        category_spending = defaultdict(float)
        for order in orders:
            category_counts[order['category']] += 1
            category_spending[order['category']] += order['total_price']
        
        # Sort categories by preference
        favorite_categories = sorted(
            category_counts.items(),
            key=lambda x: (x[1], category_spending[x[0]]),
            reverse=True
        )
        
        profile = {
            'user_info': user,
            'total_orders': total_orders,
            'total_spent': round(total_spent, 2),
            'avg_order_value': round(avg_order_value, 2),
            'favorite_categories': [cat[0] for cat in favorite_categories[:3]],
            'recent_orders': orders[:5],
            'customer_segment': self._classify_customer(total_spent, total_orders)
        }
        
        return profile
    
    def _classify_customer(self, total_spent, total_orders):
        """AI-based customer segmentation"""
        if total_spent > 2000 and total_orders > 10:
            return "VIP Customer"
        elif total_spent > 1000 or total_orders > 5:
            return "Regular Customer"
        elif total_orders > 0:
            return "Occasional Buyer"
        else:
            return "New User"
    
    def recommend_products_for_user(self, user_id, limit=5):
        """AI-powered product recommendations based on user history"""
        profile = self.build_user_profile(user_id)
        if not profile or not profile['favorite_categories']:
            # Return popular products for new users
            return self._get_popular_products(limit)
        
        # Get products from favorite categories that user hasn't bought
        purchased_product_ids = {order['product_id'] for order in profile['recent_orders']}
        favorite_cats = profile['favorite_categories']
        
        placeholders = ','.join('?' * len(favorite_cats))
        query = f"""
            SELECT 
                p.*,
                COUNT(o.order_id) as popularity_score
            FROM products p
            LEFT JOIN orders o ON p.product_id = o.product_id
            WHERE p.category IN ({placeholders})
            AND p.stock_quantity > 0
            GROUP BY p.product_id
            ORDER BY popularity_score DESC
            LIMIT ?
        """
        
        self.cursor.execute(query, (*favorite_cats, limit * 2))
        all_recommendations = [dict(row) for row in self.cursor.fetchall()]
        
        # Filter out already purchased items
        recommendations = [
            prod for prod in all_recommendations 
            if prod['product_id'] not in purchased_product_ids
        ][:limit]
        
        return recommendations
    
    def _get_popular_products(self, limit=5):
        """Get most popular products for cold start"""
        query = """
            SELECT 
                p.*,
                COUNT(o.order_id) as order_count
            FROM products p
            LEFT JOIN orders o ON p.product_id = o.product_id
            WHERE p.stock_quantity > 0
            GROUP BY p.product_id
            ORDER BY order_count DESC
            LIMIT ?
        """
        self.cursor.execute(query, (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def find_similar_users(self, user_id, limit=5):
        """Find users with similar purchase patterns (collaborative filtering)"""
        profile = self.build_user_profile(user_id)
        if not profile or not profile['favorite_categories']:
            return []
        
        target_categories = set(profile['favorite_categories'])
        
        # Find users who purchased from similar categories
        query = """
            SELECT 
                u.user_id,
                u.username,
                COUNT(DISTINCT p.category) as common_categories,
                COUNT(o.order_id) as total_orders
            FROM users u
            JOIN orders o ON u.user_id = o.user_id
            JOIN products p ON o.product_id = p.product_id
            WHERE u.user_id != ?
            AND p.category IN (?, ?, ?)
            GROUP BY u.user_id
            ORDER BY common_categories DESC, total_orders DESC
            LIMIT ?
        """
        
        categories_params = list(target_categories) + [None] * (3 - len(target_categories))
        self.cursor.execute(query, (user_id, *categories_params[:3], limit))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def predict_next_purchase(self, user_id):
        """Predict when and what user might purchase next"""
        profile = self.build_user_profile(user_id)
        if not profile or len(profile['recent_orders']) < 2:
            return None
        
        orders = profile['recent_orders']
        
        # Calculate average time between orders
        time_diffs = []
        for i in range(len(orders) - 1):
            date1 = datetime.fromisoformat(orders[i]['order_date'])
            date2 = datetime.fromisoformat(orders[i + 1]['order_date'])
            diff_days = abs((date1 - date2).days)
            time_diffs.append(diff_days)
        
        avg_days_between_orders = np.mean(time_diffs) if time_diffs else 30
        
        # Get last order date
        last_order_date = datetime.fromisoformat(orders[0]['order_date'])
        days_since_last = (datetime.now() - last_order_date).days
        
        # Predict next purchase date
        predicted_days_until_next = max(0, avg_days_between_orders - days_since_last)
        
        # Get recommended product category
        recommended_category = profile['favorite_categories'][0] if profile['favorite_categories'] else None
        
        return {
            'avg_days_between_orders': round(avg_days_between_orders, 1),
            'days_since_last_order': days_since_last,
            'predicted_days_until_next_purchase': round(predicted_days_until_next, 1),
            'likely_category': recommended_category,
            'purchase_probability': self._calculate_purchase_probability(days_since_last, avg_days_between_orders)
        }
    
    def _calculate_purchase_probability(self, days_since, avg_days):
        """Calculate probability of purchase using simple sigmoid function"""
        # Probability increases as days_since approaches avg_days
        if avg_days == 0:
            return 0.1
        ratio = days_since / avg_days
        # Simple probability curve
        probability = min(1.0, max(0.1, ratio))
        return round(probability, 2)
    
    def get_smart_search_results(self, search_term, user_id=None):
        """AI-enhanced search that personalizes results"""
        # Basic search query
        query = """
            SELECT p.*, COUNT(o.order_id) as popularity
            FROM products p
            LEFT JOIN orders o ON p.product_id = o.product_id
            WHERE p.product_name LIKE ? OR p.category LIKE ?
            GROUP BY p.product_id
            ORDER BY popularity DESC
            LIMIT 20
        """
        
        search_pattern = f"%{search_term}%"
        self.cursor.execute(query, (search_pattern, search_pattern))
        results = [dict(row) for row in self.cursor.fetchall()]
        
        # If user_id provided, personalize ranking
        if user_id:
            profile = self.build_user_profile(user_id)
            if profile and profile['favorite_categories']:
                favorite_cats = set(profile['favorite_categories'])
                # Boost results from favorite categories
                for result in results:
                    if result['category'] in favorite_cats:
                        result['relevance_score'] = result['popularity'] * 1.5
                    else:
                        result['relevance_score'] = result['popularity']
                
                results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return results[:10]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def demo_ai_features():
    """Demonstrate AI-powered data access features"""
    print("\n" + "="*70)
    print("AI-POWERED DATA ACCESSOR DEMONSTRATION")
    print("="*70)
    
    ai = AIDataAccessor('optimized_database.db')
    
    try:
        ai.connect()
        
        # Demo 1: Direct access by unique ID
        print("\n" + "="*70)
        print("1. DIRECT DATA ACCESS BY UNIQUE ID")
        print("="*70)
        
        user_id = 15
        user = ai.get_user_by_id(user_id)
        print(f"\n[USER] User #{user_id}:")
        print(f"   Username: {user['username']}")
        print(f"   Email: {user['email']}")
        print(f"   Active: {'Yes' if user['is_active'] else 'No'}")
        
        product_id = 10
        product = ai.get_product_by_id(product_id)
        print(f"\n[PRODUCT] Product #{product_id}:")
        print(f"   Name: {product['product_name']}")
        print(f"   Category: {product['category']}")
        print(f"   Price: ${product['price']}")
        print(f"   Stock: {product['stock_quantity']} units")
        
        order_id = 50
        order = ai.get_order_by_id(order_id)
        print(f"\n[ORDER] Order #{order_id}:")
        print(f"   Customer: {order['username']}")
        print(f"   Product: {order['product_name']}")
        print(f"   Quantity: {order['quantity']}")
        print(f"   Total: ${order['total_price']}")
        print(f"   Status: {order['status']}")
        
        # Demo 2: AI User Profile
        print("\n" + "="*70)
        print("2. AI-POWERED USER PROFILE")
        print("="*70)
        
        profile = ai.build_user_profile(user_id)
        print(f"\n[AI PROFILE] AI Profile for User #{user_id} ({profile['user_info']['username']}):")
        print(f"   Customer Segment: {profile['customer_segment']}")
        print(f"   Total Orders: {profile['total_orders']}")
        print(f"   Total Spent: ${profile['total_spent']}")
        print(f"   Avg Order Value: ${profile['avg_order_value']}")
        print(f"   Favorite Categories: {', '.join(profile['favorite_categories'])}")
        
        # Demo 3: Product Recommendations
        print("\n" + "="*70)
        print("3. AI PRODUCT RECOMMENDATIONS")
        print("="*70)
        
        recommendations = ai.recommend_products_for_user(user_id, limit=5)
        print(f"\n[RECOMMENDATIONS] Personalized Recommendations for User #{user_id}:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec['product_name']} ({rec['category']}) - ${rec['price']}")
        
        # Demo 4: Similar Users
        print("\n" + "="*70)
        print("4. COLLABORATIVE FILTERING - SIMILAR USERS")
        print("="*70)
        
        similar = ai.find_similar_users(user_id, limit=5)
        print(f"\n[SIMILAR USERS] Users similar to User #{user_id}:")
        for user in similar:
            print(f"   - {user['username']}: {user['common_categories']} common categories, "
                  f"{user['total_orders']} orders")
        
        # Demo 5: Purchase Prediction
        print("\n" + "="*70)
        print("5. PREDICTIVE ANALYTICS - NEXT PURCHASE")
        print("="*70)
        
        prediction = ai.predict_next_purchase(user_id)
        if prediction:
            print(f"\n[PREDICTION] Purchase Prediction for User #{user_id}:")
            print(f"   Avg Days Between Orders: {prediction['avg_days_between_orders']}")
            print(f"   Days Since Last Order: {prediction['days_since_last_order']}")
            print(f"   Predicted Days Until Next: {prediction['predicted_days_until_next_purchase']}")
            print(f"   Likely Category: {prediction['likely_category']}")
            print(f"   Purchase Probability: {prediction['purchase_probability'] * 100}%")
        
        # Demo 6: Smart Search
        print("\n" + "="*70)
        print("6. AI-ENHANCED SEARCH")
        print("="*70)
        
        search_results = ai.get_smart_search_results("Product", user_id=user_id)
        print(f"\n[SEARCH] Personalized search results for 'Product':")
        for i, result in enumerate(search_results[:5], 1):
            relevance = result.get('relevance_score', result['popularity'])
            print(f"   {i}. {result['product_name']} ({result['category']}) - "
                  f"Relevance: {relevance:.1f}")
        
        # Demo 7: Batch Retrieval
        print("\n" + "="*70)
        print("7. BATCH DATA RETRIEVAL BY IDs")
        print("="*70)
        
        user_ids = [5, 10, 15, 20, 25]
        users = ai.get_multiple_records('users', user_ids)
        print(f"\n[BATCH] Retrieved {len(users)} users in batch:")
        for u in users:
            print(f"   - User #{u['user_id']}: {u['username']}")
        
        print("\n" + "="*70)
        print("[SUCCESS] AI-powered data access demonstration completed!")
        print("="*70 + "\n")
        
    except sqlite3.Error as e:
        print(f"\n[ERROR] Database error: {e}")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        ai.close()


if __name__ == "__main__":
    demo_ai_features()
