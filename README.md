# En Préparation

# Wiki Chatbot Docker

AI-powered chatbot for Wiki.js - Technical documentation from GitLab with Ollama responses.

## 🚀 Quick Start

```bash
cd /path/to/wiki-chatbot-docker-simple
sudo docker compose up -d
⚙️ Configuration (.env)
Variable	Description
WIKI_URL	Wiki.js URL
GIT_REPO_URL	GitLab URL with token
OLLAMA_URL	Ollama server URL
OLLAMA_MODEL	AI model (e.g., qwen3:4b)
🔧 Common Commands
# View logs
sudo docker logs wiki-chatbot-flask -f

# Restart
sudo docker compose restart

# Test API
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "docker"}'

# Manual refresh
curl -X POST http://localhost:5001/api/refresh
📦 Wiki.js Integration
Go to Administration → Theme → Footer Script
Copy entire content of widget.html
Save
Chatbot button appears bottom-left
🔄 Automation
Service	Frequency	Description
Watchtower	1h	Docker image updates
Auto-refresh Git	24h	Automatic git pull
Webhook GitLab	Push	Instant update on changes
GitLab Webhook Setup
In GitLab: Settings → Webhooks

URL: http://YOUR_IP:5001/api/webhook
Triggers: Push events
SSL: Disabled (if self-signed)
📊 API Endpoints
Endpoint	Method	Description
/	GET	Test page (standalone)
/api/search	POST	Search + AI response
/api/refresh	POST	Manual document refresh
/api/webhook	POST	GitLab webhook
Example Search Request
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "how to configure docker?"}'
Example Response
{
  "answer": "To configure Docker...",
  "sources": [
    {"title": "Docker Wiki", "url": "https://wiki.../docker"},
    {"title": "Docker Training", "url": "https://wiki.../formation"}
  ]
}
🐛 Troubleshooting
Git clone fails
# Check token
sudo docker exec -it wiki-chatbot-flask env | grep GIT

# Test manually
sudo docker exec -it wiki-chatbot-flask \
  git clone https://oauth2:TOKEN@gitlab.example.com/repo.git /tmp/test
Ollama not responding
# Test from container
sudo docker exec -it wiki-chatbot-flask \
  curl http://OLLAMA_IP:11434/api/tags
Widget not showing
Check browser console (F12)
Hard refresh (Ctrl+F5)
Verify API URL in widget.html
Full logs
sudo docker logs wiki-chatbot-flask --tail 100
📝 Migration to Another Machine
Copy wiki-chatbot-docker-migration.tar.gz
Extract: tar -xzvf wiki-chatbot-docker-migration.tar.gz
Update .env and widget.html with new IP
Start: sudo docker compose up -d
🛡️ Security Notes
GitLab token: read-only access
Ollama token: limited permissions
CORS: Open for Wiki.js (restrict in production)
SSL: Disabled for GitLab (enable in production)
📄 License
Internal Use Only
