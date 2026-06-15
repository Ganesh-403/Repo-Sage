# RepoSage Frontend — High-Performance AI Codebase Client

This is the front-end user interface for RepoSage, built using **React**, **Vite**, **Tailwind CSS**, and **Framer Motion**. It replaces the legacy Streamlit mockup with a state-of-the-art, fully responsive, and animated single-page application.

---

## Design & Interactive Features

- **Technical Mock Terminal**: A command-typing splash animation on the landing screen, guiding the user through the indexing workflow.
- **Interactive Repository Dashboard**: A collapsible, sidebar-equipped control panel displaying indexed repositories, file stats, and files parsed.
- **Spring-Physics Animations**: UI elements like input blocks, cards, and sidebar toggles use Framer Motion spring physics for smooth, organic, and lag-free feedback.
- **Streaming Chat Workspace**: Real-time message streaming using standard Server-Sent Events (SSE). Code blocks, markdown tables, and headers are parsed and highlighted on the fly.
- **Interactive Citation Badges**: Inline citations are parsed from the SSE stream and rendered as clickable source badges, allowing users to trace answers to exact file lines.

---

## File Architecture

All files are modularized under the `src/` directory:

```text
src/
├── components/
│   ├── LandingPage.jsx       # Splash page with technical mock terminal text inputs
│   ├── RepoDashboard.jsx     # Side menu directories, active repo stats, and action items
│   └── ChatInterface.jsx     # Chat container, agent/RAG toggle, and streaming message feed
├── utils/
│   └── markdown.js           # Safe, custom markdown-to-React node converter with syntax styling
├── App.jsx                   # Central page router, global indexing states, and layouts
├── index.css                 # Global Tailwind setup, Custom Scrollbars, and glassmorphism styling
└── main.jsx                  # Root React mount node
```

---

## Getting Started

### 1. Prerequisites
- **Node.js 18** or higher
- **npm** or **yarn**

### 2. Local Setup
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The application will boot on **[http://localhost:5173](http://localhost:5173)**.

### 3. Build & Production Preview
To compile the frontend for production:
```bash
# Build the optimized production assets:
npm run build

# Preview the production build locally:
npm run preview
```

---

## Environment Configuration

The frontend uses Vite environment variables:
- **`VITE_BACKEND_URL`**: Specifies the FastAPI backend URL.
  - Defaults to `http://localhost:8000` (for local setup) or `http://localhost:8001` (for Docker Compose mapping).
  
To override, create a `.env` file in the `frontend` root:
```env
VITE_BACKEND_URL=http://localhost:8001
```
