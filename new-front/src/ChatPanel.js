import { useState, useEffect, useRef } from 'react';
import { Send, Database, Plus, MessageSquare, Trash2, Copy, Bot, User } from 'lucide-react';
import TypingIndicator from './components/TypingIndicator';
import MessageRenderer from './components/MessageRenderer';
import { useToast } from './components/Toast';

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
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const toast = useToast();

  const handleSendMessage = () => {
    // Only process messages if RAG is enabled
    if (inputMessage.trim() && isRagMode) {
      setIsTyping(true);
      // Call the onSendMessage function with the input message
      onSendMessage(inputMessage, selectedModelName, () => {
        // This callback is called after the message is sent
        setIsTyping(false);
      });

      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content).then(() => {
      toast.success('Message copied to clipboard');
    }).catch(() => {
      toast.error('Failed to copy message');
    });
  };

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isTyping]);

  return (
    <div className="flex h-full">
      {/* Conversation Sidebar */}
      <div className="w-64 glass-dark border-r border-purple-600/50 flex flex-col">
        <div className="p-4 border-b border-purple-600/50">
          <button
            onClick={onCreateConversation}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-purple-300 text-sm animate-fadeIn">
              <MessageSquare size={32} className="mx-auto mb-2 text-purple-400" />
              No conversations yet
            </div>
          ) : (
            conversations.map((conversation, index) => (
              <div
                key={conversation.id || conversation.conversationId}
                className={`p-3 border-b border-purple-600/30 cursor-pointer transition-all duration-200 hover:bg-purple-700/30 animate-slideIn ${
                  currentConversationId === (conversation.id || conversation.conversationId) ? 'bg-purple-700/50 border-l-4 border-l-indigo-500' : ''
                }`}
                style={{ animationDelay: `${index * 0.1}s` }}
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
                    className="text-purple-400 hover:text-red-400 transition-colors p-1 rounded hover:bg-red-500/20"
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
          <div className="status-success px-4 py-3 flex items-center border-b border-green-500/30 animate-fadeIn">
            <Database size={16} className="text-green-400 mr-2 animate-pulse-slow" />
            <span className="text-green-300 text-sm font-medium">
              RAG active: AI responses will incorporate recently scraped content.
            </span>
          </div>
        ) : (
          <div className="status-error px-4 py-3 flex items-center border-b border-red-500/30 animate-fadeIn">
            <Database size={16} className="text-red-400 mr-2" />
            <span className="text-red-300 text-sm font-medium">
              Chat disabled: Enable RAG for this project to use the chat functionality.
            </span>
          </div>
        )}

        <div className="flex-1 p-4 overflow-auto">
          {chatMessages.length === 0 ? (
            <div className="text-center text-purple-300 mt-8 animate-fadeIn">
              <MessageSquare size={48} className="mx-auto mb-4 text-purple-400" />
              <p className="text-lg font-medium mb-2">
                {currentConversationId ?
                  "Start a conversation" :
                  "Create a new conversation"
                }
              </p>
              <p className="text-sm">
                {currentConversationId ?
                  "Send a message below to begin chatting with the AI" :
                  "Click 'New Chat' to start a conversation"
                }
              </p>
            </div>
          ) : (
            <>
              {chatMessages.filter(message => !message.isLoading).map((message, index) => (
                <div
                  key={`${message.id}-${message.timestamp || index}`}
                  className={`mb-6 flex items-start gap-3 animate-fadeIn ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {/* Avatar */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shadow-lg ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-purple-600 to-indigo-600'
                      : 'bg-gradient-to-r from-indigo-600 to-purple-600'
                  }`}>
                    {message.role === 'user' ? (
                      <User size={16} className="text-white" />
                    ) : (
                      <Bot size={16} className="text-white" />
                    )}
                  </div>

                  {/* Message bubble */}
                  <div className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} max-w-xs md:max-w-md lg:max-w-lg`}>
                    <div
                      className={`relative group ${
                        message.role === 'user' ? 'message-user' : 'message-ai'
                      }`}
                    >
                      {message.role === 'assistant' ? (
                        <MessageRenderer
                          content={message.content}
                          onCopy={copyMessage}
                          isEnhanced={message.isEnhanced || true} // Use enhanced rendering for all AI messages
                        />
                      ) : (
                        <>
                          {message.content}
                          {/* Copy button for user messages */}
                          <button
                            onClick={() => copyMessage(message.content)}
                            className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/10"
                            title="Copy message"
                          >
                            <Copy size={14} />
                          </button>
                        </>
                      )}
                    </div>

                    {/* Timestamp */}
                    <div className={`text-xs text-purple-400 mt-1 ${message.role === 'user' ? 'text-right' : 'text-left'}`}>
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}

              {/* Typing indicator */}
              <TypingIndicator isVisible={isTyping} />

              {/* Auto-scroll anchor */}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        <div className="glass-dark border-t border-purple-600/50 p-4">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                disabled={!isRagMode || !currentConversationId}
                placeholder={
                  !isRagMode ? "Chat disabled. Enable RAG to use chat." :
                  !currentConversationId ? "Create a conversation to start chatting" :
                  "Ask about scraped content... (Press Enter to send, Shift+Enter for new line)"
                }
                className={`input-primary resize-none min-h-[44px] max-h-32 ${
                  isRagMode && currentConversationId ? "" : "opacity-50 cursor-not-allowed"
                }`}
                rows={1}
                style={{
                  height: 'auto',
                  minHeight: '44px',
                }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px';
                }}
              />
            </div>
            <button
              onClick={handleSendMessage}
              disabled={!isRagMode || !currentConversationId || !inputMessage.trim()}
              className={`btn-primary p-3 ${
                isRagMode && currentConversationId && inputMessage.trim()
                  ? "opacity-100"
                  : "opacity-50 cursor-not-allowed"
              }`}
              title="Send message"
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