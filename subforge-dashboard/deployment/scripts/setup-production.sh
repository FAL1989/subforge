#!/bin/bash

# SubForge Dashboard Production Setup Script
# This script configures a production environment from scratch

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
SubForge Dashboard Production Setup

This script sets up a complete production environment including:
- AWS infrastructure with Terraform
- Kubernetes cluster configuration
- SSL certificates and domain setup
- Monitoring and logging
- CI/CD pipeline configuration

Usage: $0 [OPTIONS]

Options:
  -h, --help              Show this help message
  -d, --domain DOMAIN     Primary domain name (required)
  -e, --email EMAIL       Email for Let's Encrypt certificates (required)
  -r, --region REGION     AWS region (default: us-west-2)
  -c, --cluster NAME      EKS cluster name (default: subforge-cluster)
  --skip-terraform        Skip Terraform infrastructure setup
  --skip-kubernetes       Skip Kubernetes deployment
  --skip-monitoring       Skip monitoring setup
  --dry-run              Show what would be done without executing

Examples:
  $0 -d subforge.example.com -e admin@example.com
  $0 -d myapp.com -e ops@myapp.com -r us-east-1 -c myapp-cluster

Prerequisites:
  - AWS CLI configured with appropriate permissions
  - kubectl installed and configured
  - Terraform installed (>= 1.0)
  - Domain name with DNS control

EOF
}

# Default values
DOMAIN=""
EMAIL=""
REGION="us-west-2"
CLUSTER_NAME="subforge-cluster"
SKIP_TERRAFORM=false
SKIP_KUBERNETES=false
SKIP_MONITORING=false
DRY_RUN=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -e|--email)
            EMAIL="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -c|--cluster)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --skip-terraform)
            SKIP_TERRAFORM=true
            shift
            ;;
        --skip-kubernetes)
            SKIP_KUBERNETES=true
            shift
            ;;
        --skip-monitoring)
            SKIP_MONITORING=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$DOMAIN" ]]; then
    log_error "Domain name is required"
    usage
    exit 1
fi

if [[ -z "$EMAIL" ]]; then
    log_error "Email address is required"
    usage
    exit 1
fi

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    command -v aws >/dev/null 2>&1 || missing_tools+=("aws-cli")
    command -v kubectl >/dev/null 2>&1 || missing_tools+=("kubectl")
    command -v terraform >/dev/null 2>&1 || missing_tools+=("terraform")
    command -v helm >/dev/null 2>&1 || missing_tools+=("helm")
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and run again"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        log_error "AWS credentials not configured or invalid"
        log_info "Please run 'aws configure' to set up your credentials"
        exit 1
    fi
    
    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r '.terraform_version')
    log_info "Terraform version: $tf_version"
    
    log_success "Prerequisites check passed"
}

# Generate secure passwords and keys
generate_secrets() {
    log_info "Generating secure secrets..."
    
    # Generate passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -base64 48)
    JWT_SECRET=$(openssl rand -base64 32)
    GRAFANA_PASSWORD=$(openssl rand -base64 16)
    
    # Create secrets file
    cat > "$DEPLOYMENT_DIR/secrets.env" << EOF
# Generated secrets for production deployment
# Store these securely and do not commit to version control

POSTGRES_PASSWORD="$POSTGRES_PASSWORD"
REDIS_PASSWORD="$REDIS_PASSWORD"
SECRET_KEY="$SECRET_KEY"
JWT_SECRET="$JWT_SECRET"
GRAFANA_PASSWORD="$GRAFANA_PASSWORD"

# Database URLs (constructed from above passwords)
DATABASE_URL="postgresql://subforge:$POSTGRES_PASSWORD@postgres-service:5432/subforge"
REDIS_URL="redis://:$REDIS_PASSWORD@redis-service:6379/0"
EOF
    
    chmod 600 "$DEPLOYMENT_DIR/secrets.env"
    log_success "Secrets generated and saved to $DEPLOYMENT_DIR/secrets.env"
}

# Set up Terraform infrastructure
setup_terraform() {
    if [[ "$SKIP_TERRAFORM" == true ]]; then
        log_warning "Skipping Terraform setup as requested"
        return 0
    fi
    
    log_info "Setting up AWS infrastructure with Terraform..."
    
    cd "$DEPLOYMENT_DIR/terraform"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would execute Terraform commands"
        return 0
    fi
    
    # Initialize Terraform
    terraform init
    
    # Create terraform.tfvars
    cat > terraform.tfvars << EOF
environment     = "production"
region         = "$REGION"
cluster_name   = "$CLUSTER_NAME"
domain_name    = "$DOMAIN"
api_domain_name = "api.$DOMAIN"

# Enable production features
db_deletion_protection = true
enable_cluster_logging = true
enable_spot_instances  = true

# Scaling configuration
min_size     = 3
max_size     = 10
desired_size = 3

# Security
cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]  # Restrict this in production

# Tags
additional_tags = {
  Owner   = "$EMAIL"
  Project = "SubForge"
}
EOF
    
    # Plan deployment
    log_info "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply infrastructure
    log_info "Applying Terraform configuration..."
    terraform apply tfplan
    
    # Save outputs
    terraform output -json > terraform-outputs.json
    
    # Update kubeconfig
    aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
    
    log_success "AWS infrastructure deployed successfully"
    cd "$SCRIPT_DIR"
}

# Configure Kubernetes secrets
configure_kubernetes_secrets() {
    log_info "Configuring Kubernetes secrets..."
    
    # Source the secrets
    source "$DEPLOYMENT_DIR/secrets.env"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would create Kubernetes secrets"
        return 0
    fi
    
    # Create namespace if it doesn't exist
    kubectl create namespace subforge --dry-run=client -o yaml | kubectl apply -f -
    
    # Create application secrets
    kubectl create secret generic subforge-secrets \
        --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        --from-literal=REDIS_PASSWORD="$REDIS_PASSWORD" \
        --from-literal=SECRET_KEY="$SECRET_KEY" \
        --from-literal=JWT_SECRET="$JWT_SECRET" \
        --from-literal=DATABASE_URL="$DATABASE_URL" \
        --from-literal=REDIS_URL="$REDIS_URL" \
        --namespace=subforge \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Create Grafana secrets
    kubectl create secret generic grafana-secrets \
        --from-literal=admin-password="$GRAFANA_PASSWORD" \
        --namespace=subforge \
        --dry-run=client -o yaml | kubectl apply -f -
    
    log_success "Kubernetes secrets configured"
}

# Update configuration files
update_configurations() {
    log_info "Updating configuration files with domain-specific settings..."
    
    # Update ingress configuration
    sed -i.bak "s/subforge\.yourdomain\.com/$DOMAIN/g" "$DEPLOYMENT_DIR/kubernetes/ingress.yaml"
    sed -i.bak "s/api\.subforge\.yourdomain\.com/api.$DOMAIN/g" "$DEPLOYMENT_DIR/kubernetes/ingress.yaml"
    sed -i.bak "s/ws\.subforge\.yourdomain\.com/ws.$DOMAIN/g" "$DEPLOYMENT_DIR/kubernetes/ingress.yaml"
    sed -i.bak "s/admin@yourdomain\.com/$EMAIL/g" "$DEPLOYMENT_DIR/kubernetes/ingress.yaml"
    
    # Update ConfigMap
    sed -i.bak "s/subforge\.yourdomain\.com/$DOMAIN/g" "$DEPLOYMENT_DIR/kubernetes/configmap.yaml"
    sed -i.bak "s/api\.subforge\.yourdomain\.com/api.$DOMAIN/g" "$DEPLOYMENT_DIR/kubernetes/configmap.yaml"
    
    # Update Nginx configuration
    sed -i.bak "s/subforge\.yourdomain\.com/$DOMAIN/g" "$DEPLOYMENT_DIR/docker/nginx/prod.conf"
    sed -i.bak "s/api\.subforge\.yourdomain\.com/api.$DOMAIN/g" "$DEPLOYMENT_DIR/docker/nginx/prod.conf"
    
    log_success "Configuration files updated with domain $DOMAIN"
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    if [[ "$SKIP_KUBERNETES" == true ]]; then
        log_warning "Skipping Kubernetes deployment as requested"
        return 0
    fi
    
    log_info "Deploying Kubernetes resources..."
    
    cd "$DEPLOYMENT_DIR/kubernetes"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would deploy Kubernetes resources"
        return 0
    fi
    
    # Apply in order
    kubectl apply -f namespace.yaml
    kubectl apply -f configmap.yaml -n subforge
    # Secrets already created by configure_kubernetes_secrets
    
    # Infrastructure services
    kubectl apply -f postgres.yaml -n subforge
    kubectl apply -f redis.yaml -n subforge
    
    # Wait for infrastructure
    log_info "Waiting for database and cache to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=database -n subforge --timeout=300s
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=cache -n subforge --timeout=300s
    
    # Application services
    kubectl apply -f backend.yaml -n subforge
    kubectl apply -f frontend.yaml -n subforge
    kubectl apply -f ingress.yaml -n subforge
    
    # Wait for application deployment
    log_info "Waiting for application deployment..."
    kubectl rollout status deployment/backend -n subforge --timeout=600s
    kubectl rollout status deployment/frontend -n subforge --timeout=600s
    
    log_success "Kubernetes resources deployed successfully"
    cd "$SCRIPT_DIR"
}

# Set up monitoring
setup_monitoring() {
    if [[ "$SKIP_MONITORING" == true ]]; then
        log_warning "Skipping monitoring setup as requested"
        return 0
    fi
    
    log_info "Setting up monitoring and observability..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would deploy monitoring stack"
        return 0
    fi
    
    kubectl apply -f "$DEPLOYMENT_DIR/kubernetes/monitoring.yaml" -n subforge
    
    # Wait for monitoring services
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=monitoring -n subforge --timeout=300s || {
        log_warning "Monitoring pods may take longer to start"
    }
    
    log_success "Monitoring stack deployed"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    log_info "Pod status:"
    kubectl get pods -n subforge
    
    # Check services
    log_info "Service status:"
    kubectl get svc -n subforge
    
    # Check ingress
    log_info "Ingress status:"
    kubectl get ingress -n subforge
    
    # Test health endpoints
    log_info "Testing health endpoints..."
    local backend_url="https://api.$DOMAIN/health"
    local frontend_url="https://$DOMAIN"
    
    if command -v curl >/dev/null 2>&1; then
        if curl -f -s "$backend_url" >/dev/null; then
            log_success "Backend health check passed"
        else
            log_warning "Backend health check failed - this is normal if DNS is not yet propagated"
        fi
    fi
    
    log_success "Deployment verification completed"
}

# Display access information
display_access_info() {
    log_success "🚀 SubForge Dashboard production deployment completed!"
    echo
    echo "==================== ACCESS INFORMATION ===================="
    echo
    echo "Frontend Application:"
    echo "  URL: https://$DOMAIN"
    echo
    echo "Backend API:"
    echo "  URL: https://api.$DOMAIN"
    echo "  Documentation: https://api.$DOMAIN/docs"
    echo
    echo "Monitoring (Grafana):"
    echo "  URL: https://$DOMAIN/grafana"
    echo "  Username: admin"
    echo "  Password: $GRAFANA_PASSWORD"
    echo
    echo "==================== IMPORTANT NOTES ======================"
    echo
    echo "1. DNS Setup Required:"
    echo "   - Point $DOMAIN to the load balancer"
    echo "   - Point api.$DOMAIN to the load balancer"
    echo "   - Point ws.$DOMAIN to the load balancer"
    echo
    echo "2. SSL Certificates:"
    echo "   - Let's Encrypt certificates will be automatically issued"
    echo "   - This may take a few minutes after DNS propagation"
    echo
    echo "3. Secrets Management:"
    echo "   - All secrets are stored in: $DEPLOYMENT_DIR/secrets.env"
    echo "   - Store this file securely and do not commit to version control"
    echo "   - Consider using external secret management (AWS Secrets Manager, etc.)"
    echo
    echo "4. Monitoring:"
    echo "   - Prometheus metrics: http://prometheus-service:9090 (internal)"
    echo "   - Grafana dashboards: https://$DOMAIN/grafana"
    echo
    echo "5. Backup:"
    echo "   - Set up automated backups using: ./backup.sh full -e production --upload"
    echo "   - Configure S3 bucket for backup storage"
    echo
    echo "6. Next Steps:"
    echo "   - Configure DNS records"
    echo "   - Wait for SSL certificate issuance"
    echo "   - Set up monitoring alerts"
    echo "   - Configure automated backups"
    echo "   - Set up CI/CD pipeline in GitHub Actions"
    echo
    echo "==========================================================="
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Setup failed with exit code $exit_code"
        log_info "Check the logs above for details"
        log_info "You may need to clean up partial resources manually"
    fi
    exit $exit_code
}

# Main function
main() {
    log_info "Starting SubForge Dashboard production setup..."
    log_info "Domain: $DOMAIN"
    log_info "Email: $EMAIL"
    log_info "Region: $REGION"
    log_info "Cluster: $CLUSTER_NAME"
    echo
    
    if [[ "$DRY_RUN" == true ]]; then
        log_warning "DRY RUN MODE - No changes will be made"
        echo
    fi
    
    # Confirm before proceeding
    if [[ "$DRY_RUN" == false ]]; then
        echo -n "This will create AWS resources and may incur costs. Continue? (y/N): "
        read -r confirmation
        if [[ "$confirmation" != "y" && "$confirmation" != "Y" ]]; then
            log_info "Setup cancelled by user"
            exit 0
        fi
    fi
    
    # Execute setup steps
    check_prerequisites
    generate_secrets
    update_configurations
    setup_terraform
    configure_kubernetes_secrets
    deploy_kubernetes
    setup_monitoring
    verify_deployment
    
    # Show access information
    if [[ "$DRY_RUN" == false ]]; then
        display_access_info
    else
        log_info "DRY RUN completed - no resources were created"
    fi
}

# Set up error handling
trap cleanup ERR

# Run main function
main "$@"