import { motion } from 'framer-motion';
import { BrainCircuit, Rocket, Network, Terminal, Shield } from 'lucide-react';

export default function LandingPage() {
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
