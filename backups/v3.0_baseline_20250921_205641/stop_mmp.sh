#!/bin/bash
# MMP Application Stop Script
# Stop the running MMP service gracefully

# Color definitions
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

# Show help information
show_help() {
    echo "MMP Application Stop Script"
    echo
    echo "Usage:"
    echo "  $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help           Show this help information"
    echo "  -f, --force          Force kill processes"
    echo "  -v, --verbose        Verbose output"
    echo
    echo "Examples:"
    echo "  $0                   # Stop MMP service gracefully"
    echo "  $0 -f                # Force stop MMP service"
    echo "  $0 -v                # Stop with verbose output"
}

# Parse arguments
parse_arguments() {
    FORCE_KILL=false
    VERBOSE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -f|--force)
                FORCE_KILL=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                log_error "Extra parameter: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Find MMP processes
find_mmp_processes() {
    log_info "Looking for MMP processes..."
    
    # Find processes matching MMP patterns
    local pids=($(pgrep -f "python.*run_app.py\|python.*app/web_app.py" 2>/dev/null || true))
    
    if [[ ${#pids[@]} -eq 0 ]]; then
        log_info "No MMP processes found"
        return 1
    fi
    
    if [[ "$VERBOSE" == true ]]; then
        log_info "Found MMP processes:"
        for pid in "${pids[@]}"; do
            local cmd=$(ps -p "$pid" -o cmd --no-headers 2>/dev/null || echo "Unknown")
            log_info "  PID $pid: $cmd"
        done
    else
        log_info "Found ${#pids[@]} MMP process(es): ${pids[*]}"
    fi
    
    echo "${pids[@]}"
    return 0
}

# Stop processes gracefully
stop_processes_gracefully() {
    local pids=($1)
    
    log_info "Stopping processes gracefully..."
    
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Sending TERM signal to process $pid"
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    
    # Wait for processes to stop
    local wait_time=10
    log_info "Waiting up to ${wait_time} seconds for processes to stop..."
    
    for i in $(seq 1 $wait_time); do
        local running_pids=()
        for pid in "${pids[@]}"; do
            if kill -0 "$pid" 2>/dev/null; then
                running_pids+=("$pid")
            fi
        done
        
        if [[ ${#running_pids[@]} -eq 0 ]]; then
            log_success "All processes stopped gracefully"
            return 0
        fi
        
        if [[ "$VERBOSE" == true ]]; then
            log_info "Still running: ${running_pids[*]} (${i}s)"
        fi
        
        sleep 1
    done
    
    # Some processes are still running
    local still_running=()
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            still_running+=("$pid")
        fi
    done
    
    if [[ ${#still_running[@]} -gt 0 ]]; then
        log_warning "Some processes are still running: ${still_running[*]}"
        echo "${still_running[@]}"
        return 1
    fi
    
    return 0
}

# Force kill processes
force_kill_processes() {
    local pids=($1)
    
    log_warning "Force killing processes..."
    
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Force killing process $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    # Wait a moment and check
    sleep 2
    
    local still_running=()
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            still_running+=("$pid")
        fi
    done
    
    if [[ ${#still_running[@]} -eq 0 ]]; then
        log_success "All processes force killed successfully"
        return 0
    else
        log_error "Failed to kill some processes: ${still_running[*]}"
        return 1
    fi
}

# Clean up PID files
cleanup_pid_files() {
    log_info "Cleaning up PID files..."
    
    local pid_files=(
        "/tmp/mmp_service.pid"
        "/var/run/mmp.pid"
        "/tmp/mmp.pid"
    )
    
    for pid_file in "${pid_files[@]}"; do
        if [[ -f "$pid_file" ]]; then
            rm -f "$pid_file"
            log_info "Removed PID file: $pid_file"
        fi
    done
}

# Check if processes are really stopped
verify_stop() {
    log_info "Verifying all MMP processes are stopped..."
    
    local remaining_pids=($(pgrep -f "python.*run_app.py\|python.*app/web_app.py" 2>/dev/null || true))
    
    if [[ ${#remaining_pids[@]} -eq 0 ]]; then
        log_success "All MMP processes have been stopped"
        return 0
    else
        log_error "Some MMP processes are still running: ${remaining_pids[*]}"
        if [[ "$VERBOSE" == true ]]; then
            for pid in "${remaining_pids[@]}"; do
                local cmd=$(ps -p "$pid" -o cmd --no-headers 2>/dev/null || echo "Unknown")
                log_error "  PID $pid: $cmd"
            done
        fi
        return 1
    fi
}

# Main function
main() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}      MMP Application Stop Script${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
    
    # Parse arguments
    parse_arguments "$@"
    
    # Find MMP processes
    local pids_str
    if ! pids_str=$(find_mmp_processes); then
        log_success "No MMP processes to stop"
        exit 0
    fi
    
    local pids=($pids_str)
    
    if [[ "$FORCE_KILL" == true ]]; then
        # Force kill directly
        if force_kill_processes "${pids[*]}"; then
            cleanup_pid_files
            verify_stop
            log_success "MMP application stopped (force killed)"
        else
            log_error "Failed to force kill some processes"
            exit 1
        fi
    else
        # Try graceful stop first
        local remaining_pids_str
        if ! remaining_pids_str=$(stop_processes_gracefully "${pids[*]}"); then
            # Some processes didn't stop gracefully
            local remaining_pids=($remaining_pids_str)
            log_warning "Some processes didn't stop gracefully, force killing..."
            
            if force_kill_processes "${remaining_pids[*]}"; then
                log_success "Remaining processes force killed"
            else
                log_error "Failed to stop all processes"
                exit 1
            fi
        fi
        
        cleanup_pid_files
        verify_stop
        log_success "MMP application stopped successfully"
    fi
    
    echo
    log_info "Stop process completed!"
}

# Signal handling
trap 'log_error "Stop process interrupted"; exit 1' INT TERM

# Run main function
main "$@"
