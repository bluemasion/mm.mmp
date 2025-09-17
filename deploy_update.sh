#!/bin/bash
# MMP System Deployment Update Script
# Deploy the fixed version to production server

set -e  # Exit on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_PREFIX="mmp_backup"
LOG_FILE="/tmp/mmp_deploy_$(date +%Y%m%d_%H%M%S).log"

# Logging functions
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Show help information
show_help() {
    echo "MMP System Deployment Update Script"
    echo
    echo "Usage:"
    echo "  $0 [options] <target_path>"
    echo
    echo "Options:"
    echo "  -h, --help           Show this help information"
    echo "  -b, --backup-only    Only create backup, do not deploy"
    echo "  -n, --no-backup      Skip backup step"
    echo "  -t, --test           Test mode, do not actually deploy"
    echo "  -f, --force          Force deployment, skip confirmation"
    echo
    echo "Examples:"
    echo "  $0 /opt/mmp                    # Deploy to /opt/mmp"
    echo "  $0 -b /opt/mmp                 # Only backup /opt/mmp"
    echo "  $0 -n /opt/mmp                 # Deploy without backup"
    echo "  $0 -t /opt/mmp                 # Test mode"
}

# Parse arguments
parse_arguments() {
    BACKUP_ONLY=false
    NO_BACKUP=false
    TEST_MODE=false
    FORCE_DEPLOY=false
    TARGET_PATH=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -b|--backup-only)
                BACKUP_ONLY=true
                shift
                ;;
            -n|--no-backup)
                NO_BACKUP=true
                shift
                ;;
            -t|--test)
                TEST_MODE=true
                shift
                ;;
            -f|--force)
                FORCE_DEPLOY=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                if [[ -z "$TARGET_PATH" ]]; then
                    TARGET_PATH="$1"
                else
                    log_error "Extra parameter: $1"
                    exit 1
                fi
                shift
                ;;
        esac
    done
    
    if [[ -z "$TARGET_PATH" ]]; then
        log_error "Please specify target deployment path"
        show_help
        exit 1
    fi
}

# Check source files
check_source_files() {
    log_info "Checking source files..."
    
    local required_files=(
        "run_app.py"
        "app/web_app.py"
        "app/workflow_service.py"
        "app/data_loader.py"
        "requirements.txt"
        "config.py"
    )
    
    local missing_files=()
    for file in "${required_files[@]}"; do
        if [[ ! -f "$SCRIPT_DIR/$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing required source files:"
        for file in "${missing_files[@]}"; do
            log_error "  - $file"
        done
        exit 1
    fi
    
    log_success "Source files check passed"
}

# Check target environment
check_target_environment() {
    log_info "Checking target environment: $TARGET_PATH"
    
    # Check if target path exists
    if [[ ! -d "$TARGET_PATH" ]]; then
        log_warning "Target path does not exist: $TARGET_PATH"
        if [[ "$FORCE_DEPLOY" != true ]] && [[ "$TEST_MODE" != true ]]; then
            read -p "Create target directory? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Deployment cancelled"
                exit 0
            fi
        fi
        
        if [[ "$TEST_MODE" != true ]]; then
            mkdir -p "$TARGET_PATH"
            log_success "Created target directory: $TARGET_PATH"
        fi
    fi
    
    # Check if it's an MMP project directory
    if [[ -f "$TARGET_PATH/app/web_app.py" ]] || [[ -f "$TARGET_PATH/run_app.py" ]]; then
        log_success "Detected existing MMP project"
    else
        log_warning "Target path does not seem to be an MMP project directory"
        if [[ "$FORCE_DEPLOY" != true ]] && [[ "$TEST_MODE" != true ]]; then
            read -p "Continue deployment? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "Deployment cancelled"
                exit 0
            fi
        fi
    fi
    
    # Check disk space
    local available_space=$(df "$TARGET_PATH" | awk 'NR==2 {print $4}')
    local required_space=102400  # 100MB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        log_warning "Disk space may be insufficient (available: ${available_space}KB, required: ${required_space}KB)"
    fi
    
    # Check permissions
    if [[ ! -w "$TARGET_PATH" ]]; then
        log_error "No write permission for target path: $TARGET_PATH"
        exit 1
    fi
    
    log_success "Target environment check passed"
}

# Create backup
create_backup() {
    if [[ "$NO_BACKUP" == true ]]; then
        log_info "Skipping backup step"
        return 0
    fi
    
    log_info "Creating backup..."
    
    local backup_name="${BACKUP_PREFIX}_$(date +%Y%m%d_%H%M%S)"
    local backup_path="${TARGET_PATH}/../${backup_name}"
    
    if [[ -d "$TARGET_PATH" ]] && [[ "$(ls -A "$TARGET_PATH" 2>/dev/null)" ]]; then
        if [[ "$TEST_MODE" != true ]]; then
            cp -r "$TARGET_PATH" "$backup_path"
            log_success "Backup created: $backup_path"
            echo "$backup_path" > "/tmp/mmp_last_backup.txt"
        else
            log_info "[Test Mode] Will create backup: $backup_path"
        fi
    else
        log_info "Target path is empty, skipping backup"
    fi
}

# Stop existing service
stop_existing_service() {
    log_info "Stopping existing MMP service..."
    
    local pids=($(pgrep -f "python.*run_app.py\|python.*app/web_app.py" || true))
    
    if [[ ${#pids[@]} -gt 0 ]]; then
        log_info "Found running MMP processes: ${pids[*]}"
        
        if [[ "$TEST_MODE" != true ]]; then
            for pid in "${pids[@]}"; do
                kill "$pid" 2>/dev/null || true
                log_info "Stopping process: $pid"
            done
            
            # Wait for processes to stop completely
            sleep 3
            
            # Force kill processes still running
            for pid in "${pids[@]}"; do
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                    log_warning "Force stopped process: $pid"
                fi
            done
        else
            log_info "[Test Mode] Will stop processes: ${pids[*]}"
        fi
        
        log_success "MMP service stopped"
    else
        log_info "No running MMP service found"
    fi
}

# Deploy files
deploy_files() {
    log_info "Deploying files to: $TARGET_PATH"
    
    if [[ "$TEST_MODE" == true ]]; then
        log_info "[Test Mode] Will copy the following files:"
        find "$SCRIPT_DIR" -type f -name "*.py" -o -name "*.txt" -o -name "*.md" -o -name "*.html" -o -name "*.sh" | \
            grep -v "__pycache__" | grep -v ".DS_Store" | sort
        return 0
    fi
    
    # Create target directory structure
    mkdir -p "$TARGET_PATH/app"
    mkdir -p "$TARGET_PATH/templates"
    
    # Copy files, excluding unnecessary files
    rsync -av --exclude='__pycache__' \
              --exclude='.DS_Store' \
              --exclude='*.pyc' \
              --exclude='.git' \
              --exclude='venv' \
              --exclude='*.log' \
              "$SCRIPT_DIR/" "$TARGET_PATH/"
    
    # Set execution permissions
    chmod +x "$TARGET_PATH/run_app.py"
    chmod +x "$TARGET_PATH"/*.sh 2>/dev/null || true
    
    log_success "File deployment completed"
}

# Update dependencies
update_dependencies() {
    log_info "Updating Python dependencies..."
    
    cd "$TARGET_PATH"
    
    if [[ "$TEST_MODE" == true ]]; then
        log_info "[Test Mode] Will execute: pip3 install -r requirements.txt"
        return 0
    fi
    
    # Check Python and pip
    if ! command -v python3 &> /dev/null; then
        log_error "python3 command not found"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 command not found"
        exit 1
    fi
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        pip3 install -r requirements.txt
        log_success "Dependencies update completed"
    else
        log_warning "requirements.txt file not found"
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    cd "$TARGET_PATH"
    
    # Check critical files
    local critical_files=(
        "run_app.py"
        "app/web_app.py"
        "app/workflow_service.py"
        "requirements.txt"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Missing critical file: $file"
            return 1
        fi
    done
    
    # Test Python import
    if [[ "$TEST_MODE" != true ]]; then
        if python3 -c "from app.web_app import app; print('Flask application imported successfully')" 2>/dev/null; then
            log_success "Python module import test passed"
        else
            log_error "Python module import test failed"
            return 1
        fi
    fi
    
    log_success "Deployment verification passed"
}

# Start service
start_service() {
    if [[ "$TEST_MODE" == true ]]; then
        log_info "[Test Mode] Will start service: python3 run_app.py"
        return 0
    fi
    
    log_info "Starting MMP service..."
    
    cd "$TARGET_PATH"
    
    # Start service in background
    nohup python3 run_app.py > app.log 2>&1 &
    local service_pid=$!
    
    # Wait for service to start
    sleep 5
    
    # Check if service is running
    if kill -0 "$service_pid" 2>/dev/null; then
        log_success "MMP service started successfully (PID: $service_pid)"
        echo "$service_pid" > "/tmp/mmp_service.pid"
        
        # Test service response
        if command -v curl &> /dev/null; then
            if curl -s http://localhost:5000 > /dev/null 2>&1; then
                log_success "Service response test passed"
            else
                log_warning "Service may still be starting..."
            fi
        fi
    else
        log_error "MMP service startup failed"
        return 1
    fi
}

# Show deployment result
show_deployment_result() {
    echo
    log_success "=================================="
    log_success "    MMP System Deployment Complete!"
    log_success "=================================="
    echo
    log_info "Deployment Information:"
    log_info "- Target Path: $TARGET_PATH"
    log_info "- Deployment Time: $(date)"
    log_info "- Log File: $LOG_FILE"
    
    if [[ -f "/tmp/mmp_last_backup.txt" ]]; then
        local backup_path=$(cat "/tmp/mmp_last_backup.txt")
        log_info "- Backup Path: $backup_path"
    fi
    
    if [[ -f "/tmp/mmp_service.pid" ]]; then
        local service_pid=$(cat "/tmp/mmp_service.pid")
        log_info "- Service PID: $service_pid"
    fi
    
    echo
    log_info "Usage:"
    log_info "- Access application: http://localhost:5000"
    log_info "- View logs: tail -f $TARGET_PATH/app.log"
    log_info "- Stop service: pkill -f 'python3 run_app.py'"
    log_info "- Restart service: cd $TARGET_PATH && python3 run_app.py"
    
    if [[ "$BACKUP_ONLY" != true ]]; then
        echo
        log_warning "Important Reminders:"
        log_warning "- Please test all core functions"
        log_warning "- Monitor application logs for errors"
        log_warning "- Use backup for quick rollback if needed"
    fi
}

# Main function
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}      MMP System Deployment Script v1.0${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    
    # Start logging
    log_info "Starting deployment update process..."
    log_info "Log file: $LOG_FILE"
    
    # Parse arguments
    parse_arguments "$@"
    
    # Display configuration
    log_info "Deployment Configuration:"
    log_info "- Target Path: $TARGET_PATH"
    log_info "- Backup Only: $BACKUP_ONLY"
    log_info "- Skip Backup: $NO_BACKUP"
    log_info "- Test Mode: $TEST_MODE"
    log_info "- Force Deploy: $FORCE_DEPLOY"
    echo
    
    # Check source files
    check_source_files
    
    # Check target environment
    check_target_environment
    
    # Create backup
    create_backup
    
    if [[ "$BACKUP_ONLY" == true ]]; then
        log_success "Backup-only mode completed"
        exit 0
    fi
    
    # Stop existing service
    stop_existing_service
    
    # Deploy files
    deploy_files
    
    # Update dependencies
    update_dependencies
    
    # Verify deployment
    if ! verify_deployment; then
        log_error "Deployment verification failed"
        exit 1
    fi
    
    # Start service
    if ! start_service; then
        log_error "Service startup failed"
        exit 1
    fi
    
    # Show results
    show_deployment_result
    
    log_success "Deployment update script execution completed!"
}

# Signal handling
trap 'log_error "Deployment process interrupted"; exit 1' INT TERM

# Run main function
main "$@"
