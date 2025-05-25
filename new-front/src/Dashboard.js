import { useState, useEffect } from 'react';
import { MessageCircle, Globe, Settings, AlertCircle, ChevronDown,
         Database, Clock, Folder, Home } from 'lucide-react';
import URLManagement from './URLsManagement';
import ChatPanel from './ChatPanel';
import HistoryPanel from './History';
import SettingsModal from './SettingsModal';
import ProjectsPanel from './ProjectsPanel';
import RagPromptModal from './RagPromptModal';
import ConfirmationModal from './ConfirmationModal';
import { executeScrape, queryRagApi } from './lib/api';

function WebScrapingDashboard() {
  const [projects, setProjects] = useState([]);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const activeProject = projects.find(p => p.id === activeProjectId);

  // Add loading state
  const [isLoading, setIsLoading] = useState(false);

  // Cache for scraping sessions to avoid redundant API calls
  const [sessionsCache, setSessionsCache] = useState({});

  // Fetch projects from the backend when the component mounts (only once)
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setIsLoading(true);
        const response = await fetch('http://localhost:8000/api/v1/projects');
        if (!response.ok) {
          throw new Error('Failed to fetch projects');
        }

        const data = await response.json();
        console.log('Fetched projects:', data);

        // Convert the backend projects to the format expected by the frontend
        // but don't reset the URLs, scrapingResults, and history if they already exist
        const formattedProjects = data.map(project => {
          // Find existing project data if available
          const existingProject = projects.find(p => p.id === project.id);

          return {
            id: project.id,
            name: project.name,
            // Keep existing data if available, otherwise initialize with empty arrays
            urls: existingProject?.urls || [],
            scrapingResults: existingProject?.scrapingResults || null,
            isScrapingError: existingProject?.isScrapingError || false,
            errorMessage: existingProject?.errorMessage || '',
            // Preserve null history to ensure "No history" message shows correctly
            history: existingProject?.history !== undefined ? existingProject.history : null,
            createdAt: project.created_at,
            ragStatus: project.rag_enabled ? 'enabled' : 'unprompted',
          };
        });

        setProjects(formattedProjects);
        setIsLoading(false);

        // If there's an active project, fetch its scraping sessions
        if (activeProjectId) {
          const activeProject = formattedProjects.find(p => p.id === activeProjectId);
          if (activeProject) {
            fetchScrapingSessions(activeProjectId);
          }
        }
      } catch (error) {
        console.error('Error fetching projects:', error);
        setIsLoading(false);
      }
    };

    fetchProjects();
  }, []); // Only run once when component mounts

  const [activeTab, setActiveTab] = useState('projects');
  const [selectedAiModel, setSelectedAiModel] = useState('gpt-4o-mini');
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
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

  const aiModels = [
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Faster, more efficient version' },
    { id: 'gpt-4o', name: 'GPT-4o', description: 'OpenAI\'s powerful multimodal model' },
    { id: 'gemini/gemini-2.0-flash', name: 'gemini/gemini-2.0-flash', description: 'Google\'s multimodal AI model' }
  ];

  const getSelectedModelName = () => {
    const model = aiModels.find(model => model.id === selectedAiModel);
    return model ? model.name : 'Unknown Model';
  };

  const handleAddProject = async (projectName) => {
    try {
      // Call the backend API to create a new project
      const response = await fetch('http://localhost:8000/api/v1/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: projectName,
          initial_urls: []
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create project');
      }

      const data = await response.json();
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
        ragStatus: data.rag_enabled ? 'enabled' : 'unprompted',
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

  const fetchScrapingSessions = async (projectId) => {
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
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/sessions`);
      if (!response.ok) {
        throw new Error('Failed to fetch scraping sessions');
      }

      const sessions = await response.json();
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
      const projectUrlsPromise = fetch(`http://localhost:8000/api/v1/projects/${projectId}/urls`)
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

      // Process each session
      sessions.forEach((session) => {
        // Find matching project URL if it exists
        const matchingUrl = projectUrls.find(url => url.url === session.url);

        // Get conditions and display format from matching URL or use defaults
        const conditions = matchingUrl ? matchingUrl.conditions : "title, description, price, content";
        const displayFormat = matchingUrl ? matchingUrl.display_format : "table";

        // Try to parse structured data from session (simplified)
        let structuredData = session.structured_data || {};

        // If no structured data, try to extract from raw_markdown
        if (Object.keys(structuredData).length === 0 && session.raw_markdown) {
          try {
            const markdown = session.raw_markdown;
            // Simple extraction of title
            const titleMatch = markdown.match(/# (.*)/);
            if (titleMatch) structuredData.title = titleMatch[1];

            // Extract price if available
            const priceMatch = markdown.match(/\$(\d+(\.\d+)?)/);
            if (priceMatch) structuredData.price = priceMatch[1];

            // Extract description if available
            const descriptionMatch = markdown.match(/## Description\s+(.*?)(\n##|\n$)/s);
            if (descriptionMatch) structuredData.description = descriptionMatch[1].trim();
          } catch (e) {
            console.error('Error extracting data from markdown:', e);
          }
        }

        // Use tabular_data from the backend if available, otherwise create it
        const tabularData = session.tabular_data || [structuredData];

        // Use fields from the backend if available, otherwise create them from conditions
        const fields = session.fields || conditions.split(',').map(field => field.trim());

        // Create formatted results (simplified)
        const formattedResults = fields
          .filter(field => {
            // Check if the field exists in the first row of tabular data
            return tabularData.length > 0 && tabularData[0][field];
          })
          .map(field => ({
            title: field,
            value: tabularData.length > 0 ? tabularData[0][field] : ''
          }));

        // If no results were found, add some default ones
        if (formattedResults.length === 0) {
          formattedResults.push({ title: "URL", value: session.url });
          formattedResults.push({ title: "Status", value: session.status });
          formattedResults.push({ title: "Scraped At", value: new Date(session.scraped_at).toLocaleString() });
        }

        // Create a scraping result entry
        const resultEntry = {
          url: session.url,
          conditions: conditions,
          results: formattedResults,
          tabularData: tabularData,
          fields: fields,
          display_format: displayFormat || session.display_format || 'table',
          formatted_data: session.formatted_tabular_data, // Use the formatted data from the backend
          project_id: projectId,
          session_id: session.id
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
  };

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
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectToDelete.id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete project');
      }

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


  const handleRagDecision = async (projectId, decision) => {
    // Update the local state
    updateProjectById(projectId, { ragStatus: decision });
    setIsRagPromptModalOpen(false);
    setProjectToPromptRagId(null);

    if (decision === 'enabled') {
      console.log(`RAG enabled for project ${projectId}. All existing and future data will be considered for RAG.`);

      // Call the backend API to update the project's RAG status
      try {
        const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            rag_enabled: true
          }),
        });

        if (!response.ok) {
          console.error('Failed to update RAG status on the backend');
        }
      } catch (error) {
        console.error('Error updating RAG status:', error);
      }
    }
  };

  const handleSendMessage = async (userMessage, modelName, addSystemResponseCallback) => {
    try {
      console.log('Using model:', modelName); // Log the model name being used
      
      if (activeProject && activeProject.ragStatus === 'enabled') {
        // Use our API client to query the RAG API
        const result = await queryRagApi(activeProjectId, userMessage, modelName);
        addSystemResponseCallback(result.answer);
      } else {
        // If RAG is not enabled, return an error message
        addSystemResponseCallback("Chat is disabled. Please enable RAG for this project to use the chat functionality.");
      }
    } catch (error) {
      console.error('Error sending message:', error);
      addSystemResponseCallback(`Error: ${error.message || 'Failed to process your request'}`);
    }
  };

  const handleAddUrl = async (newUrlData) => {
    if (!activeProject) return;

    try {
      // Call the backend API to create a new URL
      const response = await fetch(`http://localhost:8000/api/v1/projects/${activeProjectId}/urls`, {
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
          const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
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
      const response = await fetch(`http://localhost:8000/api/v1/projects/${activeProjectId}/urls`, {
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

        const response = await fetch(`http://localhost:8000/api/v1/projects/${activeProjectId}/urls/${urlId}`, {
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
          const response = await fetch(`http://localhost:8000/api/v1/projects/${activeProjectId}/sessions/${scrapingResultToDelete.session_id}`, {
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
    if (!activeProject) return;

    let baseUpdates = {
      scrapingResults: null,
      isScrapingError: false,
      errorMessage: '',
    };

    if (activeProject.urls.length === 0) {
      updateProjectById(activeProjectId, {
        ...baseUpdates,
        isScrapingError: true,
        errorMessage: 'No URLs to scrape. Please add at least one URL to the project.',
      });
      return;
    }

    // Get caching preference from localStorage
    const cachingEnabled = localStorage.getItem('cachingEnabled') !== 'false'; // Default to true if not set

    const urlsWithoutConditions = activeProject.urls.filter(url => !url.conditions || url.conditions.trim() === "");
    if (urlsWithoutConditions.length > 0) {
      updateProjectById(activeProjectId, {
        ...baseUpdates,
        isScrapingError: true,
        errorMessage: 'Error: Some URLs seem to be missing scraping conditions.',
      });
      console.error("Attempted to scrape with missing conditions:", urlsWithoutConditions);
      return;
    }

    try {
      // Update URLs to "processing" status
      const processingUrlsForProject = activeProject.urls.map(url => ({ ...url, status: "processing" }));
      updateProjectById(activeProjectId, {
        ...baseUpdates,
        urls: processingUrlsForProject,
      });

      // Use the real API to scrape the first URL
      const url = activeProject.urls[0].url;

      // Get the display format and conditions from the URL if available
      const displayFormat = activeProject.urls[0].display_format || 'table';
      const conditions = activeProject.urls[0].conditions || '';

      // Generate a proper UUID for the session ID
      const generateUUID = () => {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
      };

      const sessionId = generateUUID();

      // Call the API client to execute the scrape
      const result = await executeScrape(
        activeProjectId,
        url,
        sessionId,
        !cachingEnabled, // forceRefresh if caching is disabled
        displayFormat,
        conditions
      );
      
      console.log('Scraping result:', result);

      // Update URLs to "completed" status
      const updatedUrlsForProject = activeProject.urls.map(url => ({ ...url, status: "completed" }));

      // Process the real results from the backend
      const processedResults = updatedUrlsForProject.map(url => {
        // Get the fields from the result or from the URL conditions
        const fields = result.fields || url.conditions.split(',').map(field => field.trim());

        // Get the tabular data from the result or create a default one
        const tabularData = result.tabular_data || [];

        // Convert tabular data to the format expected by the frontend
        const formattedResults = [];

        if (tabularData.length > 0) {
          // For each field, create a result entry
          fields.forEach(field => {
            if (tabularData[0][field]) {
              formattedResults.push({
                title: field,
                value: tabularData[0][field]
              });
            }
          });
        }

        // If no results were found, add some default ones
        if (formattedResults.length === 0) {
          formattedResults.push({ title: "Title", value: "Scraped from " + url.url });
          formattedResults.push({ title: "Status", value: result.status });
          formattedResults.push({ title: "Message", value: result.message });
        }

        return {
          url: url.url,
          conditions: url.conditions,
          results: formattedResults,
          tabularData: tabularData,
          fields: fields
        };
      });

      const timestamp = new Date().toISOString();
      const newHistoryId = (activeProject.history && activeProject.history.length > 0 ? Math.max(...activeProject.history.map(h => h.id)) : 0) + 1;
      const newHistoryItem = {
        id: newHistoryId,
        timestamp: timestamp,
        url: updatedUrlsForProject.length === 1 ? updatedUrlsForProject[0].url : `${updatedUrlsForProject.length} URLs scraped`,
        dataSize: "1.0 MB",
        itemsScraped: updatedUrlsForProject.length,
        status: "completed",
        session_id: sessionId // Add session_id to connect history items with scraping sessions
      };

      const finalUpdatesForScraping = {
        ...baseUpdates,
        urls: updatedUrlsForProject,
        scrapingResults: processedResults,
        history: [newHistoryItem, ...(activeProject.history || [])],
      };

      setProjects(prevProjects => {
          const newProjects = prevProjects.map(p =>
              p.id === activeProjectId ? { ...p, ...finalUpdatesForScraping } : p
          );
          const projectAfterUpdate = newProjects.find(p => p.id === activeProjectId);
          if (projectAfterUpdate && (projectAfterUpdate.ragStatus === 'unprompted' || projectAfterUpdate.ragStatus === 'prompt_later')) {
              setProjectToPromptRagId(activeProjectId);
              setIsRagPromptModalOpen(true);
          }
          return newProjects;
      });

      // Clear the cache for this project to force a fresh fetch
      setSessionsCache(prevCache => {
        const newCache = { ...prevCache };
        delete newCache[activeProjectId];
        return newCache;
      });

      // We're no longer fetching scraping sessions after a scraping operation
      // This prevents the data in the table from disappearing
      // The scraping results are already in the project state from the API response
      console.log("Scraping operation completed successfully");
    } catch (error) {
      console.error('Error scraping URL:', error);
      updateProjectById(activeProjectId, {
        ...baseUpdates,
        isScrapingError: true,
        errorMessage: `Error: ${error.message || 'Failed to scrape URL'}`,
      });
    }
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
          const response = await fetch(`http://localhost:8000/api/v1/projects/${activeProjectId}/sessions/${historyItemToDelete.session_id}`, {
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
  const fetchProjectUrls = async (projectId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/urls`);
      if (!response.ok) {
        throw new Error('Failed to fetch URLs');
      }

      const urls = await response.json();
      console.log("Fetched URLs from backend:", urls);

      // Update the project with the URLs from the backend
      if (urls && urls.length > 0) {
        // Get the existing URLs to preserve their status
        const existingUrls = projects.find(p => p.id === projectId)?.urls || [];

        updateProjectById(projectId, {
          urls: urls.map(url => {
            // Find the existing URL to get its status
            const existingUrl = existingUrls.find(eu => eu.id === url.id);

            return {
              id: url.id, // Use the UUID from the backend
              url: url.url,
              // Preserve the existing status if available, otherwise use "pending"
              status: existingUrl?.status || "pending",
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
  };

  // Fetch scraping sessions and URLs when activeProjectId changes
  useEffect(() => {
    if (activeProjectId) {
      console.log("Active project changed, fetching data for:", activeProjectId);
      fetchScrapingSessions(activeProjectId);
      fetchProjectUrls(activeProjectId);
    }
  }, [activeProjectId]);

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
            projectName={currentActiveProject.name}
          />
        ) : (<div className="p-6 text-center text-purple-300">Please select or create a project to manage URLs.</div>);
      case 'chat':
        return currentActiveProject ? (
           <ChatPanel
             key={currentActiveProject.id + '-chat'}
             isRagMode={currentActiveProject.ragStatus === 'enabled'}
             selectedModelName={selectedAiModel}
             onSendMessage={handleSendMessage}
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
      <header className="bg-purple-800 p-4 shadow-lg border-b border-purple-600">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Folder className="text-purple-300" size={24} />
            <h1 className="text-2xl font-bold text-purple-200">
                Web Scraper {activeProject ? `/ ${activeProject.name}` : '/ Projects'}
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <button
                onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
                className="bg-purple-700 hover:bg-purple-600 p-2 rounded-lg flex items-center space-x-2"
              >
                <Database size={16} className="text-purple-300 mr-1" />
                <span>AI: {getSelectedModelName()}</span>
                <ChevronDown size={16} />
              </button>
              {isModelDropdownOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-purple-800 rounded-lg shadow-xl border border-purple-600 z-20">
                  <div className="p-2">
                    <h3 className="text-sm font-semibold text-purple-300 mb-2 px-2">Select AI Model</h3>
                    {aiModels.map(model => (
                      <button
                        key={model.id}
                        onClick={() => {
                          setSelectedAiModel(model.id);
                          setIsModelDropdownOpen(false);
                        }}
                        className={`w-full text-left p-2 rounded-md flex flex-col ${
                          selectedAiModel === model.id
                            ? 'bg-indigo-700'
                            : 'hover:bg-purple-700'
                        }`}
                      >
                        <span className="font-medium">{model.name}</span>
                        <span className="text-xs text-purple-300">{model.description}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <button
              onClick={openSettingsModal}
              className="bg-purple-700 hover:bg-purple-600 p-2 rounded-lg flex items-center space-x-2"
            >
              <Settings size={18} />
              <span>Settings</span>
            </button>
            <div className="relative w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
              <span className="font-bold">U</span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        <div className="w-16 bg-purple-800 flex flex-col items-center py-4 border-r border-purple-700">
          <button
            onClick={navigateToProjects}
            className={`p-3 rounded-lg mb-4 ${activeTab === 'projects' && !activeProjectId ? 'bg-purple-600' : 'hover:bg-purple-700'}`}
            title="Projects"
          >
            <Home size={20} className="text-purple-200" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('urls') : alert("Please select or create a project first.")}
            className={`p-3 rounded-lg mb-4 ${activeTab === 'urls' && activeProjectId ? 'bg-purple-600' : 'hover:bg-purple-700'} ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
            title="URL Management"
            disabled={!activeProjectId}
          >
            <Globe size={20} className="text-purple-200" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('chat') : alert("Please select or create a project first.")}
            className={`p-3 rounded-lg mb-4 ${activeTab === 'chat' && activeProjectId ? 'bg-purple-600' : 'hover:bg-purple-700'} ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
             title="Chat"
             disabled={!activeProjectId}
          >
            <MessageCircle size={20} className="text-purple-200" />
          </button>
          <button
            onClick={() => activeProjectId ? setActiveTab('history') : alert("Please select or create a project first.")}
            className={`p-3 rounded-lg mb-4 ${activeTab === 'history' && activeProjectId ? 'bg-purple-600' : 'hover:bg-purple-700'} ${!activeProjectId ? 'opacity-50 cursor-not-allowed' : ''}`}
             title="History"
             disabled={!activeProjectId}
          >
            <Clock size={20} className="text-purple-200" />
          </button>
          <div className="flex-1"></div>
          <button className="p-3 rounded-lg hover:bg-purple-700" title="Help/Info">
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