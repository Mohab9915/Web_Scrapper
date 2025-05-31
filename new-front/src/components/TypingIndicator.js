import React from 'react';
import { Bot } from 'lucide-react';

const TypingIndicator = ({ isVisible = false }) => {
  if (!isVisible) return null;

  return (
    <div className="flex items-start gap-3 mb-6 animate-fadeIn">
      {/* AI Avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg">
        <Bot size={16} className="text-white" />
      </div>

      {/* Typing bubble */}
      <div className="message-ai">
        <div className="flex items-center space-x-2">
          {/* Animated typing dots */}
          <div className="flex space-x-1">
            <div className="w-2 h-2 bg-purple-300 rounded-full animate-typing"></div>
            <div className="w-2 h-2 bg-purple-300 rounded-full animate-typing" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-purple-300 rounded-full animate-typing" style={{ animationDelay: '0.4s' }}></div>
          </div>
          {/* Typing text */}
          <span className="text-purple-300 text-sm animate-pulse-slow">AI is thinking...</span>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
