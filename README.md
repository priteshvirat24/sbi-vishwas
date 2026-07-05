<div align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/c/cc/SBI-logo.svg" alt="SBI Logo" width="100"/>
  <h1>SBI Vishwas</h1>
  <p><strong>Autonomous AI Banking Operating System</strong></p>
  <p>Eliminating bureaucratic friction through proactive, multi-agent AI.</p>

  <a href="https://priteshvirat24.github.io/sbi-vishwas/judge"><strong>🏆 View Cinematic Live Demo »</strong></a>
</div>

<br />

## 🚀 The Problem: Digital Adoption vs. Bureaucracy

Time-consuming processes plague various banking services. Customers face significant frustration dealing with inconsistent information, arbitrary demands by bank staff, and mandatory product bundling (like insurance) even for basic services like zero-balance accounts.

> *"Went to SBI to open an account... they kept me there for 3 hours just to open a mere bank account, this is absolutely nuts bruh, we're living in 2026."* — Real Customer Frustration

## 💡 The Solution: SBI Vishwas

**SBI Vishwas** shifts banking from a reactive, human-bottlenecked model to a proactive, AI-driven one. It is an autonomous, multi-agent AI operating system that resolves complex customer requests—from PMJDY account fee waivers to account opening—while strictly adhering to RBI guidelines.

### Key Features
- **Multi-Agent Orchestration**: Specialized agents for Customer Interaction, Policy Compliance, and Journey Tracking.
- **Autonomous Resolution**: Resolves routine branch queries automatically (e.g., reversing incorrect minimum balance deductions).
- **Judge Experience Mode**: A cinematic, real-time 3D visualization command center that allows stakeholders to trace every AI thought process, tool execution, and policy validation live.

## 🛠️ Technology Stack

- **Frontend**: Next.js 16 (App Router), React, Tailwind CSS, Framer Motion & Three.js
- **Backend**: FastAPI (Python), LangChain/LangGraph
- **Database & Memory**: PostgreSQL (Relational), Qdrant (Vector Embeddings for RBI Policies), Redis (Caching & State)
- **Infrastructure**: Docker Compose, GitHub Actions, Prometheus
- **LLM**: Powered by Advanced Agentic Reasoning

## 🎬 Cinematic Judge Mode

We built a custom, interactive command center specifically designed to demonstrate the AI's internal reasoning to stakeholders in under 60 seconds.
**[Experience it live here](https://priteshvirat24.github.io/sbi-vishwas/judge)**

## 💻 Run Locally

Want to spin up the entire 6-container architecture on your local machine?

```bash
# Clone the repository
git clone https://github.com/priteshvirat24/sbi-vishwas.git
cd sbi-vishwas

# Start all microservices (Postgres, Redis, Qdrant, FastAPI, Next.js, Prometheus)
docker compose up -d

# Check the backend health
curl http://localhost:8000/api/v1/health

# Access the frontend
http://localhost:3000
```

## 📈 Commercial Potential

For a massive institution like SBI, resolving even 20% of routine branch queries autonomously translates to millions of hours saved annually. This drastically reduces branch footfall for routine operations, cuts operational costs by up to 60%, and frees up human staff to focus on high-value wealth management and loan advisory services.

---
*Built with ❤️ for the Hackathon.*
