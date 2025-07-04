import React, { memo, useMemo, useCallback } from 'react';
import { Copy, ExternalLink, ShoppingCart, DollarSign, Star, Package } from 'lucide-react';
import StableChartRenderer from './StableChartRenderer';

const MessageRenderer = memo(({ content, chartData, onCopy }) => {

  // Define helper functions using useCallback to avoid dependency issues
  const extractChartData = useCallback((text) => {
    if (!text) return null;
    
    try {
      // Look for JSON code blocks that contain chart data
      const jsonMatch = text.match(/```json\s*(\{[\s\S]*?\})\s*```/);
      if (jsonMatch) {
        const jsonStr = jsonMatch[1];
        const data = JSON.parse(jsonStr);

        // Check if it's chart data (support both chart_type and chartType)
        const hasChartType = data.chart_type || data.chartType;
        const hasRequiredFields = data.title && data.data;
        
        if (hasChartType && hasRequiredFields) {
          // Normalize to use chartType
          return {
            ...data,
            chartType: data.chartType || data.chart_type,
          };
        }
      }
      return null;
    } catch (error) {
      // Error parsing chart data, return null
      return null;
    }
  }, []);

  const renderEnhancedText = (text) => {
    // Handle empty text
    if (!text || !text.trim()) {
      return null;
    }

    // Split by paragraphs and render with better formatting
    const paragraphs = text.split('\n\n');
    return paragraphs.map((paragraph, index) => (
      <p key={index} className="mb-3 text-purple-100 leading-relaxed">
        {paragraph}
      </p>
    ));
  };

  const renderChartWithText = (text, chartData) => {
    // Split content to show text before/after chart
    const jsonMatch = text.match(/```json\s*\{[\s\S]*?\}\s*```/);
    if (jsonMatch) {
      const beforeChart = text.substring(0, jsonMatch.index).trim();
      const afterChart = text.substring(jsonMatch.index + jsonMatch[0].length).trim();

      return (
        <div>
          {beforeChart && (
            <div className="mb-4">
              {renderEnhancedText(beforeChart)}
            </div>
          )}
          <StableChartRenderer chartData={chartData} className="my-4" />
          {afterChart && (
            <div className="mt-4">
              {renderEnhancedText(afterChart)}
            </div>
          )}
        </div>
      );
    }

    // If we have chart data but no JSON in content, render text + chart
    return (
      <div>
        {text && text.trim() && (
          <div className="mb-4">
            {renderEnhancedText(text)}
          </div>
        )}
        <StableChartRenderer chartData={chartData} className="my-4" />
      </div>
    );
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

  // Memoize chart data - prioritize chartData prop over extracting from content
  const finalChartData = useMemo(() => {
    // If chartData is provided as a prop, use it directly
    // Handle both chartType (camelCase) and chart_type (snake_case)
    if (chartData && (chartData.chartType || chartData.chart_type) && chartData.data) {
      // Normalize to camelCase for the frontend
      const normalizedChartData = {
        ...chartData,
        chartType: chartData.chartType || chartData.chart_type,
      };
      return normalizedChartData;
    }

    // Otherwise, try to extract from content (legacy support)
    const extracted = extractChartData(content);
    if (extracted) {
      // Ensure extracted data is also normalized
      return {
        ...extracted,
        chartType: extracted.chartType || extracted.chart_type,
      };
    }
    return null;
  }, [chartData, content, extractChartData]);

  // Parse and render different content types
  const renderContent = useMemo(() => {
    // Handle chart data first (highest priority)
    if (finalChartData) {
      return renderChartWithText(content || "", finalChartData);
    }

    // Show a warning if chart was requested but not generated
    if (content && content.toLowerCase().includes('chart generation failed')) {
      return (
        <div className="bg-red-900/30 border border-red-600/30 rounded-lg p-4 text-red-200 my-4">
          <strong>Chart could not be generated.</strong> The system could not extract valid chart data from your request. Please try rephrasing your question or ensure the data is suitable for charting.
        </div>
      );
    }

    // Handle empty content
    if (!content || !content.trim()) {
      return null;
    }

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content, finalChartData]);

  return (
    <div className="relative">
      {renderContent}

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
});

export default MessageRenderer;
