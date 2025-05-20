'use server';
import type { Project, ScrapedSession, ChatMessage } from '@/types';
import { structureScrapedData } from '@/ai/flows/structure-scraped-data';
import { queryProjectData } from '@/ai/flows/query-project-data';

let projects: Project[] = [
  {
    id: '1',
    name: 'Competitor Analysis Q3',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    scrapedSessionsCount: 2,
    ragStatus: 'Enabled',
  },
  {
    id: '2',
    name: 'Tech News Roundup',
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString(),
    scrapedSessionsCount: 0,
    ragStatus: 'Disabled',
  },
];

let scrapedSessions: ScrapedSession[] = [
  {
    id: 's1',
    projectId: '1',
    url: 'https://example.com/competitor-a',
    scrapedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 4).toISOString(),
    status: 'Embedded for RAG',
    markdownContent: '# Competitor A\n\nThis is some scraped content about Competitor A.',
    structuredData: { title: 'Competitor A', summary: 'This is some scraped content about Competitor A.'},
    downloadLinkJson: `/api/download/1/s1/json`, // Placeholder
    downloadLinkCsv: `/api/download/1/s1/csv`, // Placeholder
  },
  {
    id: 's2',
    projectId: '1',
    url: 'https://example.com/competitor-b',
    scrapedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    status: 'Embedded for RAG',
    markdownContent: '# Competitor B\n\nInformation regarding features and pricing of Competitor B.',
    structuredData: { title: 'Competitor B', details: 'Information regarding features and pricing of Competitor B.'},
    downloadLinkJson: `/api/download/1/s2/json`, // Placeholder
    downloadLinkCsv: `/api/download/1/s2/csv`, // Placeholder
  },
];

let chatMessages: { [projectId: string]: ChatMessage[] } = {
  '1': [
    { id: 'm1', role: 'user', content: 'What are the key features of Competitor A?', timestamp: new Date().toISOString() },
    { id: 'm2', role: 'assistant', content: 'Competitor A focuses on ease of use and integration with other services.', timestamp: new Date().toISOString(), cost: 0.002, sources: ['https://example.com/competitor-a'] },
  ],
};

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export async function getProjects(): Promise<Project[]> {
  await delay(500);
  return projects.map(p => ({
    ...p,
    scrapedSessionsCount: scrapedSessions.filter(s => s.projectId === p.id).length,
  }));
}

export async function getProjectById(id: string): Promise<Project | undefined> {
  await delay(300);
  const project = projects.find(p => p.id === id);
  if (project) {
    return {
      ...project,
      scrapedSessionsCount: scrapedSessions.filter(s => s.projectId === project.id).length,
    };
  }
  return undefined;
}

export async function createProject(name: string, initialUrls?: string[]): Promise<Project> {
  await delay(700);
  const newProject: Project = {
    id: String(Date.now()),
    name,
    createdAt: new Date().toISOString(),
    scrapedSessionsCount: 0,
    ragStatus: 'Disabled',
    initialUrls: initialUrls,
  };
  projects.push(newProject);
  return newProject;
}

export async function updateProjectRAGStatus(projectId: string, enable: boolean): Promise<Project | undefined> {
  await delay(1000);
  const project = projects.find(p => p.id === projectId);
  if (project) {
    project.ragStatus = enable ? 'Enabled' : 'Disabled';
    // Simulate backend processing for enabling RAG
    if (enable) {
      const projectSessions = scrapedSessions.filter(s => s.projectId === projectId);
      for (const session of projectSessions) {
        session.status = 'Embedded for RAG'; // Simulate embedding
      }
    }
    return { ...project };
  }
  return undefined;
}

export async function updateProjectName(projectId: string, newName: string): Promise<Project | undefined> {
  await delay(500);
  const project = projects.find(p => p.id === projectId);
  if (project) {
    project.name = newName;
    return { ...project };
  }
  return undefined;
}

export async function deleteProject(projectId: string): Promise<boolean> {
  await delay(1000);
  const initialLength = projects.length;
  projects = projects.filter(p => p.id !== projectId);
  scrapedSessions = scrapedSessions.filter(s => s.projectId !== projectId);
  delete chatMessages[projectId];
  return projects.length < initialLength;
}

export async function getScrapedSessions(projectId: string): Promise<ScrapedSession[]> {
  await delay(400);
  return scrapedSessions.filter(s => s.projectId === projectId);
}

// Mock for initiating interactive scrape - in a real app, this would return a URL to a sandboxed browser
export async function initiateInteractiveScrape(projectId: string, url: string): Promise<{ interactive_browser_url: string, session_id: string }> {
  await delay(1500);
  // This URL would be to a service like KasmVNC, Browserless.io, or a custom Puppeteer/Playwright instance
  // For mock, we just return the original URL and a new session ID
  const sessionId = `session_${Date.now()}`;
  return { interactive_browser_url: url, session_id: sessionId };
}

export async function executeScrape(projectId: string, url: string, sessionId: string): Promise<ScrapedSession> {
  await delay(3000); // Simulate scraping time
  const project = projects.find(p => p.id === projectId);
  if (!project) throw new Error('Project not found');

  // Simulate scraping with Crawl4AI - get markdown
  const mockMarkdownContent = `# Scraped Content from ${url}\n\nThis is some dummy markdown content generated at ${new Date().toLocaleTimeString()}.\n\n- Item 1\n- Item 2\n\n## Sub-section\nSome details here.`;
  
  let structuredData: Record<string, any> = { rawMarkdown: mockMarkdownContent };
  try {
    const structuredResult = await structureScrapedData({ markdownContent: mockMarkdownContent });
    structuredData = JSON.parse(structuredResult.structuredData);
  } catch (error) {
    console.error("Failed to structure data with AI:", error);
    // Fallback to raw markdown if structuring fails
  }

  const newSession: ScrapedSession = {
    id: sessionId,
    projectId,
    url,
    scrapedAt: new Date().toISOString(),
    status: project.ragStatus === 'Enabled' ? 'Embedded for RAG' : 'Scraped',
    markdownContent: mockMarkdownContent,
    structuredData,
    downloadLinkJson: `/api/download/${projectId}/${sessionId}/json`, // Placeholder
    downloadLinkCsv: `/api/download/${projectId}/${sessionId}/csv`, // Placeholder
  };
  scrapedSessions.push(newSession);
  return newSession;
}

export async function deleteScrapedSession(projectId: string, sessionId: string): Promise<boolean> {
  await delay(500);
  const initialLength = scrapedSessions.length;
  scrapedSessions = scrapedSessions.filter(s => !(s.projectId === projectId && s.id === sessionId));
  return scrapedSessions.length < initialLength;
}

export async function getChatMessages(projectId: string): Promise<ChatMessage[]> {
  await delay(200);
  return chatMessages[projectId] || [];
}

export async function postChatMessage(projectId: string, content: string): Promise<ChatMessage> {
  await delay(2000); // Simulate LLM response time
  const project = projects.find(p => p.id === projectId);
  if (!project || project.ragStatus !== 'Enabled') {
    throw new Error("RAG is not enabled for this project or project not found.");
  }

  const userMessage: ChatMessage = {
    id: `msg_${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date().toISOString(),
  };

  if (!chatMessages[projectId]) {
    chatMessages[projectId] = [];
  }
  chatMessages[projectId].push(userMessage);

  // Simulate RAG query using the AI flow
  try {
    const ragResponse = await queryProjectData({ projectId, query: content });
    const assistantMessage: ChatMessage = {
      id: `msg_${Date.now() + 1}`,
      role: 'assistant',
      content: ragResponse.answer,
      timestamp: new Date().toISOString(),
      cost: ragResponse.generationCost, // This will be 0 from the mock flow
      sources: ragResponse.sourceDocuments, // This will be [] from the mock flow
    };
    chatMessages[projectId].push(assistantMessage);
    return assistantMessage;
  } catch (error) {
    console.error("Error querying RAG:", error);
    const errorMessage: ChatMessage = {
      id: `msg_${Date.now() + 1}`,
      role: 'assistant',
      content: "Sorry, I encountered an error trying to answer your question.",
      timestamp: new Date().toISOString(),
    };
    chatMessages[projectId].push(errorMessage);
    return errorMessage;
  }
}
