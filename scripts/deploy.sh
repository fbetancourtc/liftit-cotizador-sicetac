#!/bin/bash
# Production deployment script for SICETAC platform

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="sicetac"
DEPLOY_ENV="${1:-production}"
SSL_EMAIL="${SSL_EMAIL:-admin@liftit.com}"
DOMAIN="${DOMAIN:-sicetac.liftit.com}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check environment file
    if [ ! -f ".env.${DEPLOY_ENV}" ]; then
        log_error ".env.${DEPLOY_ENV} file not found"
        exit 1
    fi

    log_info "All requirements met"
}

setup_ssl() {
    log_info "Setting up SSL certificates..."

    # Check if certificates already exist
    if [ -f "nginx/ssl/fullchain.pem" ] && [ -f "nginx/ssl/privkey.pem" ]; then
        log_warn "SSL certificates already exist"
        return
    fi

    # Create SSL directory
    mkdir -p nginx/ssl

    # Generate certificates using certbot (standalone method)
    docker run -it --rm \
        -v $(pwd)/nginx/ssl:/etc/letsencrypt \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --non-interactive \
        --agree-tos \
        --email ${SSL_EMAIL} \
        -d ${DOMAIN} \
        -d www.${DOMAIN}

    # Copy certificates to nginx/ssl directory
    if [ -d "nginx/ssl/live/${DOMAIN}" ]; then
        cp nginx/ssl/live/${DOMAIN}/fullchain.pem nginx/ssl/
        cp nginx/ssl/live/${DOMAIN}/privkey.pem nginx/ssl/
        log_info "SSL certificates installed successfully"
    else
        log_error "Failed to generate SSL certificates"
        exit 1
    fi
}

backup_existing() {
    log_info "Creating backup of existing deployment..."

    # Create backup directory
    BACKUP_DIR="backups/deploy_$(date +%Y%m%d_%H%M%S)"
    mkdir -p ${BACKUP_DIR}

    # Backup database if running
    if docker ps | grep -q "${PROJECT_NAME}-db"; then
        log_info "Backing up database..."
        docker exec ${PROJECT_NAME}-db pg_dump -U sicetac_user sicetac_db | gzip > ${BACKUP_DIR}/database.sql.gz
    fi

    # Backup environment files
    cp .env.${DEPLOY_ENV} ${BACKUP_DIR}/ 2>/dev/null || true

    log_info "Backup created in ${BACKUP_DIR}"
}

deploy() {
    log_info "Starting deployment for ${DEPLOY_ENV} environment..."

    # Load environment variables
    export $(cat .env.${DEPLOY_ENV} | grep -v '^#' | xargs)

    # Build images
    log_info "Building Docker images..."
    docker-compose -f docker-compose.prod.yml build --no-cache

    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose -f docker-compose.prod.yml down

    # Start new containers
    log_info "Starting new containers..."
    docker-compose -f docker-compose.prod.yml up -d

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Check health status
    for service in postgres redis app nginx; do
        if docker ps | grep -q "${PROJECT_NAME}-${service}"; then
            log_info "✓ ${service} is running"
        else
            log_error "✗ ${service} is not running"
        fi
    done

    # Run database migrations
    log_info "Running database migrations..."
    docker exec ${PROJECT_NAME}-app python -c "from app.models.database_prod import init_database; init_database()"

    log_info "Deployment completed successfully!"
}

post_deploy_checks() {
    log_info "Running post-deployment checks..."

    # Check API health
    if curl -f http://localhost/api/healthz > /dev/null 2>&1; then
        log_info "✓ API health check passed"
    else
        log_error "✗ API health check failed"
    fi

    # Check database connection
    if docker exec ${PROJECT_NAME}-db pg_isready -U sicetac_user > /dev/null 2>&1; then
        log_info "✓ Database connection successful"
    else
        log_error "✗ Database connection failed"
    fi

    # Show container status
    log_info "Container status:"
    docker-compose -f docker-compose.prod.yml ps

    # Show recent logs
    log_info "Recent application logs:"
    docker-compose -f docker-compose.prod.yml logs --tail=20 app
}

cleanup() {
    log_info "Cleaning up old resources..."

    # Remove unused Docker images
    docker image prune -f

    # Remove old backup files (keep last 30 days)
    find backups -type f -mtime +30 -delete 2>/dev/null || true

    log_info "Cleanup completed"
}

rollback() {
    log_warn "Rolling back deployment..."

    # Stop current containers
    docker-compose -f docker-compose.prod.yml down

    # Restore from latest backup
    LATEST_BACKUP=$(ls -t backups/deploy_* | head -1)
    if [ -z "$LATEST_BACKUP" ]; then
        log_error "No backup found for rollback"
        exit 1
    fi

    log_info "Restoring from ${LATEST_BACKUP}..."

    # Restore database
    if [ -f "${LATEST_BACKUP}/database.sql.gz" ]; then
        gunzip < ${LATEST_BACKUP}/database.sql.gz | docker exec -i ${PROJECT_NAME}-db psql -U sicetac_user sicetac_db
    fi

    # Restart with previous configuration
    docker-compose -f docker-compose.prod.yml up -d

    log_info "Rollback completed"
}

# Main execution
main() {
    echo "======================================"
    echo "SICETAC Platform Deployment Script"
    echo "Environment: ${DEPLOY_ENV}"
    echo "======================================"

    case "${2:-deploy}" in
        deploy)
            check_requirements
            backup_existing
            if [ "${DEPLOY_ENV}" == "production" ]; then
                setup_ssl
            fi
            deploy
            post_deploy_checks
            cleanup
            ;;
        rollback)
            rollback
            ;;
        ssl)
            setup_ssl
            ;;
        backup)
            backup_existing
            ;;
        *)
            echo "Usage: $0 [production|staging] [deploy|rollback|ssl|backup]"
            exit 1
            ;;
    esac

    log_info "Operation completed successfully!"
}

# Run main function
main "$@"