#!/bin/bash

# SubForge Dashboard Backup Script
# Handles database backups, file backups, and disaster recovery

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-/opt/subforge/backups}"
S3_BUCKET="${S3_BUCKET:-subforge-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Print usage
usage() {
    cat << EOF
SubForge Dashboard Backup Script

Usage: $0 [OPTIONS] COMMAND

Commands:
  database            Backup PostgreSQL database
  files               Backup application files
  full                Full system backup (database + files)
  restore             Restore from backup
  list                List available backups
  cleanup             Remove old backups
  verify              Verify backup integrity

Options:
  -h, --help          Show this help message
  -e, --environment   Environment (local, staging, production)
  -f, --file          Backup file for restore operations
  -d, --date          Backup date (YYYY-MM-DD) for restore
  -t, --type          Backup type (database, files, full)
  --encrypt           Encrypt backup files
  --compress          Compress backup files
  --upload            Upload to S3 after backup
  --verify            Verify backup after creation
  --dry-run           Show what would be done without executing

Examples:
  $0 database -e production --encrypt --upload
  $0 restore -e staging -f backup-2023-12-01.sql.gz
  $0 cleanup --dry-run
  $0 full -e production --encrypt --compress --upload --verify

EOF
}

# Parse arguments
COMMAND=""
ENVIRONMENT=""
BACKUP_FILE=""
BACKUP_DATE=""
BACKUP_TYPE=""
ENCRYPT=false
COMPRESS=false
UPLOAD=false
VERIFY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -f|--file)
            BACKUP_FILE="$2"
            shift 2
            ;;
        -d|--date)
            BACKUP_DATE="$2"
            shift 2
            ;;
        -t|--type)
            BACKUP_TYPE="$2"
            shift 2
            ;;
        --encrypt)
            ENCRYPT=true
            shift
            ;;
        --compress)
            COMPRESS=true
            shift
            ;;
        --upload)
            UPLOAD=true
            shift
            ;;
        --verify)
            VERIFY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        database|files|full|restore|list|cleanup|verify)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate command
if [[ -z "$COMMAND" ]]; then
    log_error "Command is required"
    usage
    exit 1
fi

# Set default environment if not specified
if [[ -z "$ENVIRONMENT" ]]; then
    ENVIRONMENT="production"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get timestamp
TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

# Environment-specific configurations
case "$ENVIRONMENT" in
    local)
        DB_HOST="localhost"
        DB_PORT="5432"
        DB_NAME="subforge_dev"
        DB_USER="subforge"
        DB_PASSWORD="${POSTGRES_PASSWORD:-subforge_dev_pass}"
        KUBECONFIG_PATH=""
        ;;
    staging)
        DB_HOST="${DB_HOST:-postgres-service}"
        DB_PORT="5432"
        DB_NAME="subforge"
        DB_USER="subforge"
        DB_PASSWORD="${POSTGRES_PASSWORD}"
        KUBECONFIG_PATH="${HOME}/.kube/staging-config"
        ;;
    production)
        DB_HOST="${DB_HOST:-postgres-service}"
        DB_PORT="5432"
        DB_NAME="subforge"
        DB_USER="subforge"
        DB_PASSWORD="${POSTGRES_PASSWORD}"
        KUBECONFIG_PATH="${HOME}/.kube/production-config"
        ;;
    *)
        log_error "Invalid environment: $ENVIRONMENT"
        exit 1
        ;;
esac

# Check required tools
check_dependencies() {
    local missing_tools=()
    
    command -v pg_dump >/dev/null 2>&1 || missing_tools+=("postgresql-client")
    
    if [[ "$COMPRESS" == true ]]; then
        command -v gzip >/dev/null 2>&1 || missing_tools+=("gzip")
    fi
    
    if [[ "$ENCRYPT" == true ]]; then
        command -v gpg >/dev/null 2>&1 || missing_tools+=("gpg")
    fi
    
    if [[ "$UPLOAD" == true ]]; then
        command -v aws >/dev/null 2>&1 || missing_tools+=("aws-cli")
    fi
    
    if [[ "${ENVIRONMENT}" != "local" ]]; then
        command -v kubectl >/dev/null 2>&1 || missing_tools+=("kubectl")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
}

# Database backup
backup_database() {
    log_info "Starting database backup for $ENVIRONMENT environment..."
    
    local backup_file="$BACKUP_DIR/db-backup-${ENVIRONMENT}-${TIMESTAMP}.sql"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would backup database to $backup_file"
        return 0
    fi
    
    # Create backup based on environment
    case "$ENVIRONMENT" in
        local)
            PGPASSWORD="$DB_PASSWORD" pg_dump \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                --verbose \
                --no-password \
                --format=custom \
                --compress=9 \
                --file="$backup_file.dump"
            ;;
        staging|production)
            # Use kubectl to create backup
            kubectl --kubeconfig="$KUBECONFIG_PATH" -n "${ENVIRONMENT/staging/subforge-staging}" -n "${ENVIRONMENT/production/subforge}" \
                exec -i deployment/postgres -- pg_dump \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                --verbose \
                --format=custom \
                --compress=9 > "$backup_file.dump"
            ;;
    esac
    
    # Apply additional processing
    local final_file="$backup_file"
    
    if [[ "$COMPRESS" == true ]]; then
        log_info "Compressing backup..."
        gzip "$backup_file.dump"
        final_file="$backup_file.dump.gz"
    else
        mv "$backup_file.dump" "$backup_file"
    fi
    
    if [[ "$ENCRYPT" == true ]]; then
        log_info "Encrypting backup..."
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            log_error "Encryption key not provided"
            exit 1
        fi
        gpg --symmetric --cipher-algo AES256 --compress-algo 1 --passphrase "$ENCRYPTION_KEY" "$final_file"
        rm "$final_file"
        final_file="$final_file.gpg"
    fi
    
    log_success "Database backup created: $final_file"
    
    # Upload to S3 if requested
    if [[ "$UPLOAD" == true ]]; then
        upload_to_s3 "$final_file"
    fi
    
    # Verify backup if requested
    if [[ "$VERIFY" == true ]]; then
        verify_backup "$final_file"
    fi
}

# Files backup
backup_files() {
    log_info "Starting files backup for $ENVIRONMENT environment..."
    
    local backup_file="$BACKUP_DIR/files-backup-${ENVIRONMENT}-${TIMESTAMP}.tar"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would backup files to $backup_file"
        return 0
    fi
    
    # Define files/directories to backup
    local backup_paths=(
        "/opt/subforge/data"
        "/opt/subforge/logs"
        "/opt/subforge/config"
    )
    
    # Create archive
    tar -cvf "$backup_file" "${backup_paths[@]}" 2>/dev/null || {
        log_warning "Some files could not be backed up, continuing..."
    }
    
    # Apply compression and encryption
    local final_file="$backup_file"
    
    if [[ "$COMPRESS" == true ]]; then
        log_info "Compressing files backup..."
        gzip "$backup_file"
        final_file="$backup_file.gz"
    fi
    
    if [[ "$ENCRYPT" == true ]]; then
        log_info "Encrypting files backup..."
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            log_error "Encryption key not provided"
            exit 1
        fi
        gpg --symmetric --cipher-algo AES256 --compress-algo 1 --passphrase "$ENCRYPTION_KEY" "$final_file"
        rm "$final_file"
        final_file="$final_file.gpg"
    fi
    
    log_success "Files backup created: $final_file"
    
    # Upload to S3 if requested
    if [[ "$UPLOAD" == true ]]; then
        upload_to_s3 "$final_file"
    fi
}

# Full backup
backup_full() {
    log_info "Starting full backup for $ENVIRONMENT environment..."
    backup_database
    backup_files
    log_success "Full backup completed"
}

# Upload to S3
upload_to_s3() {
    local file="$1"
    local s3_key="subforge/${ENVIRONMENT}/$(basename "$file")"
    
    log_info "Uploading $file to S3..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would upload to s3://$S3_BUCKET/$s3_key"
        return 0
    fi
    
    aws s3 cp "$file" "s3://$S3_BUCKET/$s3_key" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256
    
    log_success "Uploaded to S3: s3://$S3_BUCKET/$s3_key"
}

# Verify backup
verify_backup() {
    local file="$1"
    
    log_info "Verifying backup: $file"
    
    if [[ ! -f "$file" ]]; then
        log_error "Backup file not found: $file"
        return 1
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo "0")
    if [[ "$file_size" -eq 0 ]]; then
        log_error "Backup file is empty"
        return 1
    fi
    
    # Verify based on file type
    case "$file" in
        *.gpg)
            log_info "Verifying encrypted backup..."
            if [[ -z "$ENCRYPTION_KEY" ]]; then
                log_error "Encryption key required for verification"
                return 1
            fi
            echo "$ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 --decrypt "$file" > /dev/null 2>&1
            ;;
        *.gz)
            log_info "Verifying compressed backup..."
            gzip -t "$file"
            ;;
        *.dump)
            log_info "Verifying database backup..."
            pg_restore --list "$file" > /dev/null 2>&1
            ;;
        *.tar)
            log_info "Verifying tar backup..."
            tar -tf "$file" > /dev/null 2>&1
            ;;
    esac
    
    log_success "Backup verification passed: $file"
}

# List backups
list_backups() {
    log_info "Available backups:"
    
    if [[ "$UPLOAD" == true ]]; then
        log_info "S3 backups:"
        aws s3 ls "s3://$S3_BUCKET/subforge/$ENVIRONMENT/" --recursive
    fi
    
    log_info "Local backups:"
    ls -la "$BACKUP_DIR"/*"$ENVIRONMENT"* 2>/dev/null || log_info "No local backups found"
}

# Cleanup old backups
cleanup_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would remove the following files:"
        find "$BACKUP_DIR" -name "*$ENVIRONMENT*" -mtime +$RETENTION_DAYS -type f
        return 0
    fi
    
    # Local cleanup
    find "$BACKUP_DIR" -name "*$ENVIRONMENT*" -mtime +$RETENTION_DAYS -type f -delete
    
    # S3 cleanup if upload is enabled
    if [[ "$UPLOAD" == true ]]; then
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" '+%Y-%m-%d')
        aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "subforge/$ENVIRONMENT/" \
            --query "Contents[?LastModified<='$cutoff_date'].Key" \
            --output text | \
        while read -r key; do
            if [[ -n "$key" ]]; then
                aws s3 rm "s3://$S3_BUCKET/$key"
                log_info "Removed: s3://$S3_BUCKET/$key"
            fi
        done
    fi
    
    log_success "Cleanup completed"
}

# Restore from backup
restore_backup() {
    if [[ -z "$BACKUP_FILE" ]]; then
        log_error "Backup file is required for restore"
        exit 1
    fi
    
    log_info "Restoring from backup: $BACKUP_FILE"
    
    if [[ "$DRY_RUN" == true ]]; then
        log_info "DRY RUN: Would restore from $BACKUP_FILE"
        return 0
    fi
    
    # Download from S3 if needed
    if [[ "$BACKUP_FILE" =~ ^s3:// ]]; then
        local local_file="$BACKUP_DIR/$(basename "$BACKUP_FILE")"
        aws s3 cp "$BACKUP_FILE" "$local_file"
        BACKUP_FILE="$local_file"
    fi
    
    # Decrypt if needed
    if [[ "$BACKUP_FILE" =~ \.gpg$ ]]; then
        log_info "Decrypting backup..."
        if [[ -z "$ENCRYPTION_KEY" ]]; then
            log_error "Encryption key required for decryption"
            exit 1
        fi
        local decrypted_file="${BACKUP_FILE%.gpg}"
        echo "$ENCRYPTION_KEY" | gpg --batch --yes --passphrase-fd 0 --decrypt "$BACKUP_FILE" > "$decrypted_file"
        BACKUP_FILE="$decrypted_file"
    fi
    
    # Decompress if needed
    if [[ "$BACKUP_FILE" =~ \.gz$ ]]; then
        log_info "Decompressing backup..."
        gunzip "$BACKUP_FILE"
        BACKUP_FILE="${BACKUP_FILE%.gz}"
    fi
    
    # Restore based on backup type
    case "$BACKUP_FILE" in
        *db-backup*)
            log_info "Restoring database..."
            case "$ENVIRONMENT" in
                local)
                    PGPASSWORD="$DB_PASSWORD" pg_restore \
                        -h "$DB_HOST" \
                        -p "$DB_PORT" \
                        -U "$DB_USER" \
                        -d "$DB_NAME" \
                        --clean --if-exists \
                        "$BACKUP_FILE"
                    ;;
                staging|production)
                    kubectl --kubeconfig="$KUBECONFIG_PATH" -n "${ENVIRONMENT/staging/subforge-staging}" -n "${ENVIRONMENT/production/subforge}" \
                        exec -i deployment/postgres -- pg_restore \
                        -U "$DB_USER" \
                        -d "$DB_NAME" \
                        --clean --if-exists < "$BACKUP_FILE"
                    ;;
            esac
            ;;
        *files-backup*)
            log_info "Restoring files..."
            tar -xf "$BACKUP_FILE" -C /
            ;;
    esac
    
    log_success "Restore completed"
}

# Main execution
main() {
    log_info "SubForge Backup Script - Command: $COMMAND, Environment: $ENVIRONMENT"
    
    # Check dependencies
    check_dependencies
    
    case "$COMMAND" in
        database)
            backup_database
            ;;
        files)
            backup_files
            ;;
        full)
            backup_full
            ;;
        restore)
            restore_backup
            ;;
        list)
            list_backups
            ;;
        cleanup)
            cleanup_backups
            ;;
        verify)
            if [[ -n "$BACKUP_FILE" ]]; then
                verify_backup "$BACKUP_FILE"
            else
                log_error "Backup file required for verification"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Error handling
error_handler() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script failed with exit code $exit_code"
    fi
    exit $exit_code
}

trap error_handler ERR

# Run main function
main "$@"