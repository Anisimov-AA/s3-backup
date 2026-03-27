from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class ReplicatorStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 src_bucket: s3.Bucket,
                 dst_bucket: s3.Bucket,
                 table: dynamodb.Table,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # ---- Replicator Lambda ----
        self.replicator_lambda = _lambda.Function(self, "ReplicatorLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="replicator.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "DST_BUCKET": dst_bucket.bucket_name,
                "SRC_BUCKET": src_bucket.bucket_name,
                "TABLE_NAME": table.table_name,
            },
        )

        # Grant permissions
        src_bucket.grant_read(self.replicator_lambda)
        dst_bucket.grant_read_write(self.replicator_lambda)
        table.grant_read_write_data(self.replicator_lambda)

        # ---- EventBridge Rule: trigger on PUT events ----
        put_rule = events.Rule(self, "S3PutRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [src_bucket.bucket_name]},
                },
            ),
        )
        put_rule.add_target(targets.LambdaFunction(self.replicator_lambda))

        # ---- EventBridge Rule: trigger on DELETE events ----
        delete_rule = events.Rule(self, "S3DeleteRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Deleted"],
                detail={
                    "bucket": {"name": [src_bucket.bucket_name]},
                },
            ),
        )
        delete_rule.add_target(targets.LambdaFunction(self.replicator_lambda))