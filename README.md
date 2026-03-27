# Object Backup System

Automated S3 object backup system built with AWS CDK (Python). Maintains up to 3 backup copies per object with automatic cleanup of deleted objects.

## Architecture

| Resource | Purpose |
|----------|---------|
| Bucket Src | Source S3 bucket |
| Bucket Dst | Destination S3 bucket for backup copies |
| Table T | DynamoDB table mapping originals to copies |
| Replicator Lambda | Handles S3 PUT/DELETE events via EventBridge |
| Cleaner Lambda | Runs every 1 min, deletes disowned copies older than 10s |

## CDK Stacks

- **StorageStack** — S3 buckets, DynamoDB table with GSI
- **ReplicatorStack** — Replicator Lambda, EventBridge S3 event rule
- **CleanerStack** — Cleaner Lambda, EventBridge scheduled rule

## DynamoDB Table Design

**Main Table:** `original_key` (PK) + `copy_key` (SK)

**GSI (StatusIndex):** `status` (PK) + `disowned_at` (SK)

All operations use queries — no scans needed.

## Setup

```bash
npm install -g aws-cdk
python -m venv .venv

# Windows
.venv\Scripts\activate.bat
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
cdk bootstrap
cdk deploy --all
```

## Cleanup

```bash
cdk destroy --all
```