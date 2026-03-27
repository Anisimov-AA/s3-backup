import aws_cdk as cdk
from backup_system.storage_stack import StorageStack
from backup_system.replicator_stack import ReplicatorStack
from backup_system.cleaner_stack import CleanerStack

app = cdk.App()

storage = StorageStack(app, "StorageStack")

replicator = ReplicatorStack(app, "ReplicatorStack",
    src_bucket=storage.src_bucket,
    dst_bucket=storage.dst_bucket,
    table=storage.table,
)

cleaner = CleanerStack(app, "CleanerStack",
    dst_bucket=storage.dst_bucket,
    table=storage.table,
)

app.synth()