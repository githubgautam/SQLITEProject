"""
Quick Demo Script
Runs a quick demonstration of the SQLite project features.
"""

import sqlite3

def quick_demo():
    print("\n" + "="*60)
    print("SQLITE PROJECT QUICK DEMO")
    print("="*60)
    
    conn = sqlite3.connect('optimized_database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Demo 1: Direct ID access
    print("\n1. DIRECT DATA ACCESS BY UNIQUE ID")
    print("-" * 60)
    
    user_id = 15
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    print(f"\nUser #{user_id}:")
    print(f"  Username: {user['username']}")
    print(f"  Email: {user['email']}")
    print(f"  Active: {'Yes' if user['is_active'] else 'No'}")
    
    product_id = 10
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    print(f"\nProduct #{product_id}:")
    print(f"  Name: {product['product_name']}")
    print(f"  Category: {product['category']}")
    print(f"  Price: ${product['price']}")
    
    # Demo 2: Optimized JOIN
    print("\n\n2. OPTIMIZED JOIN QUERY")
    print("-" * 60)
    
    cursor.execute("""
        SELECT o.order_id, u.username, p.product_name, o.total_price
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN products p ON o.product_id = p.product_id
        WHERE o.status = 'delivered'
        LIMIT 5
    """)
    
    print("\nRecent Delivered Orders:")
    for row in cursor.fetchall():
        print(f"  Order #{row['order_id']}: {row['username']} - {row['product_name']} - ${row['total_price']}")
    
    # Demo 3: Aggregation
    print("\n\n3. AGGREGATION QUERY")
    print("-" * 60)
    
    cursor.execute("""
        SELECT 
            p.category,
            COUNT(*) as order_count,
            SUM(o.total_price) as total_revenue
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.status = 'delivered'
        GROUP BY p.category
        ORDER BY total_revenue DESC
        LIMIT 5
    """)
    
    print("\nTop Categories by Revenue:")
    for row in cursor.fetchall():
        print(f"  {row['category']:15} - Orders: {row['order_count']:3}, Revenue: ${row['total_revenue']:8.2f}")
    
    # Demo 4: User's order history
    print("\n\n4. USER PROFILE (User #15)")
    print("-" * 60)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(total_price) as total_spent,
            AVG(total_price) as avg_order
        FROM orders
        WHERE user_id = ?
    """, (user_id,))
    
    stats = cursor.fetchone()
    print(f"\nUser Statistics:")
    print(f"  Total Orders: {stats['total_orders']}")
    print(f"  Total Spent: ${stats['total_spent']:.2f}")
    print(f"  Avg Order Value: ${stats['avg_order']:.2f}")
    
    # Demo 5: Database stats
    print("\n\n5. DATABASE STATISTICS")
    print("-" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"\nTotal Users: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Total Products: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    print(f"Total Orders: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = cursor.fetchall()
    print(f"\nOptimized Indexes: {len(indexes)}")
    for idx in indexes[:5]:
        print(f"  - {idx[0]}")
    if len(indexes) > 5:
        print(f"  ... and {len(indexes) - 5} more")
    
    print("\n" + "="*60)
    print("DEMO COMPLETED SUCCESSFULLY")
    print("="*60 + "\n")
    
    conn.close()

if __name__ == "__main__":
    quick_demo()
