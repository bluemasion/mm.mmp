#!/bin/bash
# MMP Application Management Script - Simple Commands

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Show help
show_help() {
    echo "MMP Application Management Commands"
    echo
    echo "Usage:"
    echo "  $0 <command>"
    echo
    echo "Commands:"
    echo "  start                Start MMP application"
    echo "  stop                 Stop MMP application"  
    echo "  restart              Restart MMP application"
    echo "  status               Show MMP application status"
    echo
    echo "Examples:"
    echo "  $0 start             # Start MMP"
    echo "  $0 stop              # Stop MMP"
    echo "  $0 restart           # Restart MMP"
    echo "  $0 status            # Check status"
}

# Check if MMP is running
is_running() {
    pgrep -f "python.*run_app.py" > /dev/null 2>&1
}

# Start MMP
start_mmp() {
    echo -e "${BLUE}[INFO]${NC} Starting MMP application..."
    
    if is_running; then
        echo -e "${YELLOW}[WARNING]${NC} MMP is already running"
        return 1
    fi
    
    cd "$SCRIPT_DIR"
    nohup python3 run_app.py > app.log 2>&1 &
    sleep 3
    
    if is_running; then
        echo -e "${GREEN}[SUCCESS]${NC} MMP started successfully"
        echo -e "${BLUE}[INFO]${NC} Access: http://localhost:5000"
        echo -e "${BLUE}[INFO]${NC} Logs: tail -f $SCRIPT_DIR/app.log"
    else
        echo -e "${RED}[ERROR]${NC} Failed to start MMP"
        return 1
    fi
}

# Stop MMP
stop_mmp() {
    echo -e "${BLUE}[INFO]${NC} Stopping MMP application..."
    
    if ! is_running; then
        echo -e "${BLUE}[INFO]${NC} MMP is not running"
        return 0
    fi
    
    pkill -f "python.*run_app.py"
    sleep 2
    
    if ! is_running; then
        echo -e "${GREEN}[SUCCESS]${NC} MMP stopped successfully"
    else
        echo -e "${YELLOW}[WARNING]${NC} Force killing MMP..."
        pkill -9 -f "python.*run_app.py"
        sleep 1
        if ! is_running; then
            echo -e "${GREEN}[SUCCESS]${NC} MMP force stopped"
        else
            echo -e "${RED}[ERROR]${NC} Failed to stop MMP"
            return 1
        fi
    fi
}

# Show status
show_status() {
    echo -e "${BLUE}MMP Application Status:${NC}"
    
    if is_running; then
        local pids=$(pgrep -f "python.*run_app.py" | tr '\n' ' ')
        echo -e "Status: ${GREEN}RUNNING${NC}"
        echo -e "PIDs: $pids"
        
        # Test if service responds
        if command -v curl &> /dev/null && curl -s http://localhost:5000 > /dev/null 2>&1; then
            echo -e "Service: ${GREEN}RESPONDING${NC}"
            echo -e "URL: http://localhost:5000"
        else
            echo -e "Service: ${YELLOW}NOT RESPONDING${NC}"
        fi
    else
        echo -e "Status: ${RED}STOPPED${NC}"
    fi
    
    # Show log info
    if [[ -f "$SCRIPT_DIR/app.log" ]]; then
        local log_size=$(du -h "$SCRIPT_DIR/app.log" 2>/dev/null | cut -f1 || echo "Unknown")
        echo -e "Log: $SCRIPT_DIR/app.log ($log_size)"
    fi
}

# Main function
main() {
    case "${1:-help}" in
        start)
            start_mmp
            ;;
        stop)
            stop_mmp
            ;;
        restart)
            echo -e "${BLUE}[INFO]${NC} Restarting MMP application..."
            stop_mmp
            sleep 2
            start_mmp
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
