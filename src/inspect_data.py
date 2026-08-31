import os
import json
from io import BytesIO

import boto3
import pandas as pd
from dotenv import load_dotenv


# --------------------------------------------------
# 1. Load configuration
# --------------------------------------------------

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")


# --------------------------------------------------
# 2. Connect to MinIO
# --------------------------------------------------

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1",
)


# --------------------------------------------------
# 3. List CSV files in MinIO
# --------------------------------------------------

response = s3.list_objects_v2(Bucket=MINIO_BUCKET)

files = [
    obj["Key"]
    for obj in response.get("Contents", [])
    if obj["Key"].endswith(".csv")
]

print(f"\nFound {len(files)} CSV files:\n")

for file in files:
    print(f"  {file}")


# --------------------------------------------------
# 4. Inspect each dataset
# --------------------------------------------------

report = {}

for file in files:

    print(f"\n{'=' * 70}")
    print(f"DATASET: {file}")
    print(f"{'=' * 70}")

    # Download file from MinIO into memory
    obj = s3.get_object(
        Bucket=MINIO_BUCKET,
        Key=file
    )

    df = pd.read_csv(
        BytesIO(obj["Body"].read())
    )

    # Basic information
    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns):,}")

    print("\nColumns:")
    print(list(df.columns))

    # Missing values
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)

    print("\nMissing values:")

    if missing.empty:
        print("  None")
    else:
        print(missing)

    # Duplicate rows
    duplicates = df.duplicated().sum()

    print(f"\nDuplicate rows: {duplicates:,}")

    # Data types
    print("\nData types:")
    print(df.dtypes)

    # Build report
    report[file] = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "duplicates": int(duplicates),
        "missing_values": {
            str(k): int(v)
            for k, v in missing.items()
        },
        "data_types": {
            str(k): str(v)
            for k, v in df.dtypes.items()
        },
    }


# --------------------------------------------------
# 5. Save report
# --------------------------------------------------

os.makedirs("reports", exist_ok=True)

with open(
    "reports/data_quality_report.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        report,
        f,
        indent=2
    )

print("\n" + "=" * 70)
print("Inspection complete.")
print("Report saved to: reports/data_quality_report.json")
print("=" * 70)