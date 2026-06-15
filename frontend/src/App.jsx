import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Box, Rocket, Trash2, Activity, BrainCircuit, ChevronRight, ChevronLeft
} from 'lucide-react';
import LandingPage from './components/LandingPage.jsx';
import ChatInterface from './components/ChatInterface.jsx';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

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

export default App;
