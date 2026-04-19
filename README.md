
# 📊 Hackathon Project — Customer Analytics & Churn Prediction

## 📌 Overview

This project was developed during a Rostelecom hackathon and focuses on **customer behavior analysis**, **conversion funnel optimization**, and **churn prediction**.

The goal is to extract actionable insights from user event data and build models that help:

* understand user journeys
* identify drop-off points in the funnel
* predict customer churn
* improve retention and monetization strategies

---

## 🧠 Key Features

### 1. Funnel Analysis

* Event-based user journey tracking
* Separate analysis for:

  * anonymous users
  * authorized users
* Sankey diagrams for visualizing transitions

📁 Files:

* `Event-based buyer funnel analysis.ipynb`
* `sankey_anonymous.html`
* `sankey_authorized.html`
* `sankey_links_*.csv`

---

### 2. Customer Behavior Analytics

* Weekly session statistics
* Traffic source and browser impact
* Margin analysis across segments

📁 Files:

* `sessions_weekly_stats.csv`
* `margin_by_source_and_browser.csv`
* `weekly_margin_analytics.csv`
* `source_control.ipynb`

---

### 3. Churn Prediction Model

* Machine learning model for predicting customer churn
* Output predictions for further business use

📁 Files:

* `churn_model.ipynb`
* `customer_churn_predictions.csv`

---

### 4. Purchase Behavior Analysis

* Time intervals between purchases
* Identification of inactive users

📁 Files:

* `intervals_between_purchases_*.csv`
* `lose.ipynb`

---

### 5. Recommendation System

* Prototype of recommendation logic based on user behavior

📁 Files:

* `recommend.ipynb`

---

### 6. Dashboard Preparation

* Data preprocessing for dashboards and visualization tools

📁 Files:

* `ForDashBoard.ipynb`

---

## 🏗 Project Structure

```
hackathon-main/
│
├── Dima/        # Funnel analysis & traffic analytics
├── Viktor/      # Behavioral analysis & dashboards
├── artem/       # Churn model & recommendations
│
├── *.csv        # Processed datasets
├── *.ipynb      # Jupyter notebooks with analysis
```

---

## ⚙️ Technologies Used

* Python
* Jupyter Notebook
* Pandas / NumPy
* Matplotlib / Plotly (for visualization)
* Machine Learning (likely sklearn / similar)

---

## 🚀 How to Run

1. Clone the repository:

```bash
git clone <repo-url>
cd hackathon-main
```

2. Install dependencies:

```bash
pip install pandas numpy matplotlib jupyter
```

3. Run notebooks:

```bash
jupyter notebook
```

---

## 📈 Results & Insights

* Identified key drop-off points in user funnel
* Built churn prediction model for proactive retention
* Analyzed impact of traffic sources on revenue
* Derived behavioral patterns from purchase intervals

---

## 💡 Business Value

This project enables:

* targeted retention campaigns
* improved conversion rates
* better marketing channel allocation
* personalized recommendations

---

## 👥 Team

* Dima — Funnel & traffic analytics
* Viktor — Behavioral analysis & dashboards
* Artem — ML & churn prediction

---

## 📝 Notes

* Some notebooks are experimental and may contain intermediate results
* Data is preprocessed and partially anonymized
* Visualization outputs are included as `.html` files
