import { useState, useEffect, useCallback } from 'react';
import { MessageCircle, Globe, Settings, AlertCircle, ChevronDown,
         Database, Clock, Folder, Home, Brain } from 'lucide-react';
import URLManagement from './URLsManagement';
import ChatPanel from './ChatPanel';
import HistoryPanel from './History';
import SettingsModal from './SettingsModal';
import ProjectsPanel from './ProjectsPanel';
import RagPromptModal from './RagPromptModal';
import ConfirmationModal from './ConfirmationModal';
import RagManagement from './components/RagManagement';
import { executeScrape, sendChatMessage, getProjectConversations, createConversation, deleteConversation, getConversationMessages, queryEnhancedRagApi, getProjects, createProject, deleteProject, getScrapedSessions, updateProjectRAGStatus, API_URL } from './lib/api';
import { useToast } from './components/Toast';

function WebScrapingDashboard() {
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const activeProject = projects.find(p => p.id === activeProjectId);
  const toast = useToast();

  // Background data loading function
  const loadProjectDataInBackground = async (projects) => {
    try {
      toast.info('Loading project data...', 'Fetching URLs and history');

      // Load data for projects one by one to avoid overwhelming the server
      for (const project of projects) {
        try {
          // Fetch URLs for this project with timeout
          const urlsController = new AbortController();
          const urlsTimeout = setTimeout(() => urlsController.abort(), 5000); // 5 second timeout

          const urlsResponse = await fetch(`${API_URL}/projects/${project.id}/urls`, {
            signal: urlsController.signal,
            headers: {
              'Content-Type': 'application/json',
            }
          });
          clearTimeout(urlsTimeout);

          if (urlsResponse.ok) {
            const urls = await urlsResponse.json();

            // Fetch sessions for this project with timeout
            const sessionsController = new AbortController();
            const sessionsTimeout = setTimeout(() => sessionsController.abort(), 5000); // 5 second timeout

            const sessionsResponse = await fetch(`${API_URL}/projects/${project.id}/sessions`, {
              signal: sessionsController.signal,
              headers: {
                'Content-Type': 'application/json',
              }
            });
            clearTimeout(sessionsTimeout);

            const sessions = sessionsResponse.ok ? await sessionsResponse.json() : [];

            // Update project with actual data
            setProjects(prevProjects =>
              prevProjects.map(p =>
                p.id === project.id
                  ? {
                      ...p,
                      urls: urls || [],
                      history: sessions && sessions.length > 0 ? sessions : null
                    }
                  : p
              )
            );
          }
        } catch (error) {
          if (error.name === 'AbortError') {
            console.warn(`Timeout loading data for project ${project.id}`);
          } else {
            console.error(`Error loading data for project ${project.id}:`, error);
          }
        }

        // Small delay between requests to avoid overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      toast.success('Project data loaded successfully');
    } catch (error) {
      console.error('Error in background data loading:', error);
      toast.error('Some project data failed to load');
    }
  };

  // Add loading state
  const [isLoading, setIsLoading] = useState(false);

  // Cache for scraping sessions to avoid redundant API calls
  const [sessionsCache, setSessionsCache] = useState({});

  // Chat history state
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [conversations, setConversations] = useState({});
  const [chatMessages, setChatMessages] = useState([]);

  // Fetch projects from the backend when the component mounts (only once)
  useEffect(() => {
    const fetchProjectsData = async () => {
      try {
        setIsLoading(true);
        const data = await getProjects();
        console.log('Fetched projects:', data);

        // Convert the backend projects to the format expected by the frontend
        const formattedProjects = data.map(project => ({
          id: project.id,
          name: project.name,
          // Initialize with empty arrays for new projects - will be populated by fetchProjectUrls
          urls: [],
          scrapingResults: null,
          isScrapingError: false,
          errorMessage: '',
          // Use null to ensure "No history" message shows correctly - will be populated by fetchScrapingSessions
          history: null,
          createdAt: project.created_at,
          // Fix RAG status logic: use ragEnabled (camelCase) from transformed API response
          ragStatus: project.ragEnabled ? 'enabled' : 'disabled',
        }));

        setProjects(formattedProjects);
        setIsLoading(false);

        // Load additional data in the background (non-blocking)
        if (formattedProjects.length > 0) {
          // Don't await this - let it run in background
          loadProjectDataInBackground(formattedProjects);
        }
      } catch (error) {
        console.error('Error fetching projects:', error);
        setIsLoading(false);
      }
    };

    fetchProjectsData();
  }, []); // Empty dependency array - only run once on mount

  // Chat history management functions - defined early to avoid hoisting issues
  const loadChatMessages = useCallback(async (conversationIdOverride = null) => {
    const conversationIdToUse = conversationIdOverride || currentConversationId;

    console.log('loadChatMessages called with:', {
      conversationIdOverride,
      currentConversationId,
      conversationIdToUse,
      activeProjectId
    });

    if (!activeProjectId || !conversationIdToUse) {
      console.log('Clearing messages - missing activeProjectId or conversationId');
      setChatMessages([]);
      return;
    }

    try {
      console.log('Loading messages for conversation:', conversationIdToUse, 'in project:', activeProjectId);
      // Use getConversationMessages which is specifically designed for fetching conversation messages
      const messages = await getConversationMessages(activeProjectId, conversationIdToUse);
      console.log('Retrieved messages:', messages);
      console.log('Number of messages:', messages ? messages.length : 0);
      setChatMessages(messages || []);
    } catch (error) {
      console.error('Error loading chat messages:', error);
      setChatMessages([]);
    }
  }, [activeProjectId, currentConversationId]);

  // Load chat data when active project changes
  useEffect(() => {
    const loadData = async () => {
      if (activeProjectId) {
        // Load conversations
        try {
          console.log('Loading conversations for project:', activeProjectId);
          const projectConversations = await getProjectConversations(activeProjectId);
          console.log('Retrieved conversations:', projectConversations);
          console.log('Number of conversations:', projectConversations ? projectConversations.length : 0);

          setConversations(prev => ({
            ...prev,
            [activeProjectId]: projectConversations || []
          }));

          // If there's no current conversation but there are conversations, select the first one
          if (projectConversations && projectConversations.length > 0 && !currentConversationId) { // currentConversationId is used
            const firstConversationId = projectConversations[0].conversation_id;
            console.log('Auto-selecting first conversation:', firstConversationId);
            setCurrentConversationId(firstConversationId);
          } else {
            console.log('Not auto-selecting conversation:', {
              hasConversations: projectConversations && projectConversations.length > 0,
              currentConversationId
            });
          }
        } catch (error) {
          console.error('Error loading conversations:', error);
        }
      } else {
        // Clear chat state when no project is selected
        setCurrentConversationId(null);
        setChatMessages([]);
      }
    };

    loadData();
  }, [activeProjectId]); // Remove currentConversationId to avoid infinite loops

  // Load messages when conversation changes
  useEffect(() => {
    if (activeProjectId && currentConversationId) {
      console.log('Conversation ID changed, loading messages for:', currentConversationId);
      loadChatMessages(currentConversationId);
    } else {
      console.log('Clearing chat messages - no active project or conversation');
      setChatMessages([]);
    }
  }, [activeProjectId, currentConversationId, loadChatMessages]); // Added loadChatMessages back

  const [activeTab, setActiveTab] = useState('projects');
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);

  const [isRagPromptModalOpen, setIsRagPromptModalOpen] = useState(false);
  const [projectToPromptRagId, setProjectToPromptRagId] = useState(null);

  // Confirmation modal states
  const [isDeleteProjectModalOpen, setIsDeleteProjectModalOpen] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [isDeletingProject, setIsDeletingProject] = useState(false);

  const [isRemoveAllUrlsModalOpen, setIsRemoveAllUrlsModalOpen] = useState(false);
  const [isDeletingUrls, setIsDeletingUrls] = useState(false);

  const [isDeleteHistoryItemModalOpen, setIsDeleteHistoryItemModalOpen] = useState(false);
  const [historyItemToDelete, setHistoryItemToDelete] = useState(null);
  const [isDeletingHistoryItem, setIsDeletingHistoryItem] = useState(false);

  // New confirmation modal states for URL and scraping result deletion
  const [isDeleteUrlModalOpen, setIsDeleteUrlModalOpen] = useState(false);
  const [urlToDelete, setUrlToDelete] = useState(null);
  const [isDeletingUrl, setIsDeletingUrl] = useState(false);

  const [isDeleteScrapingResultModalOpen, setIsDeleteScrapingResultModalOpen] = useState(false);
  const [scrapingResultToDelete, setScrapingResultToDelete] = useState(null);
  const [isDeletingScrapingResult, setIsDeletingScrapingResult] = useState(false);



  const handleAddProject = async (projectName) => {
    try {
      // Call the backend API to create a new project
      const data = await createProject(projectName, []);
      console.log('Created project:', data);

      // Create a new project with the UUID from the backend
      const newProject = {
        id: data.id,
        name: projectName,
        urls: [],
        scrapingResults: null,
        isScrapingError: false,
        errorMessage: '',
        history: null, // Use null instead of empty array to show "No history" message
        createdAt: new Date().toISOString(),
        ragStatus: data.ragEnabled ? 'enabled' : 'disabled',
      };

      setProjects(prevProjects => [...prevProjects, newProject]);
      setActiveProjectId(newProject.id);
      setActiveTab('urls');

      // Fetch any existing scraping sessions for the new project
      fetchScrapingSessions(newProject.id);
    } catch (error) {
      console.error('Error creating project:', error);
      alert('Failed to create project. Please try again.');
    }
  };

  const fetchScrapingSessions = useCallback(async (projectId) => {
    try {
      // Show loading state
      setIsLoading(true);

      // Check if we have cached data for this project
      if (sessionsCache[projectId]) {
        console.log('Using cached scraping sessions for project:', projectId);
        // Update the project with the cached data
        updateProjectById(projectId, sessionsCache[projectId]);
        setIsLoading(false);
        return;
      }

      console.log('Fetching scraping sessions for project:', projectId);

      // Fetch scraping sessions from the backend
      const sessions = await getScrapedSessions(projectId);
      console.log('Fetched scraping sessions:', sessions);

      if (!sessions || sessions.length === 0) {
        console.log('No scraping sessions found for project:', projectId);

        // Even if there are no sessions, we should still update the project data
        // to ensure that the history property is preserved correctly
        const existingProject = projects.find(p => p.id === projectId);
        const projectData = {
          scrapingResults: null,
          // Preserve the existing history property (which could be null)
          history: existingProject?.history
        };

        // Cache the data
        setSessionsCache(prevCache => ({
          ...prevCache,
          [projectId]: projectData
        }));

        // Update the project with the data
        updateProjectById(projectId, projectData);

        setIsLoading(false);
        return;
      }

      // Fetch project URLs to get conditions and display format (in parallel)
      const projectUrlsPromise = fetch(`${API_URL}/projects/${projectId}/urls`, {
          headers: {
            'Content-Type': 'application/json',
          }
        })
        .then(res => res.ok ? res.json() : [])
        .catch(err => {
          console.warn('Failed to fetch project URLs, using default values:', err);
          return [];
        });

      // Wait for the project URLs to be fetched
      const projectUrls = await projectUrlsPromise;
      console.log('Fetched project URLs:', projectUrls);

      // Convert the sessions to the format expected by the frontend
      const scrapingResults = [];
      // IMPORTANT: Don't create history entries here to avoid recreating deleted history items

      // Process each projectUrlItem (which might have latest_scrape_data)
      sessions.forEach((projectUrlItem) => {
        // The API transforms snake_case to camelCase, so latest_scrape_data becomes latestScrapeData
        const latestScrapeData = projectUrlItem.latestScrapeData || projectUrlItem.latest_scrape_data;



        // Conditions and display_format come from the projectUrlItem itself
        const conditions = projectUrlItem.conditions || "title, description, price, content";
        const displayFormatFromProjectUrl = projectUrlItem.display_format || "table";

        if (!latestScrapeData) {
          // No actual scrape session data, create a placeholder entry for the URL
          const emptyResultEntry = {
            url: projectUrlItem.url,
            conditions: conditions,
            results: [], // No simplified results
            tabularData: [], // No tabular data
            fields: conditions.split(',').map(f => f.trim()), // Fields from conditions
            display_format: displayFormatFromProjectUrl,
            structuredData: {}, // Empty structured data
            project_id: projectId,
            session_id: null, // No session ID
            error: "No scrape data available for this URL."
          };
          scrapingResults.push(emptyResultEntry);
          return; // Next projectUrlItem
        }

        // If latestScrapeData exists, use its properties
        let structuredData = latestScrapeData.structured_data || {};
        
        // Fallback: if structuredData is empty and raw_markdown exists, try basic extraction
        // This should ideally be a last resort or handled by ensuring LLM always returns something, even if empty fields.
        if (Object.keys(structuredData).length === 0 && latestScrapeData.raw_markdown) {
          try {
            const markdown = latestScrapeData.raw_markdown;
            const titleMatch = markdown.match(/# (.*)/);
            if (titleMatch) structuredData.title = titleMatch[1];
            const priceMatch = markdown.match(/\$(\d+(\.\d+)?)/);
            if (priceMatch) structuredData.price = priceMatch[1];
            const descriptionMatch = markdown.match(/## Description\s+(.*?)(\n##|\n$)/s);
            if (descriptionMatch) structuredData.description = descriptionMatch[1].trim();
          } catch (e) {
            console.error('Error extracting data from markdown fallback:', e);
          }
        }

        // Data from the ScrapedSessionResponse (latestScrapeData)
        // The API transforms snake_case to camelCase, so tabular_data becomes tabularData
        const tabularData = latestScrapeData.tabularData || latestScrapeData.tabular_data || (Object.keys(structuredData).length > 0 ? [structuredData] : []);


        const fields = latestScrapeData.fields && latestScrapeData.fields.length > 0 
                       ? latestScrapeData.fields 
                       : conditions.split(',').map(field => field.trim());
        const display_format = latestScrapeData.display_format || displayFormatFromProjectUrl;
        const formatted_data = latestScrapeData.formatted_tabular_data || null; // This is for paragraph/raw views

        // Create formatted results (simplified single-row summary for potential fallback display)
        // Include ALL selected fields, even if they don't have values in the first row
        const formattedResults = fields.map(field => {
          let value = '';

          // Try to get value from the first row of tabular data
          if (tabularData.length > 0 && tabularData[0] && typeof tabularData[0] === 'object') {
            value = tabularData[0][field] || '';
          }

          // If no value found in tabular data, try to get from structured data
          if (!value && structuredData && typeof structuredData === 'object') {
            value = structuredData[field] || '';
          }

          return {
            title: field,
            value: value
          };
        });

        // Only add fallback metadata if no meaningful content was extracted and no tabularData exists
        // This prevents unwanted metadata tables when actual content is available
        if (formattedResults.length === 0 && (!tabularData || tabularData.length === 0)) {
          // Don't create metadata tables - let the component handle empty state gracefully
        }

        // Create a scraping result entry
        const resultEntry = {
          url: projectUrlItem.url, // URL from the project_urls table entry
          conditions: conditions,    // Conditions from the project_urls table entry
          results: formattedResults, // Simplified single-row summary
          tabularData: tabularData,  // Actual tabular data from scrape session
          fields: fields,            // Fields from scrape session or conditions
          display_format: display_format, // Display format from scrape session or project_urls
          formatted_data: formatted_data, // Pre-formatted data for paragraph/raw views
          structuredData: structuredData, // Full structured JSON from scrape session
          project_id: projectId,
          session_id: latestScrapeData.id // ID of the scrape session
        };



        scrapingResults.push(resultEntry);

        // IMPORTANT: We removed the code that creates history entries to avoid recreating deleted history items
      });

      // Get the existing project from the projects state to preserve history items
      const existingProject = projects.find(p => p.id === projectId);

      // Create the data object to update the project - IMPORTANT: Don't include URLs here
      const projectData = {
        scrapingResults: scrapingResults,
        // Preserve the existing history items to avoid losing deleted history items
        // If history is null or empty array, keep it as is to ensure proper display
        history: existingProject?.history
      };

      // Cache the data
      setSessionsCache(prevCache => ({
        ...prevCache,
        [projectId]: projectData
      }));

      // Update the project with the fetched data
      updateProjectById(projectId, projectData);

      // Hide loading state
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching scraping sessions:', error);
      setIsLoading(false);
    }
  }, [projects, sessionsCache]); // Dependencies for useCallback

  const handleSelectProject = (projectId) => {
    setActiveProjectId(projectId);
    setActiveTab('urls');

    // Fetch scraping sessions for the selected project
    fetchScrapingSessions(projectId);
  };

  const handleDeleteProject = (projectId) => {
    const project = projects.find(p => p.id === projectId);
    setProjectToDelete(project);
    setIsDeleteProjectModalOpen(true);
  };

  const confirmDeleteProject = async () => {
    if (!projectToDelete) return;

    try {
      setIsDeletingProject(true);

      // Call the backend API to delete the project
      await deleteProject(projectToDelete.id);

      // Update the frontend state
      setProjects(prevProjects => prevProjects.filter(p => p.id !== projectToDelete.id));

      // If the active project is being deleted, reset the active project
      if (activeProjectId === projectToDelete.id) {
        setActiveProjectId(null);
        setActiveTab('projects');
      }

      // Clear the cache for this project
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[projectToDelete.id];
        return newCache;
      });

      // Close the modal
      setIsDeleteProjectModalOpen(false);
      setProjectToDelete(null);
    } catch (error) {
      console.error('Error deleting project:', error);
      alert('Failed to delete project. Please try again.');
    } finally {
      setIsDeletingProject(false);
    }
  };

  const updateProjectById = (projectId, updates) => {
    setProjects(prevProjects =>
      prevProjects.map(p =>
        p.id === projectId ? { ...p, ...updates } : p
      )
    );
  };

  const handleUpdateProjectName = (projectId, newName) => {
    updateProjectById(projectId, { name: newName.trim() });
  };


  const handleEnableRag = async (projectId, sessionId) => {
    try {
      console.log(`Enabling RAG for project ${projectId} with session ${sessionId}`);

      // Update project RAG status to enabled
      await updateProjectRAGStatus(projectId, true);

      // Update local state immediately to reflect the change
      updateProjectById(projectId, { ragStatus: 'enabled' });

      // Call the enable-rag endpoint to process the data
      const ragResponse = await fetch(`${API_URL}/projects/${projectId}/enable-rag`, {
        method: 'POST'
      });

      if (!ragResponse.ok) {
        throw new Error('Failed to process RAG data');
      }

      // Clear the cache for this project to force fresh data fetch
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[projectId];
        return newCache;
      });

      // Fetch sessions to update UI and show RAG status
      // This will also update the ragStatus based on the fresh data from the server
      fetchScrapingSessions(projectId);

      alert('RAG has been successfully enabled for this project! You can now use the chat feature to query your scraped data.');

    } catch (error) {
      console.error('Error enabling RAG:', error);
      // Revert the local state since the operation failed
      updateProjectById(projectId, { ragStatus: 'disabled' });
      alert(`Failed to enable RAG: ${error.message}`);
    }
  };

  const handleRagDecision = async (projectId, decision) => {
    // Don't update local state immediately - let fetchScrapingSessions handle it
    setIsRagPromptModalOpen(false);
    setProjectToPromptRagId(null);

    // Call the backend API to update the project's RAG status
    try {
      const ragEnabled = decision === 'enabled';

      // Update RAG status at the project level
      await updateProjectRAGStatus(projectId, ragEnabled);

      // Update local state immediately to reflect the change
      updateProjectById(projectId, { ragStatus: ragEnabled ? 'enabled' : 'disabled' });

      if (ragEnabled) {
        console.log(`RAG enabled for project ${projectId}. All existing and future data will be considered for RAG.`);

        // Call the enable-rag endpoint to process the data
        const ragResponse = await fetch(`${API_URL}/projects/${projectId}/enable-rag`, {
          method: 'POST'
        });

        if (!ragResponse.ok) {
          throw new Error('Failed to process RAG data');
        }

        // Clear the cache for this project to force fresh data fetch
        setSessionsCache(prevCache => {
          const newCache = { ...prevCache };
          delete newCache[projectId];
          return newCache;
        });

        // Fetch sessions to update UI
        fetchScrapingSessions(projectId);
      } else {
        console.log(`RAG disabled for project ${projectId}.`);
      }
    } catch (error) {
      console.error('Error updating RAG status:', error);
      // Revert the local state since the operation failed
      const revertStatus = decision === 'enabled' ? 'disabled' : 'enabled';
      updateProjectById(projectId, { ragStatus: revertStatus });
    }
  };

  const handleSendMessage = async (userMessage, callback) => {
    if (!activeProject || activeProject.ragStatus !== 'enabled') {
      console.log('RAG not enabled for this project, cannot send message');
      if (callback) callback();
      return;
    }

    // Create a conversation if none exists
    let conversationIdToUse = currentConversationId;
    if (!conversationIdToUse) {
      console.log('No conversation ID found, creating a new conversation...');
      conversationIdToUse = await createNewConversation();
      console.log('New conversation created with ID:', conversationIdToUse);
      if (!conversationIdToUse) {
        console.error('Failed to create a new conversation');
        if (callback) callback();
        return;
      }
    }

    try {
      console.log('Sending message with conversation ID:', conversationIdToUse);
      console.log('Message content:', userMessage);

      // Set the current conversation ID
      setCurrentConversationId(conversationIdToUse);

      // Update UI immediately with user message
      const tempUserMessage = {
        id: 'temp-' + Date.now(),
        role: 'user',
        content: userMessage,
        timestamp: new Date()
      };
      setChatMessages(prev => [...prev, tempUserMessage]);

      // Use the proper chat API that saves messages to database
      const response = await sendChatMessage(
        activeProjectId,
        userMessage,
        conversationIdToUse
      );

      console.log('Response from chat API:', response);

      // Remove the temporary user message and add the real messages
      setChatMessages(prev => prev.filter(msg => msg.id !== tempUserMessage.id));

      // Reload messages from database to get the saved conversation
      await loadChatMessages(conversationIdToUse);

      // Reload conversations to get updated titles (especially for first message)
      await loadConversations();

      // Call the callback to hide typing indicator
      if (callback) callback();

    } catch (error) {
      console.error('Error sending message:', error);
      // Add an error message
      setChatMessages(prev => [...prev, {
        id: 'error-' + Date.now(),
        role: 'system',
        content: `Error: ${error.message || 'Failed to send message'}`,
        timestamp: new Date(),
        isError: true
      }]);

      // Call the callback to hide typing indicator
      if (callback) callback();
    }
  };



  const loadConversations = useCallback(async () => {
    if (!activeProjectId) return;

    try {
      const conversations = await getProjectConversations(activeProjectId);
      setConversations(prev => ({
        ...prev,
        [activeProjectId]: conversations || []
      }));
    } catch (error) {
      console.error('Error loading conversations:', error);
    }
  }, [activeProjectId]);

  const createNewConversation = useCallback(async () => {
    if (!activeProjectId) return;

    try {
      console.log('Creating new conversation for project:', activeProjectId);
      const response = await createConversation(activeProjectId);
      console.log('New conversation created:', response);
      const newConversationId = response.conversation_id;
      setCurrentConversationId(newConversationId);
      await loadConversations();
      setChatMessages([]);
      return newConversationId; // Return the new conversation ID for immediate use
    } catch (error) {
      console.error('Error creating conversation:', error);
      return null;
    }
  }, [activeProjectId, loadConversations]);

  const switchConversation = useCallback(async (conversationId) => {
    setCurrentConversationId(conversationId);
    await loadChatMessages(conversationId);
  }, [loadChatMessages]);

  const handleDeleteConversation = useCallback(async (conversationId) => {
    if (!activeProjectId) return;

    try {
      await deleteConversation(activeProjectId, conversationId);

      // If we deleted the current conversation, clear it
      if (currentConversationId === conversationId) {
        setCurrentConversationId(null);
        setChatMessages([]);
      }

      // Reload conversations
      await loadConversations();
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  }, [activeProjectId, currentConversationId, loadConversations]);

  const handleAddUrl = async (newUrlData) => {
    if (!activeProject) return;

    try {
      // Call the backend API to create a new URL
      const response = await fetch(`${API_URL}/projects/${activeProjectId}/urls`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: newUrlData.url,
          conditions: newUrlData.conditions,
          display_format: newUrlData.display_format || 'table',
          project_id: activeProjectId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to add URL');
      }

      // Get the created URL from the response
      const createdUrl = await response.json();
      console.log("Created URL:", createdUrl);

      // Add the new URL to the frontend state
      const newUrlEntry = {
        id: createdUrl.id, // Use the UUID from the backend
        url: createdUrl.url,
        status: "pending",
        conditions: createdUrl.conditions,
        display_format: createdUrl.display_format
      };

      updateProjectById(activeProjectId, {
        urls: [...activeProject.urls, newUrlEntry],
        isScrapingError: false,
        errorMessage: ''
      });
    } catch (error) {
      console.error('Error adding URL:', error);
      alert('Failed to add URL. Please try again.');

      // If the API call fails, still add the URL to the frontend state
      // with a temporary ID that will be replaced when the page is refreshed
      const generateUUID = () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = (Math.random() * 16) | 0, v = c === 'x' ? r : ((r & 0x3) | 0x8);
          return v.toString(16);
        });
      };

      const newId = generateUUID();
      const newUrlEntry = {
        id: newId,
        url: newUrlData.url,
        status: "pending",
        conditions: newUrlData.conditions,
        display_format: newUrlData.display_format || 'table'
      };

      updateProjectById(activeProjectId, {
        urls: [...activeProject.urls, newUrlEntry],
        isScrapingError: false,
        errorMessage: ''
      });
    }
  };

  const handleRemoveAllUrls = () => {
    if (!activeProject) return;
    setIsRemoveAllUrlsModalOpen(true);
  };

  const confirmRemoveAllUrls = async () => {
    if (!activeProject) return;

    try {
      setIsDeletingUrls(true);

      // Call the backend API to delete all URLs for this project
      const response = await fetch(`${API_URL}/projects/${activeProjectId}/urls`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to remove URLs');
      }

      // Update the frontend state
      updateProjectById(activeProjectId, {
        urls: [],
        scrapingResults: null,
        isScrapingError: false,
        errorMessage: '',
        history: null // Set history to null when all URLs are removed
      });

      // Clear the cache for this project
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[activeProjectId];
        return newCache;
      });

      // Close the modal
      setIsRemoveAllUrlsModalOpen(false);
    } catch (error) {
      console.error('Error removing URLs:', error);
      alert('Failed to remove URLs. Please try again.');
    } finally {
      setIsDeletingUrls(false);
    }
  };

  const handleDeleteUrl = (urlId) => {
    if (!activeProject) return;
    const url = activeProject.urls.find(u => u.id === urlId);
    setUrlToDelete(url);
    setIsDeleteUrlModalOpen(true);
  };

  const confirmDeleteUrl = async () => {
    if (!activeProject || !urlToDelete) return;

    try {
      setIsDeletingUrl(true);

      console.log("Deleting URL with ID:", urlToDelete.id);

      // Call the backend API to delete the URL first
      try {
        // Use the UUID from the backend
        const urlId = urlToDelete.id;
        console.log("Sending DELETE request for URL ID:", urlId);

        const response = await fetch(`${API_URL}/projects/${activeProjectId}/urls/${urlId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          console.warn('Failed to delete URL from backend');
          console.warn('Response status:', response.status);
          const errorText = await response.text();
          console.warn('Error text:', errorText);
          throw new Error('Failed to delete URL from backend');
        } else {
          console.log("Successfully deleted URL from backend");
        }
      } catch (apiError) {
        console.warn('API error when deleting URL:', apiError);
        throw apiError; // Re-throw to be caught by the outer try/catch
      }

      // Update the frontend state after successful backend deletion
      const updatedUrls = activeProject.urls.filter(u => u.id !== urlToDelete.id);

      // Also remove any scraping results for this URL
      const updatedScrapingResults = activeProject.scrapingResults
        ? activeProject.scrapingResults.filter(r => r.url !== urlToDelete.url)
        : null;

      // Update the frontend state
      updateProjectById(activeProjectId, {
        urls: updatedUrls,
        scrapingResults: updatedScrapingResults,
        // If all URLs are deleted, set history to null
        ...(updatedUrls.length === 0 ? { history: null } : {})
      });

      // Close the modal
      setIsDeleteUrlModalOpen(false);
      setUrlToDelete(null);

      // Clear the cache for this project to force a fresh fetch
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[activeProjectId];
        return newCache;
      });

      // Refresh the data from the backend
      fetchScrapingSessions(activeProjectId);
      fetchProjectUrls(activeProjectId);

      // Show success message
      alert('URL and all associated data have been successfully deleted.');
    } catch (error) {
      console.error('Error deleting URL:', error);
      alert('Failed to delete URL. Please try again.');
    } finally {
      setIsDeletingUrl(false);
    }
  };

  const handleDeleteScrapingResult = (resultIndex) => {
    if (!activeProject || !activeProject.scrapingResults) return;
    const result = activeProject.scrapingResults[resultIndex];
    setScrapingResultToDelete(result);
    setIsDeleteScrapingResultModalOpen(true);
  };

  const confirmDeleteScrapingResult = async () => {
    if (!activeProject || !scrapingResultToDelete) return;

    try {
      setIsDeletingScrapingResult(true);

      // Update the frontend state regardless of backend success
      const updatedScrapingResults = activeProject.scrapingResults.filter(r => r !== scrapingResultToDelete);

      // Call the backend API to delete the scraping result if session_id is available
      if (scrapingResultToDelete.session_id) {
        try {
          const response = await fetch(`${API_URL}/projects/${activeProjectId}/sessions/${scrapingResultToDelete.session_id}`, {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          if (!response.ok) {
            console.warn('Failed to delete scraping result from backend, but frontend state will still be updated');
          }
        } catch (apiError) {
          console.warn('API error when deleting scraping result:', apiError);
        }
      }

      // Update the frontend state
      updateProjectById(activeProjectId, {
        scrapingResults: updatedScrapingResults.length > 0 ? updatedScrapingResults : null,
      });

      // Clear the cache for this project to force a fresh fetch
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[activeProjectId];
        return newCache;
      });

      // Close the modal
      setIsDeleteScrapingResultModalOpen(false);
      setScrapingResultToDelete(null);
    } catch (error) {
      console.error('Error deleting scraping result:', error);
      alert('Failed to delete scraping result. Please try again.');
    } finally {
      setIsDeletingScrapingResult(false);
    }
  };

  const handleStartScraping = async () => {
    if (!activeProject || activeProject.urls.length === 0) {
      updateProjectById(activeProjectId, {
        isScrapingError: true,
        errorMessage: 'No URLs to scrape. Please add at least one URL.',
        scrapingResults: null,
      });
      return;
    }

    // Initial UI update: set all URLs to "processing"
    const processingUrls = activeProject.urls.map(url => ({ ...url, status: "processing" }));
    updateProjectById(activeProjectId, { 
      urls: processingUrls,
      scrapingResults: null, // Clear previous results
      isScrapingError: false, 
      errorMessage: '' 
    });

    const cachingEnabled = localStorage.getItem('cachingEnabled') !== 'false';
    const newScrapingResults = [];
    let overallError = null;
    let allUrlsStatus = [...processingUrls]; // To keep track of individual URL statuses

    // Helper to generate UUID if not globally available
    const generateUUID = () => {
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = (Math.random() * 16) | 0, v = c === 'x' ? r : ((r & 0x3) | 0x8);
        return v.toString(16);
      });
    };

    for (let i = 0; i < activeProject.urls.length; i++) {
      const urlEntry = activeProject.urls[i];

      if (!urlEntry.conditions || urlEntry.conditions.trim() === "") {
        const errorMsg = `URL "${urlEntry.url}" is missing scraping conditions.`;
        overallError = overallError ? `${overallError}\n${errorMsg}` : errorMsg;
        allUrlsStatus = allUrlsStatus.map(u => u.id === urlEntry.id ? { ...u, status: "failed" } : u);
        newScrapingResults.push({
          url: urlEntry.url,
          conditions: urlEntry.conditions,
          error: "Missing scraping conditions.",
          display_format: urlEntry.display_format || 'table',
        });
        continue; 
      }

      try {
        const sessionId = generateUUID();
        // Make sure executeScrape is called with correct parameters from urlEntry
        const result = await executeScrape(
          activeProjectId,
          urlEntry.url,
          sessionId, // This sessionId is for the request, backend generates its own for the session record
          !cachingEnabled, // forceRefresh
          urlEntry.display_format || 'table',
          urlEntry.conditions
        );
        
        console.log(`Scraping result for ${urlEntry.url}:`, result); // Log the raw API result

        const currentTabularData = result.tabularData || [];
        const currentFields = result.fields || [];
        const currentDisplayFormat = result.displayFormat || urlEntry.display_format || 'table';
        const currentFormattedData = result.formattedData || null;
        const currentSessionId = result.id || sessionId;
        const currentRagStatus = result.ragStatus;

        // Log what's actually being used to build the newScrapingResults entry
        console.log(`For URL ${urlEntry.url} - Preparing resultEntry with:`);
        console.log(`  tabularData (${currentTabularData ? currentTabularData.length : 'undefined'} items):`, currentTabularData);
        console.log(`  fields (${currentFields ? currentFields.length : 'undefined'} items):`, currentFields);
        console.log(`  display_format:`, currentDisplayFormat);


        newScrapingResults.push({
          url: urlEntry.url,
          conditions: urlEntry.conditions,
          tabularData: currentTabularData,
          fields: currentFields,
          display_format: currentDisplayFormat,
          formatted_data: currentFormattedData, 
          // Add structuredData here for consistency with fetchScrapingSessions if possible,
          // though it's not directly in the executeScrape response.
          // For now, URLsManagement relies on tabularData primarily for fresh scrapes.
          // structuredData: result.structuredData, // 'result' from executeScrape doesn't have a top-level structuredData field.
                                                 // The full LLM output is effectively what becomes tabularData or is in formattedData.
          project_id: activeProjectId, 
          session_id: currentSessionId 
        });
        
        // Handle status updates more intelligently
        if (currentRagStatus === "Processing for RAG") {
          // Set to processing_rag and set up refresh
          allUrlsStatus = allUrlsStatus.map(u =>
            u.id === urlEntry.id ? { ...u, status: "processing_rag" } : u
          );

          console.log(`Setting up delayed refresh for ${urlEntry.url} after RAG processing`);
          setTimeout(() => {
            console.log(`Refreshing status for ${urlEntry.url} after RAG processing delay`);
            fetchProjectUrls(activeProjectId);
          }, 8000); // Refresh after 8 seconds to get the updated status
        } else {
          // For non-RAG or completed RAG, set to completed
          allUrlsStatus = allUrlsStatus.map(u =>
            u.id === urlEntry.id ? { ...u, status: "completed" } : u
          );
        }

      } catch (error) {
        console.error(`Error scraping ${urlEntry.url}:`, error);
        const errorMsg = `Failed to scrape ${urlEntry.url}: ${error.message}`;
        overallError = overallError ? `${overallError}\n${errorMsg}` : errorMsg;
        allUrlsStatus = allUrlsStatus.map(u => u.id === urlEntry.id ? { ...u, status: "failed" } : u);
        newScrapingResults.push({
          url: urlEntry.url,
          conditions: urlEntry.conditions,
          error: error.message,
          display_format: urlEntry.display_format || 'table',
        });
      }
    }

    // Final state update
    const finalUpdates = {
      urls: allUrlsStatus, // Update with final statuses
      scrapingResults: newScrapingResults.length > 0 ? newScrapingResults : null,
      isScrapingError: !!overallError,
      errorMessage: overallError || '',
    };
    
    console.log("Final scrapingResults to be set in state:", finalUpdates.scrapingResults); // <-- THIS IS THE CRUCIAL LOG

    updateProjectById(activeProjectId, finalUpdates);

    if (newScrapingResults.filter(r => !r.error).length > 0 && !overallError) {
        const timestamp = new Date().toISOString();
        const newHistoryId = (activeProject.history?.length > 0 ? Math.max(...activeProject.history.map(h => h.id)) : 0) + 1;
        const newHistoryItem = {
            id: newHistoryId,
            timestamp: timestamp,
            url: `${activeProject.urls.length} URLs processed`,
            dataSize: "N/A", 
            itemsScraped: newScrapingResults.filter(r => !r.error).length,
            status: "completed",
        };
        finalUpdates.history = [newHistoryItem, ...(activeProject.history || [])];
    }
    
    updateProjectById(activeProjectId, finalUpdates);

    if (newScrapingResults.filter(r => !r.error).length > 0 && (activeProject.ragStatus === 'unprompted' || activeProject.ragStatus === 'prompt_later')) {
        setProjectToPromptRagId(activeProjectId);
        setIsRagPromptModalOpen(true);
    }
    
    setSessionsCache(prevCache => {
      const newCache = { ...prevCache };
      delete newCache[activeProjectId];
      return newCache;
    });
    console.log("Batch scraping operation completed successfully");
  };

  const handleDeleteHistoryItem = (historyItemId) => {
    if (!activeProject) return;
    const historyItem = activeProject.history?.find(item => item.id === historyItemId);
    setHistoryItemToDelete(historyItem);
    setIsDeleteHistoryItemModalOpen(true);
  };

  const confirmDeleteHistoryItem = async () => {
    if (!activeProject || !historyItemToDelete) return;

    try {
      setIsDeletingHistoryItem(true);

      // Delete the corresponding scraping session from the backend if session_id is available
      if (historyItemToDelete.session_id) {
        try {
          const response = await fetch(`${API_URL}/projects/${activeProjectId}/sessions/${historyItemToDelete.session_id}`, {
            method: 'DELETE',
            headers: {
              'Content-Type': 'application/json',
            },
          });

          if (!response.ok) {
            console.warn('Failed to delete scraping session from backend, but frontend state will still be updated');
          } else {
            console.log('Successfully deleted scraping session from backend');
          }
        } catch (apiError) {
          console.warn('API error when deleting scraping session:', apiError);
        }
      } else {
        console.warn('No session_id available for this history item, only updating frontend state');
      }

      // Even if the API call fails, we'll update the frontend state
      // In a real implementation, you would check response.ok

      // Update the frontend state
      const updatedHistory = activeProject.history?.filter(item => item.id !== historyItemToDelete.id) || [];
      // If the history array is empty after deletion, set it to null instead of an empty array
      // This ensures the "No scraping history yet" message is shown instead of empty columns
      updateProjectById(activeProjectId, { history: updatedHistory.length > 0 ? updatedHistory : null });

      // Clear the cache for this project to force a fresh fetch
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[activeProjectId];
        return newCache;
      });

      // Close the modal
      setIsDeleteHistoryItemModalOpen(false);
      setHistoryItemToDelete(null);
    } catch (error) {
      console.error('Error deleting history item:', error);

      // Even if the API call fails, we'll update the frontend state
      const updatedHistory = activeProject.history?.filter(item => item.id !== historyItemToDelete.id) || [];
      // If the history array is empty after deletion, set it to null instead of an empty array
      updateProjectById(activeProjectId, { history: updatedHistory.length > 0 ? updatedHistory : null });

      // Clear the cache for this project to force a fresh fetch
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[activeProjectId];
        return newCache;
      });

      // Close the modal
      setIsDeleteHistoryItemModalOpen(false);
      setHistoryItemToDelete(null);
    } finally {
      setIsDeletingHistoryItem(false);
    }
  };

  const openSettingsModal = () => setIsSettingsModalOpen(true);
  const closeSettingsModal = () => setIsSettingsModalOpen(false);

  useEffect(() => {
    if (!activeProjectId && activeTab !== 'projects' && activeTab !== 'settings') {
      setActiveTab('projects');
    }
    if (activeProjectId && activeTab === 'projects') {
        setActiveTab('urls');
    }
  }, [activeProjectId, activeTab]);

  // Fetch URLs from the backend
  const fetchProjectUrls = useCallback(async (projectId) => {
    try {
      const response = await fetch(`${API_URL}/projects/${projectId}/urls`);
      if (!response.ok) {
        throw new Error('Failed to fetch URLs');
      }

      const urls = await response.json();
      console.log("Fetched URLs from backend:", urls);

      // Update the project with the URLs from the backend
      if (urls && urls.length > 0) {
        console.log("Processing URLs from backend:", urls);

        updateProjectById(projectId, {
          urls: urls.map(url => {
            console.log(`URL ${url.url} has backend status: ${url.status}`);
            return {
              id: url.id, // Use the UUID from the backend
              url: url.url,
              // Use the status from the backend API response
              status: url.status || "pending",
              conditions: url.conditions,
              display_format: url.display_format
            };
          })
        });
      } else if (urls && urls.length === 0) {
        // If there are no URLs, make sure to set the history to null
        const existingProject = projects.find(p => p.id === projectId);
        if (existingProject && existingProject.urls && existingProject.urls.length === 0) {
          updateProjectById(projectId, {
            urls: [],
            history: null
          });
        }
      }
    } catch (error) {
      console.error('Error fetching URLs:', error);
    }
  }, [projects]); // Dependencies for useCallback

  // Fetch scraping sessions and URLs when activeProjectId changes
  useEffect(() => {
    if (activeProjectId) {
      console.log("Active project changed, fetching data for:", activeProjectId);
      fetchScrapingSessions(activeProjectId);
      fetchProjectUrls(activeProjectId);
    }
  }, [activeProjectId]); // Only depend on activeProjectId to avoid infinite loops

  const renderActivePanel = () => {
    const currentActiveProject = projects.find(p => p.id === activeProjectId);

    if (!currentActiveProject && activeTab !== 'projects' && activeTab !== 'settings') {
      return <ProjectsPanel
                projects={projects}
                onAddProject={handleAddProject}
                onSelectProject={handleSelectProject}
                onDeleteProject={handleDeleteProject}
                onUpdateProjectName={handleUpdateProjectName}
                activeProjectId={activeProjectId}
              />;
    }

    switch (activeTab) {
      case 'projects':
        return (
          <ProjectsPanel
            projects={projects}
            onAddProject={handleAddProject}
            onSelectProject={handleSelectProject}
            onDeleteProject={handleDeleteProject}
            onUpdateProjectName={handleUpdateProjectName}
            activeProjectId={activeProjectId}
          />
        );
      case 'urls':
        return currentActiveProject ? (
          <URLManagement
            key={currentActiveProject.id + '-urls'}
            urls={currentActiveProject.urls}
            scrapingResults={currentActiveProject.scrapingResults}
            isScrapingError={currentActiveProject.isScrapingError}
            errorMessage={currentActiveProject.errorMessage}
            onAddUrl={handleAddUrl}
            onRemoveAllUrls={handleRemoveAllUrls}
            onStartScraping={handleStartScraping}
            onDeleteUrl={handleDeleteUrl}
            onDeleteScrapingResult={handleDeleteScrapingResult}
            onOpenSettings={openSettingsModal}
            projectName={currentActiveProject.name}
            onUpdateDisplayFormat={(resultIndex, newFormat) => {
              const updatedScrapingResults = [...currentActiveProject.scrapingResults];
              if (updatedScrapingResults[resultIndex]) {
                updatedScrapingResults[resultIndex].display_format = newFormat;
                updateProjectById(activeProjectId, { scrapingResults: updatedScrapingResults });
              }
            }}
            onEnableRag={handleEnableRag}
            projectRagStatus={currentActiveProject.ragStatus}
          />
        ) : (<div className="p-6 text-center text-purple-300">Please select or create a project to manage URLs.</div>);
      case 'chat':
        return currentActiveProject ? (
           <ChatPanel
             key={currentActiveProject.id + '-chat'}
             isRagMode={currentActiveProject.ragStatus === 'enabled'}
             onSendMessage={handleSendMessage}
             conversations={conversations[activeProjectId] || []}
             currentConversationId={currentConversationId}
             chatMessages={chatMessages}
             onCreateConversation={createNewConversation}
             onSwitchConversation={switchConversation}
             onDeleteConversation={(conversationId) => handleDeleteConversation(conversationId)}
             projectName={currentActiveProject.name}
            />
        ) : (<div className="p-6 text-center text-purple-300">Please select a project to use the chat.</div>);
      case 'history':
        return currentActiveProject ? (
            <HistoryPanel
              key={currentActiveProject.id + '-history'}
              scrapingHistory={currentActiveProject.history}
              projectName={currentActiveProject.name}
              onDeleteHistoryItem={handleDeleteHistoryItem}
            />
        ) : (<div className="p-6 text-center text-purple-300">Please select a project to view its history.</div>);
      case 'rag':
        return currentActiveProject ? (
            <RagManagement
              key={currentActiveProject.id + '-rag'}
              projectId={currentActiveProject.id}
              onStatusUpdate={(status) => {
                // Update project RAG status when RAG status changes
                if (status.rag_enabled !== undefined) {
                  updateProjectById(currentActiveProject.id, {
                    ragStatus: status.rag_enabled ? 'enabled' : 'disabled'
                  });
                }
              }}
            />
        ) : (<div className="p-6 text-center text-purple-300">Please select a project to manage RAG.</div>);
      default:
        if (activeTab !== 'settings') {
            setActiveTab('projects');
        }
        return null;
    }
  };

  const navigateToProjects = () => {
    setActiveProjectId(null);
    setActiveTab('projects');
  };

  const projectForModal = projects.find(p => p.id === projectToPromptRagId);

  return (
    <div className="flex flex-col h-screen bg-purple-900 text-white">
      <header className="glass-dark border-b border-purple-500/30 p-4 shadow-2xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg">
              <Folder className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">
                Web Scraper
              </h1>
              {activeProject && (
                <p className="text-sm text-purple-300">
                  {activeProject.name}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 px-4 py-2 glass-dark rounded-lg border border-purple-500/30">
              <Database size={16} className="text-purple-300" />
              <span className="text-white text-sm font-medium">AI: Azure OpenAI GPT-4o</span>
            </div>
            <button
              onClick={openSettingsModal}
              data-settings-button
              className="btn-secondary flex items-center space-x-2 px-4 py-2"
            >
              <Settings size={18} />
              <span>Settings</span>
            </button>
            <div className="relative w-10 h-10 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
              <span className="font-bold text-white">U</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-16 glass-dark flex flex-col items-center py-4 border-r border-purple-500/30">
          <button
            onClick={navigateToProjects}
            className={`p-3 rounded-xl mb-4 transition-all duration-200 ${
              activeTab === 'projects' && !activeProjectId
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg'
                : 'hover:bg-purple-700/50'
            }`}
            title="Projects"
          >
            <Home size={20} className="text-white" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('urls') : alert("Please select or create a project first.")}
            className={`p-3 rounded-xl mb-4 transition-all duration-200 ${
              activeTab === 'urls' && activeProjectId
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg'
                : 'hover:bg-purple-700/50'
            } ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
            title="URL Management"
            disabled={!activeProjectId}
          >
            <Globe size={20} className="text-white" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('chat') : alert("Please select or create a project first.")}
            className={`p-3 rounded-xl mb-4 transition-all duration-200 ${
              activeTab === 'chat' && activeProjectId
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg'
                : 'hover:bg-purple-700/50'
            } ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
             title="Chat"
             disabled={!activeProjectId}
          >
            <MessageCircle size={20} className="text-white" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('history') : alert("Please select or create a project first.")}
            className={`p-3 rounded-xl mb-4 transition-all duration-200 ${
              activeTab === 'history' && activeProjectId
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg'
                : 'hover:bg-purple-700/50'
            } ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
             title="History"
             disabled={!activeProjectId}
          >
            <Clock size={20} className="text-white" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('rag') : alert("Please select or create a project first.")}
            className={`p-3 rounded-xl mb-4 transition-all duration-200 ${
              activeTab === 'rag' && activeProjectId
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 shadow-lg'
                : 'hover:bg-purple-700/50'
            } ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
             title="RAG Management"
             disabled={!activeProjectId}
          >
            <Brain size={20} className="text-white" />
          </button>
          <div className="flex-1"></div>
          <button className="p-3 rounded-xl hover:bg-purple-700/50 transition-all duration-200" title="Help/Info">
            <AlertCircle size={20} className="text-purple-300" />
          </button>
        </div>

        <div className="flex-1 flex flex-col bg-gradient-to-br from-purple-900 to-indigo-900 overflow-hidden relative">
           <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {[...Array(50)].map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full bg-white"
                style={{
                  width: Math.random() * 3 + 'px',
                  height: Math.random() * 3 + 'px',
                  top: Math.random() * 100 + '%',
                  left: Math.random() * 100 + '%',
                  opacity: Math.random() * 0.8
                }}
              ></div>
            ))}
          </div>
           <div className="relative z-10 flex flex-col flex-1 overflow-hidden">
             {isLoading && (
               <div className="absolute inset-0 bg-purple-900 bg-opacity-70 flex items-center justify-center z-50">
                 <div className="flex flex-col items-center">
                   <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                   <p className="mt-4 text-indigo-300 font-medium">Loading data...</p>
                 </div>
               </div>
             )}
             {renderActivePanel()}
           </div>
        </div>
      </div>

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={closeSettingsModal}
      />
      {projectForModal && (
        <RagPromptModal
          isOpen={isRagPromptModalOpen && projectToPromptRagId === projectForModal.id}
          onClose={() => {
            if (projectForModal.ragStatus === 'unprompted') {
              handleRagDecision(projectForModal.id, 'prompt_later');
            } else {
               setIsRagPromptModalOpen(false);
               setProjectToPromptRagId(null);
            }
          }}
          onDecision={(decision) => handleRagDecision(projectForModal.id, decision)}
          projectName={projectForModal.name}
        />
      )}

      {/* Project Deletion Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteProjectModalOpen}
        onClose={() => {
          setIsDeleteProjectModalOpen(false);
          setProjectToDelete(null);
        }}
        onConfirm={confirmDeleteProject}
        title="Delete Project?"
        message={projectToDelete ? `Are you sure you want to delete "${projectToDelete.name}"? This will permanently delete all associated data including URLs, scraping results, and history.` : ''}
        confirmButtonText="Delete Project"
        isDeleting={isDeletingProject}
        itemName={projectToDelete?.name}
        itemType="project"
      />

      {/* Remove All URLs Confirmation Modal */}
      <ConfirmationModal
        isOpen={isRemoveAllUrlsModalOpen}
        onClose={() => setIsRemoveAllUrlsModalOpen(false)}
        onConfirm={confirmRemoveAllUrls}
        title="Remove All URLs?"
        message={`Are you sure you want to remove all URLs from project "${activeProject?.name}"? This will also remove all associated scraping results.`}
        confirmButtonText="Remove All"
        isDeleting={isDeletingUrls}
        itemType="URLs"
      />

      {/* History Item Deletion Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteHistoryItemModalOpen}
        onClose={() => {
          setIsDeleteHistoryItemModalOpen(false);
          setHistoryItemToDelete(null);
        }}
        onConfirm={confirmDeleteHistoryItem}
        title="Delete History Item?"
        message="Are you sure you want to delete this history item? This action cannot be undone."
        confirmButtonText="Delete Item"
        isDeleting={isDeletingHistoryItem}
        itemType="history item"
      />

      {/* URL Deletion Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteUrlModalOpen}
        onClose={() => {
          setIsDeleteUrlModalOpen(false);
          setUrlToDelete(null);
        }}
        onConfirm={confirmDeleteUrl}
        title="Delete URL and All Associated Data?"
        message={urlToDelete ? `Are you sure you want to delete the URL "${urlToDelete.url}"? This will permanently delete:

1. The URL from your project
2. All scraped content and tables for this URL
3. All RAG data associated with this URL

This action cannot be undone.` : ''}
        confirmButtonText="Delete URL and All Data"
        isDeleting={isDeletingUrl}
        itemType="URL"
      />

      {/* Scraping Result Deletion Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteScrapingResultModalOpen}
        onClose={() => {
          setIsDeleteScrapingResultModalOpen(false);
          setScrapingResultToDelete(null);
        }}
        onConfirm={confirmDeleteScrapingResult}
        title="Delete Scraping Result?"
        message="Are you sure you want to delete this scraping result? This action cannot be undone."
        confirmButtonText="Delete Result"
        isDeleting={isDeletingScrapingResult}
        itemType="scraping result"
      />
    </div>
  );
}

export default WebScrapingDashboard;
