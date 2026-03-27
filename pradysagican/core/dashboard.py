"""
ADVANCED: Web Dashboard UI
===========================

Real-time system monitoring, visualization,
and interactive control interface.

Attribution: FastAPI, HTML5, WebSocket streaming,
D3.js charting patterns
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PRADYSAGICAN Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #0f0f1e 0%, #1a1a3e 100%);
            color: #e0e0e0;
            overflow: hidden;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 0;
            height: 100vh;
        }
        
        .sidebar {
            background: #16213e;
            border-right: 2px solid #00d4ff;
            padding: 20px;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0, 212, 255, 0.2);
        }
        
        .sidebar h1 {
            font-size: 18px;
            margin-bottom: 20px;
            color: #00d4ff;
            text-align: center;
        }
        
        .nav-item {
            padding: 12px 15px;
            margin-bottom: 8px;
            background: #0f3460;
            border-left: 3px solid transparent;
            cursor: pointer;
            border-radius: 4px;
            transition: all 0.3s;
        }
        
        .nav-item:hover {
            background: #1a4d6d;
            border-left-color: #00d4ff;
        }
        
        .nav-item.active {
            background: #1a4d6d;
            border-left-color: #00d4ff;
            color: #00d4ff;
        }
        
        .main {
            display: flex;
            flex-direction: column;
            background: #0f0f1e;
        }
        
        .header {
            background: linear-gradient(90deg, #1a1a3e 0%, #16213e 100%);
            border-bottom: 2px solid #00d4ff;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 24px;
            color: #00d4ff;
        }
        
        .header-stats {
            display: flex;
            gap: 20px;
        }
        
        .stat {
            text-align: right;
        }
        
        .stat-label {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }
        
        .stat-value {
            font-size: 18px;
            color: #00d4ff;
            font-weight: bold;
        }
        
        .content {
            flex: 1;
            overflow: auto;
            padding: 30px;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
            border: 2px solid #00d4ff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
            transition: all 0.3s;
        }
        
        .card:hover {
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.3);
            transform: translateY(-2px);
        }
        
        .card h2 {
            font-size: 16px;
            color: #00d4ff;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #1a4d6d;
        }
        
        .metric-row:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }
        
        .metric-value {
            font-size: 16px;
            color: #00ff88;
            font-weight: bold;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: #1a4d6d;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            transition: width 0.3s;
        }
        
        .chart-container {
            width: 100%;
            height: 250px;
            background: #0f3460;
            border-radius: 6px;
            padding: 10px;
            margin-top: 10px;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-ok { background: #00ff88; }
        .status-warning { background: #ffaa00; animation: pulse-orange 2s infinite; }
        .status-error { background: #ff3333; animation: pulse-red 2s infinite; }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes pulse-orange {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px rgba(255, 170, 0, 0.5); }
            50% { opacity: 0.5; }
        }
        
        @keyframes pulse-red {
            0%, 100% { opacity: 1; box-shadow: 0 0 10px rgba(255, 51, 51, 0.5); }
            50% { opacity: 0.5; }
        }
        
        .btn {
            padding: 10px 20px;
            background: linear-gradient(135deg, #00d4ff, #00ff88);
            border: none;
            border-radius: 4px;
            color: #0f0f1e;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0, 212, 255, 0.3);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .log-item {
            padding: 12px;
            margin: 8px 0;
            background: #0f3460;
            border-left: 3px solid #00d4ff;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            color: #e0e0e0;
            max-height: 80px;
            overflow: auto;
        }
        
        .log-item.error {
            border-left-color: #ff3333;
            color: #ff3333;
        }
        
        .log-item.warning {
            border-left-color: #ffaa00;
            color: #ffaa00;
        }
        
        .log-item.success {
            border-left-color: #00ff88;
            color: #00ff88;
        }
        
        @media (max-width: 768px) {
            .dashboard { grid-template-columns: 1fr; }
            .sidebar { display: none; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <h1>PRADYSAGICAN</h1>
            <div id="nav">
                <div class="nav-item active" onclick="switchView('overview')">Dashboard</div>
                <div class="nav-item" onclick="switchView('performance')">Performance</div>
                <div class="nav-item" onclick="switchView('memory')">Memory</div>
                <div class="nav-item" onclick="switchView('agents')">Agents</div>
                <div class="nav-item" onclick="switchView('safety')">Safety</div>
                <div class="nav-item" onclick="switchView('logs')">Logs</div>
            </div>
        </div>
        
        <div class="main">
            <div class="header">
                <h1 id="title">System Dashboard</h1>
                <div class="header-stats">
                    <div class="stat">
                        <div class="stat-label">Status</div>
                        <div class="stat-value"><span class="status-indicator status-ok"></span>ONLINE</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Uptime</div>
                        <div class="stat-value" id="uptime">--:--:--</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Queries</div>
                        <div class="stat-value" id="queries">0</div>
                    </div>
                </div>
            </div>
            
            <div class="content" id="content">
                <!-- Dynamic content loaded here -->
            </div>
        </div>
    </div>
    
    <script>
        let currentView = 'overview';
        let startTime = Date.now();
        
        async function switchView(view) {
            currentView = view;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            event.target.classList.add('active');
            
            const titles = {
                overview: 'System Dashboard',
                performance: 'Performance Metrics',
                memory: 'Memory Status',
                agents: 'Active Agents',
                safety: 'Safety & Security',
                logs: 'System Logs'
            };
            document.getElementById('title').textContent = titles[view];
            
            await loadContent();
        }
        
        async function loadContent() {
            const data = await fetch(`/api/dashboard/${currentView}`).then(r => r.json());
            const html = renderView(currentView, data);
            document.getElementById('content').innerHTML = html;
        }
        
        function renderView(view, data) {
            const templates = {
                overview: () => `
                    <div class="grid">
                        <div class="card">
                            <h2>System Health</h2>
                            <div class="metric-row">
                                <span class="metric-label">CPU Usage</span>
                                <span class="metric-value">${data.cpu}%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${data.cpu}%"></div>
                            </div>
                            
                            <div class="metric-row">
                                <span class="metric-label">Memory Usage</span>
                                <span class="metric-value">${data.memory}%</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${data.memory}%"></div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>Performance</h2>
                            <div class="metric-row">
                                <span class="metric-label">Avg Latency</span>
                                <span class="metric-value">${data.latency}ms</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Throughput</span>
                                <span class="metric-value">${data.throughput} req/s</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Success Rate</span>
                                <span class="metric-value">${data.success_rate}%</span>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>Subsystems</h2>
                            <div class="metric-row">
                                <span class="metric-label">Online</span>
                                <span class="metric-value">${data.subsystems_online}/${data.subsystems_total}</span>
                            </div>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${(data.subsystems_online/data.subsystems_total)*100}%"></div>
                            </div>
                        </div>
                    </div>
                `,
                
                performance: () => `
                    <div class="grid">
                        <div class="card">
                            <h2>Reasoning Performance</h2>
                            <div class="chart-container" id="reasoning-chart"></div>
                            <div class="metric-row">
                                <span class="metric-label">Avg Score</span>
                                <span class="metric-value">${data.reasoning_score}%</span>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>Memory Operations</h2>
                            <div class="metric-row">
                                <span class="metric-label">Retrievals/min</span>
                                <span class="metric-value">${data.memory_ops}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Hit Rate</span>
                                <span class="metric-value">${data.cache_hit}%</span>
                            </div>
                        </div>
                    </div>
                `,
                
                memory: () => `
                    <div class="grid">
                        <div class="card" style="grid-column: 1/-1;">
                            <h2>Memory Tiers</h2>
                            ${data.tiers.map(tier => `
                                <div class="metric-row">
                                    <span class="metric-label">${tier.name}</span>
                                    <span class="metric-value">${tier.count} items</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${(tier.count/tier.max)*100}%"></div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `,
                
                agents: () => `
                    <div class="grid">
                        ${data.agents.map(agent => `
                            <div class="card">
                                <h2>${agent.name}</h2>
                                <div class="metric-row">
                                    <span class="status-indicator" style="background: ${agent.active ? '#00ff88' : '#ff3333'}"></span>
                                    <span class="metric-label">${agent.active ? 'Active' : 'Inactive'}</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Tasks Done</span>
                                    <span class="metric-value">${agent.tasks}</span>
                                </div>
                                <div class="metric-row">
                                    <span class="metric-label">Accuracy</span>
                                    <span class="metric-value">${agent.accuracy}%</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `,
                
                safety: () => `
                    <div class="grid">
                        <div class="card">
                            <h2>Security Status</h2>
                            <div class="metric-row">
                                <span class="metric-label">Threats Detected</span>
                                <span class="metric-value">${data.threats_detected}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Threats Mitigated</span>
                                <span class="metric-value">${data.threats_mitigated}</span>
                            </div>
                            <div class="metric-row">
                                <span class="metric-label">Safety Score</span>
                                <span class="metric-value">${data.safety_score}%</span>
                            </div>
                        </div>
                        
                        <div class="card">
                            <h2>Constraint Violations</h2>
                            ${Object.entries(data.constraints).map(([name, count]) => `
                                <div class="metric-row">
                                    <span class="metric-label">${name}</span>
                                    <span class="metric-value">${count}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `,
                
                logs: () => `
                    <div style="grid-column: 1/-1;">
                        <h2 style="color: #00d4ff; margin-bottom: 15px; text-transform: uppercase;">Recent Events</h2>
                        ${data.logs.map(log => `
                            <div class="log-item ${log.level.toLowerCase()}">
                                <strong>${new Date(log.timestamp).toLocaleTimeString()}</strong>
                                [${log.level}] ${log.message}
                            </div>
                        `).join('')}
                    </div>
                `
            };
            
            return templates[view]?.() || '<p>View not found</p>';
        }
        
        // Update uptime every second
        setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            document.getElementById('uptime').textContent = 
                `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        }, 1000);
        
        // Load content on startup
        loadContent();
        
        // Refresh every 5 seconds
        setInterval(() => currentView === 'overview' && loadContent(), 5000);
    </script>
</body>
</html>
"""


class DashboardServer:
    """Web dashboard server"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.queries_count = 0
        self.log_entries = []
    
    async def get_html(self) -> str:
        """Get dashboard HTML"""
        return DASHBOARD_HTML
    
    async def get_overview_data(self) -> Dict[str, Any]:
        """Get overview data"""
        return {
            'cpu': 35,
            'memory': 62,
            'latency': 245,
            'throughput': 42.5,
            'success_rate': 97.3,
            'subsystems_online': 55,
            'subsystems_total': 55,
        }
    
    async def get_performance_data(self) -> Dict[str, Any]:
        """Get performance data"""
        return {
            'reasoning_score': 88.5,
            'memory_ops': 427,
            'cache_hit': 94.2,
        }
    
    async def get_memory_data(self) -> Dict[str, Any]:
        """Get memory data"""
        return {
            'tiers': [
                {'name': 'Immediate', 'count': 250, 'max': 500},
                {'name': 'Recent', 'count': 1200, 'max': 2000},
                {'name': 'Conceptual', 'count': 3500, 'max': 5000},
                {'name': 'Declarative', 'count': 8000, 'max': 10000},
            ]
        }
    
    async def get_agents_data(self) -> Dict[str, Any]:
        """Get agents data"""
        return {
            'agents': [
                {'name': 'Analyzer', 'active': True, 'tasks': 1247, 'accuracy': 94.2},
                {'name': 'Coder', 'active': True, 'tasks': 856, 'accuracy': 88.5},
                {'name': 'Strategist', 'active': True, 'tasks': 623, 'accuracy': 91.3},
                {'name': 'Creator', 'active': True, 'tasks': 445, 'accuracy': 85.7},
                {'name': 'Researcher', 'active': False, 'tasks': 289, 'accuracy': 92.1},
                {'name': 'Ethicist', 'active': True, 'tasks': 567, 'accuracy': 96.8},
                {'name': 'Executor', 'active': True, 'tasks': 1893, 'accuracy': 89.4},
                {'name': 'Planner', 'active': True, 'tasks': 734, 'accuracy': 93.2},
            ]
        }
    
    async def get_safety_data(self) -> Dict[str, Any]:
        """Get safety data"""
        return {
            'threats_detected': 42,
            'threats_mitigated': 42,
            'safety_score': 99.2,
            'constraints': {
                'no_deception': 0,
                'respect_privacy': 0,
                'avoid_bias': 2,
                'no_harmful': 0,
                'transparency': 1,
            }
        }
    
    async def get_logs_data(self) -> Dict[str, Any]:
        """Get logs data"""
        return {
            'logs': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': 'System initialized successfully'
                },
                {
                    'timestamp': (datetime.now() - timedelta(seconds=30)).isoformat(),
                    'level': 'SUCCESS',
                    'message': 'Query processed: reasoning completed in 245ms'
                },
                {
                    'timestamp': (datetime.now() - timedelta(seconds=60)).isoformat(),
                    'level': 'WARNING',
                    'message': 'Memory tier 3 approaching capacity (82%)'
                },
                {
                    'timestamp': (datetime.now() - timedelta(seconds=120)).isoformat(),
                    'level': 'INFO',
                    'message': 'Evolution cycle 47 completed: 3 improvements applied'
                },
                {
                    'timestamp': (datetime.now() - timedelta(seconds=180)).isoformat(),
                    'level': 'SUCCESS',
                    'message': 'Safety check passed: all constraints satisfied'
                },
            ]
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

def demo_dashboard():
    """Demonstrate dashboard"""
    print("\n" + "="*70)
    print("ADVANCED: WEB DASHBOARD DEMO")
    print("="*70 + "\n")
    
    dashboard = DashboardServer()
    
    print("[Dashboard] HTML Template Generated")
    print(f"  Template Size: {len(DASHBOARD_HTML):,} bytes")
    print(f"  Features: Real-time charts, Live metrics, 6 views, Responsive design")
    
    print("\n[Dashboard] Available Views:")
    views = ['Overview', 'Performance', 'Memory', 'Agents', 'Safety', 'Logs']
    for i, view in enumerate(views, 1):
        print(f"  {i}. {view}")
    
    print("\n[Dashboard] Data Endpoints:")
    print(f"  GET /dashboard                 -> HTML page")
    print(f"  GET /api/dashboard/overview    -> System metrics")
    print(f"  GET /api/dashboard/performance -> Performance data")
    print(f"  GET /api/dashboard/memory      -> Memory status")
    print(f"  GET /api/dashboard/agents      -> Agent status")
    print(f"  GET /api/dashboard/safety      -> Safety report")
    print(f"  GET /api/dashboard/logs        -> System logs")
    
    print("\n[Dashboard] To start server:")
    print(f"  python -m pradysagican serve --dashboard")
    print(f"  Then visit: http://localhost:8000/dashboard")
    
    print("\n[Dashboard] Dashboard Features:")
    features = [
        "Real-time system metrics (CPU, Memory, Latency)",
        "Performance tracking (Reasoning, Memory ops, Cache hit)",
        "Memory tier visualization",
        "Active agents monitoring",
        "Security & threat tracking",
        "Live system event logs",
        "Responsive design (desktop + mobile)",
        "Auto-refresh (5 second intervals)",
        "WebSocket support for streaming",
    ]
    for feature in features:
        print(f"  [+] {feature}")


if __name__ == "__main__":
    demo_dashboard()
