export interface Project {
  id: string;
  name: string;
  createdAt: string;
  scrapedSessionsCount: number;
  ragStatus: 'Enabled' | 'Disabled' | 'Enabling';
  initialUrls?: string[]; // Optional: URLs provided at project creation
}

export interface ScrapedSession {
  id: string;
  projectId: string;
  url: string;
  scrapedAt: string;
  status: 'Scraped' | 'Embedded for RAG' | 'Error';
  structuredData?: Record<string, any>; // Could be markdown string or structured JSON
  markdownContent?: string; // Raw markdown from scraping
  downloadLinkJson?: string; // Mock link
  downloadLinkCsv?: string; // Mock link
  tabularData?: Record<string, any>[]; // Structured data in tabular format
  fields?: string[]; // List of fields extracted
  displayFormat?: string; // Display format: 'table', 'paragraph', or 'raw'
  formattedTabularData?: Record<string, any>; // Data formatted according to display_format
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  cost?: number;
  sources?: string[];
}

export interface ApiKeys {
  [key: string]: string; // Example: openAIKey, googleAIKey
}
