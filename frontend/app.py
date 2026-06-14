"""
RepoSage — Premium AI Codebase Intelligence Dashboard (v2)

A world-class Streamlit frontend with:
- Compact hero that fits above the fold
- SVG-based icons for premium feel
- Glassmorphic dark theme with ambient glow effects
- Animated landing page with feature showcase
- ChatGPT-style conversation interface with sticky input
- Source code citations with syntax highlighting
- Modern sidebar with brand identity
"""

import os
import json
import requests
import streamlit as st

# ─── Configuration ───
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

# ─── Page Config ───
st.set_page_config(
    page_title="RepoSage — AI Codebase Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── SVG Icon Library ───
ICONS = {
    "architecture": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#818CF8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><path d="M10 6.5h4M6.5 10v4M17.5 10v4M10 17.5h4"/></svg>',
    "api": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#A78BFA" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16M4 12h16M4 18h16"/><circle cx="8" cy="6" r="1.5" fill="#A78BFA"/><circle cx="16" cy="12" r="1.5" fill="#A78BFA"/><circle cx="11" cy="18" r="1.5" fill="#A78BFA"/></svg>',
    "security": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#34D399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2l8 4v6c0 5.25-3.5 9.74-8 11-4.5-1.26-8-5.75-8-11V6l8-4z"/><path d="M9 12l2 2 4-4"/></svg>',
    "dependency": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#FBBF24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="6" r="3"/><circle cx="12" cy="18" r="3"/><path d="M8.5 7.5L10.5 16M15.5 7.5L13.5 16"/></svg>',
    "search": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#22D3EE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/><path d="M8 8l6 6"/></svg>',
    "ai": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#F472B6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93"/><path d="M8.5 6A4 4 0 0 1 12 2"/><circle cx="12" cy="14" r="4"/><path d="M12 18v4M8 22h8"/><path d="M6 14a6 6 0 0 0 12 0"/></svg>',
    "rocket": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>',
    "play": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
}

# ─── Premium CSS Design System ───
st.markdown("""
<style>
    /* ═══════ Google Fonts ═══════ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* ═══════ CSS Custom Properties ═══════ */
    :root {
        --bg-primary: #0B1220;
        --bg-surface: #111827;
        --bg-surface-2: #1E293B;
        --bg-surface-3: #0F172A;
        --border: rgba(30, 41, 59, 0.8);
        --border-hover: #334155;
        --primary: #6366F1;
        --primary-light: #818CF8;
        --primary-glow: rgba(99, 102, 241, 0.15);
        --primary-glow-strong: rgba(99, 102, 241, 0.3);
        --secondary: #8B5CF6;
        --success: #10B981;
        --success-glow: rgba(16, 185, 129, 0.15);
        --warning: #F59E0B;
        --danger: #EF4444;
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --text-tertiary: #64748B;
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
        --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    }

    /* ═══════ Global Overrides ═══════ */
    .stApp {
        background: var(--bg-primary) !important;
        font-family: var(--font-sans) !important;
    }

    /* Ambient glow orbs */
    .stApp::before {
        content: '';
        position: fixed;
        top: -200px;
        right: -100px;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(99,102,241,0.06) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }
    .stApp::after {
        content: '';
        position: fixed;
        bottom: -200px;
        left: -100px;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(139,92,246,0.05) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Scrollbar styling */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--bg-surface-2); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-hover); }

    /* ═══════ Sidebar ═══════ */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.92) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(99, 102, 241, 0.06) !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0.75rem !important;
        padding-bottom: 0.5rem !important;
    }

    /* Sidebar brand */
    .sidebar-brand {
        padding: 0.25rem 0 0.75rem 0;
        border-bottom: 1px solid transparent;
        border-image: linear-gradient(90deg, rgba(99,102,241,0.5), rgba(139,92,246,0.3), transparent) 1;
        margin-bottom: 0.75rem;
    }
    .sidebar-brand-name {
        font-family: var(--font-sans);
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sidebar-brand-name .logo-icon {
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border-radius: 7px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.85rem;
        flex-shrink: 0;
        box-shadow: 0 2px 12px rgba(99, 102, 241, 0.3);
    }
    .sidebar-brand-sub {
        font-size: 0.7rem;
        color: var(--text-tertiary);
        font-weight: 500;
        margin-top: 2px;
        padding-left: 36px;
        letter-spacing: 0.5px;
    }

    /* Status indicator */
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 5px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        letter-spacing: 0.3px;
    }
    .status-online {
        background: rgba(16, 185, 129, 0.06);
        border: 1px solid rgba(16, 185, 129, 0.12);
        color: var(--success);
    }
    .status-offline {
        background: rgba(239, 68, 68, 0.06);
        border: 1px solid rgba(239, 68, 68, 0.12);
        color: var(--danger);
    }
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .status-dot.online {
        background: var(--success);
        box-shadow: 0 0 6px var(--success);
        animation: pulse-dot 2s infinite;
    }
    .status-dot.offline {
        background: var(--danger);
    }
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    /* Sidebar section labels */
    .sidebar-section-label {
        font-size: 0.6rem;
        font-weight: 700;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 0.75rem 0 0.35rem 0;
    }

    /* Sidebar stat row */
    .sidebar-stat-row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 10px;
        background: rgba(30, 41, 59, 0.3);
        border-radius: 6px;
        margin: 3px 0;
    }
    .sidebar-stat-icon { font-size: 0.8rem; width: 18px; text-align: center; }
    .sidebar-stat-label { font-size: 0.72rem; color: var(--text-secondary); flex: 1; }
    .sidebar-stat-value { font-family: var(--font-mono); font-size: 0.78rem; font-weight: 600; color: var(--primary-light); }

    /* ═══════ Main Content ═══════ */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1100px !important;
    }

    /* ═══════ Hero Section ═══════ */
    .hero-container {
        text-align: center;
        padding: 1rem 1rem 0.75rem 1rem;
        animation: fadeInUp 0.6s ease-out;
        position: relative;
    }
    .hero-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border-radius: 14px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        margin-bottom: 0.6rem;
        box-shadow: 0 4px 24px rgba(99, 102, 241, 0.35);
        animation: float 4s ease-in-out infinite;
    }
    .hero-title {
        font-family: var(--font-sans);
        font-size: 2.5rem;
        font-weight: 900;
        letter-spacing: -1.5px;
        line-height: 1.05;
        margin-bottom: 0.15rem;
        background: linear-gradient(135deg, #F1F5F9 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-tagline {
        font-family: var(--font-sans);
        font-size: 1.1rem;
        font-weight: 300;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        letter-spacing: -0.3px;
    }
    .hero-tagline .highlight {
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
    }
    .hero-desc {
        font-size: 0.85rem;
        color: var(--text-tertiary);
        max-width: 520px;
        margin: 0 auto 1rem auto;
        line-height: 1.6;
    }

    /* Hero CTA */
    .hero-cta-row {
        display: flex;
        gap: 10px;
        justify-content: center;
        flex-wrap: wrap;
    }
    .cta-primary {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 10px 22px;
        background: linear-gradient(135deg, #6366F1, #7C3AED);
        color: white !important;
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-size: 0.85rem;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
        cursor: pointer;
        border: none;
    }
    .cta-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(99, 102, 241, 0.45);
    }
    .cta-secondary {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 10px 22px;
        background: rgba(30, 41, 59, 0.5);
        color: var(--text-secondary) !important;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        font-weight: 500;
        font-size: 0.85rem;
        text-decoration: none;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .cta-secondary:hover {
        border-color: var(--primary);
        color: var(--primary-light) !important;
        background: var(--primary-glow);
    }

    /* ═══════ Feature Cards ═══════ */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin: 1.25rem 0;
        animation: fadeInUp 0.6s ease-out 0.15s backwards;
    }
    .feature-card {
        background: rgba(17, 24, 39, 0.5);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(30, 41, 59, 0.6);
        border-radius: var(--radius-md);
        padding: 16px 18px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: default;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.08);
        background: rgba(17, 24, 39, 0.7);
    }
    .feature-icon-wrap {
        width: 38px;
        height: 38px;
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 10px;
    }
    .fi-indigo   { background: rgba(99, 102, 241, 0.1); }
    .fi-violet   { background: rgba(139, 92, 246, 0.1); }
    .fi-emerald  { background: rgba(16, 185, 129, 0.1); }
    .fi-amber    { background: rgba(245, 158, 11, 0.1); }
    .fi-cyan     { background: rgba(6, 182, 212, 0.1); }
    .fi-rose     { background: rgba(244, 63, 94, 0.1); }
    .feature-card-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    .feature-card-desc {
        font-size: 0.72rem;
        color: var(--text-tertiary);
        line-height: 1.5;
    }

    /* ═══════ How It Works ═══════ */
    .how-section {
        margin: 1.5rem 0 1rem 0;
        animation: fadeInUp 0.6s ease-out 0.3s backwards;
    }
    .section-label {
        font-size: 0.6rem;
        font-weight: 700;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 2px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .how-steps {
        display: flex;
        gap: 12px;
        justify-content: center;
        align-items: stretch;
    }
    .how-step {
        flex: 1;
        text-align: center;
        padding: 16px 12px;
        background: rgba(17, 24, 39, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.6);
        border-radius: var(--radius-md);
        position: relative;
    }
    .how-step-number {
        width: 28px;
        height: 28px;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.75rem;
        color: white;
        margin-bottom: 8px;
    }
    .how-step-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 4px;
    }
    .how-step-desc {
        font-size: 0.72rem;
        color: var(--text-tertiary);
        line-height: 1.45;
    }
    .step-connector {
        display: flex;
        align-items: center;
        color: var(--text-tertiary);
        font-size: 0.9rem;
        padding: 0 2px;
        opacity: 0.4;
    }

    /* ═══════ Example Prompts ═══════ */
    .prompts-section {
        margin: 1rem 0 1.5rem 0;
        text-align: center;
        animation: fadeInUp 0.6s ease-out 0.4s backwards;
    }
    .prompts-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        justify-content: center;
    }
    .prompt-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 7px 14px;
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.7);
        border-radius: 20px;
        font-size: 0.75rem;
        color: var(--text-secondary);
        transition: all 0.25s ease;
        cursor: default;
        font-family: var(--font-sans);
    }
    .prompt-pill:hover {
        border-color: rgba(99, 102, 241, 0.3);
        color: var(--primary-light);
        background: var(--primary-glow);
        transform: translateY(-1px);
    }

    /* ═══════ Repo Header ═══════ */
    .repo-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 4px 0;
        animation: fadeInUp 0.4s ease-out;
    }
    .repo-header-icon {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg, #6366F1, #8B5CF6);
        border-radius: var(--radius-sm);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
    }
    .repo-header-name {
        font-family: var(--font-sans);
        font-size: 1.25rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }
    .repo-header-sub {
        font-size: 0.72rem;
        color: var(--text-tertiary);
    }

    /* ═══════ Suggested Q Cards ═══════ */
    .suggested-q-card {
        padding: 10px 14px;
        background: rgba(30, 41, 59, 0.25);
        border: 1px solid rgba(30, 41, 59, 0.6);
        border-radius: var(--radius-sm);
        font-size: 0.78rem;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.25s ease;
    }
    .suggested-q-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: var(--primary-glow);
        color: var(--primary-light);
    }

    /* ═══════ Chat Messages ═══════ */
    .stChatMessage {
        border-radius: var(--radius-md) !important;
        border: 1px solid rgba(30, 41, 59, 0.5) !important;
        margin-bottom: 8px !important;
        animation: fadeInUp 0.3s ease-out;
    }
    [data-testid="stChatMessageContent"] {
        font-family: var(--font-sans) !important;
        font-size: 0.88rem !important;
        line-height: 1.65 !important;
    }
    .stChatMessage pre {
        background: var(--bg-surface-3) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        font-family: var(--font-mono) !important;
        font-size: 0.8rem !important;
    }
    .stChatMessage code {
        font-family: var(--font-mono) !important;
        font-size: 0.8rem !important;
    }

    /* ═══════ Source Badges ═══════ */
    .source-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        background: rgba(99, 102, 241, 0.07);
        border: 1px solid rgba(99, 102, 241, 0.12);
        border-radius: 16px;
        padding: 3px 10px;
        margin: 2px 3px;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        font-weight: 500;
        color: var(--primary-light);
        transition: all 0.2s ease;
    }
    .source-badge:hover {
        background: rgba(99, 102, 241, 0.14);
        transform: translateY(-1px);
    }
    .source-badge::before { content: '📄'; font-size: 0.65rem; }

    /* ═══════ Chat Input ═══════ */
    .stChatInput > div {
        background: var(--bg-surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
    }
    .stChatInput textarea { font-family: var(--font-sans) !important; }

    /* ═══════ Form Inputs ═══════ */
    .stTextInput > div > div > input {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(30, 41, 59, 0.8) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
        font-family: var(--font-sans) !important;
        font-size: 0.82rem !important;
        padding: 8px 12px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 2px var(--primary-glow) !important;
    }
    .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(30, 41, 59, 0.8) !important;
        border-radius: 6px !important;
    }

    /* ═══════ Buttons ═══════ */
    .stButton > button {
        border-radius: 6px !important;
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        transition: all 0.25s ease !important;
        border: 1px solid var(--border) !important;
        padding: 0.4rem 0.8rem !important;
    }
    .stButton > button:hover {
        border-color: rgba(99, 102, 241, 0.4) !important;
        box-shadow: 0 2px 12px var(--primary-glow) !important;
    }
    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #6366F1, #7C3AED) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        font-size: 0.82rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 12px rgba(99, 102, 241, 0.25) !important;
    }
    .stFormSubmitButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.35) !important;
    }

    /* ═══════ Expander ═══════ */
    .streamlit-expanderHeader {
        background: var(--bg-surface) !important;
        border-radius: var(--radius-sm) !important;
        font-family: var(--font-sans) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }

    /* ═══════ Metrics ═══════ */
    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.25);
        border: 1px solid rgba(30, 41, 59, 0.5);
        border-radius: var(--radius-sm);
        padding: 12px !important;
    }
    [data-testid="stMetricLabel"] {
        font-family: var(--font-sans) !important;
        font-size: 0.68rem !important;
        color: var(--text-tertiary) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetricValue"] {
        font-family: var(--font-mono) !important;
        font-size: 1.1rem !important;
        color: var(--primary-light) !important;
    }

    /* ═══════ Dividers & Alerts ═══════ */
    hr { border-color: rgba(30, 41, 59, 0.5) !important; }
    .stSuccess {
        background: rgba(16, 185, 129, 0.06) !important;
        border: 1px solid rgba(16, 185, 129, 0.15) !important;
        border-radius: 6px !important;
    }
    .stError {
        background: rgba(239, 68, 68, 0.06) !important;
        border: 1px solid rgba(239, 68, 68, 0.15) !important;
        border-radius: 6px !important;
    }
    .stInfo {
        background: rgba(99, 102, 241, 0.06) !important;
        border: 1px solid rgba(99, 102, 241, 0.1) !important;
        border-radius: 6px !important;
    }

    /* ═══════ Animations ═══════ */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(16px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
    }

    /* ═══════ Responsive ═══════ */
    @media (max-width: 768px) {
        .features-grid { grid-template-columns: 1fr !important; }
        .how-steps { flex-direction: column; align-items: center; }
        .step-connector { display: none; }
        .hero-title { font-size: 1.8rem !important; }
    }
    @media (max-width: 1024px) {
        .features-grid { grid-template-columns: repeat(2, 1fr) !important; }
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


# ═══════════════════════════════════════════════════════════
# ─── Sidebar ───
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-name">
            <div class="logo-icon">🧠</div>
            RepoSage
        </div>
        <div class="sidebar-brand-sub">AI Codebase Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    # Backend status
    backend_ok = check_backend()
    if backend_ok:
        st.markdown('<div class="status-indicator status-online"><div class="status-dot online"></div>System Online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-indicator status-offline"><div class="status-dot offline"></div>Backend Offline</div>', unsafe_allow_html=True)
        st.caption(f"Expected at: `{BACKEND_URL}`")
        st.stop()

    fetch_repos()

    # Repositories
    st.markdown('<div class="sidebar-section-label">Repositories</div>', unsafe_allow_html=True)

    if st.session_state.repos:
        repo_names = [r["name"] for r in st.session_state.repos]
        selected = st.selectbox(
            "Select repository",
            repo_names,
            index=repo_names.index(st.session_state.current_repo)
            if st.session_state.current_repo in repo_names else 0,
            key="repo_selector",
            label_visibility="collapsed",
        )

        if selected != st.session_state.current_repo:
            st.session_state.current_repo = selected
            st.session_state.messages = []
            st.session_state.sources = []
            st.rerun()

        repo_info = next(
            (r for r in st.session_state.repos if r["name"] == selected), None
        )
        if repo_info:
            chunks = repo_info.get('chunks', '?')
            st.markdown(f"""
            <div class="sidebar-stat-row">
                <span class="sidebar-stat-icon">📊</span>
                <span class="sidebar-stat-label">Chunks</span>
                <span class="sidebar-stat-value">{chunks}</span>
            </div>
            """, unsafe_allow_html=True)

        if st.button("🗑  Delete", use_container_width=True):
            try:
                requests.delete(f"{BACKEND_URL}/repos/{selected}", timeout=10)
                st.session_state.current_repo = None
                st.session_state.messages = []
                st.session_state.sources = []
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")
    else:
        st.markdown("""
        <div style="text-align:center; padding:14px 10px; background:rgba(30,41,59,0.2); border:1px dashed rgba(30,41,59,0.5); border-radius:8px; margin:2px 0;">
            <div style="font-size:1.2rem; margin-bottom:4px; opacity:0.6;">📂</div>
            <div style="font-size:0.72rem; color:var(--text-tertiary);">No repos indexed yet</div>
        </div>
        """, unsafe_allow_html=True)

    # Index form
    st.markdown('<div class="sidebar-section-label">Index New Repo</div>', unsafe_allow_html=True)

    with st.form("index_form"):
        github_url = st.text_input("URL", placeholder="https://github.com/user/repo", label_visibility="collapsed")
        github_token = st.text_input("Token", type="password", placeholder="Token (optional, private repos)", label_visibility="collapsed")
        submitted = st.form_submit_button("🚀 Index Repository", use_container_width=True)

    if submitted and github_url:
        with st.spinner("Indexing... (1-3 min)"):
            try:
                result = index_repo(github_url, github_token or None)
                st.success(f"✅ **{result['repo']}** — {result['files_processed']} files, {result['chunks']} chunks")
                st.session_state.current_repo = result["repo"]
                st.session_state.messages = []
                st.session_state.sources = []
                fetch_repos()
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    # Sources
    if st.session_state.sources:
        st.markdown('<div class="sidebar-section-label">Sources</div>', unsafe_allow_html=True)
        source_html = " ".join(f'<span class="source-badge">{src}</span>' for src in st.session_state.sources)
        st.markdown(source_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ─── Main Content ───
# ═══════════════════════════════════════════════════════════

if not st.session_state.current_repo:
    # ═══════ LANDING PAGE ═══════

    # Hero
    st.markdown(f"""
    <div class="hero-container">
        <div class="hero-logo">🧠</div>
        <div class="hero-title">RepoSage</div>
        <div class="hero-tagline">
            Understand Any Codebase <span class="highlight">in Minutes</span>
        </div>
        <div class="hero-desc">
            Index any GitHub repo and ask natural language questions.
            Get answers with precise <strong style="color:var(--text-secondary)">file:line</strong> citations, powered by RAG and local LLMs.
        </div>
        <div class="hero-cta-row">
            <span class="cta-primary">{ICONS['rocket']} Index Repository</span>
            <span class="cta-secondary">{ICONS['play']} How It Works</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Feature Cards
    st.markdown(f"""
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon-wrap fi-indigo">{ICONS['architecture']}</div>
            <div class="feature-card-title">Architecture Analysis</div>
            <div class="feature-card-desc">Map module connections, entry points, and overall system design.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-wrap fi-violet">{ICONS['api']}</div>
            <div class="feature-card-title">API Discovery</div>
            <div class="feature-card-desc">Find all endpoints, routes, schemas, and middleware chains.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-wrap fi-emerald">{ICONS['security']}</div>
            <div class="feature-card-title">Security Review</div>
            <div class="feature-card-desc">Identify auth patterns, input validation, and token handling.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-wrap fi-amber">{ICONS['dependency']}</div>
            <div class="feature-card-title">Dependency Mapping</div>
            <div class="feature-card-desc">Trace function calls with a knowledge graph from AST analysis.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-wrap fi-cyan">{ICONS['search']}</div>
            <div class="feature-card-title">Code Search</div>
            <div class="feature-card-desc">Hybrid semantic + BM25 search with multi-query expansion.</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon-wrap fi-rose">{ICONS['ai']}</div>
            <div class="feature-card-title">AI Q&A</div>
            <div class="feature-card-desc">Ask anything in plain English. Get cited source answers.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # How It Works
    st.markdown("""
    <div class="how-section">
        <div class="section-label">How It Works</div>
        <div class="how-steps">
            <div class="how-step">
                <div class="how-step-number">1</div>
                <div class="how-step-title">Paste URL</div>
                <div class="how-step-desc">Drop any GitHub repo URL into the sidebar</div>
            </div>
            <div class="step-connector">→</div>
            <div class="how-step">
                <div class="how-step-number">2</div>
                <div class="how-step-title">AI Indexes</div>
                <div class="how-step-desc">AST-aware chunking creates semantic code blocks</div>
            </div>
            <div class="step-connector">→</div>
            <div class="how-step">
                <div class="how-step-number">3</div>
                <div class="how-step-title">Ask Anything</div>
                <div class="how-step-desc">Get cited answers from relevant code chunks</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Example Prompts
    st.markdown("""
    <div class="prompts-section">
        <div class="section-label">Try Asking</div>
        <div class="prompts-row">
            <span class="prompt-pill">💬 How does authentication work?</span>
            <span class="prompt-pill">📡 List all API endpoints</span>
            <span class="prompt-pill">🗄️ Where is the database connection?</span>
            <span class="prompt-pill">🏗️ Architecture overview</span>
            <span class="prompt-pill">⚠️ Error handling patterns</span>
            <span class="prompt-pill">🔒 How are secrets managed?</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ═══════ CHAT INTERFACE (repo selected) ═══════

# Repo header
st.markdown(f"""
<div class="repo-header">
    <div class="repo-header-icon">📦</div>
    <div>
        <div class="repo-header-name">{st.session_state.current_repo}</div>
        <div class="repo-header-sub">Ask questions about this codebase</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Show summary on first visit
if not st.session_state.messages:
    summary = get_summary(st.session_state.current_repo)
    if summary and summary.get("summary"):
        with st.expander(f"📊 Repository Overview", expanded=False):
            st.markdown(summary["summary"])
            meta = summary.get("metadata", {})
            if meta:
                cols = st.columns(3)
                cols[0].metric("Chunks", meta.get("total_chunks", "?"))
                languages = [l for l in (meta.get("languages", []) or []) if l]
                if len(languages) > 3:
                    lang_str = ", ".join(languages[:2]) + f" (+{len(languages)-2} more)"
                elif languages:
                    lang_str = ", ".join(languages)
                else:
                    lang_str = "None"
                cols[1].metric("Languages", lang_str)
                cols[2].metric("Files", meta.get("files_sampled", "?"))

    # Suggested Questions
    st.markdown('<div class="section-label" style="text-align:left; margin-top:0.5rem;">Suggested Questions</div>', unsafe_allow_html=True)

    suggested_questions = [
        ("🏗️", "Give me a high-level architecture overview"),
        ("📡", "List all the API endpoints and what they do"),
        ("🔐", "How does authentication work?"),
        ("⚠️", "What error handling patterns are used?"),
    ]

    cols = st.columns(2)
    for i, (icon, question) in enumerate(suggested_questions):
        with cols[i % 2]:
            if st.button(f"{icon}  {question}", key=f"sq_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": question})
                with st.spinner("🔍 Searching codebase..."):
                    try:
                        result = query_repo(st.session_state.current_repo, question)
                        st.session_state.messages.append({"role": "assistant", "content": result["answer"]})
                        st.session_state.sources = result.get("sources", [])
                    except Exception as e:
                        st.session_state.messages.append({"role": "assistant", "content": f"❌ Query failed: {e}"})
                st.rerun()

    st.markdown("---")


# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and st.session_state.sources and msg == st.session_state.messages[-1]:
            sources = st.session_state.sources
            if sources:
                st.markdown("---")
                source_html = " ".join(f'<span class="source-badge">{s}</span>' for s in sources)
                st.markdown(f"**Sources:** {source_html}", unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input(f"Ask about {st.session_state.current_repo}...", key="chat_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[-6:]
    ]

    with st.chat_message("assistant"):
        with st.spinner("🔍 Searching codebase..."):
            try:
                result = query_repo(st.session_state.current_repo, prompt, chat_history)
                answer = result["answer"]
                sources = result.get("sources", [])
                chunks_used = result.get("chunks_used", 0)

                st.markdown(answer)

                if sources:
                    st.markdown("---")
                    source_html = " ".join(f'<span class="source-badge">{s}</span>' for s in sources)
                    st.markdown(f"**Sources:** {source_html}", unsafe_allow_html=True)
                    st.caption(f"Retrieved {chunks_used} chunks via multi-query RAG")

                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.session_state.sources = sources
            except Exception as e:
                st.error(f"❌ Query failed: {e}")
