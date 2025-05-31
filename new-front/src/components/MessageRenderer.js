import React from 'react';
import { Copy, ExternalLink, ShoppingCart, DollarSign, Star, Package } from 'lucide-react';

const MessageRenderer = ({ content, onCopy }) => {
  // Check if content contains structured data patterns
  const isStructuredResponse = content.includes('|') || 
                              content.includes('```') || 
                              content.includes('**') ||
                              content.includes('###') ||
                              content.includes('---');

  // Parse and render different content types
  const renderContent = () => {
    // Handle code blocks (tables, JSON, etc.)
    if (content.includes('```')) {
      return renderCodeBlocks(content);
    }
    
    // Handle markdown tables
    if (content.includes('|') && content.includes('---')) {
      return renderMarkdownTable(content);
    }
    
    // Handle structured cards
    if (content.includes('**') || content.includes('###')) {
      return renderStructuredContent(content);
    }
    
    // Default text rendering with enhanced formatting
    return renderEnhancedText(content);
  };

  const renderCodeBlocks = (text) => {
    const parts = text.split('```');
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        // This is inside a code block
        const lines = part.split('\n');
        const language = lines[0].trim();
        const code = lines.slice(1).join('\n');
        
        if (language === 'json') {
          return (
            <div key={index} className="my-4 bg-purple-900/30 rounded-lg border border-purple-600/30 overflow-hidden">
              <div className="bg-purple-800/50 px-4 py-2 text-sm text-purple-300 font-medium">
                JSON Data
              </div>
              <pre className="p-4 text-sm text-purple-100 overflow-x-auto">
                <code>{code}</code>
              </pre>
            </div>
          );
        } else {
          return (
            <div key={index} className="my-4 bg-purple-900/30 rounded-lg border border-purple-600/30 overflow-hidden">
              <div className="bg-purple-800/50 px-4 py-2 text-sm text-purple-300 font-medium">
                {language || 'Code'}
              </div>
              <pre className="p-4 text-sm text-purple-100 overflow-x-auto">
                <code>{code}</code>
              </pre>
            </div>
          );
        }
      } else {
        // Regular text
        return <div key={index} className="whitespace-pre-wrap">{part}</div>;
      }
    });
  };

  const renderMarkdownTable = (text) => {
    const lines = text.split('\n');
    const tableLines = [];
    const otherLines = [];
    let inTable = false;

    lines.forEach(line => {
      if (line.includes('|')) {
        tableLines.push(line);
        inTable = true;
      } else if (inTable && line.trim() === '') {
        // End of table
        inTable = false;
        otherLines.push(renderTable(tableLines));
        tableLines.length = 0;
        otherLines.push(<br key={Math.random()} />);
      } else {
        if (tableLines.length > 0) {
          otherLines.push(renderTable(tableLines));
          tableLines.length = 0;
        }
        otherLines.push(line);
        inTable = false;
      }
    });

    if (tableLines.length > 0) {
      otherLines.push(renderTable(tableLines));
    }

    return otherLines.map((item, index) => 
      typeof item === 'string' ? 
        <div key={index} className="whitespace-pre-wrap">{item}</div> : 
        item
    );
  };

  const renderTable = (tableLines) => {
    if (tableLines.length < 2) return null;

    const headers = tableLines[0].split('|').map(h => h.trim()).filter(h => h);
    const rows = tableLines.slice(2).map(line => 
      line.split('|').map(cell => cell.trim()).filter(cell => cell)
    );

    return (
      <div className="my-4 overflow-x-auto">
        <table className="w-full bg-purple-900/20 rounded-lg border border-purple-600/30">
          <thead>
            <tr className="bg-purple-800/50">
              {headers.map((header, index) => (
                <th key={index} className="px-4 py-3 text-left text-sm font-semibold text-purple-200 border-b border-purple-600/30">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-purple-800/20 transition-colors">
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} className="px-4 py-3 text-sm text-purple-100 border-b border-purple-700/20">
                    {renderCellContent(cell)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderCellContent = (cell) => {
    // Check if cell contains price information
    if (cell.includes('$') || cell.includes('price') || cell.includes('cost')) {
      return (
        <span className="flex items-center gap-1 text-green-400 font-medium">
          <DollarSign size={14} />
          {cell}
        </span>
      );
    }
    
    // Check if cell contains rating information
    if (cell.includes('★') || cell.includes('star') || cell.includes('rating')) {
      return (
        <span className="flex items-center gap-1 text-yellow-400">
          <Star size={14} />
          {cell}
        </span>
      );
    }
    
    // Check if cell contains URL
    if (cell.startsWith('http')) {
      return (
        <a href={cell} target="_blank" rel="noopener noreferrer" 
           className="flex items-center gap-1 text-blue-400 hover:text-blue-300 transition-colors">
          <ExternalLink size={14} />
          View
        </a>
      );
    }
    
    return cell;
  };

  const renderStructuredContent = (text) => {
    const lines = text.split('\n');
    const elements = [];
    let currentCard = null;
    let currentList = [];

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('###')) {
        // Finish previous card if exists
        if (currentCard) {
          elements.push(renderCard(currentCard));
          currentCard = null;
        }
        
        // Start new section
        const title = trimmed.replace(/^###\s*/, '');
        elements.push(
          <h3 key={index} className="text-lg font-semibold text-purple-200 mt-6 mb-3 flex items-center gap-2">
            <Package size={18} className="text-indigo-400" />
            {title}
          </h3>
        );
      } else if (trimmed.startsWith('**') && trimmed.endsWith('**')) {
        // Card title
        const title = trimmed.replace(/\*\*/g, '');
        if (currentCard) {
          elements.push(renderCard(currentCard));
        }
        currentCard = { title, content: [] };
      } else if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
        // List item
        const item = trimmed.replace(/^[•-]\s*/, '');
        if (currentCard) {
          currentCard.content.push({ type: 'list', text: item });
        } else {
          currentList.push(item);
        }
      } else if (trimmed) {
        // Regular content
        if (currentList.length > 0) {
          elements.push(renderList(currentList));
          currentList = [];
        }
        
        if (currentCard) {
          currentCard.content.push({ type: 'text', text: trimmed });
        } else {
          elements.push(<p key={index} className="mb-2 text-purple-100">{trimmed}</p>);
        }
      }
    });

    // Finish any remaining card or list
    if (currentCard) {
      elements.push(renderCard(currentCard));
    }
    if (currentList.length > 0) {
      elements.push(renderList(currentList));
    }

    return elements;
  };

  const renderCard = (card) => (
    <div key={Math.random()} className="my-4 bg-purple-900/30 rounded-lg border border-purple-600/30 p-4">
      <h4 className="font-semibold text-purple-200 mb-3 flex items-center gap-2">
        <ShoppingCart size={16} className="text-indigo-400" />
        {card.title}
      </h4>
      <div className="space-y-2">
        {card.content.map((item, index) => (
          <div key={index} className="text-purple-100">
            {item.type === 'list' ? (
              <div className="flex items-start gap-2">
                <span className="text-indigo-400 mt-1">•</span>
                <span>{item.text}</span>
              </div>
            ) : (
              <p>{item.text}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderList = (items) => (
    <ul key={Math.random()} className="my-4 space-y-2">
      {items.map((item, index) => (
        <li key={index} className="flex items-start gap-2 text-purple-100">
          <span className="text-indigo-400 mt-1">•</span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );

  const renderEnhancedText = (text) => {
    // Split by paragraphs and render with better formatting
    const paragraphs = text.split('\n\n');
    return paragraphs.map((paragraph, index) => (
      <p key={index} className="mb-3 text-purple-100 leading-relaxed">
        {paragraph}
      </p>
    ));
  };

  return (
    <div className="relative">
      {renderContent()}
      
      {/* Copy button */}
      <button
        onClick={() => onCopy && onCopy(content)}
        className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-white/10"
        title="Copy message"
      >
        <Copy size={14} />
      </button>
    </div>
  );
};

export default MessageRenderer;
