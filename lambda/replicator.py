import boto3
import os
from datetime import datetime, timezone

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
DST_BUCKET = os.environ["DST_BUCKET"]
SRC_BUCKET = os.environ["SRC_BUCKET"]


def lambda_handler(event, context):
    # EventBridge event format
    detail_type = event["detail-type"]
    original_key = event["detail"]["object"]["key"]

    if detail_type == "Object Created":
        handle_put(original_key)
    elif detail_type == "Object Deleted":
        handle_delete(original_key)


def handle_put(original_key):
    # 1. Create a unique copy name using timestamp
    now = datetime.now(timezone.utc).isoformat()
    copy_key = f"{original_key}_{now}"

    # 2. Copy object from Src to Dst
    s3.copy_object(
        CopySource={"Bucket": SRC_BUCKET, "Key": original_key},
        Bucket=DST_BUCKET,
        Key=copy_key,
    )

    # 3. Record the mapping in Table T
    table.put_item(Item={
        "original_key": original_key,
        "copy_key": copy_key,
        "copy_timestamp": now,
        "status": "ACTIVE",
    })

    # 4. Query all ACTIVE copies for this original object
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("original_key").eq(original_key),
        FilterExpression=boto3.dynamodb.conditions.Attr("status").eq("ACTIVE"),
    )
    copies = response["Items"]

    # 5. If more than 3 copies, delete the oldest
    if len(copies) > 3:
        # Sort by copy_timestamp, oldest first
        copies.sort(key=lambda x: x["copy_timestamp"])
        oldest = copies[0]

        # Delete oldest copy from Dst bucket
        s3.delete_object(Bucket=DST_BUCKET, Key=oldest["copy_key"])

        # Remove oldest record from Table T
        table.delete_item(Key={
            "original_key": original_key,
            "copy_key": oldest["copy_key"],
        })


def handle_delete(original_key):
    # 1. Query all ACTIVE copies for this original object
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("original_key").eq(original_key),
        FilterExpression=boto3.dynamodb.conditions.Attr("status").eq("ACTIVE"),
    )
    copies = response["Items"]

    # 2. Mark each copy as DISOWNED
    now = datetime.now(timezone.utc).isoformat()
    for copy in copies:
        table.update_item(
            Key={
                "original_key": original_key,
                "copy_key": copy["copy_key"],
            },
            UpdateExpression="SET #s = :status, disowned_at = :disowned_at",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={
                ":status": "DISOWNED",
                ":disowned_at": now,
            },
        )