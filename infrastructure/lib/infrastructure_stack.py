from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_logs as logs,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    CfnOutput,
    aws_ecr_assets as ecr_assets,
)
from constructs import Construct
import os


class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC with public and private subnets
        vpc = ec2.Vpc(
            self, "YakiVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="PublicSubnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="PrivateSubnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Create ECS Cluster
        cluster = ecs.Cluster(
            self, "YakiCluster",
            vpc=vpc,
            cluster_name="yaki-fastapi-cluster"
        )

        # Create CloudWatch Log Group
        log_group = logs.LogGroup(
            self, "YakiLogGroup",
            log_group_name="/ecs/yaki-fastapi",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create IAM role for ECS task (provides AWS credentials automatically)
        task_role = iam.Role(
            self, "YakiTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )

        # Add custom S3 permissions for your specific bucket
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                resources=[
                    "arn:aws:s3:::yaki-aws-wrangler-learning-*",
                    "arn:aws:s3:::yaki-aws-wrangler-learning-*/*"
                ]
            )
        )

        # Get build variables from environment (set by GitHub Actions)
        build_date = os.environ.get('CDK_BUILD_DATE', 'unknown')
        vcs_ref = os.environ.get('CDK_VCS_REF', 'unknown')
        version = os.environ.get('CDK_VERSION', 'latest')

        docker_image_asset = ecr_assets.DockerImageAsset(
            self, 'YakiFastAPIImage', 
            directory='..',  # Project root directory
            file='docker/Dockerfile',  # Dockerfile path relative to directory
            # Add build arguments for better image tracking
            build_args={
                "BUILD_DATE": build_date,
                "VCS_REF": vcs_ref,
                "VERSION": version
            },
            # Add platform specification for consistency
            platform=ecr_assets.Platform.LINUX_AMD64,
            # Invalidate cache when source code changes
            invalidation=ecr_assets.DockerImageAssetInvalidationOptions(
                build_args=True,
                extra_hash=True  # Include commit hash for unique builds
            )
        )

        # Create Fargate service with Application Load Balancer
        # This uses the NEW ASSET SYSTEM - publishes to default bootstrap repository
        fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "YakiFargateService",
            cluster=cluster,
            memory_limit_mib=1024,
            cpu=512,
            desired_count=2,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                # 🚀 NEW ASSET SYSTEM: This automatically publishes to the default ECR repository
                # created during 'cdk bootstrap'. No repositoryName needed!
                image=ecs.ContainerImage.from_docker_image_asset(docker_image_asset),
                container_port=8000,
                task_role=task_role,
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="yaki-fastapi",
                    log_group=log_group
                ),
                environment={
                    "AWS_DEFAULT_REGION": self.region,
                    "S3_BUCKET_NAME": "yaki-aws-wrangler-learning-20241209"
                }
                # No secrets needed - ECS task automatically uses IAM role credentials!
            ),
            public_load_balancer=True,
            protocol=elbv2.ApplicationProtocol.HTTP,
            listener_port=80
        )

        # Configure health check
        fargate_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(10),
            healthy_threshold_count=2,
            unhealthy_threshold_count=3
        )

        # Configure auto scaling
        scalable_target = fargate_service.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=10
        )

        scalable_target.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=70,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(300)
        )

        scalable_target.scale_on_memory_utilization(
            "MemoryScaling",
            target_utilization_percent=80,
            scale_in_cooldown=Duration.seconds(300),
            scale_out_cooldown=Duration.seconds(300)
        )

        # Output the Load Balancer URL
        CfnOutput(
            self, "LoadBalancerURL",
            value=f"http://{fargate_service.load_balancer.load_balancer_dns_name}",
            description="URL of the load balancer"
        )

        # Output the ECS Cluster name
        CfnOutput(
            self, "ECSClusterName",
            value=cluster.cluster_name,
            description="Name of the ECS cluster"
        )

        # Output the ECR Repository URI (from bootstrap)
        CfnOutput(
            self, "ECRRepositoryInfo",
            value="Images are stored in the default CDK bootstrap ECR repository",
            description="ECR repository information - check AWS Console for exact URI"
        )

        # Output IAM Role information
        CfnOutput(
            self, "TaskRoleARN",
            value=task_role.role_arn,
            description="ARN of the ECS task IAM role (provides AWS credentials automatically)"
        )

        # Output Docker Image Build Information
        CfnOutput(
            self, "ImageBuildInfo",
            value=f"Version: {version} | Commit: {vcs_ref} | Built: {build_date}",
            description="Docker image build information and metadata"
        )

        # Output Image Asset ID for tracking
        CfnOutput(
            self, "ImageAssetId",
            value=docker_image_asset.asset_hash,
            description="Docker image asset hash for tracking deployments"
        )
