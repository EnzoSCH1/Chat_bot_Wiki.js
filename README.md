# En Préparation

# Wiki Chatbot Docker

AI-powered chatbot for **Wiki.js** - Technical documentation from **GitLab** with **Ollama AI responses**.

![interface_web](interface_web_wiki_chatbot.png)
![widget_wiki](widget_wiki.png)
---

##  Quick Start

```bash
cd /path/to/wiki-chatbot-docker-simple
sudo docker compose up -d
```

---

#  Configuration (.env)

| Variable | Description |
|---|---|
| `WIKI_URL` | Wiki.js URL |
| `GIT_REPO_URL` | GitLab URL with token |
| `OLLAMA_URL` | Ollama server URL |
| `OLLAMA_MODEL` | AI model (example: `qwen3:4b`) |
| `FLASK_PORT` | Flask listening port (default: `5001`) |

---

#  Common Commands

## View logs

```bash
sudo docker logs wiki-chatbot-flask -f
```

## Restart

```bash
sudo docker compose restart
```

## Stop

```bash
sudo docker compose down
```

## Rebuild (after code changes or new doc)

```bash
sudo docker compose down
sudo docker compose build
sudo docker compose up -d
```

## Test API

```bash
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "docker"}'
```

## Manual document refresh

```bash
curl -X POST http://localhost:5001/api/refresh
```

---

#  Wiki.js Integration

1. Open **Wiki.js** in your browser
2. Go to:

```
Administration → Theme → Footer Script
```

3. Copy the entire content of `widget.html`
4. Save changes
5. Refresh any Wiki.js page

The chatbot button should appear in the **bottom-left corner**.

---

## GitLab Webhook Setup

In GitLab:

```
Settings → Webhooks
```

Configuration:

```
URL:
http://YOUR_SERVER_IP:5001/api/webhook

Triggers:
Push events

SSL verification:
Disabled (if self-signed)
```

---

# API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Standalone test page |
| `/api/search` | POST | Search + AI response |
| `/api/refresh` | POST | Manual document refresh |
| `/api/webhook` | POST | GitLab webhook |

---

## Example Search Request

```bash
curl -X POST http://localhost:5001/api/search \
  -H "Content-Type: application/json" \
  -d '{"question": "how to configure docker?"}'
```

---

## Example Response

```json
{
  "answer": "To configure Docker, first add the repository...",
  "sources": [
    {
      "title": "Docker Documentation",
      "url": "https://wiki.example.com/docker"
    },
    {
      "title": "Docker Training",
      "url": "https://wiki.example.com/training"
    }
  ]
}
```

---

# Troubleshooting

## Git clone fails

Check token configuration:

```bash
sudo docker exec -it wiki-chatbot-flask env | grep GIT
```

Test manually:

```bash
sudo docker exec -it wiki-chatbot-flask \
git clone https://oauth2:TOKEN@gitlab.example.com/repo.git /tmp/test
```

---

## Ollama not responding

Test from container:

```bash
sudo docker exec -it wiki-chatbot-flask \
curl http://OLLAMA_IP:11434/api/tags
```

---

## Widget not showing

Check:

- Browser console (`F12`) for errors
- Hard refresh page:

```
Ctrl + F5
```

- Verify API URL in `widget.html` matches your server IP

---

## View full logs

```bash
sudo docker logs wiki-chatbot-flask --tail 100
```

---

# Migration to Another Server

1. Copy:

```
wiki-chatbot-docker-migration.tar.gz
```

to the new server.

2. Extract:

```bash
tar -xzvf wiki-chatbot-docker-migration.tar.gz
```

3. Update `.env`:

- New server tokens
- New URLs

4. Update `widget.html`:

- New server IP

5. Start:

```bash
sudo docker compose up -d
```

---

# Security Notes

- GitLab token: **read-only access** to repository
- Ollama token: **limited permissions**
- CORS: Open for Wiki.js (restrict in production)
- SSL: Disabled for GitLab (enable in production)

---

# License

**Internal Use Only**
