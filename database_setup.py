"""
SQLite Database Setup with Optimization
Creates an optimized database with proper indexing and sample data.
"""

import sqlite3
import random
from datetime import datetime, timedelta

class DatabaseSetup:
    def __init__(self, db_name='optimized_database.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        print(f"✓ Connected to database: {self.db_name}")
    
    def create_tables(self):
        """Create optimized database tables with proper schema"""
        
        # Users table with proper constraints
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Products table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0),
                stock_quantity INTEGER DEFAULT 0 CHECK(stock_quantity >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Orders table with foreign keys
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                total_price REAL NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
        print("✓ Tables created successfully")
    
    def create_indexes(self):
        """Create optimized indexes for better query performance"""
        
        indexes = [
            # Index on user email for fast lookups
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            
            # Index on username for search operations
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            
            # Composite index for active users
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, created_at)",
            
            # Index on product category for filtering
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)",
            
            # Index on product price for range queries
            "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price)",
            
            # Composite index for product search
            "CREATE INDEX IF NOT EXISTS idx_products_category_price ON products(category, price)",
            
            # Index on user_id for order lookups
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
            
            # Index on product_id for order analytics
            "CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id)",
            
            # Index on order date for time-based queries
            "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)",
            
            # Composite index for order status and date
            "CREATE INDEX IF NOT EXISTS idx_orders_status_date ON orders(status, order_date)"
        ]
        
        for index_query in indexes:
            self.cursor.execute(index_query)
        
        self.conn.commit()
        print(f"✓ Created {len(indexes)} optimized indexes")
    
    def populate_sample_data(self, num_users=100, num_products=50, num_orders=500):
        """Populate database with sample data for testing"""
        
        # Sample data generators
        categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Toys']
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        
        # Insert users
        users_data = []
        for i in range(1, num_users + 1):
            username = f"user_{i:04d}"
            email = f"user{i:04d}@example.com"
            is_active = random.choice([True, True, True, False])  # 75% active
            users_data.append((username, email, is_active))
        
        self.cursor.executemany(
            'INSERT OR IGNORE INTO users (username, email, is_active) VALUES (?, ?, ?)',
            users_data
        )
        print(f"✓ Inserted {num_users} users")
        
        # Insert products
        products_data = []
        for i in range(1, num_products + 1):
            product_name = f"Product_{i:03d}"
            category = random.choice(categories)
            price = round(random.uniform(9.99, 999.99), 2)
            stock = random.randint(0, 500)
            products_data.append((product_name, category, price, stock))
        
        self.cursor.executemany(
            'INSERT INTO products (product_name, category, price, stock_quantity) VALUES (?, ?, ?, ?)',
            products_data
        )
        print(f"✓ Inserted {num_products} products")
        
        # Insert orders
        orders_data = []
        base_date = datetime.now() - timedelta(days=365)
        
        for _ in range(num_orders):
            user_id = random.randint(1, num_users)
            product_id = random.randint(1, num_products)
            quantity = random.randint(1, 5)
            
            # Get product price
            self.cursor.execute('SELECT price FROM products WHERE product_id = ?', (product_id,))
            price = self.cursor.fetchone()[0]
            total_price = round(price * quantity, 2)
            
            # Random order date within last year
            order_date = base_date + timedelta(days=random.randint(0, 365))
            status = random.choice(statuses)
            
            orders_data.append((user_id, product_id, quantity, total_price, order_date, status))
        
        self.cursor.executemany(
            '''INSERT INTO orders (user_id, product_id, quantity, total_price, order_date, status) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            orders_data
        )
        print(f"✓ Inserted {num_orders} orders")
        
        self.conn.commit()
    
    def analyze_database(self):
        """Analyze database and display statistics"""
        
        # Update SQLite statistics for better query planning
        self.cursor.execute('ANALYZE')
        
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)
        
        # Count records in each table
        tables = ['users', 'products', 'orders']
        for table in tables:
            self.cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = self.cursor.fetchone()[0]
            print(f"{table.capitalize()}: {count:,} records")
        
        # Display index information
        print("\nIndexes created:")
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = self.cursor.fetchall()
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        print("="*50)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("\n✓ Database connection closed")


def main():
    """Main execution function"""
    print("\n" + "="*50)
    print("SQLITE DATABASE SETUP & OPTIMIZATION")
    print("="*50 + "\n")
    
    # Initialize and setup database
    db = DatabaseSetup('optimized_database.db')
    
    try:
        db.connect()
        db.create_tables()
        db.create_indexes()
        db.populate_sample_data(num_users=100, num_products=50, num_orders=500)
        db.analyze_database()
        
        print("\n✓ Database setup completed successfully!")
        print(f"✓ Database file: optimized_database.db")
        
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
