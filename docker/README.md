# Docker Image Tagging System

This document explains the comprehensive image tagging system implemented for the Yaki FastAPI application.

## 🏷️ Tagging Strategy

### Automatic Tags
Every Docker image built includes the following metadata:

- **Version Tag**: Git tag or commit hash (e.g., `v1.2.3` or `abc1234`)
- **Build Date**: ISO 8601 timestamp of when the image was built
- **VCS Reference**: Short Git commit hash
- **Labels**: Comprehensive metadata labels following the Label Schema specification

### Tag Examples
```
yaki-fastapi:abc1234        # Git commit hash
yaki-fastapi:v1.2.3         # Git tag
yaki-fastapi:latest         # Latest build
```

## 🔧 Build Arguments

The Dockerfile accepts the following build arguments:

| Argument | Description | Example |
|----------|-------------|---------|
| `BUILD_DATE` | ISO 8601 build timestamp | `2024-12-09T10:30:00Z` |
| `VCS_REF` | Git commit hash | `abc1234` |
| `VERSION` | Git version/tag | `v1.2.3` or `abc1234-dirty` |

## 📋 Image Labels

Each image includes comprehensive metadata labels:

```dockerfile
LABEL maintainer="Yaki Project Team"
LABEL org.label-schema.build-date="2024-12-09T10:30:00Z"
LABEL org.label-schema.name="yaki-fastapi"
LABEL org.label-schema.description="FastAPI application for Yaki project with AWS Wrangler"
LABEL org.label-schema.vcs-ref="abc1234"
LABEL org.label-schema.version="v1.2.3"
```

## 🚀 Usage

### Local Development

#### Option 1: Use the Build Script (Recommended)
```bash
# Build with automatic tagging
./scripts/build-image.sh

# Build with custom tag
./scripts/build-image.sh my-custom-tag

# Build with version tag
./scripts/build-image.sh v1.2.3
```

#### Option 2: Manual Docker Build
```bash
# Get build variables
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD)
VERSION=$(git describe --tags --always)

# Build with metadata
docker build \
  --build-arg BUILD_DATE="$BUILD_DATE" \
  --build-arg VCS_REF="$VCS_REF" \
  --build-arg VERSION="$VERSION" \
  --tag yaki-fastapi:$VCS_REF \
  --tag yaki-fastapi:latest \
  docker/
```

### CI/CD Pipeline

The GitHub Actions workflow automatically:

1. **Generates build variables** from Git metadata
2. **Passes build arguments** to CDK
3. **Creates tagged images** in ECR
4. **Tracks deployments** with image metadata

### Viewing Image Information

#### Check Image Labels
```bash
# View all labels
docker inspect yaki-fastapi:latest --format='{{range $k, $v := .Config.Labels}}{{$k}}: {{$v}}{{"\n"}}{{end}}'

# View specific label
docker inspect yaki-fastapi:latest --format='{{.Config.Labels.org.label-schema.version}}'
```

#### List Images with Tags
```bash
# List all yaki-fastapi images
docker images yaki-fastapi

# List with custom format
docker images yaki-fastapi --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Build Arguments Not Passed
**Problem**: Labels show "unknown" values
**Solution**: Ensure build arguments are passed correctly:
```bash
docker build --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" ...
```

#### 2. Git Information Missing
**Problem**: VCS_REF shows "unknown"
**Solution**: Ensure you're in a Git repository:
```bash
git status  # Check if in Git repo
git log --oneline -1  # Check recent commits
```

#### 3. Version Shows "dirty"
**Problem**: Version includes "-dirty" suffix
**Solution**: Commit your changes:
```bash
git status  # Check uncommitted changes
git add .
git commit -m "Your commit message"
```

### Debugging Commands

```bash
# Check build arguments during build
docker build --progress=plain --no-cache ...

# Inspect image after build
docker inspect yaki-fastapi:latest | jq '.Config.Labels'

# Check image history
docker history yaki-fastapi:latest
```

## 🏗️ CDK Integration

### Environment Variables
The CDK stack reads build metadata from environment variables:

```bash
export CDK_BUILD_DATE="2024-12-09T10:30:00Z"
export CDK_VCS_REF="abc1234"
export CDK_VERSION="v1.2.3"
```

### CDK Outputs
After deployment, CDK provides:

- **ImageBuildInfo**: Build metadata summary
- **ImageAssetId**: Unique asset hash for tracking
- **ECRRepositoryInfo**: Repository information

### Viewing CDK Outputs
```bash
# Get all stack outputs
aws cloudformation describe-stacks \
  --stack-name InfrastructureStack \
  --query 'Stacks[0].Outputs'

# Get specific output
aws cloudformation describe-stacks \
  --stack-name InfrastructureStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ImageBuildInfo`].OutputValue' \
  --output text
```

## 📊 Monitoring

### ECR Image Tracking
```bash
# List images in ECR
aws ecr describe-images --repository-name cdk-assets

# Get image with specific tag
aws ecr describe-images \
  --repository-name cdk-assets \
  --image-ids imageTag=abc1234

# List recent images
aws ecr describe-images \
  --repository-name cdk-assets \
  --max-items 10 \
  --query 'imageDetails[*].{Pushed:imagePushedAt,Tags:imageTags}'
```

### ECS Task Definition Tracking
```bash
# Get current task definition
aws ecs describe-services \
  --cluster yaki-fastapi-cluster \
  --services YakiFargateService \
  --query 'services[0].taskDefinition'

# Get task definition details
aws ecs describe-task-definition \
  --task-definition arn:aws:ecs:region:account:task-definition/family:revision \
  --query 'taskDefinition.containerDefinitions[0].image'
```

## 🔒 Security Considerations

### Image Scanning
```bash
# Scan image for vulnerabilities (if ECR scanning enabled)
aws ecr describe-image-scan-findings \
  --repository-name cdk-assets \
  --image-id imageTag=abc1234
```

### Best Practices
1. **Regular Updates**: Keep base images updated
2. **Minimal Images**: Use slim/alpine variants when possible
3. **Non-root User**: Images run as non-root user
4. **Secrets Management**: Never include secrets in images
5. **Vulnerability Scanning**: Enable ECR vulnerability scanning

## 📚 References

- [Label Schema Specification](http://label-schema.org/)
- [Docker Build Arguments](https://docs.docker.com/engine/reference/builder/#arg)
- [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [CDK Docker Assets](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_ecr_assets-readme.html) 