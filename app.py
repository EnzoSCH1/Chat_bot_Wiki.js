from flask import Flask, request, jsonify, render_template_string, make_response
import requests
import os
import re
import subprocess
import hashlib
import yaml
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration CORS pour permettre les requetes depuis Wiki.js
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

WIKI_URL = os.getenv('WIKI_URL', 'http://NOUVELLE_IP:3000')
WIKI_API_TOKEN = os.getenv('WIKI_API_TOKEN', '')
GIT_REPO_URL = os.getenv('GIT_REPO_URL', '')
GIT_BRANCH = os.getenv('GIT_BRANCH', 'main')
GIT_REPO_PATH = os.getenv('GIT_REPO_PATH', '/tmp/wiki-git-repo')
OLLAMA_URL = os.getenv('OLLAMA_URL', '')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:4b')
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY', '')

#Page de test sur le navigateur
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Wiki Chatbot</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 900px; 
            margin: 50px auto; 
            padding: 20px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        h1 { 
            color: #1976d2; 
            display: flex; 
            align-items: center; 
            justify-content: space-between;
            background: white;
            padding: 20px 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        h1 span { font-size: 28px; font-weight: 600; }
        #chat { 
            border: none; 
            border-radius: 12px; 
            height: 450px; 
            overflow-y: auto; 
            padding: 20px; 
            margin-bottom: 15px; 
            background: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .user { 
            color: #1565c0; 
            margin: 12px 0; 
            padding: 12px 16px; 
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); 
            border-radius: 12px 12px 12px 4px;
            font-weight: 500;
        }
        .bot { 
            color: #2e7d32; 
            margin: 12px 0; 
            padding: 16px 20px; 
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%); 
            border-radius: 12px 12px 4px 12px; 
            position: relative;
        }
        .bot-content { white-space: pre-wrap; line-height: 1.6; }
        .bot-content strong { color: #1b5e20; font-weight: 600; }
        .bot-content code { 
            background: rgba(255,255,255,0.7); 
            padding: 3px 8px; 
            border-radius: 5px; 
            font-family: 'Consolas', 'Monaco', monospace; 
            font-size: 0.9em;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .bot-content pre { 
            background: #263238; 
            color: #aed581;
            padding: 15px; 
            border-radius: 8px; 
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.85em;
            margin: 10px 0;
        }
        .bot-content pre code { background: none; border: none; padding: 0; color: inherit; }
        .bot-content ul, .bot-content ol { margin: 10px 0; padding-left: 25px; }
        .bot-content li { margin: 6px 0; line-height: 1.5; }
        .bot-actions { 
            position: absolute; 
            top: 8px; 
            right: 8px; 
            opacity: 0; 
            transition: opacity 0.25s ease;
        }
        .bot:hover .bot-actions { opacity: 1; }
        .btn-copy { 
            background: rgba(255,255,255,0.9); 
            border: 1px solid #c8e6c9; 
            padding: 5px 10px; 
            font-size: 11px; 
            cursor: pointer; 
            border-radius: 6px;
            transition: all 0.2s;
            font-weight: 500;
        }
        .btn-copy:hover { background: #4caf50; color: white; border-color: #4caf50; }
        .sources { 
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); 
            padding: 12px 16px; 
            margin-top: 12px; 
            border-radius: 8px; 
            border-left: 4px solid #ff9800;
        }
        .sources strong { color: #e65100; }
        .sources a { color: #ef6c00; text-decoration: none; font-weight: 500; }
        .sources a:hover { text-decoration: underline; color: #e65100; }
        .examples { 
            background: white; 
            padding: 18px 20px; 
            border-radius: 12px; 
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .examples h3 { 
            margin: 0 0 12px 0; 
            color: #1976d2; 
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .example-btn { 
            background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
            border: none;
            color: white; 
            padding: 8px 16px; 
            margin: 4px; 
            border-radius: 20px; 
            cursor: pointer; 
            font-size: 13px;
            font-weight: 500;
            transition: all 0.25s ease;
            box-shadow: 0 2px 5px rgba(33,150,243,0.3);
        }
        .example-btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(33,150,243,0.4);
        }
        .input-area { 
            display: flex; 
            gap: 12px;
            background: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        input[type="text"] { 
            flex: 1; 
            padding: 14px 18px; 
            font-size: 16px; 
            border: 2px solid #e0e0e0; 
            border-radius: 10px;
            transition: border-color 0.2s;
            font-family: inherit;
        }
        input[type="text"]:focus { 
            outline: none; 
            border-color: #1976d2;
        }
        input[type="text"]::placeholder { color: #9e9e9e; }
        button { 
            padding: 14px 28px; 
            font-size: 16px; 
            cursor: pointer; 
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            color: white; 
            border: none; 
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.25s ease;
            box-shadow: 0 2px 5px rgba(25,118,210,0.3);
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(25,118,210,0.4);
        }
        button:active { transform: translateY(0); }
        button:disabled { 
            background: #bdbdbd; 
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        #loading { 
            display: none; 
            color: #757575; 
            font-style: italic; 
            margin: 15px 0;
            font-size: 15px;
        }
        .loading-dots { 
            position: relative;
            padding-left: 30px;
        }
        .loading-dots::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 20px;
            height: 20px;
            border: 3px solid #e0e0e0;
            border-top-color: #1976d2;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        .loading-dots::after { 
            content: '...';
            animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes spin { to { transform: translateY(-50%) rotate(360deg); } }
        @keyframes dots { 
            0%, 20% { content: '.'; opacity: 0.4; }
            40% { content: '..'; opacity: 0.6; }
            60%, 100% { content: '...'; opacity: 1; }
        }
        .error { 
            color: #c62828; 
            background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%); 
            padding: 12px 16px; 
            border-radius: 8px;
            border-left: 4px solid #f44336;
        }
        .status { 
            font-size: 12px; 
            color: #757575; 
            margin-top: 12px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
        }
        .header-actions { display: flex; gap: 10px; }
        .btn-refresh { 
            padding: 8px 16px; 
            font-size: 13px; 
            background: linear-gradient(135deg, #4caf50 0%, #43a047 100%);
            border-radius: 8px;
        }
        .btn-refresh:hover { background: linear-gradient(135deg, #43a047 0%, #388e3c 100%); }
        .btn-clear { 
            padding: 8px 16px; 
            font-size: 13px; 
            background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
            border-radius: 8px;
        }
        .btn-clear:hover { background: linear-gradient(135deg, #e53935 0%, #d32f2f 100%); }
        .toast { 
            position: fixed; 
            bottom: 25px; 
            right: 25px; 
            background: linear-gradient(135deg, #424242 0%, #616161 100%);
            color: white; 
            padding: 12px 24px; 
            border-radius: 10px; 
            display: none; 
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-weight: 500;
            animation: slideIn 0.3s ease;
        }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        
        /* Scrollbar personnalisée */
        #chat::-webkit-scrollbar { width: 8px; }
        #chat::-webkit-scrollbar-track { background: #f5f5f5; border-radius: 4px; }
        #chat::-webkit-scrollbar-thumb { background: #bdbdbd; border-radius: 4px; }
        #chat::-webkit-scrollbar-thumb:hover { background: #9e9e9e; }
    </style>
</head>
<body>
    <h1>
        <span>Wiki Chatbot</span>
        <div class="header-actions">
            <button class="btn-clear" onclick="clearChat()">Effacer</button>
            <button class="btn-refresh" onclick="refreshDocs()">Refresh</button>
        </div>
    </h1>
    
    <div class="examples" id="examples">
        <h3>Exemples de questions</h3>
        <div>
            <button class="example-btn" onclick="askExample('Comment installer Docker ?')">Docker</button>
            <button class="example-btn" onclick="askExample('Procedure GLPI pour creer un ticket')">GLPI</button>
            <button class="example-btn" onclick="askExample('Configuration VLAN')">VLAN</button>
            <button class="example-btn" onclick="askExample('Authentification Outlook')">Outlook</button>
            <button class="example-btn" onclick="askExample('MFA Microsoft')">MFA</button>
        </div>
    </div>
    
    <div id="chat"><div style="color:#9e9e9e;font-style:italic;text-align:center;padding:40px 20px;">Pose ta premiere question pour commencer...</div></div>
    <div id="loading" class="loading-dots">Recherche dans les documents</div>
    <div class="input-area">
        <input type="text" id="question" placeholder="Tape ta question ici..." onkeypress="if(event.key==='Enter')ask()">
        <button onclick="ask()" id="send-btn">Envoyer</button>
    </div>
    <div class="status" id="status">
        <span id="docs-count">Chargement...</span>
        <span id="last-update"></span>
    </div>
    <div class="toast" id="toast"></div>
    <script>
        let firstQuestion = true;
        
        function showToast(msg) {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.style.display = 'block';
            setTimeout(() => toast.style.display = 'none', 2000);
        }
        
        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => showToast('Copié !'));
        }
        
        function clearChat() {
            document.getElementById('chat').innerHTML = '<div style="color:#666;font-style:italic;">Pose ta premiere question...</div>';
            firstQuestion = true;
            showToast('Chat effacé');
        }
        
        function askExample(question) {
            document.getElementById('question').value = question;
            ask();
        }
        
        function formatMarkdown(text) {
            // Gras
            text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            // Code inline
            text = text.replace(/`(.+?)`/g, '<code>$1</code>');
            // Code block
            text = text.replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');
            // Listes
            text = text.replace(/^\\s*[-*]\\s+(.+)$/gm, '<li>$1</li>');
            text = text.replace(/(<li>.*<\\/li>\\n?)+/g, '<ul>$&</ul>');
            // Numérotation
            text = text.replace(/^\\s*\\d+\\.\\s+(.+)$/gm, '<li>$1</li>');
            // Nouvelles lignes
            text = text.replace(/\\n/g, '<br>');
            return text;
        }
        
        async function refreshDocs() {
            const btn = document.querySelector('.btn-refresh');
            btn.disabled = true;
            btn.textContent = 'Refresh...';
            try {
                const resp = await fetch('/api/refresh', {method: 'POST'});
                const data = await resp.json();
                if (data.success) {
                    showToast(data.message);
                    document.getElementById('docs-count').textContent = data.docs_count + ' documents';
                    document.getElementById('last-update').textContent = 'MAJ: ' + new Date().toLocaleTimeString();
                } else {
                    showToast('Erreur refresh');
                }
            } catch (err) {
                showToast('Erreur: ' + err.message);
            }
            btn.disabled = false;
            btn.textContent = 'Refresh docs';
        }
        
        async function ask() {
            const input = document.getElementById('question');
            const question = input.value.trim();
            if (!question) return;
            
            if (firstQuestion) { 
                document.getElementById('chat').innerHTML = ''; 
                firstQuestion = false; 
                document.getElementById('examples').style.display = 'none';
            }
            
            document.getElementById('chat').innerHTML += '<div class="user">Q: ' + question + '</div>';
            input.value = '';
            document.getElementById('loading').style.display = 'block';
            document.getElementById('send-btn').disabled = true;
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
            
            try {
                const resp = await fetch('/api/search', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({question: question})});
                const data = await resp.json();
                document.getElementById('loading').style.display = 'none';
                document.getElementById('send-btn').disabled = false;
                
                // Ajoute la reponse avec formatage markdown
                const botDiv = document.createElement('div');
                botDiv.className = 'bot';
                const formattedAnswer = formatMarkdown(data.answer);
                botDiv.innerHTML = '<div class="bot-content">' + formattedAnswer + '</div><div class="bot-actions"><button class="btn-copy" onclick="copyText(this.parentElement.parentElement.querySelector(\\'.bot-content\\').innerText)">📋 Copier</button></div>';
                document.getElementById('chat').appendChild(botDiv);
                
                if (data.sources && data.sources.length > 0) {
                    let sourcesHtml = '<div class="sources"><strong>Sources:</strong><br>';
                    data.sources.forEach(s => sourcesHtml += '<a href="' + s.url + '" target="_blank">' + s.title + '</a><br>');
                    sourcesHtml += '</div>';
                    document.getElementById('chat').innerHTML += sourcesHtml;
                }
            } catch (err) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('send-btn').disabled = false;
                document.getElementById('chat').innerHTML += '<div class="error">Erreur: ' + err.message + '</div>';
            }
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
        }
        
        // Charge le nombre de docs au demarrage
        refreshDocs();
    </script>
</body>
</html>
"""

# Cache des documents
docs_cache = []
docs_cache_hash = ""

def get_git_hash():
    """Calcule un hash du depot Git pour detecter les changements"""
    if not GIT_REPO_URL or not os.path.exists(GIT_REPO_PATH):
        return ""
    try:
        result = subprocess.run(['git', '-C', GIT_REPO_PATH, 'rev-parse', 'HEAD'], capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except:
        return ""

def clone_or_pull_repo():
    """Clone ou met a jour le depot Git"""
    global docs_cache, docs_cache_hash
    
    if not GIT_REPO_URL:
        print("GIT_REPO_URL non configure")
        return False
    
    current_hash = get_git_hash()
    if docs_cache and current_hash == docs_cache_hash:
        print(f"Cache Git OK (hash: {current_hash[:8]})")
        return True
    
    print(f"{'Mise a jour' if os.path.exists(GIT_REPO_PATH) else 'Clone'} du depot Git...")
    
    try:
        if os.path.exists(GIT_REPO_PATH):
            # Pull
            subprocess.run(['git', '-C', GIT_REPO_PATH, 'pull', 'origin', GIT_BRANCH], check=True, timeout=120)
        else:
            # Clone
            os.makedirs(os.path.dirname(GIT_REPO_PATH), exist_ok=True)
            subprocess.run(['git', 'clone', '-b', GIT_BRANCH, GIT_REPO_URL, GIT_REPO_PATH], check=True, timeout=120)
        
        # Scanner les fichiers Markdown
        docs_cache = []
        for root, dirs, files in os.walk(GIT_REPO_PATH):
            # Skip .git
            if '.git' in root:
                continue
            for file in files:
                if file.endswith(('.md', '.markdown')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Parser le frontmatter YAML
                        title = file
                        description = ''
                        tags = []
                        
                        # Cherche le bloc YAML au debut
                        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
                        if yaml_match:
                            try:
                                yaml_data = yaml.safe_load(yaml_match.group(1))
                                if yaml_data:
                                    title = yaml_data.get('title', file)
                                    description = yaml_data.get('description', '')
                                    tags = yaml_data.get('tags', [])
                                    if isinstance(tags, str):
                                        tags = [tags]
                            except:
                                pass
                        
                        # Contenu sans le frontmatter pour la recherche
                        content_no_yaml = content
                        if yaml_match:
                            content_no_yaml = content[yaml_match.end():]
                        
                        docs_cache.append({
                            'title': title,
                            'file': file,
                            'path': os.path.relpath(filepath, GIT_REPO_PATH),
                            'description': description,
                            'tags': tags,
                            'content': content_no_yaml[:8000],
                            'full_content_path': filepath
                        })
                    except Exception as e:
                        print(f"Erreur lecture {filepath}: {e}")
        
        docs_cache_hash = get_git_hash()
        print(f"{len(docs_cache)} documents Markdown trouves")
        return True
        
    except subprocess.TimeoutExpired:
        print("Timeout Git operation")
        return False
    except Exception as e:
        print(f"Erreur Git: {e}")
        return False

def search_docs(query):
    """Recherche dans tous les documents Markdown avec algorithme amélioré"""
    query_lower = query.lower()
    query_words = query_lower.split()  # Decoupe en mots cles
    
    # Ontologie - Catégories hiérarchiques (parent → enfants)
    # Permet de matcher "linux" → Ubuntu, Debian, etc.
    ontology = {
        # Systèmes d'exploitation
        'linux': ['ubuntu', 'debian', 'centos', 'rhel', 'redhat', 'fedora', 'suse', 'arch', 'mint'],
        'os': ['windows', 'linux', 'macos', 'mac os', 'android', 'ios'],
        'windows': ['win10', 'win11', 'windows 10', 'windows 11', 'server 2019', 'server 2022', 'w10', 'w11'],
        
        # Containers / Virtualisation
        'container': ['docker', 'kubernetes', 'k8s', 'podman', 'lxc', 'nomad'],
        'virtualisation': ['vm', 'vms', 'virtualbox', 'vmware', 'hyper-v', 'proxmox', 'xen'],
        'orchestration': ['kubernetes', 'k8s', 'docker swarm', 'nomad', 'openshift'],
        
        # Bases de données
        'database': ['mysql', 'postgresql', 'postgres', 'mongodb', 'mongo', 'mariadb', 'sqlserver', 'oracle', 'redis', 'elasticsearch'],
        'db': ['mysql', 'postgresql', 'postgres', 'mongodb', 'mongo', 'mariadb', 'sqlserver', 'oracle', 'redis'],
        'nosql': ['mongodb', 'mongo', 'redis', 'elasticsearch', 'cassandra', 'couchdb'],
        'sql': ['mysql', 'postgresql', 'postgres', 'mariadb', 'sqlserver', 'oracle'],
        
        # Langages / Dev
        'python': ['python3', 'python2', 'pip', 'django', 'flask', 'fastapi'],
        'javascript': ['js', 'node', 'nodejs', 'npm', 'react', 'vue', 'angular'],
        'web': ['html', 'css', 'javascript', 'php', 'apache', 'nginx'],
        'dev': ['git', 'github', 'gitlab', 'ci/cd', 'jenkins', 'maven', 'gradle'],
        
        # Réseau
        'network': ['vlan', 'vpn', 'dns', 'dhcp', 'proxy', 'firewall', 'routeur', 'switch', 'load balancer'],
        'reseau': ['vlan', 'vpn', 'dns', 'dhcp', 'proxy', 'firewall', 'routeur', 'switch'],
        'security': ['firewall', 'antivirus', 'kaspersky', 'defender', 'ssl', 'tls', 'certificat', 'pki'],
        'securite': ['firewall', 'antivirus', 'kaspersky', 'defender', 'ssl', 'tls', 'certificat', 'pki'],
        
        # Cloud
        'cloud': ['azure', 'aws', 'gcp', 'ovh', 'google cloud', 'amazon web services'],
        'azure': ['active directory', 'entra id', 'office 365', 'm365', 'intune'],
        
        # Hardware
        'hardware': ['cpu', 'ram', 'disk', 'gpu', 'ssd', 'hdd', 'bios', 'uefi', 'firmware'],
        'storage': ['raid', 'nas', 'san', 'ssd', 'hdd', 'disk', 'disque'],
        
        # Outils IT
        'monitoring': ['nagios', 'zabbix', 'prometheus', 'grafana', 'datadog'],
        'backup': ['veeam', 'nakivo', 'rsync', 'backupexec'],
        'ticketing': ['glpi', 'jira', 'servicenow', 'freshdesk'],
        'inventory': ['glpi', 'fusioninventory', 'ocsinventory', ' Lansweeper'],
        
        # Productivity
        'office': ['word', 'excel', 'powerpoint', 'outlook', 'teams', 'sharepoint'],
        'mail': ['outlook', 'exchange', 'smtp', 'imap', 'pop3', 'thunderbird'],
        'browser': ['chrome', 'firefox', 'edge', 'safari', 'opera'],
        
        # Mobile
        'mobile': ['iphone', 'ipad', 'android', 'samsung', 'huawei', 'oneplus'],
        'apple': ['iphone', 'ipad', 'macbook', 'imac', 'macos', 'ios'],
        
        # Impression
        'printer': ['hp', 'canon', 'epson', 'brother', 'kyocera', 'ricoh', 'xerox'],
        'imprimante': ['hp', 'canon', 'epson', 'brother', 'kyocera', 'ricoh', 'xerox'],
    }
    
    # Dictionnaire de synonymes pour recherche fuzzy
    synonyms = {
        'config': ['configuration', 'configurer', 'parametrage', 'reglage'],
        'configs': ['configurations'],
        'doc': ['documentation', 'document', 'procedure', 'guide', 'manuel'],
        'docs': ['documentation', 'documents'],
        'install': ['installation', 'installer', 'deployer', 'deploiement'],
        'installe': ['installation', 'installe', 'deploye'],
        'passwd': ['mot de passe', 'password', 'mdp', 'authentification'],
        'password': ['mot de passe', 'passwd', 'mdp'],
        'mdps': ['mots de passe', 'passwords'],
        'auth': ['authentification', 'authentication', 'connexion', 'login'],
        'user': ['utilisateur', 'utilisateurs', 'compte'],
        'users': ['utilisateurs'],
        'admin': ['administrateur', 'administration', 'adm'],
        'admins': ['administrateurs'],
        'param': ['parametre', 'parametres', 'setting', 'option'],
        'params': ['parametres', 'parametres', 'settings', 'options'],
        'setup': ['configuration', 'installation', 'mise en place'],
        'guide': ['documentation', 'tutorial', 'tuto', 'procedure'],
        'howto': ['comment', 'procedure', 'guide'],
        'network': ['reseau', 'reseaux', 'vlan', 'ip'],
        'securite': ['security', 'securiser', 'protection'],
        'backup': ['sauvegarde', 'backups', 'sauvegardes'],
        'restore': ['restauration', 'restaurer', 'recuperer'],
        'migrate': ['migration', 'migrer', 'transfert'],
        'script': ['scripts', 'automatisation', 'automation'],
        'error': ['erreur', 'erreurs', 'probleme', 'problemes'],
        'fix': ['corriger', 'reparer', 'resolution', 'debug'],
        'log': ['logs', 'journaux', 'traces'],
        'srv': ['serveur', 'serveurs'],
        'srvs': ['serveurs'],
        'vm': ['machine virtuelle', 'virtual'],
        'vms': ['machines virtuelles'],
        'db': ['base de donnees', 'database', 'bdd'],
        'api': ['apis', 'endpoint', 'endpoints'],
        'web': ['site', 'www', 'http', 'https'],
        'cloud': ['nuage', 'azure', 'aws', 'ovh'],
        'git': ['github', 'gitlab', 'repository', 'repo'],
        'docker': ['containers', 'container', 'dockerfile'],
        'k8s': ['kubernetes', 'kube', 'kubectl'],
        'mail': ['email', 'courriel', 'courrier', 'smtp', 'imap'],
        'pc': ['poste', 'ordinateur', 'machine'],
        'hp': ['imprimante', 'printer'],
        'bios': ['uefi', 'firmware'],
        'usb': ['cle usb', 'clef usb', 'peripherique'],
        'wifi': ['wireless', 'sans fil', 'reseau sans fil'],
        'vpn': ['virtual private network', 'tunnel'],
        'proxy': ['mandataire', 'proxys'],
        'dns': ['domaine', 'domain', 'resolution'],
        'dhcp': ['ip automatique', 'allocation ip'],
        'raid': ['disque', 'storage', 'stockage'],
        'cpu': ['processeur', 'coeur', 'cores'],
        'ram': ['memoire', 'memory'],
        'disk': ['disque', 'storage', 'stockage'],
        'gpu': ['carte graphique', 'graphics'],
    }
    
    # Expand query avec ontologie + synonymes
    expanded_words = set(query_words)
    
    # 1. Ajouter les enfants de l'ontologie (ex: linux → ubuntu, debian)
    for word in query_words:
        # Ontologie (parent → enfants)
        if word in ontology:
            expanded_words.update(ontology[word])
            print(f"  Ontologie: {word} → {ontology[word]}")
        
        # Synonymes
        if word in synonyms:
            expanded_words.update(synonyms[word])
        
        # Partial match dans ontology et synonyms
        for key, values in {**ontology, **synonyms}.items():
            if word in key or any(word in v for v in values):
                if key in ontology:
                    expanded_words.update(ontology[key])
                if key in synonyms:
                    expanded_words.update(synonyms[key])
                for v in values:
                    expanded_words.add(v)
    
    print(f"  Query originale: {query_words}")
    print(f"  Query expandee: {len(expanded_words)} termes")
    
    results = []
    
    # Refresh cache si besoin
    if not docs_cache:
        clone_or_pull_repo()
    
    for doc in docs_cache:
        title = doc.get('title', '')
        description = doc.get('description', '')
        tags = doc.get('tags', [])
        content = doc.get('content', '')
        
        title_lower = title.lower()
        desc_lower = description.lower() if description else ''
        content_lower = content.lower()
        tags_lower = [t.lower() for t in tags] if tags else []
        
        # Score de pertinence
        score = 0
        match_count = 0
        title_boost = 0
        tag_boost = 0
        
        # 1. Recherche dans les tags (BOOST ×8)
        for tag in tags_lower:
            # Match exact
            if query_lower in tag:
                score += 25 * 8  # BOOST TAG
                tag_boost += 25 * 8
                match_count += 3
            # Match avec mots de la query
            for word in query_words:
                if len(word) > 2 and word in tag:
                    score += 15 * 8  # BOOST TAG
                    tag_boost += 15 * 8
                    match_count += 2
            # Match avec synonymes
            for exp_word in expanded_words:
                if len(exp_word) > 2 and exp_word in tag:
                    score += 10 * 8  # BOOST TAG
                    tag_boost += 10 * 8
                    match_count += 1
        
        # 2. Recherche dans le titre (BOOST ×10)
        if query_lower in title_lower:
            score += 30 * 10  # BOOST TITRE
            title_boost += 30 * 10
            match_count += 5
        
        for word in query_words:
            if len(word) > 2 and word in title_lower:
                score += 15 * 10  # BOOST TITRE
                title_boost += 15 * 10
                match_count += 2
        
        # Match avec synonymes dans le titre
        for exp_word in expanded_words:
            if len(exp_word) > 2 and exp_word in title_lower:
                score += 8 * 10  # BOOST TITRE (moins que mot exact)
                title_boost += 8 * 10
                match_count += 1
        
        # 3. Recherche dans la description (BOOST ×3)
        if desc_lower:
            if query_lower in desc_lower:
                score += 20 * 3
                match_count += 3
            for word in query_words:
                if len(word) > 2 and word in desc_lower:
                    score += 8 * 3
                    match_count += 1
        
        # 4. Recherche dans le contenu
        # Position du match (plus c'est tot, plus c'est pertinent)
        if query_lower in content_lower:
            first_pos = content_lower.find(query_lower)
            if first_pos < 50:
                score += 25
                match_count += 4
            elif first_pos < 200:
                score += 18
                match_count += 3
            elif first_pos < 500:
                score += 12
                match_count += 2
            else:
                score += 6
                match_count += 1
            # Frequence dans le contenu
            freq = content_lower.count(query_lower)
            score += min(freq * 2, 20)
            match_count += min(freq, 5)
        
        # Match avec mots expands dans le contenu
        for exp_word in expanded_words:
            if len(exp_word) > 2 and exp_word in content_lower:
                first_pos = content_lower.find(exp_word)
                if first_pos < 200:
                    score += 8
                    match_count += 1
                else:
                    score += 4
                    match_count += 0.5
        
        # 5. Bonus pour frequence globale
        if match_count > 3:
            score += min(match_count * 2, 25)
        
        # 6. Bonus si plusieurs champs correspondent (titre + tag + contenu)
        field_matches = 0
        if title_boost > 0: field_matches += 1
        if tag_boost > 0: field_matches += 1
        if desc_lower and query_lower in desc_lower: field_matches += 1
        if query_lower in content_lower: field_matches += 1
        
        if field_matches >= 3:
            score += 30  # Bonus multi-champs
        elif field_matches >= 2:
            score += 15
        
        # SCORE MINIMUM requis (filtre les resultats hors-sujet)
        if score >= 15:  # Minimum 15 pour etre inclus
            # Si besoin, reload le contenu complet pour les meilleurs resultats
            full_content = content
            if 'full_content_path' in doc and score > 50:
                try:
                    with open(doc['full_content_path'], 'r', encoding='utf-8', errors='ignore') as f:
                        full_content = f.read()[:8000]
                except:
                    pass
            
            results.append({
                'title': title,
                'file': doc['file'],
                'path': doc['path'],
                'description': description,
                'tags': tags,
                'content': full_content,
                'score': score,
                'title_boost': title_boost,
                'tag_boost': tag_boost
            })
    
    # Trie par score decroissant
    results.sort(key=lambda x: -x['score'])
    
    print(f"  -> {len(results)} documents pertinents (sur {len(docs_cache)} totaux)")
    for r in results[:5]:
        print(f"     - {r['title']} (score: {r['score']:.1f}, titre: {r['title_boost']:.1f}, tags: {r['tag_boost']:.1f})")
    
    return results[:10]  # Top 10 pour le contexte

def ask_ollama(prompt):
    """Demande a Ollama"""
    try:
        headers = {}
        if OLLAMA_API_KEY:
            headers['Authorization'] = f"Bearer {OLLAMA_API_KEY}"
        resp = requests.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}, headers=headers, timeout=120)
        return resp.json().get('response', 'Erreur Ollama')
    except requests.exceptions.Timeout:
        return "Timeout Ollama"
    except Exception as e:
        return f"Erreur Ollama: {str(e)}"

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/search', methods=['POST'])
def api_search():
    question = request.json.get('question', '')
    print(f"Recherche: {question}")
    
    # Recherche dans les docs Git
    pages = search_docs(question)
    
    if not pages:
        return jsonify({
            "answer": "Aucun document trouve. Verifiez que le depot Git est configure et clone.",
            "sources": []
        })
    
    # Construit le contexte avec les documents les plus pertinents
    context_parts = []
    sources = []
    for page in pages:
        title = page.get('title', 'Sans titre')
        path = page.get('path', '')
        content = page.get('content', '')
        
        # Convertir le chemin fichier en URL Wiki
        # Ex: PROXIMITE/Doc_Prox/017_CA_Gestion_Tickets_GLPI/017_CA_Gestion_Tickets_GLPI.md
        # -> https://wiki.caca.com/fr/PROXIMITE/Doc_Prox/017_CA_Gestion_Tickets_GLPI/017_CA_Gestion_Tickets_GLPI
        wiki_path = path.replace('.md', '').replace('.markdown', '')
        wiki_url = f"{WIKI_URL}/fr/{wiki_path}"
        
        sources.append({"title": title, "url": wiki_url})
        context_parts.append(f"Document: {title}\nFichier: {path}\n\n{content}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    prompt = f"""Tu es un assistant expert qui repond TOUJOURS en francais.

Voici des documents pertinents:
{context[:5000]}

Question de l'utilisateur: {question}

Instructions:
- Reponds UNIQUEMENT en francais
- Base ta reponse sur les documents ci-dessus
- Cite les sources pertinentes quand tu les utilises
- Si les documents ne contiennent pas la reponse, dis-le clairement
- Sois concis et precis

Reponse:"""

    answer = ask_ollama(prompt)
    return jsonify({"answer": answer, "sources": sources})

@app.route('/api/refresh', methods=['POST'])
def api_refresh():
    """Force le refresh du cache Git"""
    global docs_cache, docs_cache_hash
    docs_cache = []
    docs_cache_hash = ""
    success = clone_or_pull_repo()
    return jsonify({
        "success": success,
        "docs_count": len(docs_cache),
        "message": f"{len(docs_cache)} documents charges" if success else "Erreur lors du refresh"
    })

@app.route('/api/webhook', methods=['POST'])
def api_webhook():
    """Webhook GitLab - refresh auto quand un doc est modifie"""
    global docs_cache, docs_cache_hash
    
    # Parse GitLab webhook payload
    data = request.json or {}
    event = request.headers.get('X-Gitlab-Event', '')
    
    print(f"Webhook recu: {event}")
    
    # Refresh seulement si push sur la bonne branche
    if event == 'Push Hook':
        ref = data.get('ref', '')
        if ref == f'refs/heads/{GIT_BRANCH}' or ref == GIT_BRANCH:
            # Documents modifies
            changes = data.get('commits', [])
            files_changed = []
            for commit in changes:
                for mod in commit.get('modified', []) + commit.get('added', []):
                    if mod.endswith('.md') or mod.endswith('.markdown'):
                        files_changed.append(mod)
            
            if files_changed:
                print(f"Documents modifies: {files_changed}")
                # Invalidate cache
                docs_cache = []
                docs_cache_hash = ""
                return jsonify({
                    "success": True,
                    "message": f"{len(files_changed)} document(s) modifie(s), cache invalide"
                })
    
    return jsonify({"success": True, "message": "Webhook ignore"})

if __name__ == '__main__':
    print(f"Wiki Chatbot demarre sur le port {os.getenv('FLASK_PORT', 5001)}")
    print(f"Git Repo: {GIT_REPO_URL or 'NON CONFIGURE'}")
    print(f"Ollama: {OLLAMA_URL}")
    
    # Pre-charger les docs au demarrage
    if GIT_REPO_URL:
        clone_or_pull_repo()
    
    app.run(host='0.0.0.0', port=int(os.getenv('FLASK_PORT', 5001)))