# Expense Tracker Dashboard

This repository contains a Streamlit-based finance dashboard for analyzing daily expenses, viewing summaries, and exploring loan-related calculations.

## What this project does

- Loads expense data from an uploaded Excel/CSV file, a provided file path, manual entry, or the default workbook path
- Visualizes spending by category, month, week, and day
- Provides a dashboard view for expense insights
- Includes a rent projection page and a loan calculator page

## Files

- `eda_on_data.py` - Main Streamlit application
- `requirement.txt` - Python dependencies

## Setup

1. Create and activate a Python environment.
2. Install the required packages:

   ```bash
   pip install -r requirement.txt
   ```

3. Run the app:

   ```bash
   streamlit run eda_on_data.py
   ```

## Notes

- The app expects expense data with columns such as `Date`, `Description`, `Category`, `Amount`, `Payment Mode`, `Type`, and `Notes`.
- If you use a local Excel file, update the default path in the script or provide the path through the app.
