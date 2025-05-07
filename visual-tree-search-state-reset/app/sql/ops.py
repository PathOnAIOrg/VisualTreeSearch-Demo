import pymysql
import json
import argparse
from datetime import datetime, date, timedelta
from decimal import Decimal

# Database connection details
DB_CONFIG = {
    "host": "172.17.0.2",
    "port": 3306,
    "user": "root",
    "password": "1234567890",
    "database": "magentodb"
}

CUSTOMER_ID = 27
OUTPUT_FILE = "customer_27_backup.json"

# Tables to extract or delete data from
TABLES = [
    "customer_entity",
    "customer_address_entity",
    "customer_entity_datetime",
    "customer_entity_decimal",
    "customer_entity_int",
    "customer_entity_text",
    "customer_entity_varchar",
    "quote",
    "quote_item",
    "quote_payment",
    "quote_shipping_rate",
    "quote_address",
    "sales_order",
    "sales_order_item",
    "sales_order_payment",
    "sales_order_status_history",
    "sales_order_address",
    "sales_invoice",
    "sales_invoice_item",
    "sales_invoice_comment",
    "sales_shipment",
    "sales_shipment_item",
    "sales_shipment_comment",
    "sales_shipment_track",
    "sales_creditmemo",
    "sales_creditmemo_item",
    "sales_creditmemo_comment",
    "wishlist",
    "wishlist_item",
    "product_alert_price",
    "product_alert_stock",
    "catalog_compare_item",
    "catalog_compare_list",
    "downloadable_link_purchased",
    "downloadable_link_purchased_item",
    "catalog_product_frontend_action",
    "report_compared_product_index",
    "report_viewed_product_index",
    "review_detail",
    "salesrule_coupon_usage",
    "salesrule_customer",
    "persistent_session",
    "oauth_token",
    "vault_payment_token",
    "paypal_billing_agreement",
    "login_as_customer_assistance_allowed"
]

# Enhanced relations for tables that don't have customer_id
# This maps tables to their relation paths to customer_id
TABLE_RELATIONS = {
    # Direct relations (table -> customer_id)
    "quote_item": {
        "related_table": "quote",
        "foreign_key": "quote_id",
        "related_key": "entity_id"
    },
    "quote_payment": {
        "related_table": "quote",
        "foreign_key": "quote_id", 
        "related_key": "entity_id"
    },
    "quote_shipping_rate": {
        "related_table": "quote_address",
        "foreign_key": "address_id",
        "related_key": "address_id"
    },
    "quote_address": {
        "related_table": "quote",
        "foreign_key": "quote_id",
        "related_key": "entity_id"
    },
    "sales_order_item": {
        "related_table": "sales_order",
        "foreign_key": "order_id",
        "related_key": "entity_id"
    },
    "sales_order_payment": {
        "related_table": "sales_order",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_order_status_history": {
        "related_table": "sales_order",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_order_address": {
        "related_table": "sales_order",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_invoice": {
        "related_table": "sales_order",
        "foreign_key": "order_id",
        "related_key": "entity_id"
    },
    "sales_invoice_item": {
        "related_table": "sales_invoice",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_invoice_comment": {
        "related_table": "sales_invoice",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_shipment": {
        "related_table": "sales_order",
        "foreign_key": "order_id",
        "related_key": "entity_id"
    },
    "sales_shipment_item": {
        "related_table": "sales_shipment",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_shipment_comment": {
        "related_table": "sales_shipment",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_shipment_track": {
        "related_table": "sales_shipment",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_creditmemo": {
        "related_table": "sales_order",
        "foreign_key": "order_id",
        "related_key": "entity_id"
    },
    "sales_creditmemo_item": {
        "related_table": "sales_creditmemo",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "sales_creditmemo_comment": {
        "related_table": "sales_creditmemo",
        "foreign_key": "parent_id",
        "related_key": "entity_id"
    },
    "wishlist_item": {
        "related_table": "wishlist",
        "foreign_key": "wishlist_id",
        "related_key": "wishlist_id"
    },
    "downloadable_link_purchased_item": {
        "related_table": "downloadable_link_purchased",
        "foreign_key": "purchased_id",
        "related_key": "purchased_id"
    }
    # Add more relations as needed
}

# Define the order of tables for deletion to handle foreign key constraints properly
# Leaf tables (with no dependencies) should be first
DELETION_ORDER = [
    # First delete leaf tables that depend on other tables
    "sales_invoice_comment",
    "sales_invoice_item", 
    "sales_shipment_comment",
    "sales_shipment_item",
    "sales_shipment_track",
    "sales_creditmemo_comment",
    "sales_creditmemo_item",
    "sales_order_status_history",
    "sales_order_payment",
    "sales_order_item",
    "sales_order_address",
    "quote_shipping_rate",
    "quote_payment",
    "quote_item",
    "quote_address",
    "downloadable_link_purchased_item",
    "wishlist_item",
    
    # Then tables that have dependencies
    "sales_invoice",
    "sales_shipment",
    "sales_creditmemo",
    "sales_order",
    "quote",
    "downloadable_link_purchased",
    "wishlist",
    
    # Then core customer data
    "customer_entity_datetime",
    "customer_entity_decimal",
    "customer_entity_int",
    "customer_entity_text",
    "customer_entity_varchar",
    "customer_address_entity",
    
    # Other tables
    "product_alert_price",
    "product_alert_stock",
    "catalog_compare_item",
    "catalog_compare_list",
    "catalog_product_frontend_action",
    "report_compared_product_index",
    "report_viewed_product_index",
    "review_detail",
    "salesrule_coupon_usage",
    "salesrule_customer",
    "persistent_session",
    "oauth_token",
    "vault_payment_token",
    "paypal_billing_agreement",
    "login_as_customer_assistance_allowed",
    
    # Lastly, the main customer entity
    "customer_entity"
]

# Define the order of tables for restoration to handle foreign key constraints
RESTORE_ORDER = [
    # First restore core customer data
    "customer_entity",
    "customer_address_entity",
    "customer_entity_datetime",
    "customer_entity_decimal",
    "customer_entity_int",
    "customer_entity_text",
    "customer_entity_varchar",
    
    # Then restore dependent sales-related data
    "wishlist",
    "wishlist_item",
    "quote",
    "quote_address",
    "quote_item",
    "quote_payment",
    "quote_shipping_rate",
    "sales_order",
    "sales_order_address",
    "sales_order_item",
    "sales_order_payment",
    "sales_order_status_history",
    "sales_invoice",
    "sales_invoice_item",
    "sales_invoice_comment",
    "sales_shipment",
    "sales_shipment_item",
    "sales_shipment_comment",
    "sales_shipment_track",
    "sales_creditmemo",
    "sales_creditmemo_item",
    "sales_creditmemo_comment",
    
    # Then restore other related data
    "product_alert_price",
    "product_alert_stock",
    "catalog_compare_item",
    "catalog_compare_list",
    "downloadable_link_purchased",
    "downloadable_link_purchased_item",
    "catalog_product_frontend_action",
    "report_compared_product_index",
    "report_viewed_product_index",
    "review_detail",
    "salesrule_coupon_usage",
    "salesrule_customer",
    "persistent_session",
    "oauth_token",
    "vault_payment_token",
    "paypal_billing_agreement",
    "login_as_customer_assistance_allowed"
]

# Custom JSON encoder to handle datetime and Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def get_column_types(cursor, table):
    """Get column types for a table to help with data type conversion."""
    cursor.execute(f"SHOW COLUMNS FROM {table}")
    return {col[0]: col[1] for col in cursor.fetchall()}  # col[0] is field name, col[1] is type

def get_foreign_key_constraints(cursor, table):
    """Get foreign key constraints for a table."""
    cursor.execute(f"""
        SELECT
            TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM
            information_schema.KEY_COLUMN_USAGE
        WHERE
            REFERENCED_TABLE_SCHEMA = DATABASE() AND
            TABLE_NAME = %s
    """, (table,))
    return cursor.fetchall()

def get_related_ids(cursor, customer_id, table, relation_path=None, visited=None):
    """
    Get all related IDs for a table that has an indirect relationship to customer_id.
    Handles recursive traversal of relationships.
    """
    if visited is None:
        visited = set()
    
    if table in visited:
        return []  # Prevent infinite recursion
    
    visited.add(table)
    
    # Check if the table has a direct customer_id column
    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'customer_id'")
    has_customer_id = cursor.fetchone() is not None
    
    if has_customer_id:
        # Get IDs directly from this table
        cursor.execute(f"SELECT entity_id FROM {table} WHERE customer_id = %s", (customer_id,))
        return [row[0] for row in cursor.fetchall()]
    
    # If this table has a defined relation, use it
    if table in TABLE_RELATIONS:
        relation = TABLE_RELATIONS[table]
        related_table = relation["related_table"]
        foreign_key = relation["foreign_key"]
        related_key = relation["related_key"]
        
        # First get IDs from the related table
        related_ids = get_related_ids(cursor, customer_id, related_table, relation_path, visited)
        
        if related_ids:
            # Then use those IDs to get IDs from this table
            placeholders = ", ".join(["%s"] * len(related_ids))
            cursor.execute(f"SELECT {related_key} FROM {related_table} WHERE entity_id IN ({placeholders})", related_ids)
            intermediate_ids = [row[0] for row in cursor.fetchall()]
            
            if intermediate_ids:
                placeholders = ", ".join(["%s"] * len(intermediate_ids))
                cursor.execute(f"SELECT entity_id FROM {table} WHERE {foreign_key} IN ({placeholders})", intermediate_ids)
                return [row[0] for row in cursor.fetchall()]
    
    # If we got here, we couldn't find a path
    return []

def fetch_data():
    """Extracts all data related to CUSTOMER_ID and saves it to a JSON file."""
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    data = {}
    
    for table in TABLES:
        try:
            print(f"Processing table: {table}")
            # Check if the table exists
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                print(f"Table {table} doesn't exist, skipping")
                continue
                
            # Check if the table has a customer_id column
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'customer_id'")
            has_customer_id = cursor.fetchone() is not None
            
            if has_customer_id:
                query = f"SELECT * FROM {table} WHERE customer_id = %s"
                cursor.execute(query, (CUSTOMER_ID,))
                records = cursor.fetchall()
                data[table] = list(records)
                print(f"Found {len(records)} records in {table}")
            elif table in TABLE_RELATIONS:
                # Handle tables with relations to customer-related tables
                relation = TABLE_RELATIONS[table]
                related_table = relation["related_table"]
                foreign_key = relation["foreign_key"]
                related_key = relation["related_key"]
                
                # Get related IDs from the related table that has customer_id
                cursor.execute(f"SHOW COLUMNS FROM {related_table} LIKE 'customer_id'")
                related_has_customer_id = cursor.fetchone() is not None
                
                if related_has_customer_id:
                    cursor.execute(f"SELECT {related_key} FROM {related_table} WHERE customer_id = %s", (CUSTOMER_ID,))
                    related_ids = [row[related_key] for row in cursor.fetchall()]
                elif related_table in TABLE_RELATIONS:
                    # Handle multi-level relations
                    related_ids = []
                    sub_relation = TABLE_RELATIONS[related_table]
                    sub_related_table = sub_relation["related_table"]
                    sub_foreign_key = sub_relation["foreign_key"]
                    sub_related_key = sub_relation["related_key"]
                    
                    cursor.execute(f"SHOW COLUMNS FROM {sub_related_table} LIKE 'customer_id'")
                    if cursor.fetchone() is not None:
                        cursor.execute(f"SELECT {sub_related_key} FROM {sub_related_table} WHERE customer_id = %s", (CUSTOMER_ID,))
                        sub_related_ids = [row[sub_related_key] for row in cursor.fetchall()]
                        
                        if sub_related_ids:
                            placeholders = ", ".join(["%s"] * len(sub_related_ids))
                            cursor.execute(f"SELECT {related_key} FROM {related_table} WHERE {sub_foreign_key} IN ({placeholders})", sub_related_ids)
                            related_ids = [row[related_key] for row in cursor.fetchall()]
                else:
                    related_ids = []
                
                if related_ids:
                    placeholders = ", ".join(["%s"] * len(related_ids))
                    query = f"SELECT * FROM {table} WHERE {foreign_key} IN ({placeholders})"
                    cursor.execute(query, related_ids)
                    records = cursor.fetchall()
                    data[table] = list(records)
                    print(f"Found {len(records)} records in {table} through relation")
                else:
                    data[table] = []
            else:
                # For tables without customer_id and no known relations, skip
                print(f"Table {table} doesn't have customer_id column and no relation defined, skipping")
                data[table] = []
        except pymysql.Error as e:
            print(f"Skipping {table}: {e}")
            data[table] = []

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, cls=CustomJSONEncoder)

    print(f"Backup saved to {OUTPUT_FILE}")

    cursor.close()
    connection.close()
    return(f"Backup saved to {OUTPUT_FILE}")


def restore_data():
    """Reads the JSON file and reinserts the data into the database in the correct order for foreign key constraints."""
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Get column types for all tables to help with data conversion
    table_column_types = {}
    for table in RESTORE_ORDER:
        if table in data and data[table]:
            try:
                table_column_types[table] = get_column_types(cursor, table)
            except pymysql.Error as e:
                print(f"Error getting column types for {table}: {e}")

    # Restore data in the proper order
    for table in RESTORE_ORDER:
        if table not in data or not data[table]:
            continue  # Skip tables not in the backup or with no records
        
        records = data[table]
        if not records:
            continue  # Skip empty tables

        # Get column types for type conversion
        column_types = table_column_types.get(table, {})

        # Convert string ISO dates back to datetime objects and handle other type conversions
        for record in records:
            for key, value in record.items():
                if value is None:
                    continue
                    
                # Handle datetime conversion
                if isinstance(value, str) and 'T' in value and value.count('-') >= 2:
                    try:
                        # Try to parse ISO format datetime strings
                        record[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        # If parsing fails, keep the original value
                        pass
                
                # Handle other type conversions based on MySQL column types
                if key in column_types:
                    col_type = column_types[key].lower()
                    if 'int' in col_type and not isinstance(value, int):
                        try:
                            record[key] = int(value)
                        except (ValueError, TypeError):
                            pass
                    elif 'decimal' in col_type and not isinstance(value, Decimal):
                        try:
                            record[key] = Decimal(str(value))
                        except (ValueError, TypeError):
                            pass

        keys = records[0].keys()
        columns = ", ".join(f"`{k}`" for k in keys)  # Escape column names with backticks
        placeholders = ", ".join(["%s"] * len(keys))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            values = [tuple(record.values()) for record in records]
            for value_set in values:
                try:
                    cursor.execute(query, value_set)
                    connection.commit()
                except pymysql.Error as e:
                    print(f"Error inserting record into {table}: {e}")
                    connection.rollback()
            
            print(f"Restored {len(records)} records into {table}")
        except pymysql.Error as e:
            print(f"Error restoring {table}: {e}")
            # Optionally, add debug info to help diagnose the issue
            print(f"Query: {query}")
            connection.rollback()

    cursor.close()
    connection.close()
    return(f"Restored {len(records)} records into {table}")
    

def delete_customer_data(existing_connection=None, existing_cursor=None):
    """Deletes all data related to CUSTOMER_ID from the database."""
    connection = existing_connection or pymysql.connect(**DB_CONFIG)
    cursor = existing_cursor or connection.cursor()
    close_connection = existing_connection is None  # Only close if we created it
    
    # Turn off foreign key checks temporarily for smoother deletion
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # Check if customer exists
    cursor.execute("SELECT entity_id FROM customer_entity WHERE entity_id = %s", (CUSTOMER_ID,))
    existing_customer = cursor.fetchone()
    
    if not existing_customer:
        print(f"Customer ID {CUSTOMER_ID} not found in the database.")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")  # Restore foreign key checks
        if close_connection:
            cursor.close()
            connection.close()
        return
    
    print(f"Deleting data for customer ID {CUSTOMER_ID}...")
    
    # Create a cache to store related IDs for tables
    related_id_cache = {}
    
    # First, gather all related IDs
    for table in TABLES:
        try:
            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                continue
                
            # Check if this table has a customer_id column
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'customer_id'")
            has_customer_id = cursor.fetchone() is not None
            
            if has_customer_id:
                # For tables with customer_id, we'll delete directly by customer_id later
                pass
            elif table in TABLE_RELATIONS:
                # Handle tables with relations to customer-related tables
                relation = TABLE_RELATIONS[table]
                related_table = relation["related_table"]
                foreign_key = relation["foreign_key"]
                related_key = relation["related_key"]
                
                # Check if we've already cached the related IDs
                if related_table not in related_id_cache:
                    # Check if related table has customer_id
                    cursor.execute(f"SHOW COLUMNS FROM {related_table} LIKE 'customer_id'")
                    related_has_customer_id = cursor.fetchone() is not None
                    
                    if related_has_customer_id:
                        cursor.execute(f"SELECT {related_key} FROM {related_table} WHERE customer_id = %s", (CUSTOMER_ID,))
                        related_id_cache[related_table] = [row[0] for row in cursor.fetchall()]
                    else:
                        # Handle multi-level relationships
                        related_id_cache[related_table] = []
                        # This would need to be implemented with a recursive approach for complex cases
                
                # Get the IDs we need to delete from the current table
                if related_table in related_id_cache and related_id_cache[related_table]:
                    related_ids = related_id_cache[related_table]
                    placeholders = ", ".join(["%s"] * len(related_ids))
                    
                    # Get the primary key for this table
                    cursor.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'")
                    primary_key_info = cursor.fetchone()
                    
                    if primary_key_info:
                        primary_key = primary_key_info[4]  # Column_name is at index 4
                        cursor.execute(f"SELECT {primary_key} FROM {table} WHERE {foreign_key} IN ({placeholders})", related_ids)
                        related_id_cache[table] = [row[0] for row in cursor.fetchall()]
                    else:
                        # If no primary key found, try using the foreign key itself for deletion
                        related_id_cache[table] = related_ids
                else:
                    related_id_cache[table] = []
        except pymysql.Error as e:
            print(f"Error gathering IDs for {table}: {e}")
            related_id_cache[table] = []
    
    # Now delete in the right order to avoid foreign key issues
    for table in DELETION_ORDER:
        try:
            # Skip if table doesn't exist
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                continue
                
            # Check if this table has a customer_id column
            cursor.execute(f"SHOW COLUMNS FROM {table} LIKE 'customer_id'")
            has_customer_id = cursor.fetchone() is not None
            
            if has_customer_id:
                cursor.execute(f"DELETE FROM {table} WHERE customer_id = %s", (CUSTOMER_ID,))
                affected_rows = cursor.rowcount
                connection.commit()
                if affected_rows > 0:
                    print(f"Deleted {affected_rows} records from {table}")
            elif table in TABLE_RELATIONS and table in related_id_cache and related_id_cache[table]:
                # Use the cached IDs to delete
                related_ids = related_id_cache[table]
                if related_ids:
                    relation = TABLE_RELATIONS[table]
                    foreign_key = relation["foreign_key"]
                    
                    # Get the primary key for this table to use in the WHERE clause
                    cursor.execute(f"SHOW KEYS FROM {table} WHERE Key_name = 'PRIMARY'")
                    primary_key_info = cursor.fetchone()
                    
                    if primary_key_info:
                        primary_key = primary_key_info[4]  # Column_name is at index 4
                        placeholders = ", ".join(["%s"] * len(related_ids))
                        cursor.execute(f"DELETE FROM {table} WHERE {primary_key} IN ({placeholders})", related_ids)
                    else:
                        # If no primary key, try deleting by the foreign key
                        placeholders = ", ".join(["%s"] * len(related_ids))
                        cursor.execute(f"DELETE FROM {table} WHERE {foreign_key} IN ({placeholders})", related_ids)
                        
                    affected_rows = cursor.rowcount
                    connection.commit()
                    if affected_rows > 0:
                        print(f"Deleted {affected_rows} records from {table}")
        except pymysql.Error as e:
            print(f"Error deleting from {table}: {e}")
            connection.rollback()
    
    # Restore foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    print(f"Customer data deletion complete.")
    
    if close_connection:
        cursor.close()
        connection.close()

def delete_data():
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    # if args.no_fk_checks:
    #     cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    delete_customer_data(connection, cursor)
    # if args.no_fk_checks:
    #     cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    cursor.close()
    connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Magento Customer Data Backup & Restore Script")
    parser.add_argument("--extract", action="store_true", help="Extract customer data to JSON")
    parser.add_argument("--restore", action="store_true", help="Restore customer data from JSON")
    parser.add_argument("--delete", action="store_true", help="Delete customer data from the database")
    parser.add_argument("--customer-id", type=int, help="Customer ID to operate on (overrides default)")
    parser.add_argument("--output", help="Output file name (overrides default)")
    parser.add_argument("--database", help="Database name (overrides default)")
    parser.add_argument("--no-fk-checks", action="store_true", help="Disable foreign key checks during operations")

    args = parser.parse_args()
    
    # Override default values if provided via command line
    if args.customer_id:
        CUSTOMER_ID = args.customer_id
        if not args.output:
            OUTPUT_FILE = f"customer_{CUSTOMER_ID}_backup.json"
    
    if args.output:
        OUTPUT_FILE = args.output
    
    if args.database:
        DB_CONFIG["database"] = args.database

    if args.extract:
        fetch_data()
    elif args.restore:
        restore_data()
    elif args.delete:
        delete_data()
    else:
        print("Please use --extract to backup data, --restore to restore data, or --delete to delete customer data.")