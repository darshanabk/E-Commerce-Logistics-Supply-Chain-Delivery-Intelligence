import os
from io import BytesIO

import boto3
import pandas as pd
from dotenv import load_dotenv


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    region_name="us-east-1",
)

BUCKET = os.getenv("MINIO_BUCKET")


# --------------------------------------------------
# Load orders
# --------------------------------------------------

obj = s3.get_object(
    Bucket=BUCKET,
    Key="brazilian-ecommerce/olist_orders_dataset.csv"
)

orders = pd.read_csv(
    BytesIO(obj["Body"].read())
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


# ==================================================
# 1. Carrier before purchase
# ==================================================

carrier_issue = orders[
    orders["order_delivered_carrier_date"].notna()
    & (
        orders["order_delivered_carrier_date"]
        < orders["order_purchase_timestamp"]
    )
].copy()

carrier_issue["difference_hours"] = (
    carrier_issue["order_delivered_carrier_date"]
    - carrier_issue["order_purchase_timestamp"]
).dt.total_seconds() / 3600


print("\n" + "=" * 70)
print("CARRIER DELIVERY BEFORE PURCHASE")
print("=" * 70)

print(
    carrier_issue[
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_carrier_date",
            "difference_hours",
        ]
    ].to_string(index=False)
)


# ==================================================
# 2. Customer delivery before carrier delivery
# ==================================================

customer_issue = orders[
    orders["order_delivered_customer_date"].notna()
    & orders["order_delivered_carrier_date"].notna()
    & (
        orders["order_delivered_customer_date"]
        < orders["order_delivered_carrier_date"]
    )
].copy()

customer_issue["difference_hours"] = (
    customer_issue["order_delivered_customer_date"]
    - customer_issue["order_delivered_carrier_date"]
).dt.total_seconds() / 3600


print("\n" + "=" * 70)
print("CUSTOMER DELIVERY BEFORE CARRIER DELIVERY")
print("=" * 70)

print(
    customer_issue[
        [
            "order_id",
            "order_status",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "difference_hours",
        ]
    ].to_string(index=False)
)


# ==================================================
# 3. Invalid payment installments
# ==================================================

obj = s3.get_object(
    Bucket=BUCKET,
    Key="brazilian-ecommerce/olist_order_payments_dataset.csv"
)

payments = pd.read_csv(
    BytesIO(obj["Body"].read())
)

payment_issue = payments[
    payments["payment_installments"] < 1
]

print("\n" + "=" * 70)
print("INVALID PAYMENT INSTALLMENTS")
print("=" * 70)

print(
    payment_issue.to_string(index=False)
)


# ==================================================
# 4. Not-defined payment types
# ==================================================

undefined_payment = payments[
    payments["payment_type"] == "not_defined"
]

print("\n" + "=" * 70)
print("NOT DEFINED PAYMENT TYPES")
print("=" * 70)

print(
    undefined_payment.to_string(index=False)
)


print("\n" + "=" * 70)
print("ANOMALY INVESTIGATION COMPLETE")
print("=" * 70)