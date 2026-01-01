"""
Query Optimization Demonstration
Shows optimized vs non-optimized queries with performance metrics.
"""

import sqlite3
import time
from contextlib import contextmanager

class QueryOptimizer:
    def __init__(self, db_name='optimized_database.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self.cursor = self.conn.cursor()
    
    @contextmanager
    def measure_query_time(self, query_name):
        """Context manager to measure query execution time"""
        start_time = time.time()
        yield
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"  [TIME] {query_name}: {execution_time:.3f}ms")
    
    def explain_query(self, query, params=None):
        """Show query execution plan"""
        explain_query = f"EXPLAIN QUERY PLAN {query}"
        if params:
            self.cursor.execute(explain_query, params)
        else:
            self.cursor.execute(explain_query)
        
        plan = self.cursor.fetchall()
        print("\n  Query Plan:")
        for row in plan:
            print(f"    {row}")
    
    def demo_indexed_lookups(self):
        """Demonstrate the benefit of indexed columns"""
        print("\n" + "="*60)
        print("1. INDEXED COLUMN LOOKUPS")
        print("="*60)
        
        # Query using indexed email column
        print("\n[INDEX] Query with INDEX (email):")
        query = "SELECT * FROM users WHERE email = ?"
        email = "user0050@example.com"
        
        self.explain_query(query, (email,))
        with self.measure_query_time("Indexed email lookup"):
            self.cursor.execute(query, (email,))
            result = self.cursor.fetchone()
        
        if result:
            print(f"  [OK] Found: {dict(result)}")
    
    def demo_composite_indexes(self):
        """Demonstrate composite index benefits"""
        print("\n" + "="*60)
        print("2. COMPOSITE INDEX USAGE")
        print("="*60)
        
        # Query using composite index (category, price)
        print("\n[COMPOSITE INDEX] Query with COMPOSITE INDEX (category, price):")
        query = """
            SELECT product_id, product_name, category, price 
            FROM products 
            WHERE category = ? AND price BETWEEN ? AND ?
            ORDER BY price
            LIMIT 10
        """
        
        self.explain_query(query, ('Electronics', 100, 500))
        with self.measure_query_time("Composite index query"):
            self.cursor.execute(query, ('Electronics', 100, 500))
            results = self.cursor.fetchall()
        
        print(f"  [OK] Found {len(results)} products")
        for row in results[:3]:
            print(f"    - {row['product_name']}: ${row['price']}")
    
    def demo_join_optimization(self):
        """Demonstrate optimized JOIN queries"""
        print("\n" + "="*60)
        print("3. OPTIMIZED JOIN QUERIES")
        print("="*60)
        
        # Optimized join with indexed foreign keys
        print("\n[JOIN] JOIN with indexed foreign keys:")
        query = """
            SELECT 
                o.order_id,
                u.username,
                p.product_name,
                o.quantity,
                o.total_price,
                o.status
            FROM orders o
            INNER JOIN users u ON o.user_id = u.user_id
            INNER JOIN products p ON o.product_id = p.product_id
            WHERE o.status = ?
            ORDER BY o.order_date DESC
            LIMIT 10
        """
        
        self.explain_query(query, ('delivered',))
        with self.measure_query_time("Optimized JOIN"):
            self.cursor.execute(query, ('delivered',))
            results = self.cursor.fetchall()
        
        print(f"  [OK] Retrieved {len(results)} orders")
        for row in results[:3]:
            print(f"    - Order #{row['order_id']}: {row['username']} - {row['product_name']}")
    
    def demo_aggregation_queries(self):
        """Demonstrate optimized aggregation queries"""
        print("\n" + "="*60)
        print("4. AGGREGATION WITH INDEXES")
        print("="*60)
        
        # Aggregation using indexed columns
        print("\n[AGGREGATION] Aggregation with indexed columns:")
        query = """
            SELECT 
                p.category,
                COUNT(*) as order_count,
                SUM(o.total_price) as total_revenue,
                AVG(o.total_price) as avg_order_value
            FROM orders o
            INNER JOIN products p ON o.product_id = p.product_id
            WHERE o.status = 'delivered'
            GROUP BY p.category
            ORDER BY total_revenue DESC
        """
        
        self.explain_query(query)
        with self.measure_query_time("Aggregation query"):
            self.cursor.execute(query)
            results = self.cursor.fetchall()
        
        print("\n  Revenue by Category:")
        for row in results:
            print(f"    {row['category']:15} - Orders: {row['order_count']:4}, "
                  f"Revenue: ${row['total_revenue']:9.2f}, Avg: ${row['avg_order_value']:7.2f}")
    
    def demo_subquery_optimization(self):
        """Demonstrate optimized subqueries"""
        print("\n" + "="*60)
        print("5. OPTIMIZED SUBQUERIES")
        print("="*60)
        
        # Find users with high-value orders
        print("\n[SUBQUERY] Subquery with indexed columns:")
        query = """
            SELECT 
                u.user_id,
                u.username,
                u.email,
                (SELECT COUNT(*) FROM orders WHERE user_id = u.user_id) as total_orders,
                (SELECT SUM(total_price) FROM orders WHERE user_id = u.user_id) as lifetime_value
            FROM users u
            WHERE u.is_active = 1
            AND (SELECT SUM(total_price) FROM orders WHERE user_id = u.user_id) > 1000
            ORDER BY lifetime_value DESC
            LIMIT 10
        """
        
        self.explain_query(query)
        with self.measure_query_time("Subquery execution"):
            self.cursor.execute(query)
            results = self.cursor.fetchall()
        
        print(f"\n  Top Customers (Lifetime Value > $1000):")
        for row in results:
            print(f"    {row['username']:12} - Orders: {row['total_orders']:3}, "
                  f"LTV: ${row['lifetime_value']:8.2f}")
    
    def demo_range_queries(self):
        """Demonstrate indexed range queries"""
        print("\n" + "="*60)
        print("6. INDEXED RANGE QUERIES")
        print("="*60)
        
        # Date range query using indexed column
        print("\n[RANGE] Date range with indexed column:")
        query = """
            SELECT 
                DATE(order_date) as order_day,
                COUNT(*) as num_orders,
                SUM(total_price) as daily_revenue
            FROM orders
            WHERE order_date >= date('now', '-30 days')
            GROUP BY DATE(order_date)
            ORDER BY order_day DESC
            LIMIT 10
        """
        
        self.explain_query(query)
        with self.measure_query_time("Date range query"):
            self.cursor.execute(query)
            results = self.cursor.fetchall()
        
        print(f"\n  Recent Daily Sales (Last 30 days):")
        for row in results[:5]:
            print(f"    {row['order_day']} - Orders: {row['num_orders']:3}, "
                  f"Revenue: ${row['daily_revenue']:8.2f}")
    
    def demo_unique_id_access(self):
        """Demonstrate fast primary key lookups"""
        print("\n" + "="*60)
        print("7. PRIMARY KEY LOOKUPS (Fastest)")
        print("="*60)
        
        # Direct primary key access
        print("\n[PRIMARY KEY] Direct access by unique ID:")
        
        # Single user lookup
        user_id = 42
        query_user = "SELECT * FROM users WHERE user_id = ?"
        with self.measure_query_time(f"Get user by ID ({user_id})"):
            self.cursor.execute(query_user, (user_id,))
            user = self.cursor.fetchone()
        
        if user:
            print(f"  [OK] User: {user['username']} ({user['email']})")
        
        # Single product lookup
        product_id = 25
        query_product = "SELECT * FROM products WHERE product_id = ?"
        with self.measure_query_time(f"Get product by ID ({product_id})"):
            self.cursor.execute(query_product, (product_id,))
            product = self.cursor.fetchone()
        
        if product:
            print(f"  [OK] Product: {product['product_name']} - ${product['price']}")
        
        # Order lookup with JOIN
        order_id = 100
        query_order = """
            SELECT o.*, u.username, p.product_name
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN products p ON o.product_id = p.product_id
            WHERE o.order_id = ?
        """
        with self.measure_query_time(f"Get order by ID ({order_id})"):
            self.cursor.execute(query_order, (order_id,))
            order = self.cursor.fetchone()
        
        if order:
            print(f"  [OK] Order: {order['username']} ordered {order['product_name']}")
    
    def show_optimization_tips(self):
        """Display optimization tips"""
        print("\n" + "="*60)
        print("OPTIMIZATION TIPS")
        print("="*60)
        
        tips = [
            "[+] Use indexes on frequently queried columns (email, username, etc.)",
            "[+] Create composite indexes for multi-column WHERE clauses",
            "[+] Use primary keys for fastest lookups",
            "[+] Index foreign key columns for efficient JOINs",
            "[+] Use EXPLAIN QUERY PLAN to verify index usage",
            "[+] Run ANALYZE periodically to update statistics",
            "[+] Avoid SELECT * when you only need specific columns",
            "[+] Use appropriate data types and constraints",
            "[+] Consider covering indexes for frequently accessed columns",
            "[+] Batch INSERT operations for better performance"
        ]
        
        for tip in tips:
            print(f"  {tip}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("SQLITE QUERY OPTIMIZATION DEMONSTRATION")
    print("="*60)
    
    optimizer = QueryOptimizer('optimized_database.db')
    
    try:
        optimizer.connect()
        
        # Run optimization demonstrations
        optimizer.demo_indexed_lookups()
        optimizer.demo_composite_indexes()
        optimizer.demo_join_optimization()
        optimizer.demo_aggregation_queries()
        optimizer.demo_subquery_optimization()
        optimizer.demo_range_queries()
        optimizer.demo_unique_id_access()
        optimizer.show_optimization_tips()
        
        print("\n" + "="*60)
        print("[SUCCESS] Query optimization demonstration completed!")
        print("="*60 + "\n")
        
    except sqlite3.Error as e:
        print(f"\n[ERROR] Database error: {e}")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
    finally:
        optimizer.close()


if __name__ == "__main__":
    main()
