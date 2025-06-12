#!/bin/bash

# Build script for Yaki FastAPI Docker image with proper tagging
# Usage: ./scripts/build-image.sh [tag]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Building Yaki FastAPI Docker Image${NC}"
echo "========================================"

# Get build variables
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo 'latest')
BRANCH=$(git branch --show-current 2>/dev/null || echo 'unknown')

# Use provided tag or generate one
if [ -n "$1" ]; then
    IMAGE_TAG="$1"
else
    IMAGE_TAG="${VCS_REF}"
fi

IMAGE_NAME="yaki-fastapi"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${YELLOW}📋 Build Information:${NC}"
echo "  Image Name: ${FULL_IMAGE_NAME}"
echo "  Build Date: ${BUILD_DATE}"
echo "  VCS Ref: ${VCS_REF}"
echo "  Version: ${VERSION}"
echo "  Branch: ${BRANCH}"
echo ""

# Determine if we're running from scripts/ directory or project root
if [ -d "docker" ]; then
    # Running from project root
    BUILD_CONTEXT="."
    DOCKERFILE_PATH="docker/Dockerfile"
elif [ -d "../docker" ]; then
    # Running from scripts/ directory
    BUILD_CONTEXT=".."
    DOCKERFILE_PATH="../docker/Dockerfile"
else
    echo -e "${RED}❌ Error: docker/ directory not found${NC}"
    echo "Please run this script from either:"
    echo "  - Project root directory: ./scripts/build-image.sh"
    echo "  - Scripts directory: ./build-image.sh"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo -e "${RED}❌ Error: Dockerfile not found at $DOCKERFILE_PATH${NC}"
    exit 1
fi

# Check if required files exist in build context
if [ ! -f "$BUILD_CONTEXT/requirements.txt" ]; then
    echo -e "${RED}❌ Error: requirements.txt not found in build context${NC}"
    exit 1
fi

if [ ! -d "$BUILD_CONTEXT/api" ]; then
    echo -e "${RED}❌ Error: api/ directory not found in build context${NC}"
    exit 1
fi

if [ ! -f "$BUILD_CONTEXT/config.yaml" ]; then
    echo -e "${RED}❌ Error: config.yaml not found in build context${NC}"
    exit 1
fi

echo -e "${BLUE}🔨 Building Docker image...${NC}"
echo "  Build Context: $BUILD_CONTEXT"
echo "  Dockerfile: $DOCKERFILE_PATH"
echo ""

# Build the image with build arguments
docker build \
    --file "$DOCKERFILE_PATH" \
    --build-arg BUILD_DATE="${BUILD_DATE}" \
    --build-arg VCS_REF="${VCS_REF}" \
    --build-arg VERSION="${VERSION}" \
    --tag "${FULL_IMAGE_NAME}" \
    --tag "${IMAGE_NAME}:latest" \
    "$BUILD_CONTEXT"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Build completed successfully!${NC}"
    echo ""
    
    # Show image information
    echo -e "${BLUE}📦 Image Information:${NC}"
    docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}"
    echo ""
    
    # Show image labels
    echo -e "${BLUE}🏷️  Image Labels:${NC}"
    docker inspect "${FULL_IMAGE_NAME}" --format='{{range $k, $v := .Config.Labels}}{{$k}}: {{$v}}{{"\n"}}{{end}}' | sort
    echo ""
    
    echo -e "${GREEN}🚀 Ready to run:${NC}"
    echo "  docker run -p 8000:8000 ${FULL_IMAGE_NAME}"
    echo ""
    echo -e "${YELLOW}💡 Additional tags created:${NC}"
    echo "  ${IMAGE_NAME}:latest"
    
else
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi 