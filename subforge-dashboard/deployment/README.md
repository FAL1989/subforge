# SubForge Dashboard Deployment Guide

This directory contains comprehensive deployment and CI/CD infrastructure for the SubForge Dashboard, supporting multiple environments and deployment strategies.

## 📁 Directory Structure

```
deployment/
├── docker/                 # Docker configuration files
│   ├── backend.Dockerfile  # Multi-stage backend image
│   ├── frontend.Dockerfile # Multi-stage frontend image
│   ├── docker-compose.dev.yml    # Development environment
│   ├── docker-compose.prod.yml   # Production environment
│   ├── .env.example        # Environment variables template
│   ├── nginx/              # Nginx configurations
│   └── scripts/            # Database initialization scripts
├── kubernetes/             # Kubernetes manifests
│   ├── namespace.yaml      # Namespace definitions
│   ├── configmap.yaml      # Configuration maps
│   ├── secrets.yaml        # Secrets (template)
│   ├── postgres.yaml       # PostgreSQL deployment
│   ├── redis.yaml          # Redis deployment
│   ├── backend.yaml        # Backend deployment with HPA
│   ├── frontend.yaml       # Frontend deployment with HPA
│   └── ingress.yaml        # Ingress with SSL/TLS
├── terraform/              # Infrastructure as Code
│   ├── main.tf            # Main Terraform configuration
│   ├── variables.tf       # Input variables
│   └── outputs.tf         # Output values
├── github-actions/         # CI/CD pipeline
│   └── ci-cd.yml          # GitHub Actions workflow
├── scripts/               # Deployment and utility scripts
│   ├── deploy.sh          # Main deployment script
│   └── backup.sh          # Backup and restore script
└── README.md              # This file
```

## 🚀 Quick Start

### Local Development with Docker Compose

1. **Copy environment file:**
   ```bash
   cp deployment/docker/.env.example deployment/docker/.env
   # Edit .env with your local settings
   ```

2. **Start services:**
   ```bash
   ./deployment/scripts/deploy.sh local
   ```

3. **Access applications:**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Production Deployment

1. **Set up infrastructure with Terraform:**
   ```bash
   cd deployment/terraform
   terraform init
   terraform plan -var="environment=production"
   terraform apply
   ```

2. **Deploy to Kubernetes:**
   ```bash
   ./deployment/scripts/deploy.sh production --build-images
   ```

## 🐳 Docker Configuration

### Multi-Stage Dockerfiles

Both backend and frontend use optimized multi-stage builds:

- **Development Stage**: Hot reloading, debugging tools
- **Builder Stage**: Optimized build process
- **Production Stage**: Minimal runtime, security hardened

### Docker Compose Environments

- **Development** (`docker-compose.dev.yml`):
  - Hot reloading enabled
  - Debug logging
  - Volume mounts for code changes
  - Local PostgreSQL and Redis

- **Production** (`docker-compose.prod.yml`):
  - Resource limits and reservations
  - Health checks and restart policies
  - Security optimizations
  - Log aggregation ready

## ☸️ Kubernetes Deployment

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│     Ingress     │    │   Certificate   │
│   (Nginx +      │    │    Manager      │
│    SSL/TLS)     │    │  (Let's Encrypt)│
└─────────────────┘    └─────────────────┘
         │
┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │
│   (Next.js)     │────│   (FastAPI)     │
│   Replicas: 2   │    │   Replicas: 3   │
└─────────────────┘    └─────────────────┘
         │                       │
┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │      Redis      │
│  (Persistent)   │    │    (Cache)      │
└─────────────────┘    └─────────────────┘
```

### Key Features

- **Auto-scaling**: HPA for both frontend and backend
- **High Availability**: Multiple replicas, pod disruption budgets
- **Security**: Network policies, RBAC, secrets management
- **Monitoring**: Health checks, readiness/liveness probes
- **SSL/TLS**: Automated certificate management
- **Storage**: Persistent volumes for database

### Deployment Components

1. **Namespace**: Isolated environments (production, staging)
2. **ConfigMaps**: Non-sensitive configuration
3. **Secrets**: Sensitive data (passwords, keys)
4. **Deployments**: Application workloads with scaling
5. **Services**: Internal networking and load balancing
6. **Ingress**: External access with SSL termination
7. **PVCs**: Persistent storage for database

## 🏗️ Infrastructure as Code (Terraform)

### Supported Cloud Providers

- **AWS**: EKS, RDS, ElastiCache, VPC, ALB
- **Multi-AZ**: High availability across availability zones
- **Auto-scaling**: Cluster autoscaler and node groups
- **Security**: IAM roles, security groups, encryption

### Infrastructure Components

1. **VPC and Networking**: Private/public subnets, NAT gateways
2. **EKS Cluster**: Managed Kubernetes with add-ons
3. **Node Groups**: On-demand and spot instances
4. **RDS PostgreSQL**: Managed database with backups
5. **ElastiCache Redis**: Managed Redis cluster
6. **Load Balancers**: Application and network load balancers
7. **SSL Certificates**: ACM certificate management

### Deployment

```bash
cd deployment/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="environment=production" \
              -var="domain_name=subforge.yourdomain.com"

# Apply infrastructure
terraform apply

# Get outputs
terraform output -json > terraform-outputs.json
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Automated pipeline with the following stages:

1. **Security Scanning**: Trivy, Snyk vulnerability scans
2. **Testing**: Backend (pytest) and frontend (Jest/Playwright) tests
3. **Building**: Multi-platform Docker images
4. **Deployment**: Environment-specific deployments
5. **Health Checks**: Post-deployment verification

### Pipeline Features

- **Branch-based Deployments**:
  - `develop` → Staging environment
  - `main` → Production environment (with approval)
  - Pull requests → Review apps

- **Security Integration**:
  - Container vulnerability scanning
  - Dependency security checks
  - SAST/DAST security testing

- **Quality Gates**:
  - Test coverage requirements
  - Code quality checks
  - Performance benchmarks

### Environment Variables

Set in GitHub repository secrets:

```bash
# Kubernetes access
KUBE_CONFIG_STAGING=<base64-encoded-kubeconfig>
KUBE_CONFIG_PRODUCTION=<base64-encoded-kubeconfig>

# Container registry
GITHUB_TOKEN=<github-token>

# Security scanning
SNYK_TOKEN=<snyk-token>

# Notifications
SLACK_WEBHOOK_URL=<slack-webhook-url>
```

## 🛠️ Deployment Scripts

### Main Deployment Script

```bash
./deployment/scripts/deploy.sh [OPTIONS] ENVIRONMENT

# Examples
./deploy.sh local                    # Local development
./deploy.sh staging --build-images  # Build and deploy to staging
./deploy.sh production --dry-run     # Preview production deployment
./deploy.sh --rollback v1.2.0 prod  # Rollback to specific version
```

### Backup Script

```bash
./deployment/scripts/backup.sh [OPTIONS] COMMAND

# Examples
./backup.sh database -e production --encrypt --upload
./backup.sh restore -e staging -f backup-2023-12-01.sql.gz
./backup.sh full -e production --compress --verify
./backup.sh cleanup --dry-run
```

## 🔒 Security Features

### Container Security

- **Non-root users**: All containers run as non-root
- **Read-only filesystems**: Minimal write access
- **Security contexts**: Dropped capabilities, no privilege escalation
- **Image scanning**: Automated vulnerability detection

### Network Security

- **Network policies**: Micro-segmentation between pods
- **TLS encryption**: End-to-end encrypted communication
- **Ingress security**: Rate limiting, DDoS protection
- **Private networking**: Database in private subnets

### Secrets Management

- **Kubernetes secrets**: Base64 encoded sensitive data
- **External secrets**: Integration with cloud secret managers
- **Rotation**: Automated credential rotation
- **Encryption**: Secrets encrypted at rest

## 📊 Monitoring and Observability

### Health Checks

- **Liveness probes**: Container health verification
- **Readiness probes**: Traffic routing decisions
- **Startup probes**: Slow-starting container support

### Logging

- **Structured logging**: JSON format for all services
- **Log aggregation**: Centralized log collection
- **Log retention**: Configurable retention policies

### Metrics

- **Application metrics**: Custom business metrics
- **Infrastructure metrics**: CPU, memory, disk usage
- **Performance metrics**: Response times, throughput

## 🔧 Configuration Management

### Environment Variables

Critical configuration options:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
POSTGRES_PASSWORD=<strong-password>

# Redis
REDIS_URL=redis://:password@host:6379/0
REDIS_PASSWORD=<strong-password>

# Application
SECRET_KEY=<32-character-secret>
ENVIRONMENT=production
LOG_LEVEL=info

# External Services
SENTRY_DSN=<sentry-dsn>
```

### Feature Flags

Environment-specific feature toggles:

- Development: Debug mode, test data
- Staging: Feature previews, monitoring
- Production: Performance optimization, security

## 🚨 Disaster Recovery

### Backup Strategy

- **Database backups**: Daily automated backups
- **File backups**: Application data and configurations
- **Cross-region replication**: Disaster recovery
- **Point-in-time recovery**: Granular restore options

### Recovery Procedures

1. **Database Recovery**:
   ```bash
   ./backup.sh restore -e production -f latest-db-backup.sql.gz
   ```

2. **Full System Recovery**:
   ```bash
   # Restore infrastructure
   terraform apply
   
   # Restore application
   ./deploy.sh production --force
   
   # Restore data
   ./backup.sh restore -e production -t full
   ```

## 📈 Performance Optimization

### Scaling Configuration

- **Horizontal Pod Autoscaler**: CPU/memory-based scaling
- **Vertical Pod Autoscaler**: Resource optimization
- **Cluster Autoscaler**: Node-level scaling

### Caching Strategy

- **Redis**: Session and application caching
- **CDN**: Static asset delivery
- **Database**: Query result caching

### Resource Optimization

- **Resource requests/limits**: Efficient resource allocation
- **Spot instances**: Cost optimization
- **Storage classes**: Performance-based storage tiers

## 🔍 Troubleshooting

### Common Issues

1. **Pod startup failures**: Check logs and resource limits
2. **Database connection errors**: Verify network policies
3. **SSL certificate issues**: Check cert-manager logs
4. **Performance issues**: Monitor resource usage

### Debug Commands

```bash
# Check pod status
kubectl get pods -n subforge

# View pod logs
kubectl logs -f deployment/backend -n subforge

# Execute into container
kubectl exec -it deployment/backend -n subforge -- bash

# Check resource usage
kubectl top pods -n subforge
```

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## 🤝 Contributing

1. Test changes in local environment first
2. Follow infrastructure as code principles
3. Update documentation for any configuration changes
4. Use feature branches for infrastructure changes
5. Ensure security best practices are followed

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify infrastructure status
3. Review recent changes
4. Consult troubleshooting guide
5. Contact DevOps team if needed

---

**Generated by SubForge v1.0 - AI-Powered Development Team Orchestration**