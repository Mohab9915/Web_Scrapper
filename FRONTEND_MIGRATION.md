# Frontend Migration Guide

This document provides instructions for switching from the old frontend (Next.js) to the new frontend (React).

## Overview

The application now supports two frontend implementations:
- **Original Frontend**: Located in the `frontend` directory, built with Next.js
- **New Frontend**: Located in the `new-front` directory, built with React (Create React App)

Both frontends provide the same functionality, including:
- RAG system with real-time progress indicators
- Cache statistics display
- Force refresh option for cached content
- WebSocket connections for real-time updates

## How to Switch Between Frontends

A script has been provided to easily switch between the two frontend implementations.

### Prerequisites

- Make sure both the `frontend` and `new-front` directories exist
- Ensure you have npm installed
- The backend server should be running on port 8000

### Switching to the New Frontend

```bash
./switch_frontend.sh --new
```

This will:
1. Stop any running frontend servers
2. Back up the original frontend directory to `frontend_backup`
3. Create a symbolic link from `frontend` to `new-front`
4. Optionally start the new frontend server

### Switching Back to the Original Frontend

```bash
./switch_frontend.sh --old
```

This will:
1. Stop any running frontend servers
2. Remove the symbolic link
3. Restore the original frontend from the backup
4. Optionally start the original frontend server

## Running the Frontends Manually

### Original Frontend (Next.js)

```bash
cd frontend
npm run dev
```

This will start the Next.js development server on port 9002.

### New Frontend (React)

```bash
cd new-front
npm run start
```

This will start the React development server on port 9002.

## API Configuration

Both frontends are configured to connect to the backend API at:
- HTTP API: `http://localhost:8000/api/v1`
- WebSocket API: `ws://localhost:8000/api/v1/ws`

## Key Components

The following components have been implemented in both frontends:

1. **RagProgressIndicator**: Displays real-time progress of RAG ingestion via WebSockets
2. **CacheStatsDisplay**: Shows cache statistics and allows refreshing the data
3. **API Client**: Handles communication with the backend API
4. **WebSocket Manager**: Manages WebSocket connections for real-time updates

## Troubleshooting

### Port Conflicts

If you encounter port conflicts, make sure no other applications are using port 9002. You can change the port in:
- Original Frontend: `frontend/package.json` (dev script)
- New Frontend: `new-front/package.json` (start script)

### API Connection Issues

If the frontend cannot connect to the backend API:
1. Ensure the backend server is running on port 8000
2. Check the CORS settings in the backend to allow connections from `http://localhost:9002`
3. Verify the API URL in the frontend configuration

### WebSocket Connection Issues

If real-time updates are not working:
1. Check the browser console for WebSocket connection errors
2. Ensure the backend WebSocket server is running
3. Verify the WebSocket URL in the frontend configuration

## Additional Notes

- Both frontends maintain all the functionality of the original application
- The new frontend uses JavaScript instead of TypeScript
- The styling may differ slightly between the two implementations
- Both frontends run on port 9002 by default
