# 🚀 Google Ads Diagnostic Tool

An automated analytics and diagnostics system for Google Ads campaigns using FastAPI.

## 📊 Features

* Dashboard metrics (CTR, ROAS, conversions)
* Campaign performance tracking
* Automated issue detection (low CTR, low ROAS, etc.)
* Trend analysis (last 30 days)
* SQLite-based data pipeline

## 🛠️ Tech Stack

* FastAPI
* Python
* SQLite
* Pandas

## 🚀 How to Run

```bash
pip install -r requirements.txt
python data_generator.py
uvicorn main:app --reload
```

## 📌 API Docs

Visit: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📷 Example Endpoints

* `/api/dashboard`
* `/api/diagnostics`
* `/api/campaigns/performance`

## 🎯 Future Improvements

* Frontend dashboard (React)
* ML-based insights
* Deployment (Render/AWS)
