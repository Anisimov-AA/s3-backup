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


class CleanerStack(Stack):
    def __init__(self, scope: Construct, id: str,
                 dst_bucket: s3.Bucket,
                 table: dynamodb.Table,
                 **kwargs):
        super().__init__(scope, id, **kwargs)

        # ---- Cleaner Lambda ----
        self.cleaner_lambda = _lambda.Function(self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="cleaner.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "DST_BUCKET": dst_bucket.bucket_name,
                "TABLE_NAME": table.table_name,
            },
        )

        # Grant permissions
        dst_bucket.grant_read_write(self.cleaner_lambda)
        table.grant_read_write_data(self.cleaner_lambda)

        # ---- EventBridge Rule: trigger every 1 minute ----
        rule = events.Rule(self, "CleanerSchedule",
            schedule=events.Schedule.rate(Duration.minutes(1)),
        )

        rule.add_target(targets.LambdaFunction(self.cleaner_lambda))