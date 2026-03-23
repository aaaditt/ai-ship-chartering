# 🚢 AI-Powered Ship Chartering System

> Intelligent vessel matching, route optimization, and AI-powered negotiation for the oil shipping industry.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61dafb.svg)](https://reactjs.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-green.svg)](https://flask.palletsprojects.com)
[![Gemini](https://img.shields.io/badge/Gemini_API-Integrated-yellow.svg)](https://ai.google.dev)

---

## 📊 Impact Metrics (Research Findings)

| Metric | Traditional | AI-Powered | Improvement |
|--------|------------|------------|-------------|
| Time per Fixture | 4-6 hours | 30 minutes | **90% faster** |
| Staff Required | 25-30 | 8-10 | **70% reduction** |
| Success Rate | 85% | 97% | **+14%** |
| Cost per Fixture | $15-25K | $3-5K | **80% savings** |
| Annual Savings | — | **$9.45M** | 233% ROI |

---

## 🏗️ Technical Architecture

```
┌─────────────────────────┐     ┌──────────────────────────┐
│      React Frontend     │     │     Flask Backend API     │
│  (Vite + Tailwind CSS)  │────▶│   (Python + Flask)       │
│                         │     │                          │
│  • Dashboard            │     │  GET  /api/vessels       │
│  • Charter Request      │     │  POST /api/vessels/match │
│  • Route Map (Leaflet)  │     │  GET  /api/routes        │
│  • AI Negotiation Chat  │     │  POST /api/routes/optimize│
│  • Analytics (Recharts) │     │  POST /api/negotiate     │
│  • Case Study Demo      │     │  GET  /api/analytics     │
└─────────────────────────┘     └──────────┬───────────────┘
                                           │
                                ┌──────────▼───────────────┐
                                │   Google Gemini API      │
                                │   (AI Negotiation)       │
                                └──────────────────────────┘
```

---

## ✨ Features

### 1. Intelligent Vessel Matching
- Multi-factor scoring algorithm (distance, capacity, age, vetting, availability)
- Cargo-to-vessel type compatibility matrix
- Top-5 ranked recommendations with score breakdowns
- Real-time cost estimates

### 2. Route Optimization
- Haversine distance calculation between any two ports
- 10 predefined major shipping routes with waypoints
- Interactive Leaflet map with dark theme
- Risk factor identification (piracy zones, canal congestion)
- Cost estimates per vessel type

### 3. AI Negotiation Simulator
- Gemini API-powered shipowner broker
- Context-aware negotiation with acceptance/counter/rejection
- Intelligent fallback when API is unavailable
- Chat-style interface with status indicators

### 4. Analytics Dashboard
- Side-by-side Traditional vs AI comparison
- Interactive freight rate trend charts
- Annual savings calculator with slider
- Financial impact summary with ROI

### 5. Reliance Case Study Demo
- One-click "Run Demo" button
- Auto-fills: 90,000 MT Gasoline, Jamnagar → Rotterdam
- Step-by-step animated workflow
- Completes in ~30 seconds (simulated)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Google Gemini API key

### Backend Setup
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python app.py
# → Running on http://localhost:5000
```

### Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
# → Running on http://localhost:5173
```

### Environment Variables
Copy `.env.example` comments to `backend/.env` for local development:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
FLASK_DEBUG=1
PORT=5000
```

No frontend `.env` file is needed for local dev — the Vite proxy forwards `/api` to the backend automatically.

---

## 🚀 Deployment

### Backend → Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com) and connect the repo.
3. Render will auto-detect `render.yaml` and configure the service.
4. Set these **Environment Variables** in the Render dashboard:
   | Variable | Value |
   |----------|-------|
   | `GEMINI_API_KEY` | your Google AI Studio key |
   | `CORS_ORIGINS` | your Vercel frontend URL (e.g. `https://ai-ship-chartering.vercel.app`) |
5. Note the service URL (e.g. `https://ai-ship-chartering-backend.onrender.com`).

### Frontend → Vercel

1. Import the repo on [vercel.com](https://vercel.com).
2. Set **Root Directory** to `frontend`.
3. Add this **Environment Variable** in the Vercel project settings:
   | Variable | Value |
   |----------|-------|
   | `VITE_API_URL` | your Render backend URL (e.g. `https://ai-ship-chartering-backend.onrender.com`) |
4. Deploy — the build command `vite build` runs automatically.

> **Note:** After deploying the frontend, go back to Render and update `CORS_ORIGINS` to the final Vercel URL, then redeploy the backend.

---

## 📁 Project Structure

```
ai-ship-chartering/
├── backend/
│   ├── app.py                  # Flask app entry point
│   ├── config.py               # Configuration
│   ├── requirements.txt        # Python dependencies
│   ├── routes/
│   │   ├── vessel_routes.py    # Vessel listing & matching API
│   │   ├── route_routes.py     # Route optimization API
│   │   ├── negotiate_routes.py # AI negotiation API
│   │   └── analytics_routes.py # Analytics & metrics API
│   └── utils/
│       ├── matching.py         # Vessel matching algorithm
│       └── route_utils.py      # Haversine & voyage estimation
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── CharterRequest.jsx
│   │   │   ├── RouteMap.jsx
│   │   │   ├── Negotiation.jsx
│   │   │   ├── Analytics.jsx
│   │   │   └── CaseStudy.jsx
│   │   ├── components/Layout.jsx
│   │   ├── services/api.js
│   │   └── index.css           # Design system
│   └── vite.config.js
├── data/
│   ├── vessels.json            # 18 tanker vessels
│   ├── routes.json             # 10 shipping routes
│   └── freight_rates.json      # Rate history & benchmarks
├── README.md
├── .env.example
└── .gitignore
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, Tailwind CSS |
| Charts | Recharts |
| Maps | React-Leaflet + Leaflet.js |
| Icons | Lucide React |
| Backend | Python, Flask, Flask-CORS |
| AI | Google Gemini API |
| Data | JSON mock data files |

---

## 📡 API Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/vessels` | GET | List vessels (filter: type, status, vetted) |
| `/api/vessels/match` | POST | Match vessels to cargo requirements |
| `/api/routes` | GET | List predefined shipping routes |
| `/api/routes/optimize` | POST | Optimize route between two ports |
| `/api/negotiate` | POST | AI-powered charter negotiation |
| `/api/analytics` | GET | Performance metrics (section: comparison, savings, rates, kpis) |

---

## 🗺️ Roadmap

- [x] Backend API with vessel matching algorithm
- [x] Frontend dashboard with fleet overview
- [x] Charter request form with recommendations
- [x] Interactive route map with Leaflet
- [x] AI negotiation chat interface
- [x] Analytics dashboard with charts
- [x] Reliance case study demo
- [ ] User authentication
- [ ] Real vessel tracking (AIS integration)
- [ ] Live freight rate feeds
- [ ] Multi-party negotiation
- [ ] Mobile app (React Native)

---

## 📄 Research Basis

This system is based on research analyzing AI integration in ship chartering,
using Reliance Industries as a case study. The research demonstrates that
AI can automate vessel selection, route optimization, and negotiation processes,
reducing operational costs by up to 80% while improving fixture success rates.

---

## 👤 Contact

**Aadit** — [GitHub](https://github.com/aadit) • [LinkedIn](https://linkedin.com/in/aadit)

---

*Built with ❤️ for the maritime industry*
