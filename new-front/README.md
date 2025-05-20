# New Frontend for RAG System

This is the new React-based frontend for the RAG (Retrieval-Augmented Generation) system. It provides the same functionality as the original Next.js frontend but with a different implementation.

## Features

- **Real-time Progress Indicators**: Display real-time progress of RAG ingestion via WebSockets
- **Cache Statistics**: View and monitor cache performance metrics
- **Force Refresh Option**: Bypass cache and fetch fresh content when needed
- **Interactive Scraping**: Scrape web pages and process them for RAG

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)
- Backend server running on port 8000

### Installation

1. Install dependencies:

```bash
npm install
```

2. Start the development server:

```bash
npm start
# or
npm run dev
```

The application will be available at http://localhost:9002.

## Components

### RagProgressIndicator

Displays real-time progress of RAG ingestion via WebSockets.

```jsx
import RagProgressIndicator from './components/RagProgressIndicator';

<RagProgressIndicator
  projectId="your-project-id"
  sessionId="your-session-id"
  onComplete={() => console.log('Processing complete!')}
/>
```

### CacheStatsDisplay

Shows cache statistics and allows refreshing the data.

```jsx
import CacheStatsDisplay from './components/CacheStatsDisplay';

<CacheStatsDisplay refreshInterval={30000} />
```

### ForceRefreshToggle

Toggle component for the force refresh option.

```jsx
import ForceRefreshToggle from './components/ForceRefreshToggle';

<ForceRefreshToggle
  checked={forceRefresh}
  onChange={setForceRefresh}
/>
```

### InteractiveScrapeModal

Modal component for interactive scraping with force refresh option.

```jsx
import InteractiveScrapeModal from './components/InteractiveScrapeModal';

<InteractiveScrapeModal
  projectId="your-project-id"
  url="https://example.com"
  sessionId="your-session-id"
  onClose={() => setShowModal(false)}
  onSuccess={(result) => console.log('Scraping successful:', result)}
/>
```

## API Client

The API client is located in `src/lib/api.js` and provides functions for interacting with the backend API.

```javascript
import { getProjects, executeScrape } from './lib/api';

// Get all projects
const projects = await getProjects();

// Execute scraping with force refresh
const result = await executeScrape(
  projectId,
  url,
  sessionId,
  true // force refresh
);
```

## WebSocket Manager

The WebSocket manager is located in `src/lib/websocket.js` and provides a class for managing WebSocket connections.

```javascript
import { webSocketManager } from './lib/websocket';

// Connect to the WebSocket server
webSocketManager.connect(projectId);

// Register a callback for WebSocket messages
const unsubscribe = webSocketManager.onMessage((message) => {
  console.log('Received message:', message);
});

// Disconnect from the WebSocket server
webSocketManager.disconnect();
```

## Configuration

The application is configured to connect to the backend API at `http://localhost:8000/api/v1`. You can change this in `src/lib/api.js`.

## Switching from the Original Frontend

See the `FRONTEND_MIGRATION.md` file in the root directory for instructions on switching from the original frontend to this new frontend.
