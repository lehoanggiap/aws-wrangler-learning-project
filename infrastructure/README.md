# Yaki FastAPI ECS Infrastructure

This directory contains AWS CDK infrastructure code to deploy the Yaki FastAPI application to AWS ECS Fargate with a complete production-ready setup.

## 🏗️ Architecture Overview

The infrastructure includes:

- **VPC**: Custom VPC with public and private subnets across 2 AZs
- **ECS Fargate**: Containerized FastAPI application with auto-scaling
- **Application Load Balancer**: Public-facing load balancer with health checks
- **CloudWatch Logs**: Centralized logging for monitoring
- **Secrets Manager**: Secure storage for AWS credentials
- **IAM Roles**: Least-privilege access for S3 and CloudWatch
- **Auto Scaling**: CPU and memory-based scaling (1-10 instances)

## 📋 Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Node.js** installed (for CDK CLI)
3. **Python 3.11+** installed
4. **Docker** installed (for container building)

## 🚀 Quick Deployment

### 1. Install Dependencies

```bash
# Install CDK CLI globally
npm install -g aws-cdk

# Navigate to infrastructure directory
cd infrastructure

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Deploy Infrastructure

```bash
# Run the deployment script
python deploy.py
```

Or manually:

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Preview changes
cdk diff

# Deploy
cdk deploy
```

## 🔧 Configuration

### Environment Variables

The ECS tasks will have access to:

- `AWS_DEFAULT_REGION`: Set automatically to deployment region
- `S3_BUCKET_NAME`: Your S3 bucket name
- `AWS_ACCESS_KEY_ID`: From Secrets Manager
- `AWS_SECRET_ACCESS_KEY`: From Secrets Manager

### Secrets Manager

After deployment, update the AWS credentials in Secrets Manager:

1. Go to AWS Secrets Manager console
2. Find secret: `yaki-fastapi/aws-credentials`
3. Update with your actual AWS credentials

## 📊 Monitoring & Logs

### CloudWatch Logs
- Log Group: `/ecs/yaki-fastapi`
- Retention: 7 days
- Stream Prefix: `yaki-fastapi`

### Health Checks
- Path: `/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Healthy threshold: 2
- Unhealthy threshold: 3

### Auto Scaling
- **CPU Scaling**: Target 70% utilization
- **Memory Scaling**: Target 80% utilization
- **Min Capacity**: 1 instance
- **Max Capacity**: 10 instances
- **Cooldown**: 5 minutes

## 🔒 Security Features

- **Non-root container user**: Application runs as `app` user
- **Private subnets**: ECS tasks run in private subnets
- **IAM least privilege**: Minimal required permissions
- **Secrets management**: Credentials stored in Secrets Manager
- **VPC isolation**: Network-level security

## 💰 Cost Optimization

- **Fargate Spot**: Consider using Spot instances for dev environments
- **Right-sizing**: 512 CPU units, 1GB memory (adjustable)
- **Log retention**: 7 days (configurable)
- **NAT Gateway**: Single NAT gateway for cost efficiency

## 🛠️ Customization

### Scaling Configuration

Edit `infrastructure_stack.py`:

```python
# Adjust CPU/Memory
memory_limit_mib=1024,  # 1GB
cpu=512,                # 0.5 vCPU

# Adjust scaling targets
target_utilization_percent=70,  # CPU
target_utilization_percent=80,  # Memory

# Adjust capacity
min_capacity=1,
max_capacity=10
```

### Environment Variables

Add more environment variables in the `environment` section:

```python
environment={
    "AWS_DEFAULT_REGION": self.region,
    "S3_BUCKET_NAME": "your-bucket-name",
    "CUSTOM_VAR": "custom-value"
}
```

## �� Testing

### Local Testing

```bash
# Build Docker image locally
docker build -t yaki-fastapi ../

# Run container
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=your_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret \
  -e AWS_DEFAULT_REGION=us-east-1 \
  yaki-fastapi
```

### Production Testing

After deployment, test the endpoints:

```bash
# Get load balancer URL from CDK output
LOAD_BALANCER_URL="http://your-alb-url"

# Test health endpoint
curl $LOAD_BALANCER_URL/health

# Test API endpoints
curl $LOAD_BALANCER_URL/api/news
curl $LOAD_BALANCER_URL/api/news/stats
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to ECS
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy CDK
        run: |
          cd infrastructure
          npm install -g aws-cdk
          pip install -r requirements.txt
          cdk deploy --require-approval never
```

## 🗑️ Cleanup

To destroy the infrastructure:

```bash
cdk destroy
```

**Warning**: This will delete all resources including the load balancer, ECS service, and VPC.

## 📞 Support

For issues or questions:

1. Check CloudWatch logs for application errors
2. Verify Secrets Manager credentials
3. Check ECS service health in AWS console
4. Review security group and network ACL settings

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [ECS Fargate Documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html)
- [Application Load Balancer Documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/)
