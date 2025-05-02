import pymysql

# Database connection details
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 33061,
    "user": "root",
    "password": "1234567890", 
    "database": "magentodb"
}

def find_customer_by_email(email):
    """Find a customer with a specific email address."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = "SELECT * FROM customer_entity WHERE email = %s"
            cursor.execute(query, (email,))
            result = cursor.fetchall()
            
            if result:
                print("\nCustomer found:")
                for key, value in result[0].items():
                    print(f"{key}: {value}")
                return result
            else:
                print(f"No customer found with email: {email}")
                return None
    finally:
        connection.close()

def get_active_quotes(customer_id):
    """Get active quotes for a specific customer ID."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT
                q.entity_id as quote_id,
                q.created_at,
                q.updated_at,
                q.is_active,
                q.items_count,
                q.items_qty,
                q.grand_total,
                q.base_grand_total
            FROM
                quote q
            WHERE
                q.customer_id = %s
                AND q.is_active = 1
            """
            cursor.execute(query, (customer_id,))
            result = cursor.fetchall()
            
            if result:
                print(f"\nActive quotes for customer ID {customer_id}:")
                for quote in result:
                    print("\nQuote:")
                    for key, value in quote.items():
                        print(f"{key}: {value}")
                return result
            else:
                print(f"No active quotes found for customer ID {customer_id}")
                return None
    finally:
        connection.close()

def get_quote_items(customer_id):
    """Get items from active quotes for a specific customer ID."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT
                qi.item_id,
                qi.quote_id,
                qi.product_id,
                qi.sku,
                qi.name,
                qi.qty,
                qi.price,
                qi.base_price,
                qi.custom_price,
                qi.discount_amount,
                qi.row_total
            FROM
                quote_item qi
            JOIN
                quote q ON qi.quote_id = q.entity_id
            WHERE
                q.customer_id = %s
                AND q.is_active = 1
            """
            cursor.execute(query, (customer_id,))
            result = cursor.fetchall()
            
            if result:
                print(f"\nItems in active quotes for customer ID {customer_id}:")
                for i, item in enumerate(result, 1):
                    print(f"\nItem {i}:")
                    for key, value in item.items():
                        print(f"{key}: {value}")
                return result
            else:
                print(f"No items found in active quotes for customer ID {customer_id}")
                return None
    finally:
        connection.close()

def get_customer_orders(customer_id):
    """Get orders for a specific customer ID."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT
                so.entity_id as order_id,
                so.increment_id as order_number,
                so.created_at,
                so.customer_email,
                so.grand_total,
                so.base_grand_total,
                so.total_qty_ordered,
                so.status,
                so.state
            FROM
                sales_order so
            WHERE
                so.customer_id = %s
            ORDER BY
                so.created_at DESC
            """
            cursor.execute(query, (customer_id,))
            result = cursor.fetchall()
            
            if result:
                print(f"\nOrders for customer ID {customer_id}:")
                for order in result:
                    print("\nOrder:")
                    for key, value in order.items():
                        print(f"{key}: {value}")
                return result
            else:
                print(f"No orders found for customer ID {customer_id}")
                return None
    finally:
        connection.close()

def get_order_items(order_id):
    """Get items from a specific order."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
            SELECT
                soi.item_id,
                soi.order_id,
                soi.product_id,
                soi.sku,
                soi.name,
                soi.qty_ordered,
                soi.price,
                soi.base_price,
                soi.discount_amount,
                soi.row_total
            FROM
                sales_order_item soi
            WHERE
                soi.order_id = %s
            """
            cursor.execute(query, (order_id,))
            result = cursor.fetchall()
            
            if result:
                print(f"\nItems in order ID {order_id}:")
                for i, item in enumerate(result, 1):
                    print(f"\nItem {i}:")
                    for key, value in item.items():
                        print(f"{key}: {value}")
                return result
            else:
                print(f"No items found in order ID {order_id}")
                return None
    finally:
        connection.close()

def get_order_history(customer_id, limit=5):
    """Get order history with all details for a specific customer."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        # First get the orders
        orders = get_customer_orders(customer_id)
        
        if not orders:
            return None
            
        # For each order, get the items
        orders_with_items = []
        
        # Limit to the most recent orders if there are many
        for order in orders[:limit]:
            order_id = order['order_id']
            order_items = get_order_items(order_id)
            
            order_with_items = {
                'order': order,
                'items': order_items
            }
            
            orders_with_items.append(order_with_items)
            
        return orders_with_items
    finally:
        connection.close()


def verifyAccountStatus():
    orderlimit=5
    # Default values for direct execution
    default_email = 'emma.lopez@gmail.com'
    default_customer_id = 27

    # Run queries with provided args or defaults
    customer_id = None

    # Use defaults without prompting
    print(f"Using default email: {default_email}")
    customer = find_customer_by_email(default_email)
    if not customer:
        # If email not found, use default customer ID
        print(f"Using default customer ID: {default_customer_id}")
        customer_id = default_customer_id
    else:
        # Use the found customer ID
        customer_id = customer[0]['entity_id']

    if customer_id:
        # Get quotes
        get_active_quotes(customer_id)
        get_quote_items(customer_id)
        # Get orders
        get_order_history(customer_id, orderlimit)

    return("verifyAccountStatus Done")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Query Magento customer, quote, and order data")
    parser.add_argument("--email", help="Customer email to search for")
    parser.add_argument("--customer-id", type=int, help="Customer ID to query")
    parser.add_argument("--host", help="Database host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, help="Database port (default: 33061)")
    parser.add_argument("--user", help="Database user (default: root)")
    parser.add_argument("--password", help="Database password")
    parser.add_argument("--database", help="Database name (default: magentodb)")
    parser.add_argument("--orders-only", action="store_true", help="Only show orders, not quotes")
    parser.add_argument("--quotes-only", action="store_true", help="Only show quotes, not orders")
    parser.add_argument("--order-limit", type=int, default=5, help="Limit on number of orders to show (default: 5)")
    
    args = parser.parse_args()
    
    # Override connection defaults if provided
    if args.host:
        DB_CONFIG["host"] = args.host
    if args.port:
        DB_CONFIG["port"] = args.port
    if args.user:
        DB_CONFIG["user"] = args.user
    if args.password:
        DB_CONFIG["password"] = args.password
    if args.database:
        DB_CONFIG["database"] = args.database
    
    # Default values for direct execution
    default_email = 'emma.lopez@gmail.com'
    default_customer_id = 27
    
    # Run queries with provided args or defaults
    customer_id = None
    
    if args.email:
        customer = find_customer_by_email(args.email)
        if customer:
            customer_id = customer[0]['entity_id']
    elif args.customer_id:
        customer_id = args.customer_id
    else:
        # Use defaults without prompting
        print(f"Using default email: {default_email}")
        customer = find_customer_by_email(default_email)
        if not customer:
            # If email not found, use default customer ID
            print(f"Using default customer ID: {default_customer_id}")
            customer_id = default_customer_id
        else:
            # Use the found customer ID
            customer_id = customer[0]['entity_id']
    
    if customer_id:
        if not args.orders_only:
            # Get quotes
            get_active_quotes(customer_id)
            get_quote_items(customer_id)
            
        if not args.quotes_only:
            # Get orders
            get_order_history(customer_id, args.order_limit)