#!/bin/bash

# Script to test the new frontend with the backend

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to check if a process is running on a specific port
check_port() {
    local port=$1
    if lsof -i :$port -t >/dev/null; then
        return 0 # Port is in use (process is running)
    else
        return 1 # Port is not in use (process is not running)
    fi
}

# Function to start the backend server
start_backend() {
    echo -e "${YELLOW}Starting backend server...${NC}"
    cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    
    # Wait for the backend to start
    echo -e "${YELLOW}Waiting for backend to start...${NC}"
    for i in {1..30}; do
        if check_port 8000; then
            echo -e "${GREEN}Backend server started successfully!${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}Failed to start backend server!${NC}"
    return 1
}

# Function to switch to the new frontend
switch_to_new_frontend() {
    echo -e "${YELLOW}Switching to the new frontend...${NC}"
    ./switch_frontend.sh --new
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to switch to the new frontend!${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Switched to the new frontend successfully!${NC}"
    return 0
}

# Function to start the new frontend server
start_frontend() {
    echo -e "${YELLOW}Starting new frontend server...${NC}"
    cd frontend && npm run dev &
    FRONTEND_PID=$!
    
    # Wait for the frontend to start
    echo -e "${YELLOW}Waiting for frontend to start...${NC}"
    for i in {1..30}; do
        if check_port 9002; then
            echo -e "${GREEN}Frontend server started successfully!${NC}"
            return 0
        fi
        sleep 1
    done
    
    echo -e "${RED}Failed to start frontend server!${NC}"
    return 1
}

# Function to test the API connection
test_api_connection() {
    echo -e "${YELLOW}Testing API connection...${NC}"
    
    # Wait a bit for the servers to fully initialize
    sleep 5
    
    # Make a simple API request to the backend
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/projects)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}API connection successful!${NC}"
        return 0
    else
        echo -e "${RED}API connection failed! Response code: $response${NC}"
        return 1
    fi
}

# Function to clean up processes
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on the ports
    lsof -i :9002 -t | xargs kill 2>/dev/null || true
    lsof -i :8000 -t | xargs kill 2>/dev/null || true
    
    echo -e "${GREEN}Cleanup complete!${NC}"
}

# Main function
main() {
    echo -e "${GREEN}=== Testing New Frontend Integration ===${NC}"
    
    # Set up trap to clean up on exit
    trap cleanup EXIT
    
    # Check if backend is already running
    if check_port 8000; then
        echo -e "${GREEN}Backend server is already running on port 8000.${NC}"
    else
        # Start the backend server
        start_backend
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to start backend server. Exiting.${NC}"
            exit 1
        fi
    fi
    
    # Switch to the new frontend
    switch_to_new_frontend
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to switch to the new frontend. Exiting.${NC}"
        exit 1
    fi
    
    # Start the frontend server
    start_frontend
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start frontend server. Exiting.${NC}"
        exit 1
    fi
    
    # Test the API connection
    test_api_connection
    if [ $? -ne 0 ]; then
        echo -e "${RED}API connection test failed. Exiting.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}=== All tests passed! The new frontend is working correctly with the backend. ===${NC}"
    echo -e "${GREEN}=== You can now access the application at http://localhost:9002 ===${NC}"
    
    # Keep the script running to maintain the servers
    echo -e "${YELLOW}Press Ctrl+C to stop the servers and exit.${NC}"
    wait
}

# Run the main function
main
