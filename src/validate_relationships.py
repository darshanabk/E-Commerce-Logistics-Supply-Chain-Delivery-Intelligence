import os
from io import BytesIO

import boto3
import pandas as pd
from dotenv import load_dotenv


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")


# --------------------------------------------------
# MinIO connection
# --------------------------------------------------

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1",
)


# --------------------------------------------------
# Load CSV from MinIO
# --------------------------------------------------

def load_csv(key):

    obj = s3.get_object(
        Bucket=MINIO_BUCKET,
        Key=key
    )

    return pd.read_csv(
        BytesIO(obj["Body"].read())
    )


# --------------------------------------------------
# Load datasets
# --------------------------------------------------

customers = load_csv(
    "brazilian-ecommerce/olist_customers_dataset.csv"
)

orders = load_csv(
    "brazilian-ecommerce/olist_orders_dataset.csv"
)

order_items = load_csv(
    "brazilian-ecommerce/olist_order_items_dataset.csv"
)

payments = load_csv(
    "brazilian-ecommerce/olist_order_payments_dataset.csv"
)

reviews = load_csv(
    "brazilian-ecommerce/olist_order_reviews_dataset.csv"
)

products = load_csv(
    "brazilian-ecommerce/olist_products_dataset.csv"
)

sellers = load_csv(
    "brazilian-ecommerce/olist_sellers_dataset.csv"
)

marketing_leads = load_csv(
    "marketing-funnel/olist_marketing_qualified_leads_dataset.csv"
)

closed_deals = load_csv(
    "marketing-funnel/olist_closed_deals_dataset.csv"
)


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def check_primary_key(df, column, table):

    duplicates = df[column].duplicated().sum()

    print(
        f"{table}.{column} | "
        f"duplicates: {duplicates:,}"
    )

    return duplicates


def check_foreign_key(
    child_df,
    child_column,
    parent_df,
    parent_column,
    relationship
):

    child_values = set(
        child_df[child_column].dropna()
    )

    parent_values = set(
        parent_df[parent_column].dropna()
    )

    orphan_values = child_values - parent_values

    orphan_rows = child_df[
        ~child_df[child_column].isin(parent_values)
    ]

    print(
        f"{relationship}"
    )

    print(
        f"  Unique child values: "
        f"{len(child_values):,}"
    )

    print(
        f"  Missing parent values: "
        f"{len(orphan_values):,}"
    )

    print(
        f"  Orphan rows: "
        f"{len(orphan_rows):,}"
    )

    return len(orphan_rows)


# --------------------------------------------------
# Primary key validation
# --------------------------------------------------

print("\n" + "=" * 70)
print("PRIMARY KEY VALIDATION")
print("=" * 70)

check_primary_key(
    customers,
    "customer_id",
    "customers"
)

check_primary_key(
    orders,
    "order_id",
    "orders"
)

check_primary_key(
    products,
    "product_id",
    "products"
)

check_primary_key(
    sellers,
    "seller_id",
    "sellers"
)

check_primary_key(
    marketing_leads,
    "mql_id",
    "marketing_leads"
)


# --------------------------------------------------
# Foreign key validation
# --------------------------------------------------

print("\n" + "=" * 70)
print("FOREIGN KEY VALIDATION")
print("=" * 70)


check_foreign_key(
    orders,
    "customer_id",
    customers,
    "customer_id",
    "orders.customer_id → customers.customer_id"
)


check_foreign_key(
    order_items,
    "order_id",
    orders,
    "order_id",
    "order_items.order_id → orders.order_id"
)


check_foreign_key(
    order_items,
    "product_id",
    products,
    "product_id",
    "order_items.product_id → products.product_id"
)


check_foreign_key(
    order_items,
    "seller_id",
    sellers,
    "seller_id",
    "order_items.seller_id → sellers.seller_id"
)


check_foreign_key(
    payments,
    "order_id",
    orders,
    "order_id",
    "payments.order_id → orders.order_id"
)


check_foreign_key(
    reviews,
    "order_id",
    orders,
    "order_id",
    "reviews.order_id → orders.order_id"
)


check_foreign_key(
    closed_deals,
    "mql_id",
    marketing_leads,
    "mql_id",
    "closed_deals.mql_id → marketing_leads.mql_id"
)


check_foreign_key(
    closed_deals,
    "seller_id",
    sellers,
    "seller_id",
    "closed_deals.seller_id → sellers.seller_id"
)


print("\n" + "=" * 70)
print("RELATIONSHIP VALIDATION COMPLETE")
print("=" * 70)