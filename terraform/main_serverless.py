#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput, TerraformAsset, AssetType
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.default_vpc import DefaultVpc
from cdktf_cdktf_provider_aws.default_subnet import DefaultSubnet
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction
from cdktf_cdktf_provider_aws.lambda_permission import LambdaPermission
from cdktf_cdktf_provider_aws.data_aws_caller_identity import DataAwsCallerIdentity
from cdktf_cdktf_provider_aws.s3_bucket import S3Bucket
from cdktf_cdktf_provider_aws.s3_bucket_cors_configuration import S3BucketCorsConfiguration, S3BucketCorsConfigurationCorsRule
from cdktf_cdktf_provider_aws.s3_bucket_notification import S3BucketNotification, S3BucketNotificationLambdaFunction
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable, DynamodbTableAttribute
class ServerlessStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)
        AwsProvider(self, "AWS", region="us-east-1")

        account_id = DataAwsCallerIdentity(self, "acount_id").account_id
        
        bucket = S3Bucket(
            self, "s3_bucket",
            bucket_prefix = "my-cdtf-test-bucket",
            acl="private",
            force_destroy=True,
            versioning={"enabled":True}
        )

        S3BucketCorsConfiguration(
            self, "cors",
            bucket=bucket.id,
            cors_rule=[S3BucketCorsConfigurationCorsRule(
                allowed_headers = ["*"],
                allowed_methods = ["GET", "HEAD", "PUT"],
                allowed_origins = ["*"]
            )]
            )
        dynamo_table = DynamodbTable(
            self, "DynamodDB-table",
            name= "posts",
            hash_key="user",
            range_key="id",
            attribute=[
                DynamodbTableAttribute(name="user",type="S" ),
                DynamodbTableAttribute(name="id",type="S" ),
            ],
            billing_mode="PROVISIONED",
            read_capacity=5,
            write_capacity=5,
        )

        # Packagage du code
        # code = TerraformAsset()

        # lambda_function = LambdaFunction()

        # permission = LambdaPermission()

        # notification = S3BucketNotification()

        TerraformOutput(
            self, "bucket",
            value=bucket.id,
        )


        TerraformOutput(
            self, "dynamodb",
            value=dynamo_table.id,
        )
        
        # TerraformOutput()

app = App()
ServerlessStack(app, "cdktf_serverless")
app.synth()

