# Terraform Outputs for SubForge Infrastructure

# Cluster Information
output "cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "cluster_arn" {
  description = "EKS cluster ARN"
  value       = module.eks.cluster_arn
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_primary_security_group_id" {
  description = "Cluster security group that was created by Amazon EKS for the cluster"
  value       = module.eks.cluster_primary_security_group_id
}

# OIDC Provider
output "oidc_provider_arn" {
  description = "The ARN of the OIDC Provider if enabled"
  value       = module.eks.oidc_provider_arn
}

# Node Groups
output "eks_managed_node_groups" {
  description = "Map of attribute maps for all EKS managed node groups created"
  value       = module.eks.eks_managed_node_groups
}

# VPC Information
output "vpc_id" {
  description = "ID of the VPC where the cluster and workers are deployed"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnets" {
  description = "List of IDs of private subnets"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "List of IDs of public subnets"
  value       = module.vpc.public_subnets
}

# Database Information
output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "database_port" {
  description = "RDS instance port"
  value       = aws_db_instance.postgres.port
}

output "database_name" {
  description = "RDS instance database name"
  value       = aws_db_instance.postgres.db_name
}

output "database_username" {
  description = "RDS instance root username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

# Redis Information
output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "Redis cluster port"
  value       = aws_elasticache_replication_group.redis.port
}

# Load Balancer Information
output "nginx_ingress_controller_load_balancer_hostname" {
  description = "The hostname of the load balancer created by the NGINX ingress controller"
  value       = try(data.kubernetes_service.nginx_ingress.status[0].load_balancer[0].ingress[0].hostname, null)
  depends_on  = [helm_release.nginx_ingress]
}

# Security Information
output "postgres_password" {
  description = "The generated password for PostgreSQL"
  value       = random_password.postgres_password.result
  sensitive   = true
}

output "redis_auth_token" {
  description = "The generated auth token for Redis"
  value       = random_password.redis_password.result
  sensitive   = true
}

# Configuration for applications
output "database_url" {
  description = "Complete database connection URL"
  value       = "postgresql://${aws_db_instance.postgres.username}:${random_password.postgres_password.result}@${aws_db_instance.postgres.endpoint}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

output "redis_url" {
  description = "Complete Redis connection URL"
  value       = "redis://:${random_password.redis_password.result}@${aws_elasticache_replication_group.redis.primary_endpoint_address}:${aws_elasticache_replication_group.redis.port}/0"
  sensitive   = true
}

# Kubernetes configuration
output "kubeconfig_filename" {
  description = "The filename of the generated kubectl config"
  value       = abspath("${path.module}/kubeconfig_${local.name}")
}

# Region and Account Information
output "region" {
  description = "AWS region"
  value       = var.region
}

output "account_id" {
  description = "AWS account ID"
  value       = data.aws_caller_identity.current.account_id
}

# DNS and Domain Information
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = try(aws_route53_zone.main[0].zone_id, null)
}

output "certificate_arn" {
  description = "ACM certificate ARN"
  value       = try(aws_acm_certificate.main[0].arn, var.certificate_arn)
}

# Monitoring and Logging
output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name for EKS cluster"
  value       = try(module.eks.cloudwatch_log_group_name, null)
}

# Backup Information
output "database_backup_window" {
  description = "The database backup window"
  value       = aws_db_instance.postgres.backup_window
}

output "database_maintenance_window" {
  description = "The database maintenance window"
  value       = aws_db_instance.postgres.maintenance_window
}

# Cost Optimization
output "spot_node_group_name" {
  description = "Name of the spot instance node group"
  value       = try(module.eks.eks_managed_node_groups["spot"].node_group_id, null)
}

# Network Information
output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.natgw_ids
}

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = module.vpc.igw_id
}

# Tags
output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.tags
}

# Data source for ingress controller service
data "kubernetes_service" "nginx_ingress" {
  metadata {
    name      = "nginx-ingress-ingress-nginx-controller"
    namespace = "ingress-nginx"
  }
  depends_on = [helm_release.nginx_ingress]
}