<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/c/cc/SBI-logo.svg" alt="SBI Logo" width="100"/>
  <h1>SBI Vishwas</h1>
  <p><strong>The Autonomous AI Banking Operating System (that never takes a 3-hour lunch break)</strong></p>

  <a href="https://priteshvirat24.github.io/sbi-vishwas/judge"><strong>🏆 Launch the Cinematic Judge Mode »</strong></a>
</div>

<br />

## 🏦 The Problem: "Come back after lunch."

Let's face it. We love our banks, but dealing with branch bureaucracy in 2026 feels like a time-travel expedition back to the 90s. 

> *"Went to SBI to open an account... they kept me there for 3 hours just to open a mere bank account, this is absolutely nuts bruh."* — A tired human on Reddit.

Customers are bounced between counters, penalized for rules they didn't know existed, and forced to buy insurance just to open a zero-balance account. We decided to fix this by throwing an entire fleet of autonomous AI agents at the problem.

## 🦸‍♂️ The Solution: Multi-Agent Bureaucracy Destroyers

**SBI Vishwas** isn't just a chatbot that says *"Press 1 for balance."* It is a proactive, multi-agent AI Operating System. 

Instead of waiting for a human manager to approve a fee waiver, Vishwas deploys a **Swarm of Agents** to autonomously fetch your CBS data, cross-reference it against the entire RBI policy vector database, realize the bank was wrong, and refund your money—all in under 5 seconds. 

---

## 🏗️ Architecture & Tech Stack (The Fun Stuff)

We built a state-of-the-art, fully containerized microservice architecture. 

### 🧠 The Brain (Backend & AI)
- **FastAPI (Python)**: High-performance async API server.
- **LangChain & LangGraph**: Orchestrating the multi-agent swarm.
  - *Orchestrator Agent*: The boss. Analyzes intent and delegates.
  - *Journey Tracker*: Hooks into the Core Banking System (CBS).
  - *Policy Compliance*: A legal nerd that reads RBI guidelines.
- **Qdrant (Vector Database)**: We embedded thousands of pages of RBI policies so our AI never hallucinates a banking rule.
- **Google Gemini**: Providing the heavy-lifting reasoning capabilities.
- **PostgreSQL & Redis**: Because we still need to store relational data and cache state like it's a real bank.

### 🎨 The Face (Frontend & UX)
- **Next.js 16 (App Router)**: Blazing fast React framework.
- **Tailwind CSS & Framer Motion**: Because enterprise software doesn't have to look like a spreadsheet from 2004.
- **Three.js / React Three Fiber**: We built a cinematic 3D "Brain" visualization.
- **Static Export**: The entire frontend is statically exported and hosted on GitHub Pages for a permanently live demo.

### 🚀 DevOps (Infrastructure)
- **Docker Compose**: 6 containers spinning in perfect harmony (Postgres, Redis, Qdrant, FastAPI, Next.js, Prometheus).
- **GitHub Actions**: Fully automated CI/CD pipeline building our static exports.
- **Prometheus**: For tracking AI token usage and latency.

---

## 🎬 Cinematic Judge Mode

Hackathon judges are busy. They don't have time to read source code. 

So, we built **Judge Mode**—an immersive, 60-second automated 3D cinematic presentation. It literally drives itself, visualizing the AI's internal thought process, tool execution, and policy validation in real-time. 

**[👉 Sit back and watch it here](https://priteshvirat24.github.io/sbi-vishwas/judge)**

---

## 💻 Run It Yourself

Want to summon the agents on your local machine? You'll need Docker.

```bash
# Clone the repository
git clone https://github.com/priteshvirat24/sbi-vishwas.git
cd sbi-vishwas

# Summon the 6-container architecture
docker compose up -d

# Verify the AI backend is breathing
curl http://localhost:8000/api/v1/health

# Open the cinematic frontend
http://localhost:3000
```

---
*Built with ❤️, ☕, and a burning desire to never wait in a bank line again.*
