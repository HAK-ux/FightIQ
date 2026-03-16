# FightIQ

A full-stack UFC analytics platform that generates data-driven fight predictions using machine learning and real-time fighter statistics.

## What It Does

FightIQ analyzes matchups between UFC fighters by computing statistical deltas across striking output, grappling efficiency, defensive metrics, and physical attributes. A trained Gradient Boosting classifier processes these features to output win probabilities, while Claude AI translates raw model outputs into analyst-style fight previews.

**Core Features:**
- **Matchup Prediction Engine** – Compare any two fighters and get ML-generated win probabilities with confidence levels
- **AI Fight Breakdowns** – Natural language analysis highlighting key advantages, win conditions, and stylistic matchups
- **Fighter Database** – 500+ UFC fighters with detailed performance stats scraped from UFCStats.com
- **Automated Data Pipeline** – Post-event scraper updates fighter stats and status fields, invalidating stale cached predictions
- **Performance Caching** – PostgreSQL-backed prediction cache with 7-day TTL to minimize redundant AI API calls

## Tech Stack

**Backend:**
- FastAPI (Python) – RESTful API with auto-generated OpenAPI docs
- PostgreSQL – Fighter profiles, stats, fight history, and prediction cache
- scikit-learn – Gradient Boosting classifier trained on historical fight outcomes
- BeautifulSoup – Web scraper for UFCStats.com data ingestion
- Anthropic Claude API – AI-generated fight analysis

**Frontend:**
- Next.js (React + TypeScript) – Server-side rendering and dynamic routing
- React Query – API state management and client-side caching
- Tailwind CSS – Responsive UI components
- Recharts – Data visualization (win probability bars, stat comparisons)

## How It Works

### 1. Feature Engineering
For any fighter matchup, the system computes deltas across 11 performance metrics:
```
reach_diff, height_diff, striking_output_diff, striking_defense_diff,
striking_accuracy_diff, striking_absorbed_diff, takedown_offense_diff,
takedown_defense_diff, takedown_accuracy_diff, win_percentage_diff,
experience_diff
```

### 2. ML Prediction
The Gradient Boosting model (trained on 2,000+ historical fights) outputs:
- Win probability for each fighter
- Confidence level (high/medium/low based on probability margin)
- Model method used (`ml_gradient_boosting` or `rule_based_fallback`)

### 3. AI Breakdown
Claude API receives:
- Fighter stats + computed deltas
- Model prediction + confidence
- Win condition heuristics derived from feature importance

Returns a 250-300 word analyst-style preview covering:
- Opening narrative hook
- Key statistical advantages for each fighter
- Most likely win paths (e.g., "control distance with reach" vs. "pressure with takedowns")
- X-factors and stylistic notes

### 4. Caching Strategy
Predictions are stored in a `matchup_cache` table with composite key `(fighter_a_id, fighter_b_id, model_version)`. Cache entries expire after 7 days or when either fighter's stats are updated via the scraper.

## Data Pipeline

The UFCStats scraper runs after each UFC event to:
1. Identify fighters who competed in the most recent event
2. Scrape updated stats (SL/min, TD%, striking defense, etc.)
3. Update `status` field (`active`, `inactive`, `retired`) based on last fight date
4. Invalidate cached predictions involving updated fighters

**Endpoint:** `POST /pipeline/update-after-event?limit=1`

## Project Structure
```
fightiq/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + endpoints
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── matchup.py           # Prediction engine + ML model loader
│   │   ├── ai_breakdown.py      # Claude API integration
│   │   └── pipeline/
│   │       ├── ufcstats_scraper.py  # Web scraper
│   │       └── ingestion.py         # Data sync service
│   ├── scripts/
│   │   ├── train_model.py       # ML model training
│   │   └── import_fighters_csv.py
│   └── models/
│       └── fight_predictor.joblib  # Trained model artifact
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx         # Home page
    │   │   ├── matchup/page.tsx # Fighter selection UI
    │   │   └── prediction/[fighterA]/[fighterB]/page.tsx
    │   ├── components/
    │   │   └── FighterCard.tsx
    │   └── lib/
    │       └── api.ts           # API client + TypeScript types
```

## Key API Endpoints
```
GET  /fighters                    # List all fighters (w/ pagination, filters)
GET  /fighters/{id}               # Single fighter profile
GET  /matchup/{a}/vs/{b}          # Get prediction (cached if available)
GET  /matchup/{a}/vs/{b}/breakdown # Full prediction + AI analysis
POST /pipeline/update-fighter     # Refresh single fighter stats
POST /pipeline/update-after-event # Sync fighters from recent events
```

## Model Performance

Current model: **Gradient Boosting Classifier**
- Training data: 2,000+ historical UFC fights
- ROC-AUC: 0.749
- Top features by importance:
  1. Win percentage differential (24.1%)
  2. Striking output differential (16.2%)
  3. Striking defense differential (14.3%)

## Installation

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
echo "DATABASE_URL=postgresql://user:pass@localhost:5432/fightiq" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env

# Initialize database
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"

# Import initial data
cd scripts
python import_fighters_csv.py

# Train model
python train_model.py

# Start API server
cd ..
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Visit `http://localhost:3000` to use the app.

## Usage

**Build a matchup:**
1. Navigate to `/matchup`
2. Select Fighter A from the list
3. Select Fighter B
4. Click "Generate Prediction"

**Update fighter data after a UFC event:**
```bash
curl -X POST "http://localhost:8000/pipeline/update-after-event?limit=1"
```

## Future Enhancements

- [ ] SHAP values for explainable AI (show which features contributed most to prediction)
- [ ] Fighter ranking system based on recent performance trends
- [ ] Real-time odds comparison vs. Vegas betting lines
- [ ] Historical prediction accuracy tracking (log predictions vs. actual outcomes)
- [ ] Ensemble model (combine Gradient Boosting + Neural Network + Logistic Regression)
