import boto3
import os
from datetime import datetime, timezone, timedelta

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
DST_BUCKET = os.environ["DST_BUCKET"]


def lambda_handler(event, context):
    # 1. Calculate the cutoff time (now - 10 seconds)
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()

    # 2. Query the GSI for all DISOWNED copies older than 10 seconds
    response = table.query(
        IndexName="StatusIndex",
        KeyConditionExpression=boto3.dynamodb.conditions.Key("status").eq("DISOWNED")
        & boto3.dynamodb.conditions.Key("disowned_at").lte(cutoff),
    )
    items = response["Items"]

    # 3. Delete each copy from Dst bucket and remove from Table T
    for item in items:
        # Delete the copy from Dst bucket
        s3.delete_object(Bucket=DST_BUCKET, Key=item["copy_key"])

        # Remove the record from Table T
        table.delete_item(Key={
            "original_key": item["original_key"],
            "copy_key": item["copy_key"],
        })

    print(f"Cleaned up {len(items)} disowned copies")