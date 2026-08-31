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
# Load CSV
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

closed_deals = load_csv(
    "marketing-funnel/olist_closed_deals_dataset.csv"
)


# --------------------------------------------------
# Convert dates
# --------------------------------------------------

date_columns = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

for column in date_columns:
    orders[column] = pd.to_datetime(
        orders[column],
        errors="coerce"
    )


# --------------------------------------------------
# Helper
# --------------------------------------------------

def report_check(name, invalid_count, total):

    percentage = (
        invalid_count / total * 100
        if total > 0
        else 0
    )

    print(
        f"{name}\n"
        f"  Invalid rows: {invalid_count:,}\n"
        f"  Total rows:   {total:,}\n"
        f"  Rate:         {percentage:.2f}%\n"
    )


# ==================================================
# ORDERS
# ==================================================

print("\n" + "=" * 70)
print("ORDER BUSINESS RULES")
print("=" * 70)


# Approval before purchase
invalid = (
    orders["order_approved_at"].notna()
    & (
        orders["order_approved_at"]
        < orders["order_purchase_timestamp"]
    )
)

report_check(
    "Approval before purchase",
    invalid.sum(),
    len(orders)
)


# Carrier delivery before purchase
invalid = (
    orders["order_delivered_carrier_date"].notna()
    & (
        orders["order_delivered_carrier_date"]
        < orders["order_purchase_timestamp"]
    )
)

report_check(
    "Carrier delivery before purchase",
    invalid.sum(),
    len(orders)
)


# Customer delivery before purchase
invalid = (
    orders["order_delivered_customer_date"].notna()
    & (
        orders["order_delivered_customer_date"]
        < orders["order_purchase_timestamp"]
    )
)

report_check(
    "Customer delivery before purchase",
    invalid.sum(),
    len(orders)
)


# Customer delivery before carrier delivery
invalid = (
    orders["order_delivered_customer_date"].notna()
    & orders["order_delivered_carrier_date"].notna()
    & (
        orders["order_delivered_customer_date"]
        < orders["order_delivered_carrier_date"]
    )
)

report_check(
    "Customer delivery before carrier delivery",
    invalid.sum(),
    len(orders)
)


# Delivered after estimated date
invalid = (
    orders["order_delivered_customer_date"].notna()
    & (
        orders["order_delivered_customer_date"]
        > orders["order_estimated_delivery_date"]
    )
)

report_check(
    "Delivered after estimated delivery date",
    invalid.sum(),
    len(orders)
)


# ==================================================
# ORDER ITEMS
# ==================================================

print("\n" + "=" * 70)
print("ORDER ITEM BUSINESS RULES")
print("=" * 70)


report_check(
    "Negative price",
    (order_items["price"] < 0).sum(),
    len(order_items)
)


report_check(
    "Negative freight value",
    (order_items["freight_value"] < 0).sum(),
    len(order_items)
)


report_check(
    "Invalid order item ID",
    (order_items["order_item_id"] < 1).sum(),
    len(order_items)
)


# ==================================================
# PAYMENTS
# ==================================================

print("\n" + "=" * 70)
print("PAYMENT BUSINESS RULES")
print("=" * 70)


report_check(
    "Negative payment value",
    (payments["payment_value"] < 0).sum(),
    len(payments)
)


report_check(
    "Invalid payment installments",
    (payments["payment_installments"] < 1).sum(),
    len(payments)
)


# ==================================================
# REVIEWS
# ==================================================

print("\n" + "=" * 70)
print("REVIEW BUSINESS RULES")
print("=" * 70)


invalid = ~reviews["review_score"].isin(
    [1, 2, 3, 4, 5]
)

report_check(
    "Invalid review score",
    invalid.sum(),
    len(reviews)
)


# ==================================================
# PRODUCTS
# ==================================================

print("\n" + "=" * 70)
print("PRODUCT BUSINESS RULES")
print("=" * 70)


report_check(
    "Negative product weight",
    (
        products["product_weight_g"].notna()
        & (products["product_weight_g"] < 0)
    ).sum(),
    len(products)
)


report_check(
    "Negative product length",
    (
        products["product_length_cm"].notna()
        & (products["product_length_cm"] < 0)
    ).sum(),
    len(products)
)


report_check(
    "Negative product height",
    (
        products["product_height_cm"].notna()
        & (products["product_height_cm"] < 0)
    ).sum(),
    len(products)
)


report_check(
    "Negative product width",
    (
        products["product_width_cm"].notna()
        & (products["product_width_cm"] < 0)
    ).sum(),
    len(products)
)


report_check(
    "Negative photo count",
    (
        products["product_photos_qty"].notna()
        & (products["product_photos_qty"] < 0)
    ).sum(),
    len(products)
)


# ==================================================
# MARKETING
# ==================================================

print("\n" + "=" * 70)
print("MARKETING BUSINESS RULES")
print("=" * 70)


report_check(
    "Negative catalog size",
    (
        closed_deals["declared_product_catalog_size"]
        .notna()
        & (
            closed_deals["declared_product_catalog_size"]
            < 0
        )
    ).sum(),
    len(closed_deals)
)


report_check(
    "Negative monthly revenue",
    (
        closed_deals["declared_monthly_revenue"]
        .notna()
        & (
            closed_deals["declared_monthly_revenue"]
            < 0
        )
    ).sum(),
    len(closed_deals)
)


# ==================================================
# CATEGORICAL VALUES
# ==================================================

print("\n" + "=" * 70)
print("ORDER STATUS VALUES")
print("=" * 70)

print(
    orders["order_status"]
    .value_counts(dropna=False)
)


print("\n" + "=" * 70)
print("PAYMENT TYPE VALUES")
print("=" * 70)

print(
    payments["payment_type"]
    .value_counts(dropna=False)
)


print("\n" + "=" * 70)
print("REVIEW SCORE DISTRIBUTION")
print("=" * 70)

print(
    reviews["review_score"]
    .value_counts()
    .sort_index()
)


print("\n" + "=" * 70)
print("BUSINESS VALIDATION COMPLETE")
print("=" * 70)