#!/bin/bash

# Script to ensure the frontend symbolic link is correctly set up
# This can be added to system startup scripts

# Set the directory names
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OLD_FRONTEND="frontend"
NEW_FRONTEND="new-front"
BACKUP_DIR="frontend_backup"

# Change to the project directory
cd "$PROJECT_DIR"

# Check if frontend directory exists
if [ -L "$OLD_FRONTEND" ]; then
    # Check if the link is pointing to the correct directory
    LINK_TARGET=$(readlink "$OLD_FRONTEND")
    if [ "$LINK_TARGET" != "$NEW_FRONTEND" ]; then
        echo "Frontend link is pointing to $LINK_TARGET instead of $NEW_FRONTEND. Fixing..."
        rm "$OLD_FRONTEND"
        ln -s "$NEW_FRONTEND" "$OLD_FRONTEND"
        echo "Frontend link fixed."
    else
        echo "Frontend link is correctly set up."
    fi
else
    # If frontend exists but is not a symlink
    if [ -d "$OLD_FRONTEND" ] && [ ! -L "$OLD_FRONTEND" ]; then
        echo "Frontend directory exists but is not a symlink. Backing up and creating link..."
        if [ -d "$BACKUP_DIR" ]; then
            rm -rf "$BACKUP_DIR"
        fi
        mv "$OLD_FRONTEND" "$BACKUP_DIR"
        ln -s "$NEW_FRONTEND" "$OLD_FRONTEND"
        echo "Frontend link created."
    elif [ ! -e "$OLD_FRONTEND" ]; then
        # If frontend doesn't exist at all
        echo "Frontend directory doesn't exist. Creating link..."
        ln -s "$NEW_FRONTEND" "$OLD_FRONTEND"
        echo "Frontend link created."
    fi
fi

echo "Frontend link check completed."
