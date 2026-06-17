import boto3
import pandas as pd

bucket = "carmen-proyecto-aemet-2025"
key = "climaticos_2016.csv"

s3 = boto3.client("s3")

obj = s3.get_object(
    Bucket=bucket,
    Key=key
)

df = pd.read_csv(obj["Body"])

print(df.head())
print(f"\nFilas: {len(df)}")