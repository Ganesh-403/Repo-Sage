// Custom lightweight markdown renderer to handle rich output without registry dependency risk
export function renderMarkdown(text) {
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
