#!/bin/bash

# SubForge Dashboard Deployment Script
# This script handles deployment to different environments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEPLOYMENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Print usage
usage() {
    cat << EOF
SubForge Dashboard Deployment Script

Usage: $0 [OPTIONS] ENVIRONMENT

Environments:
  local       - Deploy using Docker Compose for local development
  staging     - Deploy to staging Kubernetes cluster
  production  - Deploy to production Kubernetes cluster

Options:
  -h, --help              Show this help message
  -v, --verbose           Enable verbose output
  -d, --dry-run          Show what would be deployed without actually deploying
  -f, --force            Force deployment even if validation fails
  --skip-tests           Skip running tests before deployment
  --skip-migration       Skip database migration
  --rollback VERSION     Rollback to specified version
  --health-check         Only run health checks
  --build-images         Build Docker images locally

Examples:
  $0 local                           # Deploy locally with Docker Compose
  $0 staging --build-images          # Build and deploy to staging
  $0 production --dry-run            # Show what would be deployed to production
  $0 --rollback v1.2.0 production    # Rollback production to version 1.2.0

EOF
}

# Parse command line arguments
ENVIRONMENT=""
VERBOSE=false
DRY_RUN=false
FORCE=false
SKIP_TESTS=false
SKIP_MIGRATION=false
ROLLBACK_VERSION=""
HEALTH_CHECK_ONLY=false
BUILD_IMAGES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            set -x
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-migration)
            SKIP_MIGRATION=true
            shift
            ;;
        --rollback)
            ROLLBACK_VERSION="$2"
            shift 2
            ;;
        --health-check)
            HEALTH_CHECK_ONLY=true
            shift
            ;;
        --build-images)
            BUILD_IMAGES=true
            shift
            ;;
        local|staging|production)
            ENVIRONMENT="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "Environment is required"
    usage
    exit 1
fi

# Set environment-specific variables
case "$ENVIRONMENT" in
    local)
        COMPOSE_FILE="${DEPLOYMENT_DIR}/docker/docker-compose.dev.yml"
        NAMESPACE="default"
        ;;
    staging)
        NAMESPACE="subforge-staging"
        KUBECONFIG_PATH="${HOME}/.kube/staging-config"
        ;;
    production)
        NAMESPACE="subforge"
        KUBECONFIG_PATH="${HOME}/.kube/production-config"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Health check function
check_health() {
    log_info "Running health checks for $ENVIRONMENT environment..."
    
    case "$ENVIRONMENT" in
        local)
            # Check Docker services
            if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
                log_success "Local services are running"
                return 0
            else
                log_error "Local services are not healthy"
                return 1
            fi
            ;;
        staging|production)
            # Check Kubernetes deployments
            if kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" get deployments -o jsonpath='{.items[*].status.readyReplicas}' | grep -q "^[1-9]"; then
                log_success "Kubernetes deployments are healthy"
                return 0
            else
                log_error "Kubernetes deployments are not healthy"
                return 1
            fi
            ;;
    esac
}

# Run tests
run_tests() {
    if [[ "$SKIP_TESTS" == true ]]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_info "Running tests..."
    
    # Backend tests
    log_info "Running backend tests..."
    cd "${ROOT_DIR}/backend"
    if [[ -f "requirements.txt" ]]; then
        python -m pytest tests/ --cov=. --cov-report=term-missing || {
            log_error "Backend tests failed"
            return 1
        }
    fi
    
    # Frontend tests
    log_info "Running frontend tests..."
    cd "${ROOT_DIR}/frontend"
    if [[ -f "package.json" ]]; then
        npm test -- --coverage --watchAll=false || {
            log_error "Frontend tests failed"
            return 1
        }
    fi
    
    log_success "All tests passed"
    cd "$SCRIPT_DIR"
}

# Build Docker images
build_images() {
    if [[ "$BUILD_IMAGES" == false ]] && [[ "$ENVIRONMENT" == "local" ]]; then
        return 0
    fi
    
    log_info "Building Docker images..."
    
    cd "$ROOT_DIR"
    
    # Build backend image
    docker build \
        -f "${DEPLOYMENT_DIR}/docker/backend.Dockerfile" \
        -t "subforge/backend:latest" \
        --target production \
        .
    
    # Build frontend image
    docker build \
        -f "${DEPLOYMENT_DIR}/docker/frontend.Dockerfile" \
        -t "subforge/frontend:latest" \
        --target production \
        --build-arg NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}" \
        --build-arg NEXT_PUBLIC_WS_URL="${NEXT_PUBLIC_WS_URL:-ws://localhost:8000}" \
        .
    
    log_success "Docker images built successfully"
}

# Database migration
run_migration() {
    if [[ "$SKIP_MIGRATION" == true ]]; then
        log_warning "Skipping database migration as requested"
        return 0
    fi
    
    log_info "Running database migration..."
    
    case "$ENVIRONMENT" in
        local)
            # Wait for database to be ready
            log_info "Waiting for database to be ready..."
            docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U subforge -d subforge_dev
            
            # Run migration
            docker-compose -f "$COMPOSE_FILE" exec -T backend alembic upgrade head
            ;;
        staging|production)
            # Run migration in Kubernetes
            kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" \
                create job "db-migrate-$(date +%s)" --from=deployment/backend \
                --image="subforge/backend:latest" \
                -- sh -c "alembic upgrade head"
            ;;
    esac
    
    log_success "Database migration completed"
}

# Deploy to local environment
deploy_local() {
    log_info "Deploying to local environment..."
    
    cd "$DEPLOYMENT_DIR/docker"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would execute: docker-compose -f $COMPOSE_FILE up -d"
        return 0
    fi
    
    # Stop existing services
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    
    # Pull latest images if not building locally
    if [[ "$BUILD_IMAGES" == false ]]; then
        docker-compose -f "$COMPOSE_FILE" pull
    fi
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    log_success "Local deployment completed"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    log_info "Deploying to $ENVIRONMENT environment..."
    
    # Verify kubectl access
    if ! kubectl --kubeconfig="$KUBECONFIG_PATH" cluster-info &>/dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    cd "${DEPLOYMENT_DIR}/kubernetes"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would deploy the following resources:"
        kubectl --kubeconfig="$KUBECONFIG_PATH" --dry-run=client -o yaml apply -f namespace.yaml
        kubectl --kubeconfig="$KUBECONFIG_PATH" --dry-run=client -o yaml apply -f . -n "$NAMESPACE"
        return 0
    fi
    
    # Apply namespace
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f namespace.yaml
    
    # Apply configurations
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f configmap.yaml -n "$NAMESPACE"
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f secrets.yaml -n "$NAMESPACE"
    
    # Deploy infrastructure services
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f postgres.yaml -n "$NAMESPACE"
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f redis.yaml -n "$NAMESPACE"
    
    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure services..."
    kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" wait --for=condition=ready pod -l app.kubernetes.io/component=database --timeout=300s
    kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" wait --for=condition=ready pod -l app.kubernetes.io/component=cache --timeout=300s
    
    # Deploy application services
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f backend.yaml -n "$NAMESPACE"
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f frontend.yaml -n "$NAMESPACE"
    kubectl --kubeconfig="$KUBECONFIG_PATH" apply -f ingress.yaml -n "$NAMESPACE"
    
    # Wait for application rollout
    log_info "Waiting for application deployment..."
    kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" rollout status deployment/backend --timeout=600s
    kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" rollout status deployment/frontend --timeout=600s
    
    log_success "$ENVIRONMENT deployment completed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back to version $ROLLBACK_VERSION..."
    
    case "$ENVIRONMENT" in
        local)
            log_error "Rollback not supported for local environment"
            exit 1
            ;;
        staging|production)
            kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" \
                set image deployment/backend backend=subforge/backend:"$ROLLBACK_VERSION"
            kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" \
                set image deployment/frontend frontend=subforge/frontend:"$ROLLBACK_VERSION"
            
            kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" rollout status deployment/backend --timeout=300s
            kubectl --kubeconfig="$KUBECONFIG_PATH" -n "$NAMESPACE" rollout status deployment/frontend --timeout=300s
            ;;
    esac
    
    log_success "Rollback to $ROLLBACK_VERSION completed"
}

# Main deployment logic
main() {
    log_info "Starting SubForge Dashboard deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Dry run: $DRY_RUN"
    
    # Handle health check only
    if [[ "$HEALTH_CHECK_ONLY" == true ]]; then
        check_health
        exit $?
    fi
    
    # Handle rollback
    if [[ -n "$ROLLBACK_VERSION" ]]; then
        rollback_deployment
        exit 0
    fi
    
    # Pre-deployment checks
    if [[ "$FORCE" == false ]]; then
        run_tests
    fi
    
    # Build images if requested or for local deployment
    if [[ "$BUILD_IMAGES" == true ]] || [[ "$ENVIRONMENT" == "local" ]]; then
        build_images
    fi
    
    # Deploy based on environment
    case "$ENVIRONMENT" in
        local)
            deploy_local
            ;;
        staging|production)
            deploy_kubernetes
            ;;
    esac
    
    # Run database migration
    run_migration
    
    # Final health check
    log_info "Running post-deployment health check..."
    if check_health; then
        log_success "Deployment successful! 🚀"
        
        # Show access information
        case "$ENVIRONMENT" in
            local)
                log_info "Application available at:"
                log_info "  Frontend: http://localhost:3001"
                log_info "  Backend API: http://localhost:8000"
                log_info "  Backend Docs: http://localhost:8000/docs"
                ;;
            staging)
                log_info "Application available at:"
                log_info "  Frontend: https://staging.subforge.yourdomain.com"
                log_info "  Backend API: https://api-staging.subforge.yourdomain.com"
                ;;
            production)
                log_info "Application available at:"
                log_info "  Frontend: https://subforge.yourdomain.com"
                log_info "  Backend API: https://api.subforge.yourdomain.com"
                ;;
        esac
    else
        log_error "Health check failed after deployment"
        exit 1
    fi
}

# Trap for cleanup
cleanup() {
    if [[ $? -ne 0 ]]; then
        log_error "Deployment failed!"
    fi
}
trap cleanup EXIT

# Run main function
main "$@"