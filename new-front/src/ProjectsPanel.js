import { useState } from 'react';
import { FolderPlus, Trash2, Edit3, Check, X, Globe, Clock, Zap, CheckCircle, XCircle, HelpCircle, Folder as FolderIcon } from 'lucide-react';

function ProjectsPanel({ projects, onAddProject, onSelectProject, onDeleteProject, onUpdateProjectName, activeProjectId }) {
  const [newProjectName, setNewProjectName] = useState('');
  const [editingProjectId, setEditingProjectId] = useState(null);
  const [editingProjectNameText, setEditingProjectNameText] = useState('');

  const handleAdd = () => {
    if (newProjectName.trim()) {
      onAddProject(newProjectName.trim());
      setNewProjectName('');
    }
  };

  const handleEdit = (project) => {
    setEditingProjectId(project.id);
    setEditingProjectNameText(project.name);
  };

  const handleSaveEdit = (projectId) => {
    if (editingProjectNameText.trim()) {
      onUpdateProjectName(projectId, editingProjectNameText.trim());
    }
    setEditingProjectId(null);
    setEditingProjectNameText('');
  };

  const handleCancelEdit = () => {
    setEditingProjectId(null);
    setEditingProjectNameText('');
  };

  const getRagStatusDisplay = (status) => {
    switch (status) {
      case 'enabled':
        return { text: 'RAG Enabled', Icon: CheckCircle, color: 'text-green-400', bgColor: 'bg-green-900 bg-opacity-50' };
      case 'disabled':
        return { text: 'RAG Disabled', Icon: XCircle, color: 'text-red-400', bgColor: 'bg-red-900 bg-opacity-50' };
      case 'prompt_later':
        return { text: 'RAG: Decide Later', Icon: HelpCircle, color: 'text-yellow-400', bgColor: 'bg-yellow-900 bg-opacity-50' };
      case 'unprompted':
      default:
        return { text: 'RAG: Not Set', Icon: Zap, color: 'text-purple-400', bgColor: 'bg-purple-700 bg-opacity-40' };
    }
  };


  return (
    <div className="flex-1 p-6 overflow-auto">
      <h2 className="text-2xl font-semibold text-purple-200 mb-6">Your Projects</h2>

      <div className="glass-dark p-6 rounded-xl shadow-xl mb-8 border border-purple-500/30 animate-fadeIn">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <FolderPlus size={20} className="text-indigo-400" />
          Create New Project
        </h3>
        <div className="flex space-x-3">
          <input
            type="text"
            value={newProjectName}
            onChange={(e) => setNewProjectName(e.target.value)}
            placeholder="Enter project name"
            className="input-primary flex-grow"
            onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
          />
          <button
            onClick={handleAdd}
            className="btn-primary flex items-center space-x-2 px-6 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!newProjectName.trim()}
          >
            <FolderPlus size={18} />
            <span>Create</span>
          </button>
        </div>
      </div>

      {projects.length === 0 ? (
        <div className="text-center text-purple-300 py-16 animate-fadeIn">
          <FolderIcon size={64} className="mx-auto mb-6 text-purple-400" />
          <p className="text-xl font-medium mb-2">No projects yet</p>
          <p className="text-purple-400">Create your first project to get started!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {projects.map((project, index) => {
            const isEditing = editingProjectId === project.id;
            const { text: ragText, Icon: RagIcon, color: ragColor, bgColor: ragBgColor } = getRagStatusDisplay(project.ragStatus);

            return (
              <div
                key={project.id}
                className={`glass-dark rounded-xl shadow-xl flex flex-col justify-between aspect-square
                            border-2 transition-all duration-300 ease-in-out group card-hover animate-fadeIn
                            ${activeProjectId === project.id ? 'border-indigo-500 ring-2 ring-indigo-500 shadow-indigo-500/50' : 'border-purple-600/50 hover:border-purple-500'}`}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {isEditing ? (
                  <div className="p-4 flex flex-col h-full">
                    <input
                      type="text"
                      value={editingProjectNameText}
                      onChange={(e) => setEditingProjectNameText(e.target.value)}
                      className="w-full p-2 mb-3 rounded-md bg-purple-700 border border-purple-600 text-white placeholder-purple-400 focus:outline-none focus:ring-2 focus:ring-purple-400 text-sm"
                      autoFocus
                      onKeyPress={(e) => e.key === 'Enter' && handleSaveEdit(project.id)}
                    />
                    <div className="flex justify-end space-x-2 mt-auto">
                      <button onClick={() => handleSaveEdit(project.id)} className="p-2 text-green-400 hover:bg-green-700 rounded-md" title="Save">
                        <Check size={18} />
                      </button>
                      <button onClick={handleCancelEdit} className="p-2 text-red-400 hover:bg-red-700 rounded-md" title="Cancel">
                        <X size={18} />
                      </button>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <>
                    <div
                      className="p-4 flex-grow cursor-pointer overflow-hidden"
                      onClick={() => onSelectProject(project.id)}
                    >
                      <div className="flex justify-between items-start mb-2">
                          <h3
                            className="text-md font-semibold text-purple-100 group-hover:text-indigo-300 transition-colors break-all line-clamp-2"
                            title={project.name}
                           >
                            {project.name}
                          </h3>
                      </div>

                      <div className="space-y-1 text-xs text-purple-300 mt-2">
                        <div className="flex items-center" title={`${project.urls.length} URL(s)`}>
                          <Globe size={14} className="mr-2 text-purple-400 flex-shrink-0"/>
                          <span className="truncate">{project.urls.length} URL{project.urls.length !== 1 ? 's' : ''}</span>
                        </div>
                        <div className="flex items-center" title={`${project.history?.length || 0} History entr(ies)`}>
                          <Clock size={14} className="mr-2 text-purple-400 flex-shrink-0"/>
                           <span className="truncate">{project.history?.length || 0} Histor{(project.history?.length || 0) !== 1 ? 'ies' : 'y'}</span>
                        </div>
                        <div className={`flex items-center p-1 rounded-md text-xs ${ragBgColor} ${ragColor}`} title={ragText}>
                          <RagIcon size={14} className="mr-1.5 flex-shrink-0"/>
                          <span className="truncate">{ragText}</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 border-t border-purple-700 flex justify-between items-center">
                        <p className="text-xs text-purple-400">
                            {new Date(project.createdAt).toLocaleDateString()}
                        </p>
                        <div className="flex space-x-1">
                            <button
                                onClick={() => handleEdit(project)}
                                className="p-1.5 text-purple-300 hover:bg-purple-600 rounded-md transition-colors"
                                title="Edit Name"
                            >
                                <Edit3 size={14} />
                            </button>
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onDeleteProject(project.id);
                                }}
                                className="p-1.5 text-purple-300 hover:bg-red-600 rounded-md transition-colors"
                                title="Delete Project"
                            >
                                <Trash2 size={14} />
                            </button>
                        </div>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ProjectsPanel;