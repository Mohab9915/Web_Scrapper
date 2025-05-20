import { useState } from 'react';
import { Send, Database } from 'lucide-react';

function ChatPanel({ isRagMode, selectedModelName, onSendMessage }){
  const [messages, setMessages] = useState([{ id: 1, text: "Welcome! How can I assist you today?", sender: "system" }]);
  const [inputMessage, setInputMessage] = useState('');

  const handleSendMessage = () => {
    // Only process messages if RAG is enabled
    if (inputMessage.trim() && isRagMode) {
      const newUserMessage = { id: messages.length + 1, text: inputMessage, sender: "user" };
      setMessages([...messages, newUserMessage]);

      // Create a callback function to add the system response
      const addSystemResponseCallback = (responseText) => {
        // Add a new message directly (no processing message to replace)
        const systemResponse = { id: messages.length + 2, text: responseText, sender: "system"};
        setMessages(prev => [...prev, systemResponse]);
      };

      // Call the onSendMessage function with the correct parameters
      onSendMessage(inputMessage, selectedModelName, addSystemResponseCallback);

      setInputMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <>
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
        {messages.map(message => (
          <div
            key={message.id}
            className={`mb-4 max-w-3xl ${message.sender === 'user' ? 'ml-auto' : ''}`}
          >
            <div
              className={`p-3 rounded-lg shadow-md ${
                message.sender === 'user'
                ? 'bg-purple-600 text-white'
                : 'bg-indigo-800 bg-opacity-70 text-purple-100'
              }`}
            >
              {message.text}
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 bg-purple-800 bg-opacity-70 border-t border-purple-700">
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={!isRagMode}
            placeholder={isRagMode ? "Ask about scraped content..." : "Chat disabled. Enable RAG to use chat."}
            className={`flex-1 p-3 rounded-lg text-white placeholder-purple-300 border border-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-400 ${
              isRagMode ? "bg-purple-700" : "bg-purple-900 opacity-50 cursor-not-allowed"
            }`}
          />
          <button
            onClick={handleSendMessage}
            disabled={!isRagMode}
            className={`p-3 rounded-lg ${
              isRagMode
                ? "bg-indigo-600 hover:bg-indigo-500"
                : "bg-indigo-900 opacity-50 cursor-not-allowed"
            }`}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </>
  );
}

export default ChatPanel;