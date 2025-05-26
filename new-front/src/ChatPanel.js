import { useState, useEffect } from 'react';
import { Send, Database, Plus, MessageSquare, Trash2 } from 'lucide-react';

function ChatPanel({ 
  isRagMode, 
  selectedModelName, 
  onSendMessage,
  conversations = [],
  currentConversationId,
  chatMessages = [],
  onCreateConversation,
  onSwitchConversation,
  onDeleteConversation
}){
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = () => {
    // Only process messages if RAG is enabled
    if (inputMessage.trim() && isRagMode) {
      // Call the onSendMessage function with the input message
      onSendMessage(inputMessage, selectedModelName, () => {
        // This callback is called after the message is sent
        // The parent component handles updating the chat messages
      });

      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-full">
      {/* Conversation Sidebar */}
      <div className="w-64 bg-purple-900 bg-opacity-50 border-r border-purple-700 flex flex-col">
        <div className="p-4 border-b border-purple-700">
          <button
            onClick={onCreateConversation}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-purple-300 text-sm">
              No conversations yet
            </div>
          ) : (
            conversations.map(conversation => (
              <div
                key={conversation.id || conversation.conversationId}
                className={`p-3 border-b border-purple-800 hover:bg-purple-800 cursor-pointer transition-colors ${
                  currentConversationId === (conversation.id || conversation.conversationId) ? 'bg-purple-700' : ''
                }`}
                onClick={() => onSwitchConversation(conversation.id || conversation.conversationId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <MessageSquare size={14} className="text-purple-400 flex-shrink-0" />
                    <div className="text-sm text-white truncate">
                      {conversation.summary || `Chat ${(conversation.id || conversation.conversationId || 'unknown').toString().slice(0, 8)}`}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conversation.id || conversation.conversationId);
                    }}
                    className="text-purple-400 hover:text-red-400 transition-colors p-1"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
                <div className="text-xs text-purple-400 mt-1">
                  {new Date(conversation.createdAt || conversation.created_at || conversation.lastMessageAt || conversation.last_message_at).toLocaleDateString()}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {isRagMode ? (
          <div className="bg-indigo-900 bg-opacity-80 px-4 py-2 flex items-center border-b border-indigo-700">
            <Database size={16} className="text-green-400 mr-2" />
            <span className="text-green-300 text-sm">
              RAG active: AI responses will incorporate recently scraped content.
            </span>
          </div>
        ) : (
          <div className="bg-red-900 bg-opacity-80 px-4 py-2 flex items-center border-b border-red-700">
            <Database size={16} className="text-red-400 mr-2" />
            <span className="text-red-300 text-sm">
              Chat disabled: Enable RAG for this project to use the chat functionality.
            </span>
          </div>
        )}

        <div className="flex-1 p-4 overflow-auto">
          {chatMessages.length === 0 ? (
            <div className="text-center text-purple-300 mt-8">
              {currentConversationId ? 
                "Start a conversation by sending a message below" : 
                "Create a new conversation to start chatting"
              }
            </div>
          ) : (
            chatMessages.map(message => (
              <div
                key={message.id}
                className={`mb-4 max-w-3xl ${message.role === 'user' ? 'ml-auto' : ''}`}
              >
                <div
                  className={`p-3 rounded-lg shadow-md ${
                    message.role === 'user'
                    ? 'bg-purple-600 text-white'
                    : 'bg-indigo-800 bg-opacity-70 text-purple-100'
                  }`}
                >
                  {message.content}
                </div>
                <div className={`text-xs text-purple-400 mt-1 ${message.role === 'user' ? 'text-right' : ''}`}>
                  {new Date(message.timestamp).toLocaleTimeString()}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-4 bg-purple-800 bg-opacity-70 border-t border-purple-700">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={!isRagMode || !currentConversationId}
              placeholder={
                !isRagMode ? "Chat disabled. Enable RAG to use chat." :
                !currentConversationId ? "Create a conversation to start chatting" :
                "Ask about scraped content..."
              }
              className={`flex-1 p-3 rounded-lg text-white placeholder-purple-300 border border-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-400 ${
                isRagMode && currentConversationId ? "bg-purple-700" : "bg-purple-900 opacity-50 cursor-not-allowed"
              }`}
            />
            <button
              onClick={handleSendMessage}
              disabled={!isRagMode || !currentConversationId}
              className={`p-3 rounded-lg ${
                isRagMode && currentConversationId
                  ? "bg-indigo-600 hover:bg-indigo-500"
                  : "bg-indigo-900 opacity-50 cursor-not-allowed"
              }`}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatPanel;