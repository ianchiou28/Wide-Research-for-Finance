
import os

content = r"""<!DOCTYPE html>
<html lang="zh-CN" :data-theme="theme">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wide Research for Finance - AI 金融情报中心</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --warning-gradient: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            --card-bg: rgba(8, 12, 28, 0.92);
            --card-hover: rgba(15, 23, 42, 0.9);
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border-color: rgba(148, 163, 184, 0.25);
            --neon-green: #4ade80;
        }

        [data-theme="light"] {
            --card-bg: rgba(255, 255, 255, 0.92);
            --card-hover: rgba(248, 250, 252, 0.9);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --border-color: rgba(148, 163, 184, 0.35);
            --neon-green: #16a34a;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: radial-gradient(circle at top, rgba(59, 130, 246, 0.08), transparent 45%), #040714;
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
            transition: background-color 0.4s ease, color 0.4s ease;
            overflow-x: hidden;
        }

        [data-theme="light"] body {
            background: radial-gradient(circle at top, rgba(129, 140, 248, 0.2), transparent 45%), #f8fafc;
        }

        a { text-decoration: none; color: inherit; }

        .navbar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(3, 6, 17, 0.95);
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            box-shadow: 0 20px 60px -30px rgba(15, 23, 42, 0.75);
        }

        [data-theme="light"] .navbar {
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 20px 60px -35px rgba(15, 23, 42, 0.25);
        }

        .nav-container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
        }

        .nav-brand {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .nav-logo {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: var(--primary-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            color: white;
            box-shadow: 0 10px 30px -10px rgba(102, 126, 234, 0.8);
        }

        .nav-title h1 {
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        .nav-title p {
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .menu-toggle {
            display: none;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            color: var(--text-primary);
            font-size: 1.25rem;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .menu-toggle:hover {
            background: var(--card-hover);
            box-shadow: 0 10px 30px -15px rgba(15, 23, 42, 0.7);
        }

        .nav-overlay {
            position: fixed;
            inset: 0;
            background: rgba(2, 6, 23, 0.55);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s ease;
            z-index: 900;
        }

        .nav-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .mobile-drawer {
            position: fixed;
            top: 0;
            right: -320px;
            width: min(80vw, 300px);
            height: 100vh;
            background: rgba(4, 8, 22, 0.98);
            border-left: 1px solid rgba(148, 163, 184, 0.2);
            box-shadow: -20px 0 60px -30px rgba(15, 23, 42, 0.8);
            padding: 1.75rem 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            transition: right 0.3s ease;
            z-index: 950;
        }

        body.drawer-open {
            overflow: hidden;
        }

        [data-theme="light"] .mobile-drawer {
            background: rgba(255, 255, 255, 0.98);
            border-color: rgba(148, 163, 184, 0.35);
            box-shadow: -20px 0 60px -30px rgba(15, 23, 42, 0.2);
        }

        .mobile-drawer.open {
            right: 0;
        }

        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .drawer-close {
            border: none;
            background: transparent;
            color: var(--text-primary);
            font-size: 1.5rem;
            cursor: pointer;
        }

        .drawer-links {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .drawer-links a {
            padding: 0.8rem 1rem;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: var(--text-primary);
            font-weight: 600;
            background: rgba(148, 163, 184, 0.08);
        }

        .drawer-meta {
            margin-top: auto;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .hero {
            padding: 4.5rem 2rem 2rem;
            max-width: 1500px;
            margin: 0 auto;
            margin-top: 4rem;
            position: relative;
            z-index: 1;
        }

        .hero::before {
            content: '';
            position: absolute;
            top: -90px;
            left: 50%;
            transform: translateX(-50%);
            width: min(1200px, 100%);
            height: calc(100% + 180px);
            border-radius: 80px;
            background: radial-gradient(circle at 50% 15%, rgba(59, 130, 246, 0.25), transparent 65%);
            pointer-events: none;
            animation: pulse 10s ease-in-out infinite;
            z-index: 0;
        }

        html[data-theme="light"] .hero::before {
            background: radial-gradient(circle at 50% 15%, rgba(99, 102, 241, 0.18), transparent 65%);
        }

        .hero-simple {
            max-width: 900px;
            margin: 0 auto;
            padding: clamp(1.75rem, 4vw, 3rem);
            border-radius: 30px;
            border: 1px solid rgba(148, 163, 184, 0.28);
            background: rgba(4, 8, 22, 0.85);
            box-shadow: 0 35px 80px -35px rgba(2, 6, 23, 0.85);
            backdrop-filter: blur(28px) saturate(180%);
            -webkit-backdrop-filter: blur(28px) saturate(180%);
            display: flex;
            flex-direction: column;
            gap: 1rem;
            position: relative;
            overflow: hidden;
        }

        .hero-simple::after {
            content: '';
            position: absolute;
            inset: 18px;
            border-radius: 24px;
            border: 1px dashed rgba(148, 163, 184, 0.22);
            pointer-events: none;
        }

        .hero-simple > * {
            position: relative;
            z-index: 1;
        }

        [data-theme="light"] .hero-simple {
            background: rgba(255, 255, 255, 0.95);
            border-color: rgba(148, 163, 184, 0.35);
            box-shadow: 0 35px 70px -45px rgba(15, 23, 42, 0.25);
        }

        .hero-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.45rem 1rem;
            border-radius: 999px;
            border: 1px solid rgba(59, 130, 246, 0.4);
            background: rgba(59, 130, 246, 0.12);
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.15em;
            color: #93c5fd;
        }

        .hero h2 {
            font-size: clamp(2.4rem, 4vw, 3.6rem);
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0;
            background: linear-gradient(120deg, #f5a5ff, #9bb7ff, #8be7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(0 0 35px rgba(99, 102, 241, 0.35));
        }

        .hero p {
            font-size: 1.05rem;
            color: var(--text-secondary);
            max-width: 640px;
            margin: 0;
        }
        .nav-link {
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--text-secondary);
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        .nav-link:hover {
            background: var(--card-hover);
            color: var(--text-primary);
        }
        
        .nav-link.active {
            background: var(--primary-gradient);
            color: white;
        }

        .nav-status {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 0.9rem;
            border-radius: 999px;
            border: 1px solid rgba(56, 189, 248, 0.4);
            background: rgba(56, 189, 248, 0.08);
            color: #7dd3fc;
            font-size: 0.8rem;
            font-weight: 600;
        }

        [data-theme="light"] .nav-status {
            background: rgba(14, 165, 233, 0.1);
            border-color: rgba(14, 165, 233, 0.35);
            color: #0284c7;
        }
        
        .theme-toggle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 1.25rem;
        }
        
        .theme-toggle:hover {
            background: var(--card-hover);
            transform: rotate(15deg) scale(1.1);
        }
        
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .grid-2 {
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
        }
        
        .grid-3 {
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        .grid-4 {
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }

        .dashboard-section {
            margin-bottom: 2.5rem;
            position: relative;
            z-index: 1;
        }

        .section-heading {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .section-heading p {
            text-transform: uppercase;
            letter-spacing: 0.3em;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.35rem;
        }

        .section-heading h3 {
            font-size: 1.6rem;
            color: var(--text-primary);
        }

        .heading-meta {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .heading-meta span,
        .heading-meta .heading-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.4rem 0.9rem;
            border-radius: 999px;
            font-size: 0.8rem;
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: rgba(148, 163, 184, 0.08);
            color: var(--text-secondary);
        }

        .heading-time {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            color: var(--text-muted);
        }

        .heading-time strong {
            color: var(--text-primary);
            margin-left: 0.35rem;
            font-size: 0.95rem;
        }

        .status-pill {
            background: rgba(34, 197, 94, 0.18) !important;
            border-color: rgba(34, 197, 94, 0.55) !important;
            color: #4ade80 !important;
            box-shadow: 0 8px 20px -10px rgba(34, 197, 94, 0.6);
        }

        [data-theme="light"] .status-pill {
            background: rgba(34, 197, 94, 0.22) !important;
            border-color: rgba(22, 163, 74, 0.65) !important;
            color: #065f46 !important;
            box-shadow: none;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            position: relative;
        }

        .status-dot::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: inherit;
            box-shadow: 0 0 0 0 currentColor;
            animation: ping 2s infinite;
        }

        .status-dot.live {
            color: var(--neon-green);
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1.5rem;
        }

        .insight-grid.dual {
            grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
        }
        
        /* Card Styles */
        .card {
            background: rgba(8, 12, 28, 0.92);
            border-radius: 24px;
            padding: 1.5rem;
            border: 1px solid rgba(148, 163, 184, 0.2);
            box-shadow: 
                0 20px 60px -10px rgba(0, 0, 0, 0.4),
                0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
        }
        
        [data-theme="light"] .card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.3);
            box-shadow: 
                0 20px 60px -10px rgba(0, 0, 0, 0.15),
                0 0 1px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.8);
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--primary-gradient);
            opacity: 0;
            transition: opacity 0.3s ease;
            border-radius: 24px 24px 0 0;
        }
        
        .card:hover {
            transform: translateY(-12px) scale(1.02);
            box-shadow: 
                0 30px 80px -10px rgba(102, 126, 234, 0.5),
                0 0 40px rgba(102, 126, 234, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.1),
                inset 0 0 0 1px rgba(102, 126, 234, 0.4);
            border-color: rgba(102, 126, 234, 0.7);
            backdrop-filter: blur(30px) saturate(200%);
        }
        
        .card:hover::before {
            opacity: 1;
            animation: shimmer 2s ease-in-out infinite;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .card-title {
            font-size: 1.125rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .card-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }
        
        .card-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 600;
            background: rgba(59, 130, 246, 0.12);
            color: #bfdbfe;
            border: 1px solid rgba(59, 130, 246, 0.35);
        }

        [data-theme="light"] .card-badge {
            background: rgba(59, 130, 246, 0.22);
            color: #1e40af;
            border-color: rgba(37, 99, 235, 0.45);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.6);
        }
        
        /* Sentiment Component */
        .sentiment-box {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
        }
        
        .sentiment-item {
            position: relative;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            overflow: hidden;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        
        .sentiment-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            opacity: 0.1;
            z-index: 0;
        }
        
        .sentiment-positive {
            background: rgba(16, 185, 129, 0.05);
            border-color: rgba(16, 185, 129, 0.3);
        }
        
        .sentiment-positive::before {
            background: linear-gradient(135deg, #10b981, #059669);
        }
        
        .sentiment-neutral {
            background: rgba(251, 191, 36, 0.05);
            border-color: rgba(251, 191, 36, 0.3);
        }
        
        .sentiment-neutral::before {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
        }
        
        .sentiment-negative {
            background: rgba(239, 68, 68, 0.05);
            border-color: rgba(239, 68, 68, 0.3);
        }
        
        .sentiment-negative::before {
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }
        
        .sentiment-label {
            position: relative;
            z-index: 1;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }
        
        .sentiment-value {
            position: relative;
            z-index: 1;
            font-size: 2rem;
            font-weight: 800;
            margin: 0.5rem 0;
        }
        
        .sentiment-positive .sentiment-value {
            color: #10b981;
        }
        
        .sentiment-neutral .sentiment-value {
            color: #fbbf24;
        }
        
        .sentiment-negative .sentiment-value {
            color: #ef4444;
        }
        
        .sentiment-status {
            position: relative;
            z-index: 1;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-secondary);
        }
        
        /* Stock List */
        .stock-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        
        .stock-item {
            padding: 1rem;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .stock-item:hover {
            background: var(--card-hover);
            border-color: rgba(102, 126, 234, 0.4);
            transform: translateX(4px);
        }
        
        .stock-info {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        
        .stock-symbol {
            font-weight: 700;
            font-size: 1rem;
            color: #93c5fd;
            font-family: 'Courier New', monospace;
        }
        
        .stock-name {
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        
        .stock-direction {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.875rem;
        }
        
        .stock-up {
            background: rgba(16, 185, 129, 0.1);
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        
        .stock-down {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        /* Market Prediction */
        .market-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .market-item {
            position: relative;
            padding: 1.5rem;
            border-radius: 16px;
            text-align: center;
            overflow: hidden;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        
        .market-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--primary-gradient);
            opacity: 0.1;
            z-index: 0;
        }
        
        .market-item:hover {
            transform: scale(1.05);
            border-color: rgba(102, 126, 234, 0.5);
        }
        
        .market-item:hover::before {
            opacity: 0.2;
        }
        
        .market-name {
            position: relative;
            z-index: 1;
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .market-icon {
            position: relative;
            z-index: 1;
            font-size: 2rem;
            margin: 0.5rem 0;
        }
        
        .market-trend {
            position: relative;
            z-index: 1;
            font-size: 1.5rem;
            font-weight: 800;
            margin: 0.5rem 0;
            color: var(--text-primary);
        }
        
        .market-sentiment {
            position: relative;
            z-index: 1;
            font-size: 0.75rem;
            color: var(--text-secondary);
            font-weight: 500;
        }
        
        /* Hot Topics */
        .hot-topics {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
        }
        
        .topic-tag {
            position: relative;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-size: 0.875rem;
            font-weight: 600;
            background: rgba(37, 99, 235, 0.25);
            color: #e0e7ff;
            border: 1px solid rgba(96, 165, 250, 0.55);
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow: 0 8px 24px -12px rgba(37, 99, 235, 0.6);
        }
        
        .topic-tag:hover {
            background: rgba(59, 130, 246, 0.35);
            border-color: rgba(59, 130, 246, 0.7);
            transform: translateY(-2px);
            box-shadow: 0 10px 28px -12px rgba(59, 130, 246, 0.6);
        }

        [data-theme="light"] .topic-tag {
            background: rgba(59, 130, 246, 0.12);
            border-color: rgba(59, 130, 246, 0.45);
            color: #1d4ed8;
            box-shadow: none;
        }

        [data-theme="light"] .topic-tag:hover {
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(37, 99, 235, 0.55);
            color: #1e3a8a;
        }

        .hot-topics-visual {
            margin-top: 1.5rem;
            padding: 1.5rem;
            border-radius: 20px;
            background: radial-gradient(circle at top, rgba(59, 130, 246, 0.25), transparent 60%), rgba(9, 13, 27, 0.9);
            border: 1px solid rgba(59, 130, 246, 0.35);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            position: relative;
            overflow: hidden;
            text-align: center;
        }

        [data-theme="light"] .hot-topics-visual {
            background: radial-gradient(circle at top, rgba(59, 130, 246, 0.15), transparent 60%), rgba(255, 255, 255, 0.95);
            border-color: rgba(148, 163, 184, 0.4);
        }

        .hero-orb {
            --orb-size: clamp(220px, 55vw, 320px);
            width: var(--orb-size);
            aspect-ratio: 1 / 1;
            border-radius: 50%;
            margin: 0 auto;
            position: relative;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.4), transparent 70%);
            overflow: visible;
            flex-shrink: 0;
            max-width: 100%;
        }

        .hero-orb::after {
            content: '';
            position: absolute;
            inset: 28%;
            border-radius: 50%;
            background: radial-gradient(circle, #5eead4, #2563eb);
            box-shadow: 0 0 35px rgba(94, 234, 212, 0.5);
            z-index: -1;
        }

        .hero-orb-ring {
            position: absolute;
            inset: 10px;
            border-radius: 50%;
            border: 1px solid rgba(94, 234, 212, 0.4);
            animation: rotateOrb 16s linear infinite;
        }

        .hero-orb-ring:nth-child(2) { inset: 28px; animation-duration: 20s; border-color: rgba(167, 139, 250, 0.45); }
        .hero-orb-ring:nth-child(3) { inset: 46px; animation-duration: 24s; border-color: rgba(248, 113, 113, 0.35); }

        .hero-orb-hotspots {
            position: absolute;
            inset: -10px;
            border-radius: 50%;
            pointer-events: none;
        }

        .hero-orb-hotspot {
            --orbit-radius: calc(var(--orb-size, 260px) / 2 - 24px);
            --start-angle: 0deg;
            --offset: 0deg;
            position: absolute;
            top: 50%;
            left: 50%;
            transform-origin: center;
            transform: translate(-50%, -50%) rotate(var(--start-angle, 0deg)) translate(var(--orbit-radius)) rotate(calc(var(--offset, 0deg) - var(--start-angle, 0deg)));
            animation: orbitSpin var(--speed, 22s) linear infinite;
            animation-delay: var(--delay, 0s);
            animation-timing-function: linear;
        }

        .hero-orb-hotspot-empty {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 0.85rem;
            color: var(--text-muted);
            white-space: nowrap;
        }

        .hero-orb-hotspot .hotspot-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            background: rgba(5, 10, 28, 0.9);
            border: 1px solid rgba(94, 234, 212, 0.45);
            font-size: 0.78rem;
            color: #e0f2fe;
            text-shadow: 0 0 8px rgba(94, 234, 212, 0.45);
            box-shadow: 0 10px 25px -12px rgba(94, 234, 212, 0.6);
            animation: hotspotGlow 3.5s ease-in-out infinite;
            animation-delay: var(--delay, 0s);
        }

        [data-theme="light"] .hero-orb-hotspot .hotspot-chip {
            background: rgba(255, 255, 255, 0.95);
            color: #0f172a;
            text-shadow: none;
        }

        .hotspot-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #5eead4;
            box-shadow: 0 0 14px rgba(94, 234, 212, 0.9);
            animation: hotspotPulse 2s ease-in-out infinite;
        }

        .hot-topic-orb-meta {
            width: 100%;
            text-align: center;
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.7;
            max-width: 420px;
        }

        @keyframes rotateOrb {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        @keyframes hotspotPulse {
            0%, 100% { transform: scale(1); opacity: 0.9; }
            50% { transform: scale(1.4); opacity: 1; }
        }

        @keyframes hotspotGlow {
            0%, 100% { box-shadow: 0 10px 25px -12px rgba(94, 234, 212, 0.4); }
            50% { box-shadow: 0 15px 30px -12px rgba(94, 234, 212, 0.7); }
        }

        @keyframes orbitSpin {
            from {
                transform: translate(-50%, -50%) rotate(var(--start-angle, 0deg)) translate(var(--orbit-radius)) rotate(calc(var(--offset, 0deg) - var(--start-angle, 0deg)));
            }
            to {
                transform: translate(-50%, -50%) rotate(calc(var(--start-angle, 0deg) + 360deg)) translate(var(--orbit-radius)) rotate(calc(var(--offset, 0deg) - var(--start-angle, 0deg) - 360deg));
            }
        }

        @media (max-width: 992px) {
            .hot-topics-visual {
                flex-direction: column;
                align-items: stretch;
                text-align: center;
            }

            .hot-topic-orb-meta {
                max-width: none;
                text-align: center;
            }
        }

        @media (max-width: 640px) {
            .hot-topics-visual {
                padding: 1.25rem;
                gap: 1rem;
            }

            .hero-orb {
                --orb-size: clamp(180px, 70vw, 240px);
            }

            .hot-topic-orb-meta {
                font-size: 0.875rem;
            }
        }
        
        /* Report Content */
        .report-content {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            padding: 1.5rem;
            border-radius: 12px;
            max-height: 400px;
            overflow: hidden;
            white-space: pre-wrap;
            font-size: 0.875rem;
            line-height: 1.8;
            color: var(--text-primary);
            font-family: 'Courier New', monospace;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }
        
        .report-content.expanded {
            max-height: none;
            overflow-y: auto;
        }
        
        .report-content.collapsed {
            max-height: 400px;
        }
        
        .report-content.collapsed::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 80px;
            background: linear-gradient(
                to bottom,
                transparent 0%,
                var(--card-bg) 90%
            );
            pointer-events: none;
            z-index: 1;
        }
        
        .report-content.expanded::after {
            display: none;
        }
        
        .report-wrapper {
            position: relative;
            z-index: 1;
        }
        
        .expand-toggle {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            margin-top: 0.75rem;
            padding: 0.5rem 1rem;
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 8px;
            color: #93c5fd;
            font-size: 0.875rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            position: relative;
            z-index: 10;
        }
        
        .expand-toggle:hover {
            background: rgba(102, 126, 234, 0.2);
            border-color: rgba(102, 126, 234, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .expand-toggle .arrow {
            transition: transform 0.3s ease;
        }
        
        .expand-toggle.expanded .arrow {
            transform: rotate(180deg);
        }
        
        .report-content::-webkit-scrollbar {
            width: 10px;
        }
        
        .report-content::-webkit-scrollbar-track {
            background: rgba(15, 23, 42, 0.5);
            border-radius: 5px;
            margin: 4px 0;
        }
        
        .report-content::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            transition: background 0.3s ease;
        }
        
        .report-content::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #7c8ef5 0%, #8a5cb8 100%);
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
        }
        
        .loading {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }
        
        .loading::after {
            content: '...';
            animation: dots 1.5s infinite;
        }
        
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        
        /* Buttons */
        .btn {
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.875rem;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
            color: inherit;
        }
        
        .btn-primary {
            background: var(--primary-gradient);
            color: white;
            box-shadow: 0 4px 14px rgba(102, 126, 234, 0.4);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .btn-secondary {
            background: rgba(102, 126, 234, 0.1);
            color: #93c5fd;
            border: 1px solid rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary:hover {
            background: rgba(102, 126, 234, 0.2);
            border-color: rgba(102, 126, 234, 0.5);
        }
        
        .refresh-btn {
            margin-left: auto;
            margin-top: 0;
        }
        
        /* Timestamp */
        .timestamp {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.75rem;
            padding: 2rem 0;
            border-top: 1px solid var(--border-color);
        }
        
        /* Advanced Animations */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.3); }
            50% { box-shadow: 0 0 40px rgba(102, 126, 234, 0.6); }
        }
        
        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }
        
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(30px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        @keyframes ripple {
            0% {
                transform: scale(0);
                opacity: 1;
            }
            100% {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes ping {
            0% { box-shadow: 0 0 0 0 currentColor; opacity: 1; }
            70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); opacity: 0; }
            100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); opacity: 0; }
        }
        
        /* Particle Background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image:
                radial-gradient(circle at 10% 20%, rgba(56, 189, 248, 0.15), transparent 45%),
                radial-gradient(circle at 80% 30%, rgba(168, 85, 247, 0.18), transparent 50%),
                radial-gradient(circle at 60% 80%, rgba(236, 72, 153, 0.12), transparent 55%);
            pointer-events: none;
            z-index: 0;
            animation: gradientShift 20s ease infinite;
            background-size: 250% 250%;
        }

        html[data-theme="light"] body::before {
            background-image:
                radial-gradient(circle at 15% 25%, rgba(59, 130, 246, 0.12), transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(244, 114, 182, 0.12), transparent 55%),
                radial-gradient(circle at 65% 80%, rgba(14, 165, 233, 0.1), transparent 55%);
            opacity: 0.8;
        }

        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
            background-size: 140px 140px;
            opacity: 0.3;
            pointer-events: none;
            z-index: 0;
        }

        html[data-theme="light"] body::after {
            opacity: 0.15;
            background-image: linear-gradient(rgba(15, 23, 42, 0.08) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(15, 23, 42, 0.08) 1px, transparent 1px);
        }
        
        .container {
            position: relative;
            z-index: 1;
        }
        
        /* Enhanced Card Hover Effects */
        .card {
            position: relative;
            overflow: hidden;
        }
        
        .card::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                45deg,
                transparent 30%,
                rgba(255, 255, 255, 0.05) 50%,
                transparent 70%
            );
            transform: rotate(45deg);
            transition: all 0.6s ease;
            opacity: 0;
            pointer-events: none;
            z-index: 0;
        }
        
        .card:hover::after {
            animation: shimmer 1.5s ease-in-out;
        }
        
        /* Stat Card Animations */
        .stat-card {
            animation: slideInRight 0.6s ease-out backwards;
        }
        
        .stat-card:nth-child(1) { animation-delay: 0.1s; }
        .stat-card:nth-child(2) { animation-delay: 0.2s; }
        .stat-card:nth-child(3) { animation-delay: 0.3s; }
        .stat-card:nth-child(4) { animation-delay: 0.4s; }
        
        .stat-icon {
            animation: float 3s ease-in-out infinite;
        }
        
        .stat-card:nth-child(1) .stat-icon { animation-delay: 0s; }
        .stat-card:nth-child(2) .stat-icon { animation-delay: 0.5s; }
        .stat-card:nth-child(3) .stat-icon { animation-delay: 1s; }
        .stat-card:nth-child(4) .stat-icon { animation-delay: 1.5s; }
        
        /* Enhanced Button Effects */
        .btn {
            position: relative;
            overflow: hidden;
        }
        
        .btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }
        
        .btn:active::before {
            width: 300px;
            height: 300px;
        }
        
        .btn-primary:hover {
            animation: glow 2s ease-in-out infinite;
        }
        
        /* Topic Tag Enhancements */
        .topic-tag {
            position: relative;
            overflow: hidden;
        }
        
        .topic-tag::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.2),
                transparent
            );
            transition: left 0.5s;
        }
        
        .topic-tag:hover::before {
            left: 100%;
        }
        
        /* Sentiment Item Pulse */
        .sentiment-item {
            animation: slideInRight 0.6s ease-out backwards;
        }
        
        .sentiment-item:nth-child(1) { animation-delay: 0.1s; }
        .sentiment-item:nth-child(2) { animation-delay: 0.2s; }
        .sentiment-item:nth-child(3) { animation-delay: 0.3s; }
        
        .sentiment-value {
            transition: all 0.3s ease;
        }
        
        .sentiment-item:hover .sentiment-value {
            transform: scale(1.1);
            filter: drop-shadow(0 0 10px currentColor);
        }
        
        /* Stock Item Slide */
        .stock-item {
            animation: slideInRight 0.4s ease-out backwards;
        }
        
        .stock-list .stock-item:nth-child(1) { animation-delay: 0.05s; }
        .stock-list .stock-item:nth-child(2) { animation-delay: 0.1s; }
        .stock-list .stock-item:nth-child(3) { animation-delay: 0.15s; }
        .stock-list .stock-item:nth-child(4) { animation-delay: 0.2s; }
        .stock-list .stock-item:nth-child(5) { animation-delay: 0.25s; }
        
        /* Market Item Enhancements */
        .market-item {
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        
        .market-item:hover {
            transform: scale(1.08) rotate(2deg);
        }
        
        .market-icon {
            display: inline-block;
            animation: pulse 2s ease-in-out infinite;
        }
        
        /* Theme Toggle Enhancement */
        .theme-toggle {
            position: relative;
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        
        .theme-toggle:hover {
            transform: rotate(180deg) scale(1.2);
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
        }
        
        .theme-toggle:active {
            transform: rotate(180deg) scale(0.95);
        }
        
        /* Card Badge Pulse */
        .card-badge {
            animation: pulse 3s ease-in-out infinite;
        }
        
        /* Hero Badge Animation */
        .hero-badge {
            animation: float 3s ease-in-out infinite;
        }
        
        /* Smooth Scroll */
        html {
            scroll-behavior: smooth;
        }
        
        /* Loading Enhancement */
        .loading {
            position: relative;
        }
        
        .loading::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 20px;
            height: 20px;
            margin: -10px 0 0 -10px;
            border: 2px solid var(--text-muted);
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Responsive */
        @media (max-width: 1200px) {
            .hero {
                padding: 3.5rem 1.5rem 1.5rem;
            }

            .container {
                padding: 1.5rem;
            }

            .hero-simple {
                max-width: 100%;
            }
        }

        @media (max-width: 1024px) {
            .nav-links {
                display: none;
            }

            html {
                overflow-x: hidden;
            }

            .navbar {
                position: fixed;
                width: 100%;
            }



            .menu-toggle {
                display: inline-flex;
            }

            .hero-simple {
                padding: 1.75rem;
            }

            .insight-grid.dual,
            .grid-2 {
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            }
        }

        @media (max-width: 768px) {
            .hero h2 {
                font-size: 2.2rem;
            }

            .hero-simple {
                padding: 1.5rem;
            }

            .heading-meta {
                width: 100%;
                justify-content: flex-start;
            }
            
            .grid, .grid-2, .grid-3, .grid-4, .insight-grid, .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: rgba(7, 12, 28, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 20px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            box-shadow: 
                0 10px 30px -5px rgba(0, 0, 0, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        [data-theme="light"] .stat-card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.3);
            box-shadow: 
                0 10px 30px -5px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.8);
        }
        
        .stat-card:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: rgba(102, 126, 234, 0.6);
            box-shadow: 
                0 20px 50px -10px rgba(102, 126, 234, 0.4),
                0 0 30px rgba(102, 126, 234, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(30px) saturate(200%);
        }
        
        .stat-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            color: var(--text-primary);
            margin: 0.5rem 0;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            font-weight: 500;
        }
        
        .stat-trend {
            font-size: 0.75rem;
            margin-top: 0.5rem;
            font-weight: 600;
        }
        
        .trend-up {
            color: #10b981;
        }
        
        .trend-down {
            color: #ef4444;
        }
        
        [v-cloak] { display: none; }
    </style>
</head>
<body>
    <div id="app" v-cloak>
        <!-- Navigation -->
        <nav class="navbar">
            <div class="nav-container">
                <div class="nav-brand">
                    <div class="nav-logo">WR</div>
                    <div class="nav-title">
                        <h1>Wide Research</h1>
                        <p>AI Financial Intelligence</p>
                    </div>
                </div>
                <button class="menu-toggle" type="button" aria-label="打开菜单" @click="toggleDrawer()">☰</button>
                <div class="nav-links">
                    <a href="/" class="nav-link active">实时仪表盘</a>
                    <a href="/overview" class="nav-link">项目总览</a>
                    <a href="https://github.com/ianchiou28/Wide-Research-for-Finance" target="_blank" rel="noopener" class="nav-link">GitHub</a>
                    <div class="nav-status">
                        <span class="status-dot live"></span>
                        <span>Agent 在线</span>
                    </div>
                    <button class="theme-toggle" @click="toggleTheme()" title="切换主题">
                        <span>{{ theme === 'dark' ? '🌙' : '☀️' }}</span>
                    </button>
                </div>
            </div>
        </nav>

        <div class="nav-overlay" :class="{ active: isDrawerOpen }" @click="toggleDrawer(false)"></div>
        <aside class="mobile-drawer" :class="{ open: isDrawerOpen }" id="mobileDrawer" aria-hidden="true">
            <div class="drawer-header">
                <div class="nav-brand">
                    <div class="nav-logo">WR</div>
                    <div class="nav-title">
                        <h1>Wide Research</h1>
                        <p>AI Financial Intelligence</p>
                    </div>
                </div>
                <button class="drawer-close" type="button" aria-label="关闭菜单" @click="toggleDrawer(false)">×</button>
            </div>
            <nav class="drawer-links">
                <a href="/">实时仪表盘</a>
                <a href="/overview">项目总览</a>
                <a href="https://github.com/ianchiou28/Wide-Research-for-Finance" target="_blank" rel="noopener">GitHub</a>
            </nav>
            <div class="drawer-meta">
                <div class="nav-status">
                    <span class="status-dot live"></span>
                    <span>Agent 在线</span>
                </div>
                <button class="theme-toggle" @click="toggleTheme()" title="切换主题">
                    <span>{{ theme === 'dark' ? '🌙' : '☀️' }}</span>
                </button>
            </div>
        </aside>

        <!-- Hero Section -->
        <div class="hero">
            <div class="hero-simple">
                <div class="hero-badge">⚡ 实时监控 · DeepSeek Agent</div>
                <h2>金融智能情报中心</h2>
                <p>基于 DeepSeek AI 的自动化财经分析系统，每小时吞吐 200+ 全球新闻源，实时输出情绪、个股与策略指引。</p>
            </div>
        </div>
        
        <div class="container">
            <section class="dashboard-section">
                <div class="section-heading">
                    <div>
                        <p>Agent Pulse</p>
                        <h3>全局运行态势</h3>
                    </div>
                    <div class="heading-meta">
                        <span class="status-pill">
                            <span class="status-dot live"></span>
                            实时在线
                        </span>
                        <span class="heading-time">上次同步 <strong>{{ lastUpdated }}</strong></span>
                    </div>
                </div>
                <div class="stats-grid">
                    <a href="#Briefing Layer" class="stat-card" style="text-decoration: none; color: inherit; display: block; cursor: pointer;">
                        <div class="stat-icon">📊</div>
                        <div class="stat-value">{{ stats.newsCount }}</div>
                        <div class="stat-label">本小时新闻</div>
                    </a>
                    <a href="#Briefing Layer" class="stat-card" style="text-decoration: none; color: inherit; display: block; cursor: pointer;">
                        <div class="stat-icon">🎯</div>
                        <div class="stat-value">{{ stats.hotTopicsCount }}</div>
                        <div class="stat-label">热点话题</div>
                    </a>
                    <a href="#Briefing Layer" class="stat-card" style="text-decoration: none; color: inherit; display: block; cursor: pointer;">
                        <div class="stat-icon">📈</div>
                        <div class="stat-value">{{ stats.positiveCount }}</div>
                        <div class="stat-label">积极事件</div>
                    </a>
                    <a href="#Briefing Layer" class="stat-card" style="text-decoration: none; color: inherit; display: block; cursor: pointer;">
                        <div class="stat-icon">⚡</div>
                        <div class="stat-value">{{ stats.updateTime }}</div>
                        <div class="stat-label">更新时间</div>
                    </a>
                </div>
            </section>

            <section class="dashboard-section">
                <div class="section-heading">
                    <div>
                        <p>Market Intelligence</p>
                        <h3>情绪雷达 &amp; 走势预测</h3>
                    </div>
                    <div class="heading-meta">
                        <span class="heading-chip">AI Confidence 0.92</span>
                    </div>
                </div>
                <div class="insight-grid dual">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: var(--success-gradient);">💹</div>
                                市场情绪雷达
                            </div>
                            <span class="card-badge">实时</span>
                        </div>
                        <div class="sentiment-box" v-if="!loading">
                            <div class="sentiment-item sentiment-positive">
                                <div class="sentiment-label">积极情绪</div>
                                <div class="sentiment-value">{{ sentiment.breakdown.positive }}%</div>
                                <div class="sentiment-status">看多</div>
                            </div>
                            <div class="sentiment-item sentiment-neutral">
                                <div class="sentiment-label">中性情绪</div>
                                <div class="sentiment-value">{{ sentiment.breakdown.neutral }}%</div>
                                <div class="sentiment-status">观望</div>
                            </div>
                            <div class="sentiment-item sentiment-negative">
                                <div class="sentiment-label">消极情绪</div>
                                <div class="sentiment-value">{{ sentiment.breakdown.negative }}%</div>
                                <div class="sentiment-status">看空</div>
                            </div>
                        </div>
                        <div class="loading" v-else>加载数据中</div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: var(--warning-gradient);">🔮</div>
                                大盘走势预测
                            </div>
                            <span class="card-badge">AI 分析</span>
                        </div>
                        <div class="market-grid" v-if="!loading && marketPrediction.length > 0">
                            <div class="market-item" v-for="item in marketPrediction" :key="item.name">
                                <div class="market-name">{{ item.name }}</div>
                                <div class="market-icon">{{ item.icon }}</div>
                                <div class="market-trend">{{ item.trend }}</div>
                                <div class="market-sentiment">{{ item.sentiment }}</div>
                            </div>
                        </div>
                        <div class="loading" v-else-if="loading">生成预测中</div>
                        <div class="loading" v-else>暂无预测数据</div>
                    </div>
                </div>
            </section>

            <section class="dashboard-section">
                <div class="section-heading">
                    <div>
                        <p>Strategy Stream</p>
                        <h3>多市场个股指引</h3>
                    </div>
                    <div class="heading-meta">
                        <span class="heading-chip">实时推送</span>
                    </div>
                </div>
                <div class="insight-grid dual">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: linear-gradient(135deg, #ef4444, #dc2626);">🇨🇳</div>
                                A股推荐
                            </div>
                            <span class="card-badge">{{ stocks.a.length }}</span>
                        </div>
                        <ul class="stock-list" v-if="!loading && stocks.a.length > 0">
                            <li class="stock-item" v-for="stock in stocks.a" :key="stock.symbol">
                                <div class="stock-info">
                                    <span class="stock-symbol">{{ stock.symbol }}</span>
                                    <span class="stock-name">{{ stock.name }}</span>
                                </div>
                                <div class="stock-direction" :class="stock.direction === '看涨' ? 'stock-up' : 'stock-down'">
                                    {{ stock.direction }}
                                </div>
                            </li>
                        </ul>
                        <div class="loading" v-else-if="loading">分析中</div>
                        <div class="loading" v-else>暂无推荐</div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: linear-gradient(135deg, #3b82f6, #2563eb);">🇺🇸</div>
                                美股推荐
                            </div>
                            <span class="card-badge">{{ stocks.us.length }}</span>
                        </div>
                        <ul class="stock-list" v-if="!loading && stocks.us.length > 0">
                            <li class="stock-item" v-for="stock in stocks.us" :key="stock.symbol">
                                <div class="stock-info">
                                    <span class="stock-symbol">{{ stock.symbol }}</span>
                                    <span class="stock-name">{{ stock.name }}</span>
                                </div>
                                <div class="stock-direction" :class="stock.direction === '看涨' ? 'stock-up' : 'stock-down'">
                                    {{ stock.direction }}
                                </div>
                            </li>
                        </ul>
                        <div class="loading" v-else-if="loading">分析中</div>
                        <div class="loading" v-else>暂无推荐</div>
                    </div>
                </div>
            </section>

            <section class="dashboard-section" id="Briefing Layer">
                <div class="section-heading">
                    <div>
                        <p>Briefing Layer</p>
                        <h3>小时简报 &amp; 热点雷达</h3>
                    </div>
                    <div class="heading-meta">
                        <span class="heading-chip">LLM 汇总</span>
                    </div>
                </div>
                <div class="insight-grid dual">
                    <div class="card" id="hourly-report-card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: var(--primary-gradient);">📝</div>
                                本小时简报
                            </div>
                            <button class="btn btn-secondary refresh-btn" @click="fetchData">🔄 刷新</button>
                        </div>
                        <div class="report-wrapper">
                            <div class="report-content" :class="{ collapsed: !expandedReports.hourly, expanded: expandedReports.hourly }">
                                <div v-if="loading && !hourlyReport" class="loading">获取最新报告中</div>
                                <div v-else>{{ hourlyReport || '暂无报告' }}</div>
                            </div>
                            <button class="expand-toggle" :class="{ expanded: expandedReports.hourly }" @click="toggleReport('hourly')" v-if="hourlyReport">
                                <span>{{ expandedReports.hourly ? '收起内容' : '展开查看完整内容' }}</span>
                                <span class="arrow">▼</span>
                            </button>
                        </div>
                    </div>
                    <div class="card" id="hot-topics-card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: var(--secondary-gradient);">🔥</div>
                                热点追踪
                            </div>
                            <span class="card-badge">实时更新</span>
                        </div>
                        <div class="hot-topics" v-if="!loading && hotTopics.length > 0">
                            <span class="topic-tag" v-for="topic in hotTopics" :key="topic">{{ topic }}</span>
                        </div>
                        <div class="loading" v-else-if="loading">分析热点中</div>
                        <div class="hot-topics-visual">
                            <div class="hero-orb">
                                <span class="hero-orb-ring"></span>
                                <span class="hero-orb-ring"></span>
                                <span class="hero-orb-ring"></span>
                                <div class="hero-orb-hotspots">
                                    <div v-for="(topic, index) in hotTopics" :key="topic" 
                                         class="hero-orb-hotspot"
                                         :style="{ 
                                             '--speed': (20 + index * 2) + 's', 
                                             '--delay': -(index * 3) + 's',
                                             '--orbit-radius': (100 + (index % 3) * 30) + 'px',
                                             '--start-angle': (index * 60) + 'deg'
                                         }">
                                        <div class="hotspot-chip">
                                            <span class="hotspot-dot"></span>
                                            {{ topic }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="hot-topic-orb-meta">热点轨道 · 24h 高频信号</div>
                        </div>
                    </div>
                </div>
            </section>

            <section class="dashboard-section">
                <div class="section-heading">
                    <div>
                        <p>Multi Horizon</p>
                        <h3>每日摘要 &amp; 周度洞察</h3>
                    </div>
                    <div class="heading-meta">
                        <span class="heading-chip">跨周期监控</span>
                    </div>
                </div>
                <div class="insight-grid dual">
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: var(--success-gradient);">📅</div>
                                每日摘要
                            </div>
                            <span class="card-badge">过去12小时</span>
                        </div>
                        <div class="report-wrapper">
                            <div class="report-content" :class="{ collapsed: !expandedReports.daily, expanded: expandedReports.daily }">
                                <div v-if="loading && !dailySummary" class="loading">生成摘要中</div>
                                <div v-else>{{ dailySummary || '暂无摘要' }}</div>
                            </div>
                            <button class="expand-toggle" :class="{ expanded: expandedReports.daily }" @click="toggleReport('daily')" v-if="dailySummary">
                                <span>{{ expandedReports.daily ? '收起内容' : '展开查看完整内容' }}</span>
                                <span class="arrow">▼</span>
                            </button>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <div class="card-title">
                                <div class="card-icon" style="background: var(--warning-gradient);">📊</div>
                                周度分析
                            </div>
                            <span class="card-badge">过去7天</span>
                        </div>
                        <div id="weeklyContent">
                            <div class="loading">分析中</div>
                        </div>
                    </div>
                </div>
            </section>

            <div class="timestamp">
                Generated by Wide Research Agent • {{ lastUpdated }}
            </div>
        </div>
    </div>

    <script>
        const { createApp, ref, onMounted } = Vue;

        createApp({
            setup() {
                const theme = ref('dark');
                const isDrawerOpen = ref(false);
                const loading = ref(true);
                const lastUpdated = ref('--');
                
                const stats = ref({
                    newsCount: 0,
                    hotTopicsCount: 0,
                    positiveCount: 0,
                    updateTime: '--'
                });
                
                const sentiment = ref({
                    score: 0,
                    label: 'Neutral',
                    breakdown: { positive: 0, neutral: 0, negative: 0 }
                });
                
                const marketPrediction = ref([]);
                const stocks = ref({ a: [], us: [] });
                const hotTopics = ref([]);
                const hourlyReport = ref('');
                const dailySummary = ref('');
                
                const expandedReports = ref({
                    hourly: false,
                    daily: false
                });

                const toggleTheme = () => {
                    theme.value = theme.value === 'dark' ? 'light' : 'dark';
                    localStorage.setItem('theme', theme.value);
                    document.documentElement.setAttribute('data-theme', theme.value);
                };

                const toggleDrawer = (state) => {
                    isDrawerOpen.value = state !== undefined ? state : !isDrawerOpen.value;
                };

                const toggleReport = (type) => {
                    expandedReports.value[type] = !expandedReports.value[type];
                };

                const fetchData = async () => {
                    try {
                        loading.value = true;
                        
                        // 1. Get Latest Data
                        const response = await axios.get('/api/latest');
                        const data = response.data;
                        
                        if (data) {
                            lastUpdated.value = new Date().toLocaleTimeString();
                            
                            stats.value = {
                                newsCount: data.stats?.total_news || 0,
                                hotTopicsCount: data.hot_topics?.length || 0,
                                positiveCount: data.stats?.positive_news || 0,
                                updateTime: data.timestamp || '--'
                            };

                            sentiment.value = data.sentiment || { score: 0, label: 'Neutral', breakdown: { positive: 0, neutral: 0, negative: 0 } };

                            stocks.value = {
                                a: data.recommendations?.a_shares || [],
                                us: data.recommendations?.us_shares || []
                            };

                            marketPrediction.value = data.market_prediction || [];
                            hotTopics.value = data.hot_topics || [];
                        }

                        // 2. Get Reports
                        try {
                            const reportRes = await axios.get('/api/report/latest');
                            if (reportRes.data && reportRes.data.content) {
                                hourlyReport.value = reportRes.data.content;
                            }
                        } catch (e) { console.log('Report fetch failed', e); }

                        // 3. Get Daily Summary
                        try {
                            const summaryRes = await axios.get('/api/summary/latest');
                            if (summaryRes.data) dailySummary.value = summaryRes.data.content;
                        } catch (e) { console.log('Daily summary not available'); }

                    } catch (error) {
                        console.error('Error fetching data:', error);
                    } finally {
                        loading.value = false;
                    }
                };

                onMounted(() => {
                    const savedTheme = localStorage.getItem('theme');
                    if (savedTheme) {
                        theme.value = savedTheme;
                        document.documentElement.setAttribute('data-theme', savedTheme);
                    }
                    
                    fetchData();
                    setInterval(fetchData, 300000);
                });

                return {
                    theme,
                    isDrawerOpen,
                    loading,
                    lastUpdated,
                    stats,
                    sentiment,
                    marketPrediction,
                    stocks,
                    hotTopics,
                    hourlyReport,
                    dailySummary,
                    expandedReports,
                    toggleTheme,
                    toggleDrawer,
                    toggleReport,
                    fetchData
                };
            }
        }).mount('#app');
    </script>
</body>
</html>
"""

with open(r"d:\GitHub\Wide-Research-for-Finance\templates\index.html", "w", encoding="utf-8") as f:
    f.write(content)
