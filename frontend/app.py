"""
RepoSage — Streamlit Chat UI

A clean, dark-themed chat interface for interacting with indexed repositories.

Features:
- GitHub URL input with indexing progress
- Chat interface with streaming responses
- Source code viewer sidebar with file:line citations
- Repository selector for switching between indexed repos
- Conversation history with session state
"""

import os
import json
import requests
import streamlit as st

# ─── Configuration ───
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─── Page Config ───
st.set_page_config(
    page_title="RepoSage — AI Codebase Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for dark theme ───
st.markdown("""
<style>
    /* Dark theme overrides */
    .stApp {
        background-color: #080b10;
    }

    /* Header styling */
    .main-header {
        font-family: 'Segoe UI', sans-serif;
        color: #f0f6ff;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0;
    }
    .main-sub {
        color: #39d353;
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: -10px;
    }

    /* Source citation styling */
    .source-badge {
        display: inline-block;
        background: rgba(57, 211, 83, 0.08);
        border: 1px solid rgba(57, 211, 83, 0.2);
        border-radius: 6px;
        padding: 3px 10px;
        margin: 2px 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.8rem;
        color: #39d353;
    }

    /* Stats card */
    .stats-card {
        background: #0d1219;
        border: 1px solid #1a2535;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }
    .stats-label {
        font-size: 0.75rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stats-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #39d353;
        font-family: 'Courier New', monospace;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0d1219;
        border-right: 1px solid #1a2535;
    }

    /* Chat message styling */
    .stChatMessage {
        background-color: #111820 !important;
        border: 1px solid #1a2535 !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_repo" not in st.session_state:
    st.session_state.current_repo = None
if "repos" not in st.session_state:
    st.session_state.repos = []
if "sources" not in st.session_state:
    st.session_state.sources = []


# ─── Helper Functions ───

def check_backend() -> bool:
    """Check if the backend is running."""
    try:
        r = requests.get(f"{BACKEND_URL}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def fetch_repos():
    """Fetch the list of indexed repositories."""
    try:
        r = requests.get(f"{BACKEND_URL}/repos", timeout=10)
        if r.status_code == 200:
            data = r.json()
            st.session_state.repos = data.get("repos", [])
    except Exception:
        st.session_state.repos = []


def index_repo(github_url: str, token: str = None) -> dict:
    """Send index request to backend."""
    payload = {"github_url": github_url}
    if token:
        payload["github_token"] = token

    r = requests.post(f"{BACKEND_URL}/index", json=payload, timeout=300)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(r.json().get("detail", "Indexing failed"))


def query_repo(repo_name: str, question: str, chat_history: list = None) -> dict:
    """Send query request to backend."""
    payload = {
        "repo_name": repo_name,
        "question": question,
        "k": 6,
    }
    if chat_history:
        payload["chat_history"] = chat_history

    r = requests.post(f"{BACKEND_URL}/query", json=payload, timeout=60)
    if r.status_code == 200:
        return r.json()
    else:
        raise Exception(r.json().get("detail", "Query failed"))


def get_summary(repo_name: str) -> dict:
    """Fetch repository summary."""
    try:
        r = requests.get(f"{BACKEND_URL}/repos/{repo_name}/summary", timeout=30)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


# ─── Sidebar ───
with st.sidebar:
    st.markdown("### 🧠 RepoSage")
    st.markdown("*AI Codebase Intelligence*")
    st.divider()

    # Backend status
    backend_ok = check_backend()
    if backend_ok:
        st.success("✅ Backend connected")
    else:
        st.error("❌ Backend offline")
        st.caption(f"Expected at: {BACKEND_URL}")
        st.caption("Run: `uvicorn main:app --reload`")
        st.stop()

    # Refresh repos
    fetch_repos()

    # Repository selector
    st.markdown("#### 📦 Repositories")

    if st.session_state.repos:
        repo_names = [r["name"] for r in st.session_state.repos]
        selected = st.selectbox(
            "Select repository",
            repo_names,
            index=repo_names.index(st.session_state.current_repo)
            if st.session_state.current_repo in repo_names else 0,
            key="repo_selector",
        )

        if selected != st.session_state.current_repo:
            st.session_state.current_repo = selected
            st.session_state.messages = []
            st.session_state.sources = []
            st.rerun()

        # Show repo stats
        repo_info = next(
            (r for r in st.session_state.repos if r["name"] == selected), None
        )
        if repo_info:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stats-label">Indexed Chunks</div>
                <div class="stats-value">{repo_info.get('chunks', '?')}</div>
            </div>
            """, unsafe_allow_html=True)

        # Delete repo button
        if st.button("🗑️ Delete Repository", use_container_width=True):
            try:
                requests.delete(f"{BACKEND_URL}/repos/{selected}", timeout=10)
                st.session_state.current_repo = None
                st.session_state.messages = []
                st.session_state.sources = []
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete: {e}")

    else:
        st.info("No repositories indexed yet.")
        st.caption("Use the form below to index one.")

    st.divider()

    # Index new repository
    st.markdown("#### 🔗 Index New Repository")

    with st.form("index_form"):
        github_url = st.text_input(
            "GitHub URL",
            placeholder="https://github.com/user/repo",
        )
        github_token = st.text_input(
            "GitHub Token (optional, for private repos)",
            type="password",
            placeholder="ghp_...",
        )
        submitted = st.form_submit_button(
            "🚀 Index Repository",
            use_container_width=True,
        )

    if submitted and github_url:
        with st.spinner("Indexing repository... This may take 1-3 minutes."):
            try:
                result = index_repo(github_url, github_token or None)
                st.success(
                    f"✅ Indexed **{result['repo']}**: "
                    f"{result['files_processed']} files, "
                    f"{result['chunks']} chunks"
                )
                st.session_state.current_repo = result["repo"]
                st.session_state.messages = []
                st.session_state.sources = []
                fetch_repos()
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    st.divider()

    # Source citations
    if st.session_state.sources:
        st.markdown("#### 📍 Last Query Sources")
        for src in st.session_state.sources:
            st.markdown(
                f'<span class="source-badge">{src}</span>',
                unsafe_allow_html=True,
            )


# ─── Main Content ───

# Header
st.markdown('<h1 class="main-header">RepoSage</h1>', unsafe_allow_html=True)
st.markdown('<p class="main-sub">AI Codebase Intelligence System</p>', unsafe_allow_html=True)

if not st.session_state.current_repo:
    # Welcome screen
    st.markdown("---")
    st.markdown("""
    ### 👋 Welcome to RepoSage

    **Paste any GitHub repo URL** in the sidebar and start asking questions about the code.

    #### Example questions you can ask:
    - *"How does authentication work?"*
    - *"Where is the database connection managed?"*
    - *"List all the API endpoints and what they do"*
    - *"Give me a high-level architecture overview"*
    - *"Is there error handling for the payment flow?"*

    #### How it works:
    1. **Index** — Paste a GitHub URL. RepoSage clones it, parses all code files
       using AST-based chunking, and stores embeddings in ChromaDB.
    2. **Ask** — Type a natural language question. The RAG engine retrieves
       relevant code chunks and generates an answer with file:line citations.
    3. **Explore** — Every answer includes exact source locations you can verify.
    """)
    st.stop()


# Show repo summary on first visit
if not st.session_state.messages:
    summary = get_summary(st.session_state.current_repo)
    if summary and summary.get("summary"):
        with st.expander(
            f"📊 {st.session_state.current_repo} — Repository Overview",
            expanded=True,
        ):
            st.markdown(summary["summary"])
            meta = summary.get("metadata", {})
            if meta:
                cols = st.columns(3)
                cols[0].metric("Total Chunks", meta.get("total_chunks", "?"))
                cols[1].metric("Languages", ", ".join(meta.get("languages", [])))
                cols[2].metric("Files Sampled", meta.get("files_sampled", "?"))


# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# Chat input
if prompt := st.chat_input(
    f"Ask about {st.session_state.current_repo}...",
    key="chat_input",
):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build chat history for context
    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-6:]  # Last 3 turns
    ]

    # Query the backend
    with st.chat_message("assistant"):
        with st.spinner("Searching codebase..."):
            try:
                result = query_repo(
                    st.session_state.current_repo,
                    prompt,
                    chat_history,
                )
                answer = result["answer"]
                sources = result.get("sources", [])
                chunks_used = result.get("chunks_used", 0)

                st.markdown(answer)

                # Show sources inline
                if sources:
                    st.markdown("---")
                    source_html = " ".join(
                        f'<span class="source-badge">{s}</span>' for s in sources
                    )
                    st.markdown(
                        f"📍 **Sources:** {source_html}",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Retrieved {chunks_used} code chunks")

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                })
                st.session_state.sources = sources

            except Exception as e:
                st.error(f"❌ Query failed: {e}")
