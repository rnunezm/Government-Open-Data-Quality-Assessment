# Government Open Data Quality Assessment via Automated Profilers

## 1. Project Overview

This project is a **data profiling web application** built with **Python 3.11**, **Streamlit**, **Pandas** and **YData Profiling**.  
It allows users to upload a CSV file and generate an interactive profiling report.

---

## Team Structure

### Ruben Dario Nuñez Maldonado - Technical Lead

### Jorge Eduardo Gomez Garnica - Documentation & Presentation Lead

---

## 2. Dataset

https://www.kaggle.com/datasets/shivamb/government-procurement-dataset

## 3. Research Questions

1. How do core quality dimensions such as completeness, uniqueness, consistency, and validity vary across open government tabular datasets?

2. Which metric definitions are better to define if a dataset is appropriate for use across diverse civic domains?

3. How can we combine multiple dimensions into an index that generalizes across datasets?

4. What preprocessing and profiling strategies enable automated, scalable assessment across heterogeneous schemas and APIs?

5. How can standardized scoring and reports inform portal curation, publisher practices, and user decision-making in open data ecosystems?

## 4. Requirements

- Python 3.11 or higher
- Streamlit
- Pandas
- YData Profiling
- Streamlit-YData-Profiling

The required Python packages are listed in `requirements.txt`.

---

## 5. Setup Instructions

    ### Step 1 – Clone the repository
        git clone <your-repo-url>
        cd Data_engineering_project

    ## Step 2 – Create a virtual environment
        python3.11 -m venv venv

    ## Step 3 – Activate the virtual environment
        macOS / Linux:
        source venv/bin/activate
        Windows (PowerShell):
        venv\Scripts\Activate.ps1

    ## Step 4 – Upgrade pip

pip install --upgrade pip

    ## Step 5 – Install dependencies
        pip install -r requirements.txt

## 6. Running the Application

    streamlit run app.py
    The browser will open automatically.
    Upload your CSV file to generate an interactive profiling report.

## 7. Using the App

    ## Step 1. Upload a CSV file using the file uploader.
    ## Step 2. Preview the first rows of your dataset.
    ## Step 3. Generate an interactive profiling report including:
        - Summary statistics
        - Correlation analysis
        - Missing values detection
        - Distribution plots

## 8. Reproducing the Environment

    python3.11 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## 9. Notes

    Always activate the virtual environment before running the app.
    SSL warnings (NotOpenSSLWarning) on macOS can be ignored.
    Python ≥ 3.10 is required for streamlit-ydata-profiling.
    Ensure you run the app using streamlit run app.py, not /usr/bin/python3 app.py.

## 10. Folder Structure Explanation

    Government Open Data Quality Assessment via Automated Profilers/

│
├── dags/
│ └── profiling_dag.py
│
├── src/
│ ├── app.py
│ ├── ingest.py
│ ├── Touch.py
│ └── profiling.py
│
├── data/
│ └── government-procurement-via-gebiz.csv
│
├── figures/
├── tables/
│
├── requirements.txt
└── README.md

## 11. References

    YData Profiling Documentation
    Streamlit Documentation
