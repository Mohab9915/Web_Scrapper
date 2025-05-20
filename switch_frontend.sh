#!/bin/bash

# Script to switch from the old frontend to the new frontend

# Set the directory names
OLD_FRONTEND="frontend"
NEW_FRONTEND="new-front"
BACKUP_DIR="frontend_backup"

# Function to display usage information
usage() {
    echo "Usage: $0 [--new | --old]"
    echo "  --new: Switch to the new frontend (new-front)"
    echo "  --old: Switch back to the old frontend"
    exit 1
}

# Function to stop any running frontend servers
stop_servers() {
    echo "Stopping any running frontend servers..."
    pkill -f "node.*react-scripts start" || true
    pkill -f "node.*next dev" || true
    sleep 2
}

# Function to switch to the new frontend
switch_to_new() {
    echo "Switching to the new frontend..."
    
    # Stop any running servers
    stop_servers
    
    # Check if frontend directory exists
    if [ -d "$OLD_FRONTEND" ]; then
        # Check if it's a symlink
        if [ -L "$OLD_FRONTEND" ]; then
            # Remove the symlink
            rm "$OLD_FRONTEND"
        else
            # Backup the original frontend directory
            echo "Backing up original frontend to $BACKUP_DIR..."
            if [ -d "$BACKUP_DIR" ]; then
                rm -rf "$BACKUP_DIR"
            fi
            mv "$OLD_FRONTEND" "$BACKUP_DIR"
        fi
    fi
    
    # Create a symbolic link from frontend to new-front
    echo "Creating symbolic link from $OLD_FRONTEND to $NEW_FRONTEND..."
    ln -s "$NEW_FRONTEND" "$OLD_FRONTEND"
    
    echo "Frontend switched to $NEW_FRONTEND successfully!"
}

# Function to switch back to the old frontend
switch_to_old() {
    echo "Switching back to the old frontend..."
    
    # Stop any running servers
    stop_servers
    
    # Check if frontend directory exists as a symlink
    if [ -L "$OLD_FRONTEND" ]; then
        # Remove the symlink
        rm "$OLD_FRONTEND"
        
        # Check if backup directory exists
        if [ -d "$BACKUP_DIR" ]; then
            # Restore the original frontend directory
            echo "Restoring original frontend from $BACKUP_DIR..."
            mv "$BACKUP_DIR" "$OLD_FRONTEND"
        else
            echo "Error: Backup directory $BACKUP_DIR not found!"
            exit 1
        fi
    else
        echo "Frontend is not currently a symlink. No action needed."
    fi
    
    echo "Frontend switched back to original successfully!"
}

# Parse command line arguments
if [ "$#" -ne 1 ]; then
    usage
fi

case "$1" in
    --new)
        switch_to_new
        ;;
    --old)
        switch_to_old
        ;;
    *)
        usage
        ;;
esac

# Ask if user wants to start the frontend server
read -p "Do you want to start the frontend server now? (y/n): " start_server

if [ "$start_server" = "y" ] || [ "$start_server" = "Y" ]; then
    echo "Starting frontend server..."
    cd frontend && npm run dev
fi

exit 0
