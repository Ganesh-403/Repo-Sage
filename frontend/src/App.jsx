import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, Search, Box, Shield, Network, BrainCircuit, Play, 
  Rocket, Trash2, Send, FileText, Activity, Sparkles, Bot,
  Cpu, ChevronRight, ChevronLeft, RefreshCw, BarChart2, Layers
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

// Custom lightweight markdown renderer to handle rich output without registry dependency risk
function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks: ```lang ... ```
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre class="bg-slate-955/90 p-4 rounded-xl my-3 border border-indigo-500/10 overflow-x-auto font-mono text-xs text-slate-300"><code class="language-${lang}">${code.trim()}</code></pre>`;
  });

  // Inline code: `code`
  html = html.replace(/`([^`\n]+)`/g, '<code class="bg-indigo-500/10 px-1.5 py-0.5 rounded text-indigo-300 font-mono text-xs border border-indigo-500/20">$1</code>');

  // File citations: e.g. main.py:123 or src/app.js:45
  html = html.replace(/([a-zA-Z0-9_\-\.\/]+\.(?:py|js|ts|tsx|jsx|json|yaml|yml|md|html|css)):(\d+)/g, 
    '<span class="inline-flex items-center gap-1 bg-indigo-500/10 px-2 py-0.5 rounded text-xs text-indigo-300 font-mono border border-indigo-500/20 my-0.5 hover:bg-indigo-500/20 transition-colors">📄 $1:$2</span>');

  // Bold: **text**
  html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong class="font-bold text-white">$1</strong>');

  // Headers: ### text, ## text, # text
  html = html.replace(/^### (.*$)/gim, '<h4 class="text-sm font-bold text-indigo-300 mt-4 mb-2">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 class="text-md font-bold text-indigo-200 mt-5 mb-2">$1</h3>');
  html = html.replace(/^# (.*$)/gim, '<h2 class="text-lg font-bold text-white mt-6 mb-3">$1</h2>');

  // Bullet points
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li class="ml-4 list-disc text-slate-300">$1</li>');

  // Line breaks
  html = html.replace(/\n/g, '<br/>');

  return html;
}

function App() {
  const [repos, setRepos] = useState([]);
  const [currentRepo, setCurrentRepo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  
  // Indexing State
  const [indexUrl, setIndexUrl] = useState('');
  const [indexToken, setIndexToken] = useState('');
  const [isIndexing, setIsIndexing] = useState(false);
  const [indexStatus, setIndexStatus] = useState(null);

  useEffect(() => {
    fetchRepos();
  }, []);

  const fetchRepos = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/repos`);
      if (res.ok) {
        const data = await res.json();
        setRepos(data.repos || []);
      }
    } catch (e) {
      console.error("Failed to fetch repos", e);
    }
  };

  const handleIndex = async (e) => {
    e.preventDefault();
    if (!indexUrl) return;
    setIsIndexing(true);
    setIndexStatus(null);
    try {
      const res = await fetch(`${BACKEND_URL}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ github_url: indexUrl, github_token: indexToken || undefined })
      });
      const data = await res.json();
      if (res.ok) {
        setIndexStatus({ type: 'success', msg: `Indexed ${data.repo} (${data.chunks} chunks)` });
        fetchRepos();
        selectRepo(data.repo);
      } else {
        setIndexStatus({ type: 'error', msg: data.detail || 'Indexing failed' });
      }
    } catch (e) {
      setIndexStatus({ type: 'error', msg: e.message });
    }
    setIsIndexing(false);
  };

  const selectRepo = (name) => {
    setCurrentRepo(name);
    setMessages([]);
  };

  const handleDelete = async (name) => {
    try {
      await fetch(`${BACKEND_URL}/repos/${name}`, { method: 'DELETE' });
      if (currentRepo === name) selectRepo(null);
      fetchRepos();
    } catch (e) {
      console.error("Delete failed", e);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden text-slate-200 relative">
      
      {/* Background Animated Orbs wrapper */}
      <div className="ambient-glow" />

      {/* Collapsed Sidebar Restore Button */}
      {sidebarCollapsed && (
        <motion.button 
          initial={{ opacity: 0, scale: 0.8 }} 
          animate={{ opacity: 1, scale: 1 }}
          onClick={() => setSidebarCollapsed(false)}
          className="fixed left-4 top-6 w-9 h-9 rounded-xl bg-slate-900/90 border border-slate-700/50 flex items-center justify-center cursor-pointer text-slate-400 hover:text-white shadow-lg z-30 transition hover:bg-slate-800"
        >
          <ChevronRight size={18} />
        </motion.button>
      )}

      {/* Sidebar */}
      <motion.aside 
        animate={{ 
          width: sidebarCollapsed ? 0 : 288,
          opacity: sidebarCollapsed ? 0 : 1,
        }}
        transition={{ type: 'spring', stiffness: 200, damping: 24 }}
        className="bg-surface/90 backdrop-blur-2xl border-r border-indigo-500/10 flex flex-col shrink-0 relative z-20 overflow-hidden"
      >
        {/* Toggle Collapse Button */}
        {!sidebarCollapsed && (
          <button 
            onClick={() => setSidebarCollapsed(true)}
            className="absolute -right-3 top-6 w-6 h-6 rounded-full bg-slate-900 border border-slate-700/50 flex items-center justify-center cursor-pointer text-slate-400 hover:text-white shadow z-30 transition hover:scale-105 active:scale-95"
          >
            <ChevronLeft size={12} />
          </button>
        )}

        <div className="p-5 border-b border-indigo-500/10 flex items-center gap-3 w-72">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <BrainCircuit size={18} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold tracking-tight text-lg leading-tight">RepoSage</h1>
            <p className="text-xs text-slate-400 font-medium tracking-wide">AI CODE INTELLIGENCE</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-hide w-72">
          {/* Repositories */}
          <section>
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Repositories</h2>
            {repos.length === 0 ? (
              <div className="text-center p-4 border border-dashed border-slate-700 rounded-xl bg-slate-800/30 text-slate-400 text-sm">
                No repos indexed yet
              </div>
            ) : (
              <div className="space-y-2">
                {repos.map(r => (
                  <div key={r.name} className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer transition-all ${currentRepo === r.name ? 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-300' : 'hover:bg-slate-800/50 border border-transparent'}`} onClick={() => selectRepo(r.name)}>
                    <div className="flex items-center gap-2 overflow-hidden">
                      <Box size={14} className={currentRepo === r.name ? "text-indigo-400" : "text-slate-500"} />
                      <span className="text-sm font-medium truncate">{r.name}</span>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); handleDelete(r.name); }} className="opacity-0 group-hover:opacity-100 text-red-400 hover:bg-red-400/20 p-1.5 rounded-md transition">
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Index Form */}
          <section>
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Index New Repo</h2>
            <form onSubmit={handleIndex} className="space-y-3">
              <input 
                type="url" required placeholder="https://github.com/..." 
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                value={indexUrl} onChange={e => setIndexUrl(e.target.value)}
              />
              <input 
                type="password" placeholder="Token (optional)" 
                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                value={indexToken} onChange={e => setIndexToken(e.target.value)}
              />
              <button 
                type="submit" disabled={isIndexing}
                className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white font-medium rounded-lg px-4 py-2 text-sm shadow-lg shadow-indigo-500/25 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isIndexing ? <Activity size={16} className="animate-spin" /> : <Rocket size={16} />}
                {isIndexing ? 'Indexing...' : 'Index Repository'}
              </button>
            </form>
            {indexStatus && (
              <div className={`mt-3 p-3 rounded-lg text-xs border ${indexStatus.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-red-500/10 border-red-500/20 text-red-400'}`}>
                {indexStatus.msg}
              </div>
            )}
          </section>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main className="flex-1 relative flex flex-col min-w-0 bg-transparent z-10 overflow-y-auto">
        <AnimatePresence mode="wait">
          {!currentRepo ? (
            <LandingPage key="landing" />
          ) : (
            <ChatInterface 
              key="chat" 
              repo={currentRepo} 
              messages={messages} 
              setMessages={setMessages} 
            />
          )}
        </AnimatePresence>
      </main>

    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Landing Page Component (Ultra Premium)
// ════════════════════════════════════════════════════════════════════════════
function LandingPage() {
  const container = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const item = { hidden: { opacity: 0, y: 20, filter: 'blur(8px)' }, show: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { type: 'spring', stiffness: 100, damping: 20 } } };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="max-w-5xl mx-auto w-full pt-24 pb-12 px-8 flex flex-col items-center">
      <motion.div variants={item} className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl shadow-indigo-500/40 mb-8 animate-float">
        <BrainCircuit size={32} className="text-white" />
      </motion.div>
      
      <motion.h1 variants={item} className="text-5xl md:text-6xl font-black tracking-tight text-center mb-4 leading-tight">
        Understand Any Codebase <br/><span className="text-gradient">in Minutes</span>
      </motion.h1>
      
      <motion.p variants={item} className="text-slate-400 text-lg text-center max-w-2xl mb-10 leading-relaxed">
        Index any GitHub repository and ask natural language questions. Get answers with precise <strong className="text-slate-200">file:line</strong> citations, powered by RAG and local LLMs.
      </motion.p>
      
      <motion.div variants={item} className="flex gap-4 mb-16">
        <div className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold flex items-center gap-2 shadow-lg shadow-indigo-500/25">
          <Rocket size={18} /> Get Started in Sidebar
        </div>
      </motion.div>

      {/* Mock Terminal Animation */}
      <motion.div variants={item} className="w-full max-w-3xl glass-card p-4 shadow-2xl overflow-hidden mb-20 relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500 opacity-50"></div>
        <div className="flex gap-2 mb-4 px-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-amber-500"></div>
          <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
        </div>
        <div className="font-mono text-sm text-slate-300 space-y-2 px-2 pb-2">
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:0.5}} className="flex gap-3"><span className="text-indigo-400">$</span> <span>reposage index https://github.com/facebook/react</span></motion.div>
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:1.5}} className="text-slate-500">Cloning repository... done.</motion.div>
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:1.8}} className="text-slate-500">Chunking 12,453 files using AST parsing...</motion.div>
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:2.1}} className="text-emerald-400 font-semibold">Success! Indexed in 18.4s</motion.div>
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:3.0}} className="flex gap-3"><span className="text-indigo-400">$</span> <span>ask "how does the fiber reconciler handle state updates?"</span></motion.div>
          <motion.div initial={{opacity:0}} animate={{opacity:1}} transition={{delay:4.2}} className="text-slate-400 border-l-2 border-indigo-500 pl-3 py-1 my-2">The Fiber reconciler schedules updates in a queue attached to the fiber node... <span className="text-indigo-300 ml-2">📄 src/react-reconciler/ReactFiberWorkLoop.js:142</span></motion.div>
        </div>
      </motion.div>

      {/* Feature Grid */}
      <motion.div variants={container} className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl">
        <FeatureCard icon={<Network size={20}/>} title="Architecture Analysis" desc="Map module connections, entry points, and overall system design." color="text-indigo-400" bg="bg-indigo-500/10" />
        <FeatureCard icon={<Terminal size={20}/>} title="API Discovery" desc="Find all endpoints, routes, schemas, and middleware chains." color="text-violet-400" bg="bg-violet-500/10" />
        <FeatureCard icon={<Shield size={20}/>} title="Security Review" desc="Identify auth patterns, input validation, and token handling." color="text-emerald-400" bg="bg-emerald-500/10" />
      </motion.div>
    </motion.div>
  );
}

function FeatureCard({ icon, title, desc, color, bg }) {
  return (
    <motion.div 
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      className="glass-card p-6 relative overflow-hidden group cursor-default"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:translate-x-[200%] transition-transform duration-1000 ease-in-out"></div>
      <div className={`w-10 h-10 rounded-xl ${bg} ${color} flex items-center justify-center mb-4`}>{icon}</div>
      <h3 className="font-bold text-slate-200 mb-2">{title}</h3>
      <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
    </motion.div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Codebase Profile Summary Dashboard Component
// ════════════════════════════════════════════════════════════════════════════
function RepoDashboard({ repo, onSelectSuggestion, summaryData, isLoadingSummary, onRefreshSummary }) {
  if (isLoadingSummary) {
    return (
      <motion.div 
        initial={{ opacity: 0 }} 
        animate={{ opacity: 1 }} 
        exit={{ opacity: 0 }} 
        className="w-full max-w-4xl mx-auto p-6 space-y-6 pt-10"
      >
        <div className="h-7 bg-slate-800/40 rounded-lg w-1/3 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-20 bg-slate-800/30 rounded-xl border border-white/[0.02] animate-pulse"></div>
          <div className="h-20 bg-slate-800/30 rounded-xl border border-white/[0.02] animate-pulse"></div>
          <div className="h-20 bg-slate-800/30 rounded-xl border border-white/[0.02] animate-pulse"></div>
        </div>
        <div className="h-80 bg-slate-800/20 rounded-2xl border border-white/[0.02] animate-pulse"></div>
      </motion.div>
    );
  }

  if (!summaryData) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col items-center justify-center p-16 text-center">
        <Activity size={32} className="text-indigo-400 animate-spin mb-4" />
        <p className="text-slate-400 text-sm">Failed to generate codebase profile summary.</p>
        <button onClick={onRefreshSummary} className="mt-4 px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl text-xs font-semibold flex items-center gap-1.5 hover:bg-indigo-500/20 transition-all">
          <RefreshCw size={12} /> Try Again
        </button>
      </motion.div>
    );
  }

  const { summary, metadata } = summaryData;
  const languages = metadata?.languages || [];
  const totalChunks = metadata?.total_chunks || 0;
  const filesSampled = metadata?.files_sampled || 0;

  const SUGGESTIONS = [
    { text: "Explain the overall architecture and system design of this repo.", label: "Architecture" },
    { text: "What is the main entry point and setup flow?", label: "Entry Point" },
    { text: "Identify key modules and their core responsibilities.", label: "Modules" },
    { text: "What patterns and architectural decisions stand out here?", label: "Design Patterns" }
  ];

  return (
    <motion.div 
      variants={{
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.08 } }
      }}
      initial="hidden" 
      animate="show"
      exit="hidden"
      className="w-full max-w-4xl mx-auto p-6 space-y-8 pt-10"
    >
      {/* Title */}
      <motion.div variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }} className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Layers size={18} className="text-indigo-400" />
            Codebase Intelligence Profile
          </h3>
          <p className="text-xs text-slate-400">High-level analysis generated by RepoSage AI</p>
        </div>
        <button 
          onClick={onRefreshSummary} 
          title="Force Re-generate Profile Summary"
          className="p-2 hover:bg-slate-800/80 border border-slate-700/30 text-slate-400 hover:text-white rounded-xl transition flex items-center justify-center"
        >
          <RefreshCw size={14} className="hover:rotate-180 transition-transform duration-500" />
        </button>
      </motion.div>

      {/* Metadata Cards */}
      <motion.div 
        variants={{
          hidden: { opacity: 0 },
          show: { opacity: 1, transition: { staggerChildren: 0.05 } }
        }}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <StatCard 
          icon={<Terminal size={18} className="text-indigo-400" />} 
          title="Vector Index Size" 
          value={`${totalChunks} chunks`}
          desc="AST-parsed code fragments"
        />
        <StatCard 
          icon={<BarChart2 size={18} className="text-purple-400" />} 
          title="Codebase Profiled" 
          value={`${filesSampled} files`}
          desc="Used for architectural summary"
        />
        <StatCard 
          icon={<BrainCircuit size={18} className="text-emerald-400" />} 
          title="Detected Tech Stack" 
          value={languages.join(', ') || 'N/A'}
          desc="Identified source languages"
        />
      </motion.div>

      {/* Summary Content */}
      <motion.div 
        variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0 } }}
        className="glass-card glow-hover p-6 border border-white/[0.03] shadow-lg overflow-hidden relative"
      >
        <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-30"></div>
        <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-4">Architecture Summary</h4>
        <div 
          className="prose prose-invert max-w-none text-sm text-slate-300 leading-relaxed space-y-4"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(summary) }} 
        />
      </motion.div>

      {/* Quick Start Suggestions */}
      <motion.div variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }} className="space-y-3">
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Suggested Queries</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SUGGESTIONS.map((s, idx) => (
            <motion.div
              whileHover={{ y: -2, scale: 1.01 }}
              transition={{ type: "spring", stiffness: 400, damping: 30 }}
              key={idx}
              onClick={() => onSelectSuggestion(s.text)}
              className="p-4 bg-slate-900/40 hover:bg-indigo-500/[0.04] border border-white/[0.02] hover:border-indigo-500/20 rounded-xl cursor-pointer transition-colors flex items-center justify-between group shadow-sm"
            >
              <div className="space-y-0.5">
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">{s.label}</span>
                <p className="text-xs font-medium text-slate-300 leading-normal">{s.text}</p>
              </div>
              <ChevronRight size={16} className="text-slate-500 group-hover:text-indigo-400 transition-colors transform group-hover:translate-x-0.5" />
            </motion.div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}

function StatCard({ icon, title, value, desc }) {
  return (
    <motion.div 
      variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}
      whileHover={{ y: -2 }}
      className="p-4 glass-card glow-hover flex items-start gap-3 border border-white/[0.02]"
    >
      <div className="p-2.5 bg-slate-800/60 rounded-xl border border-white/[0.04] shrink-0">
        {icon}
      </div>
      <div className="min-w-0">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">{title}</span>
        <h5 className="text-sm font-semibold text-slate-200 mt-0.5 truncate">{value}</h5>
        <p className="text-[10px] text-slate-400 mt-0.5 truncate">{desc}</p>
      </div>
    </motion.div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// Chat Interface Component
// ════════════════════════════════════════════════════════════════════════════
function ChatInterface({ repo, messages, setMessages }) {
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

export default App;
