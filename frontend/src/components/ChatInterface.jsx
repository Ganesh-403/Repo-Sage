import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { 
  Box, Sparkles, Bot, BrainCircuit, FileText, Send, Search
} from 'lucide-react';
import RepoDashboard from './RepoDashboard.jsx';
import { renderMarkdown } from '../utils/markdown.js';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export default function ChatInterface({ repo, messages, setMessages }) {
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [agentMode, setAgentMode] = useState(false);
  const [agentStatusText, setAgentStatusText] = useState('');
  const [summaryData, setSummaryData] = useState(null);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    fetchSummary(false);
  }, [repo]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping, agentStatusText]);

  const fetchSummary = async (forceRefresh = false) => {
    setIsLoadingSummary(true);
    setSummaryData(null);
    try {
      const url = `${BACKEND_URL}/repos/${repo}/summary${forceRefresh ? '?refresh=true' : ''}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setSummaryData(data);
      }
    } catch (e) {
      console.error("Failed to fetch repo summary", e);
    }
    setIsLoadingSummary(false);
  };

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isTyping) return;
    sendQuery(input.trim());
  };

  const sendQuery = async (queryText) => {
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: queryText }]);
    setIsTyping(true);

    if (agentMode) {
      // ─── Agent Mode (Non-streaming, LangGraph Agent) ───
      setAgentStatusText('Analyzing repository structure...');
      setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [] }]);
      
      try {
        const res = await fetch(`${BACKEND_URL}/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_name: repo,
            question: queryText,
            k: 6,
            chat_history: messages.slice(-6)
          })
        });
        const data = await res.json();
        if (res.ok) {
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { 
              role: 'assistant', 
              content: data.answer, 
              sources: data.sources || [] 
            };
            return updated;
          });
        } else {
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { 
              role: 'assistant', 
              content: `❌ Error: ${data.detail || 'Failed to query codebase.'}` 
            };
            return updated;
          });
        }
      } catch (e) {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { 
            role: 'assistant', 
            content: `❌ Request failed: ${e.message}` 
          };
          return updated;
        });
      }
      setAgentStatusText('');
    } else {
      // ─── Fast RAG Mode (Streaming, SSE) ───
      setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [] }]);

      try {
        const response = await fetch(`${BACKEND_URL}/query/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            repo_name: repo,
            question: queryText,
            k: 6,
            chat_history: messages.slice(-6)
          })
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          setMessages(prev => {
            const updated = [...prev];
            updated[updated.length - 1] = { 
              role: 'assistant', 
              content: `❌ Error: ${errData.detail || 'Failed to stream response'}` 
            };
            return updated;
          });
          setIsTyping(false);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const cleanedLine = line.trim();
            if (!cleanedLine.startsWith('data: ')) continue;
            
            try {
              const data = JSON.parse(cleanedLine.substring(6));
              if (data.type === 'token') {
                setMessages(prev => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg && lastMsg.role === 'assistant') {
                    lastMsg.content += data.content;
                  }
                  return updated;
                });
              } else if (data.type === 'sources') {
                setMessages(prev => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg && lastMsg.role === 'assistant') {
                    lastMsg.sources = data.sources || [];
                  }
                  return updated;
                });
              } else if (data.type === 'error') {
                setMessages(prev => {
                  const updated = [...prev];
                  const lastMsg = updated[updated.length - 1];
                  if (lastMsg && lastMsg.role === 'assistant') {
                    lastMsg.content = `❌ Error: ${data.content}`;
                  }
                  return updated;
                });
              }
            } catch (err) {
              console.error('Error parsing SSE line:', err);
            }
          }
        }
      } catch (e) {
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { 
            role: 'assistant', 
            content: `❌ Request failed: ${e.message}` 
          };
          return updated;
        });
      }
    }
    
    setIsTyping(false);
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col h-full w-full max-w-4xl mx-auto">
      
      {/* Header */}
      <div className="shrink-0 p-6 border-b border-slate-800/50 bg-background/50 backdrop-blur-md sticky top-0 z-10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400"><Box size={20} /></div>
          <div>
            <h2 className="text-xl font-bold">{repo}</h2>
            <p className="text-xs text-slate-400 font-medium">Ask questions about this codebase</p>
          </div>
        </div>

        {/* Mode Selector Toggle */}
        <div className="flex items-center gap-3 bg-slate-900/40 border border-slate-700/30 px-3 py-1.5 rounded-xl shadow-inner">
          <div className="flex items-center gap-1">
            {agentMode ? <Sparkles size={13} className="text-indigo-400 animate-pulse" /> : <Bot size={13} className="text-slate-400" />}
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Agentic Reasoning</span>
          </div>
          <button 
            type="button"
            onClick={() => setAgentMode(!agentMode)}
            className={`w-9 h-5 rounded-full transition-all duration-300 relative ${agentMode ? 'bg-gradient-to-r from-indigo-500 to-purple-600' : 'bg-slate-800'}`}
          >
            <div className={`w-3.5 h-3.5 bg-white rounded-full absolute top-[3px] transition-all duration-300 shadow-sm ${agentMode ? 'left-[17px]' : 'left-[3px]'}`}></div>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        {messages.length === 0 ? (
          <RepoDashboard 
            repo={repo} 
            onSelectSuggestion={sendQuery} 
            summaryData={summaryData} 
            isLoadingSummary={isLoadingSummary} 
            onRefreshSummary={() => fetchSummary(true)} 
          />
        ) : (
          messages.map((m, i) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} 
              key={i} className={`flex gap-4 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 mt-1 shadow-md shadow-indigo-500/10">
                  <BrainCircuit size={16} className="text-white"/>
                </div>
              )}
              <div className={`px-5 py-3.5 rounded-2xl max-w-[85%] text-[0.92rem] leading-relaxed shadow-sm ${m.role === 'user' ? 'bg-indigo-500 text-white rounded-tr-sm' : 'glass-card rounded-tl-sm text-slate-300'}`}>
                <div 
                  className="prose prose-invert max-w-none text-slate-300"
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(m.content) }} 
                />
                
                {/* Inline sources rendering per-message */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-slate-700/30">
                    <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
                      <FileText size={11}/> Source Chunks
                    </h4>
                    <div className="flex flex-wrap gap-1.5">
                      {m.sources.map((src, idx) => (
                        <span key={idx} className="text-[10px] px-2 py-0.5 bg-indigo-500/5 hover:bg-indigo-500/15 border border-indigo-500/10 hover:border-indigo-500/25 text-indigo-400 hover:text-indigo-300 rounded-md font-mono flex items-center gap-1 cursor-default transition-all">
                          <FileText size={9} className="opacity-50" /> {src}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))
        )}
        
        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700/50 flex items-center justify-center shrink-0 animate-pulse">
              <BrainCircuit size={16} className="text-slate-500"/>
            </div>
            <div className="px-5 py-4 glass-card rounded-2xl rounded-tl-sm flex flex-col gap-2">
              {agentStatusText && (
                <span className="text-xs text-slate-400 italic mb-1 flex items-center gap-1.5 animate-pulse">
                  <Sparkles size={11} className="text-indigo-400" /> {agentStatusText}
                </span>
              )}
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{animationDelay:'0.2s'}}></div>
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{animationDelay:'0.4s'}}></div>
              </div>
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} className="h-2"></div>
      </div>

      {/* Input */}
      <div className="shrink-0 p-6 bg-background pt-2">
        <form onSubmit={handleSend} className="relative flex items-center">
          <input 
            type="text" 
            value={input} onChange={e => setInput(e.target.value)}
            placeholder={agentMode ? `Perform deep codebase query...` : `Ask about ${repo}...`}
            className="w-full bg-surface/50 border border-slate-700 rounded-2xl pl-5 pr-14 py-4 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all shadow-xl text-slate-200 placeholder-slate-500"
            disabled={isTyping}
          />
          <button 
            type="submit" disabled={!input.trim() || isTyping}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white rounded-xl transition-all disabled:opacity-50 disabled:hover:from-indigo-500 disabled:cursor-not-allowed shadow-md"
          >
            <Send size={18} />
          </button>
        </form>
      </div>

    </motion.div>
  );
}
