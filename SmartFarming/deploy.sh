#!/bin/bash
# Smart Farmer Marketplace - Docker Deployment Script
# Supports development, staging, and production deployments

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smartfarmer"
ENV_FILE=".env"
LOG_FILE="deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    success "✓ Docker found"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    success "✓ Docker Compose found"
    
    # Check .env file
    if [ ! -f "$ENV_FILE" ]; then
        warning ".env file not found"
        log "Creating .env from .env.example..."
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
            warning "Please update .env with your configuration values"
            warning "Current values are examples only - DO NOT use in production"
            exit 1
        else
            error ".env.example not found"
        fi
    fi
    success "✓ Configuration found"
}

# Setup Docker environment
setup_environment() {
    local environment=$1
    
    log "Setting up $environment environment..."
    
    case $environment in
        dev|development)
            log "Development mode: Using docker-compose.yml"
            export COMPOSE_FILE="docker-compose.yml"
            ;;
        staging)
            log "Staging mode: Using docker-compose.yml and docker-compose.staging.yml"
            export COMPOSE_FILE="docker-compose.yml:docker-compose.staging.yml"
            ;;
        prod|production)
            log "Production mode: Using docker-compose.yml and docker-compose.prod.yml"
            export COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
            ;;
        *)
            error "Unknown environment: $environment. Use 'dev', 'staging', or 'prod'"
            ;;
    esac
}

# Build images
build_images() {
    log "Building Docker images..."
    
    docker-compose build --no-cache || error "Failed to build images"
    success "✓ Images built successfully"
}

# Start services
start_services() {
    log "Starting services..."
    
    docker-compose up -d || error "Failed to start services"
    success "✓ Services started"
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    check_health
}

# Stop services
stop_services() {
    log "Stopping services..."
    
    docker-compose down || error "Failed to stop services"
    success "✓ Services stopped"
}

# Check service health
check_health() {
    log "Checking service health..."
    
    # Backend health
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        success "✓ Backend is healthy"
    else
        warning "⚠ Backend is not responding yet, may still be starting..."
    fi
    
    # Frontend health
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        success "✓ Frontend is healthy"
    else
        warning "⚠ Frontend is not responding yet, may still be starting..."
    fi
    
    # Database health
    if docker-compose exec -T mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
        success "✓ MySQL is healthy"
    else
        warning "⚠ MySQL is not responding yet, may still be starting..."
    fi
    
    # Redis health
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        success "✓ Redis is healthy"
    else
        warning "⚠ Redis is not responding yet, may still be starting..."
    fi
}

# Initialize database
init_database() {
    log "Initializing database..."
    
    # Wait for MySQL to be ready
    log "Waiting for MySQL to be ready..."
    for i in {1..30}; do
        if docker-compose exec -T mysql mysqladmin ping -h localhost > /dev/null 2>&1; then
            log "MySQL is ready"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    # Run initialization script
    if [ -f "backend/init_db.py" ]; then
        log "Running database initialization script..."
        docker-compose exec backend python init_db.py || warning "Database initialization may already be complete"
        success "✓ Database initialized"
    else
        warning "init_db.py not found, skipping database initialization"
    fi
}

# Show logs
show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        log "Showing logs for all services (Ctrl+C to exit)..."
        docker-compose logs -f
    else
        log "Showing logs for $service..."
        docker-compose logs -f "$service"
    fi
}

# Show service status
show_status() {
    log "Service status:"
    docker-compose ps
}

# Clean up resources
cleanup() {
    local environment=$1
    
    log "Cleaning up resources..."
    
    # Stop containers
    docker-compose down
    
    # Remove volumes (database, redis data)
    if [ "$environment" == "full" ]; then
        warning "Removing all volumes (database data will be lost)..."
        docker-compose down -v
        success "✓ All resources cleaned"
    else
        success "✓ Containers stopped (data preserved)"
    fi
}

# Backup database
backup_database() {
    log "Creating database backup..."
    
    local backup_dir="backups"
    local backup_file="$backup_dir/smart_farming_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p "$backup_dir"
    
    docker-compose exec -T mysql mysqldump -u root -proot smart_farming > "$backup_file" || error "Failed to backup database"
    success "✓ Database backed up to $backup_file"
}

# Restore database
restore_database() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
    fi
    
    log "Restoring database from $backup_file..."
    
    docker-compose exec -T mysql mysql -u root -proot smart_farming < "$backup_file" || error "Failed to restore database"
    success "✓ Database restored"
}

# Update services
update_services() {
    log "Updating services..."
    
    # Pull latest images
    docker-compose pull || warning "Failed to pull latest images"
    
    # Rebuild images
    build_images
    
    # Restart services
    stop_services
    sleep 5
    start_services
    
    success "✓ Services updated"
}

# View application URLs
show_urls() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Application URLs${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${BLUE}Frontend:${NC}    http://localhost:3000"
    echo -e "${BLUE}Backend API:${NC}  http://localhost:5000"
    echo -e "${BLUE}Backend Docs:${NC} http://localhost:5000/api"
    echo -e "${BLUE}MySQL:${NC}        localhost:3306"
    echo -e "${BLUE}Redis:${NC}        localhost:6379"
    echo -e "${GREEN}========================================${NC}"
    echo ""
}

# Show help
show_help() {
    cat << EOF
Smart Farmer Marketplace - Docker Deployment Script

Usage: $0 <command> [options]

Commands:
    setup <env>          Setup and start services (dev/staging/prod)
    start <env>          Start services
    stop                 Stop services
    restart <env>        Restart services
    status               Show service status
    logs [service]       Show logs (all or specific service)
    health               Check service health
    init-db              Initialize database
    backup               Backup database
    restore <file>       Restore database from backup
    update               Update services
    clean [full]         Clean up resources (full = remove volumes)
    help                 Show this help message

Examples:
    # Development setup
    $0 setup dev
    
    # Start production services
    $0 start prod
    
    # View backend logs
    $0 logs backend
    
    # Backup database
    $0 backup
    
    # Full cleanup (removes data)
    $0 clean full

Environment Variables:
    COMPOSE_FILE         Docker Compose files to use
    MYSQL_PASSWORD       MySQL root password (from .env)
    FLASK_ENV            Flask environment (dev/production)
    JWT_SECRET_KEY       JWT secret for authentication

For more information, see DOCKER_DEPLOYMENT_GUIDE.md

EOF
}

# Main script logic
main() {
    local command=$1
    local arg1=$2
    local arg2=$3
    
    # Ensure log file exists
    touch "$LOG_FILE"
    
    case $command in
        setup)
            check_prerequisites
            setup_environment "${arg1:-dev}"
            build_images
            start_services
            init_database
            check_health
            show_urls
            ;;
        start)
            check_prerequisites
            setup_environment "${arg1:-dev}"
            start_services
            show_urls
            ;;
        stop)
            stop_services
            ;;
        restart)
            setup_environment "${arg1:-dev}"
            stop_services
            sleep 5
            start_services
            show_urls
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$arg1"
            ;;
        health)
            check_health
            ;;
        init-db)
            init_database
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database "$arg1"
            ;;
        update)
            setup_environment "${arg1:-dev}"
            update_services
            show_urls
            ;;
        clean)
            cleanup "$arg1"
            ;;
        help)
            show_help
            ;;
        *)
            echo "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
