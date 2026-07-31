import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import calendar

# Configure page
st.set_page_config(page_title="Finance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for professional styling
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .header-section {
        padding: 20px 0;
        border-bottom: 2px solid #667eea;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for navigation
if "view" not in st.session_state:
    st.session_state.view = "overview"
if "selected_week" not in st.session_state:
    st.session_state.selected_week = None
if "selected_month" not in st.session_state:
    st.session_state.selected_month = None

# -----------------------------
# LOAD DATA (flexible input: upload / path / manual entry)
# -----------------------------
# Default file path (can be overridden with an environment variable)
DEFAULT_FILE_PATH = os.getenv("DEFAULT_FILE_PATH", "")
FILE_PATH = DEFAULT_FILE_PATH

# Sidebar: choose data source
st.sidebar.header("Data Input")
data_source = st.sidebar.radio(
    "Choose data source:",
    ("Upload File", "Provide Path", "Manual Entry", "Use Default File"),
    index=3
)

uploaded_file = None
file_path_input = ""

if data_source == "Upload File":
    uploaded_file = st.sidebar.file_uploader(
        "Upload Excel or CSV file",
        type=["xlsx", "xls", "csv"],
        help="File should contain a sheet or columns matching the daily expense tracker"
    )
elif data_source == "Provide Path":
    file_path_input = st.sidebar.text_input("Full file path", value=FILE_PATH)

# Manual entry session state
if "manual_rows" not in st.session_state:
    st.session_state.manual_rows = []

if data_source == "Manual Entry":
    with st.sidebar.form("manual_entry_form"):
        m_date = st.date_input("Date", value=datetime.now())
        m_desc = st.text_input("Description")
        m_category = st.selectbox(
            "Category",
            options=["Life Infrastructure", "Lifestyle Enjoyment", "Future Me", "Performance & Growth", "Other"]
        )
        m_amount = st.number_input("Amount (₹)", min_value=0.0, value=0.0, step=1.0, format="%.2f")
        m_payment = st.selectbox("Payment Mode", options=["UPI", "Bank Transfer", "Cash", "Card", "Other"])
        m_type = st.selectbox("Type", options=["Need", "Want", "Investment"])
        m_notes = st.text_input("Notes")
        add_row = st.form_submit_button("Add Row")

    if add_row:
        st.session_state.manual_rows.append({
            "Date": pd.to_datetime(m_date),
            "Description": m_desc,
            "Category": m_category,
            "Amount": float(m_amount),
            "Payment Mode": m_payment,
            "Type": m_type,
            "Notes": m_notes
        })

    if st.session_state.manual_rows:
        st.sidebar.write(f"{len(st.session_state.manual_rows)} manual rows added")
        if st.sidebar.button("Clear Manual Rows"):
            st.session_state.manual_rows = []


def _read_input_file(uploaded_file, path):
    # return a dataframe or None
    try:
        if uploaded_file is not None:
            name = uploaded_file.name.lower()
            if name.endswith(".csv"):
                return pd.read_csv(uploaded_file)
            else:
                # try excel - read first sheet named 'Daily Expense Tracker' if exists
                try:
                    return pd.read_excel(uploaded_file, sheet_name="Daily Expense Tracker")
                except Exception:
                    return pd.read_excel(uploaded_file)

        if path:
            if path.lower().endswith(".csv"):
                return pd.read_csv(path)
            else:
                try:
                    return pd.read_excel(path, sheet_name="Daily Expense Tracker")
                except Exception:
                    return pd.read_excel(path)

        # No file provided
        return None
    except Exception as e:
        st.error(f"Error reading input file: {e}")
        return None


def load_data(data_source, uploaded_file=None, file_path_input=None, manual_rows=None):
    # Start with reading from file if provided
    df = _read_input_file(uploaded_file, file_path_input if data_source == "Provide Path" else (FILE_PATH if data_source == "Use Default File" else None))

    if df is None:
        # If no file (e.g., only manual rows), create empty df with expected columns
        df = pd.DataFrame(columns=["Date", "Description", "Category", "Amount", "Payment Mode", "Type", "Notes"])

    # Ensure columns exist
    expected = ["Date", "Description", "Category", "Amount", "Payment Mode", "Type", "Notes"]
    for col in expected:
        if col not in df.columns:
            df[col] = None

    # Drop rows missing both Date and Amount
    df = df.dropna(subset=["Date", "Amount"], how="any") if not df.empty else df

    # Normalize types
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        # normalize amount: remove commas and convert
        try:
            df["Amount"] = pd.to_numeric(df["Amount"].astype(str).str.replace(",", ""), errors="coerce")
        except Exception:
            df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        df = df.dropna(subset=["Amount"])

        df["Year"] = df["Date"].dt.year
        df["Week"] = df["Date"].dt.isocalendar().week
        df["Month_Num"] = df["Date"].dt.month
        df["Month_Name"] = df["Date"].dt.strftime("%B")
        df["Year_Month"] = df["Date"].dt.strftime("%B %Y")
        df["Day"] = df["Date"].dt.day_name()
        df["Hour"] = df["Date"].dt.hour

    # Append manual rows if any
    if manual_rows:
        manual_df = pd.DataFrame(manual_rows)
        if not manual_df.empty:
            manual_df["Date"] = pd.to_datetime(manual_df["Date"], errors="coerce")
            manual_df = manual_df.dropna(subset=["Date"])
            try:
                manual_df["Amount"] = pd.to_numeric(manual_df["Amount"].astype(str).str.replace(",", ""), errors="coerce")
            except Exception:
                manual_df["Amount"] = pd.to_numeric(manual_df["Amount"], errors="coerce")
            manual_df = manual_df.dropna(subset=["Amount"])

            manual_df["Year"] = manual_df["Date"].dt.year
            manual_df["Week"] = manual_df["Date"].dt.isocalendar().week
            manual_df["Month_Num"] = manual_df["Date"].dt.month
            manual_df["Month_Name"] = manual_df["Date"].dt.strftime("%B")
            manual_df["Year_Month"] = manual_df["Date"].dt.strftime("%B %Y")
            manual_df["Day"] = manual_df["Date"].dt.day_name()
            manual_df["Hour"] = manual_df["Date"].dt.hour

            # Concatenate while preserving original index
            df = pd.concat([df, manual_df], ignore_index=True, sort=False)

    return df


# Load using the selected data source
df = load_data(
    data_source,
    uploaded_file=uploaded_file,
    file_path_input=file_path_input,
    manual_rows=st.session_state.get("manual_rows", [])
)

selected_page = st.sidebar.radio(
    "Choose Page",
    ("Dashboard", "Rent Projection", "Loan Calculator"),
    index=0
)


def calculate_amortization_schedule(principal, annual_rate, tenure_years, extra_payment=0, prepayment_start_month=0):
    monthly_rate = annual_rate / 12 / 100
    total_months = int(tenure_years * 12)

    if monthly_rate == 0:
        emi = principal / total_months
    else:
        emi = principal * monthly_rate * (1 + monthly_rate) ** total_months / ((1 + monthly_rate) ** total_months - 1)

    outstanding = principal
    rows = []

    for month in range(1, total_months + 1):
        interest_paid = outstanding * monthly_rate
        principal_paid = emi - interest_paid
        prepayment = 0

        if prepayment_start_month > 0 and month >= prepayment_start_month:
            prepayment = extra_payment
            principal_paid += prepayment

        if principal_paid > outstanding:
            principal_paid = outstanding
            emi = interest_paid + principal_paid

        outstanding -= principal_paid
        outstanding = max(outstanding, 0)

        rows.append({
            "Month": month,
            "EMI": round(emi),
            "Principal Paid": round(principal_paid),
            "Interest Paid": round(interest_paid),
            "Prepayment": round(prepayment),
            "Outstanding Loan": round(outstanding)
        })

        if outstanding <= 0:
            break

    schedule_df = pd.DataFrame(rows)
    total_principal = schedule_df["Principal Paid"].sum()
    total_interest = schedule_df["Interest Paid"].sum()
    total_paid = schedule_df["EMI"].sum() + schedule_df["Prepayment"].sum()

    return schedule_df, round(emi), round(total_principal), round(total_interest), round(total_paid)


def render_rent_projection():
    st.title("🏠 Rent Projection Calculator")
    st.markdown("*Projected rent growth and total rent paid over time.*")

    st.sidebar.header("Rent Projection Inputs")
    initial_rent = st.sidebar.number_input(
        "Initial Monthly Rent (₹)",
        value=30000,
        step=1000,
        min_value=0
    )

    years = st.sidebar.slider(
        "Projection Years",
        1,
        40,
        20
    )

    annual_increase = st.sidebar.slider(
        "Annual Rent Increase (%)",
        0.0,
        15.0,
        6.0,
        0.5
    )

    move_after = st.sidebar.slider(
        "Move to Bigger House After (Years)",
        0,
        years,
        10
    )

    jump_percent = st.sidebar.slider(
        "Rent Jump After Moving (%)",
        0,
        100,
        20
    )

    include_move = st.sidebar.checkbox(
        "Include Lifestyle Upgrade",
        True
    )

    rent = initial_rent
    rows = []
    cumulative = 0

    for year in range(1, years + 1):
        rent *= (1 + annual_increase / 100)

        if include_move and move_after > 0 and year == move_after:
            rent *= (1 + jump_percent / 100)

        yearly_cost = rent * 12
        cumulative += yearly_cost

        rows.append({
            "Year": year,
            "Monthly Rent": round(rent),
            "Annual Rent": round(yearly_cost),
            "Cumulative Rent": round(cumulative)
        })

    projection_df = pd.DataFrame(rows)

    st.subheader("Projection")
    st.dataframe(projection_df, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(
            projection_df,
            x="Year",
            y="Monthly Rent",
            markers=True,
            title="Monthly Rent Growth"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.line(
            projection_df,
            x="Year",
            y="Cumulative Rent",
            markers=True,
            title="Total Rent Paid"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.metric(
        f"Monthly Rent After {years} Years",
        f"₹{projection_df.iloc[-1]['Monthly Rent']:,}"
    )
    st.metric(
        "Total Rent Paid",
        f"₹{projection_df.iloc[-1]['Cumulative Rent']:,}"
    )


def render_loan_calculator():
    st.title("🏦 Loan Amortization Calculator")
    st.markdown("*Calculate loan EMI, interest, principal repayment, and outstanding balance month by month.*")

    st.sidebar.header("Loan Inputs")
    loan_amount = st.sidebar.number_input(
        "Loan Amount (₹)",
        min_value=0,
        value=5000000,
        step=10000,
        format="%d"
    )

    annual_rate = st.sidebar.number_input(
        "Annual Interest Rate (%)",
        min_value=0.0,
        value=8.0,
        step=0.1,
        format="%.2f"
    )

    tenure_years = st.sidebar.slider(
        "Loan Tenure (Years)",
        1,
        40,
        25
    )

    include_prepayment = st.sidebar.checkbox("Include Monthly Prepayment", False)
    prepayment_start_month = 0
    monthly_prepayment = 0

    if include_prepayment:
        prepayment_start_month = st.sidebar.number_input(
            "Prepayment starts after month",
            min_value=1,
            max_value=tenure_years * 12,
            value=1,
            step=1
        )
        monthly_prepayment = st.sidebar.number_input(
            "Monthly Prepayment Amount (₹)",
            min_value=0,
            value=0,
            step=1000,
            format="%d"
        )

    schedule_df, emi, total_principal, total_interest, total_paid = calculate_amortization_schedule(
        loan_amount,
        annual_rate,
        tenure_years,
        extra_payment=monthly_prepayment,
        prepayment_start_month=prepayment_start_month
    )

    st.subheader("Loan Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Monthly EMI", f"₹{emi:,}")
    col2.metric("Total Principal Paid", f"₹{total_principal:,}")
    col3.metric("Total Interest Paid", f"₹{total_interest:,}")
    col4.metric("Total Amount Paid", f"₹{total_paid:,}")

    st.subheader("Amortization Schedule")
    st.dataframe(
        schedule_df,
        use_container_width=True
    )

    with st.expander("Show charts"):
        fig = px.line(
            schedule_df,
            x="Month",
            y=["Outstanding Loan", "Interest Paid", "Principal Paid"],
            title="Loan Balance and Repayments Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)


if selected_page == "Rent Projection":
    render_rent_projection()
    st.stop()
elif selected_page == "Loan Calculator":
    render_loan_calculator()
    st.stop()

st.title("💰 Personal Finance Intelligence Dashboard")
st.markdown("*Professional expense tracking & financial analysis*")

# Calculate metrics (robust to empty/malformed data)
def _safe_sum(series):
    try:
        return float(series.sum())
    except Exception:
        return 0.0

total_spend = _safe_sum(df["Amount"]) if "Amount" in df.columns else 0.0
need_spend = _safe_sum(df[df.get("Type") == "Need"]["Amount"]) if "Type" in df.columns else 0.0
want_spend = _safe_sum(df[df.get("Type") == "Want"]["Amount"]) if "Type" in df.columns else 0.0
investment = _safe_sum(df[df.get("Category") == "Performance & Growth"]["Amount"]) if "Category" in df.columns else 0.0

# KPI Section
st.markdown("<div class='header-section'>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("💰 Total Spend", f"₹{total_spend:,.0f}", delta=None)
with col2:
    need_pct = f"{(need_spend/total_spend*100):.1f}%" if total_spend else "0.0%"
    st.metric("📌 Need Spend", f"₹{need_spend:,.0f}", need_pct)
with col3:
    want_pct = f"{(want_spend/total_spend*100):.1f}%" if total_spend else "0.0%"
    st.metric("🎯 Want Spend", f"₹{want_spend:,.0f}", want_pct)
with col4:
    invest_pct = f"{(investment/total_spend*100):.1f}%" if total_spend else "0.0%"
    st.metric("📈 Investments", f"₹{investment:,.0f}", invest_pct)

st.markdown("</div>", unsafe_allow_html=True)

# Helper functions for drilling down
def get_week_month_name(week_num, month_num):
    """Get month name for a given week"""
    try:
        if "Week" in df.columns and week_num in df["Week"].values:
            year_vals = df[df["Week"] == week_num]["Year"]
            if not year_vals.empty:
                year = int(year_vals.iloc[0])
            else:
                year = datetime.now().year
        else:
            year = datetime.now().year
    except Exception:
        year = datetime.now().year
    return f"Week {week_num}"

def get_top_transactions_by_week(week_num):
    """Get top transactions for a specific week"""
    if "Week" not in df.columns:
        return pd.DataFrame(columns=["Date", "Description", "Category", "Amount"])
    week_data = df[df["Week"] == week_num].sort_values("Amount", ascending=False).head(10)
    cols = [c for c in ["Date", "Description", "Category", "Amount"] if c in week_data.columns]
    return week_data[cols]

def get_top_transactions_by_month(month_name):
    """Get top transactions for a specific month"""
    if "Year_Month" not in df.columns:
        return pd.DataFrame(columns=["Date", "Description", "Category", "Amount"])
    month_data = df[df["Year_Month"] == month_name].sort_values("Amount", ascending=False).head(10)
    cols = [c for c in ["Date", "Description", "Category", "Amount"] if c in month_data.columns]
    return month_data[cols]

# NAVIGATION LOGIC
if st.session_state.view == "overview":
    
    # ========== WEEKLY ANALYSIS ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("📅 Weekly Spending Analysis")
    st.markdown("</div>", unsafe_allow_html=True)
    
    weekly = (
        df.groupby("Week")["Amount"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "Amount", "count": "Transactions"})
    )
    if weekly.empty:
        st.info("No weekly data available to display.")
    else:
        weekly["Week_Label"] = "Week " + weekly["Week"].astype(str)
        
        # Line chart with interactive hover
        fig_weekly = px.line(
            weekly,
            x="Week",
            y="Amount",
            markers=True,
            hover_data={"Week": False, "Week_Label": True, "Amount": ":.0f", "Transactions": True},
            labels={"Week": "Week Number", "Amount": "Total Spending (₹)"},
            title="Weekly Spending Trend",
            color_discrete_sequence=["#667eea"]
        )
        
        fig_weekly.update_layout(
            hovermode='x unified',
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_weekly, use_container_width=True)
        
        # Weekly summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_week = weekly['Amount'].mean()
            if not np.isfinite(avg_week):
                avg_week = 0
            st.metric("Average Weekly Spend", f"₹{avg_week:,.0f}")
        with col2:
            max_week = weekly['Amount'].max()
            if not np.isfinite(max_week):
                max_week = 0
            st.metric("Highest Week", f"₹{max_week:,.0f}")
        with col3:
            st.metric("Number of Weeks", f"{len(weekly)}")
        
        # Interactive weekly selection
        st.subheader("Drill Down: Select a Week for Details")
        week_options = sorted([w for w in df["Week"].unique() if pd.notna(w)]) if "Week" in df.columns else []
        if week_options:
            selected_week = st.selectbox(
                "Choose a week to view top transactions:",
                options=week_options,
                format_func=lambda x: f"Week {x}",
                key="week_selector"
            )

            if selected_week is not None:
                week_amount = df[df["Week"] == selected_week]["Amount"].sum()
                week_count = len(df[df["Week"] == selected_week])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Week {selected_week}** • Total: ₹{week_amount:,.0f}")
                with col2:
                    st.info(f"**{week_count} transactions** in this week")
                
                if st.button("📊 View Top Transactions for Week", key=f"view_week_{selected_week}"):
                    st.session_state.view = "weekly_detail"
                    st.session_state.selected_week = selected_week
                    st.rerun()
        else:
            st.info("No weeks available for selection.")
    
    # ========== MONTHLY ANALYSIS ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("📈 Monthly Spending Analysis")
    st.markdown("</div>", unsafe_allow_html=True)
    
    monthly = (
        df.groupby("Year_Month")["Amount"]
        .agg(["sum", "count"])
        .reset_index()
        .rename(columns={"sum": "Amount", "count": "Transactions"})
    )
    if monthly.empty:
        st.info("No monthly data available to display.")
    else:
        # Bar chart with interactive hover
        fig_monthly = px.bar(
            monthly,
            x="Year_Month",
            y="Amount",
            hover_data={"Amount": ":.0f", "Transactions": True},
            labels={"Year_Month": "Month", "Amount": "Total Spending (₹)"},
            title="Monthly Spending Breakdown",
            color="Amount",
            color_continuous_scale="RdYlGn_r"
        )
        
        fig_monthly.update_layout(
            height=400,
            template="plotly_white",
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Monthly summary cards
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_month = monthly['Amount'].mean()
            if not np.isfinite(avg_month):
                avg_month = 0
            st.metric("Average Monthly Spend", f"₹{avg_month:,.0f}")
        with col2:
            max_month = monthly['Amount'].max()
            if not np.isfinite(max_month):
                max_month = 0
            st.metric("Highest Month", f"₹{max_month:,.0f}")
        with col3:
            st.metric("Number of Months", f"{len(monthly)}")
        
        # Interactive monthly selection
        st.subheader("Drill Down: Select a Month for Details")
        month_options = sorted([m for m in df["Year_Month"].unique() if pd.notna(m)]) if "Year_Month" in df.columns else []
        if month_options:
            selected_month = st.selectbox(
                "Choose a month to view top transactions:",
                options=month_options,
                key="month_selector"
            )

            if selected_month is not None:
                month_amount = df[df["Year_Month"] == selected_month]["Amount"].sum()
                month_count = len(df[df["Year_Month"] == selected_month])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**{selected_month}** • Total: ₹{month_amount:,.0f}")
                with col2:
                    st.info(f"**{month_count} transactions** in this month")
                
                if st.button("📊 View Top Transactions for Month", key=f"view_month_{selected_month}"):
                    st.session_state.view = "monthly_detail"
                    st.session_state.selected_month = selected_month
                    st.rerun()
        else:
            st.info("No months available for selection.")

elif st.session_state.view == "weekly_detail":
    # Back button
    if st.button("← Back to Overall Dashboard"):
        st.session_state.view = "overview"
        st.session_state.selected_week = None
        st.rerun()
    
    week = st.session_state.selected_week
    if week is None or "Week" not in df.columns or week not in df["Week"].values:
        st.info("No data available for the selected week. Use the back button to choose another view.")
        if st.button("← Back to Overall Dashboard"):
            st.session_state.view = "overview"
            st.session_state.selected_week = None
            st.rerun()
        st.stop()

    st.header(f"📅 Week {week} - Top Transactions")
    
    week_data = df[df["Week"] == week]
    week_total = week_data["Amount"].sum() if not week_data.empty else 0
    week_avg = week_data["Amount"].mean() if not week_data.empty and np.isfinite(week_data["Amount"].mean()) else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Week Total", f"₹{week_total:,.0f}")
    with col2:
        st.metric("Average Transaction", f"₹{week_avg:,.0f}")
    with col3:
        st.metric("Transaction Count", f"{len(week_data)}")
    
    # Top transactions chart
    if not week_data.empty:
        top_week = week_data.nlargest(10, "Amount")
        fig = px.bar(
            top_week,
            x="Description",
            y="Amount",
            color="Category",
            hover_data=["Date", "Category", "Type"],
            title=f"Top 10 Transactions - Week {week}",
            labels={"Amount": "Amount (₹)", "Description": "Transaction"}
        )
        fig.update_layout(height=400, xaxis_tickangle=-45, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions for this week.")
    
    # Transaction table
    st.subheader("All Transactions")
    display_data = week_data[["Date", "Description", "Category", "Type", "Amount"]].sort_values("Amount", ascending=False)
    st.dataframe(display_data, use_container_width=True)

elif st.session_state.view == "monthly_detail":
    # Back button
    if st.button("← Back to Overall Dashboard"):
        st.session_state.view = "overview"
        st.session_state.selected_month = None
        st.rerun()
    
    month = st.session_state.selected_month
    if month is None or "Year_Month" not in df.columns or month not in df["Year_Month"].values:
        st.info("No data available for the selected month. Use the back button to choose another view.")
        if st.button("← Back to Overall Dashboard"):
            st.session_state.view = "overview"
            st.session_state.selected_month = None
            st.rerun()
        st.stop()

    st.header(f"📈 {month} - Top Transactions")
    
    month_data = df[df["Year_Month"] == month]
    month_total = month_data["Amount"].sum() if not month_data.empty else 0
    month_avg = month_data["Amount"].mean() if not month_data.empty and np.isfinite(month_data["Amount"].mean()) else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Month Total", f"₹{month_total:,.0f}")
    with col2:
        st.metric("Average Transaction", f"₹{month_avg:,.0f}")
    with col3:
        st.metric("Transaction Count", f"{len(month_data)}")
    
    # Top transactions chart
    if not month_data.empty:
        top_month = month_data.nlargest(10, "Amount")
        fig = px.bar(
            top_month,
            x="Description",
            y="Amount",
            color="Category",
            hover_data=["Date", "Category", "Type"],
            title=f"Top 10 Transactions - {month}",
            labels={"Amount": "Amount (₹)", "Description": "Transaction"}
        )
        fig.update_layout(height=400, xaxis_tickangle=-45, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transactions for this month.")
    
    # Transaction table
    st.subheader("All Transactions")
    display_data = month_data[["Date", "Description", "Category", "Type", "Amount"]].sort_values("Amount", ascending=False)
    st.dataframe(display_data, use_container_width=True)

# Continue analysis sections (visible only in overview)
if st.session_state.view == "overview":
    
    # ========== CATEGORY & SPENDING BREAKDOWN ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("🏷️ Category & Spending Analysis")
    st.markdown("</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Category Wise Spending")
        cat = (
            df.groupby("Category")["Amount"]
            .sum()
            .sort_values(ascending=False)
        )
        
        fig = px.pie(
            values=cat.values,
            names=cat.index,
            title="Spending by Category",
            hole=0.4
        )
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Need vs Want Analysis")
        need_want = (
            df.groupby("Type")["Amount"]
            .sum()
        )
        
        colors = {"Need": "#2ecc71", "Want": "#e74c3c"}
        fig = px.pie(
            values=need_want.values,
            names=need_want.index,
            color_discrete_map=colors,
            title="Need vs Want Distribution"
        )
        fig.update_layout(height=400, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    # ========== PAYMENT MODE ANALYSIS ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("💳 Payment Mode Analysis")
    st.markdown("</div>", unsafe_allow_html=True)
    
    payment = (
        df.groupby("Payment Mode")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )
    
    fig = px.bar(
        x=payment.index,
        y=payment.values,
        color=payment.values,
        color_continuous_scale="Viridis",
        labels={"x": "Payment Mode", "y": "Amount (₹)"},
        title="Spending by Payment Mode"
    )
    fig.update_layout(height=400, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== INVESTMENT PERSPECTIVE ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("💡 Investment Perspective: Future Impact Analysis")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    **How Current Spending Impacts Your Financial Future:**
    """)
    
    col1, col2, col3 = st.columns(3)
    
    # Calculate investment insights (guard against empty date ranges)
    unique_days = len(df["Date"].dropna().unique()) if "Date" in df.columns else 0
    if unique_days > 0 and total_spend > 0:
        annual_spend = total_spend * (365 / unique_days)
        annual_invest = investment * (365 / unique_days)
        annual_want = want_spend * (365 / unique_days)
    else:
        annual_spend = 0.0
        annual_invest = 0.0
        annual_want = 0.0

    # 5-year projection
    five_year_spend = annual_spend * 5
    five_year_invest = annual_invest * 5
    five_year_want = annual_want * 5

    # Assuming 7% annual return on investments
    five_year_invest_compounded = annual_invest * (((1.07**5 - 1) / 0.07)) if annual_invest else 0.0
    
    with col1:
        st.info(f"""
        **Annual Projection**
        
        💰 Annual Spending: ₹{annual_spend:,.0f}
        
        📈 Annual Investment: ₹{annual_invest:,.0f}
        """)
    
    with col2:
        st.warning(f"""
        **5-Year Outlook**
        
        💸 Total Spent: ₹{five_year_spend:,.0f}
        
        📊 Total Invested: ₹{five_year_invest:,.0f}
        """)
    
    with col3:
        st.success(f"""
        **5-Year Investment Growth**
        
        📈 With 7% Return: ₹{five_year_invest_compounded:,.0f}
        
        💹 Projected Gain: ₹{five_year_invest_compounded - five_year_invest:,.0f}
        """)
    
    # Investment breakdown visualization
    st.subheader("Spending vs Investment Balance")
    
    balance_data = pd.DataFrame({
        "Category": ["Annual Need", "Annual Want", "Annual Investment"],
        "Amount": [
            need_spend * (365 / len(df["Date"].unique())),
            want_spend * (365 / len(df["Date"].unique())),
            investment * (365 / len(df["Date"].unique()))
        ]
    })
    
    fig = px.bar(
        balance_data,
        x="Category",
        y="Amount",
        color="Category",
        color_discrete_map={
            "Annual Need": "#3498db",
            "Annual Want": "#e74c3c",
            "Annual Investment": "#2ecc71"
        },
        title="Annual Breakdown: Needs, Wants, and Investments",
        labels={"Amount": "Amount (₹)", "Category": ""}
    )
    fig.update_layout(height=400, template="plotly_white", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Key insights
    st.subheader("🎯 Key Investment Insights")
    
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        investment_ratio = (investment / total_spend) * 100
        st.metric("Investment Ratio", f"{investment_ratio:.1f}%", 
                 "Target: 10-20%" if investment_ratio < 10 else "On Track" if investment_ratio <= 20 else "Exceeds Target")
    
    with insight_col2:
        want_ratio = (want_spend / total_spend) * 100
        st.metric("Discretionary Spending", f"{want_ratio:.1f}%",
                 "High" if want_ratio > 40 else "Moderate" if want_ratio > 20 else "Low")
    
    # ========== TOP EXPENSES ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("🔥 Top 15 Transactions")
    st.markdown("</div>", unsafe_allow_html=True)
    
    top = (
        df.sort_values(
            "Amount",
            ascending=False
        )
        .head(15)
    )
    
    display_top = top[["Date", "Description", "Category", "Type", "Amount"]].copy()
    display_top["Date"] = display_top["Date"].dt.strftime("%Y-%m-%d")
    
    st.dataframe(display_top, use_container_width=True, hide_index=True)
    
    # ========== IMPROVED SPENDING HEATMAP ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("📊 Spending Heatmap by Day of Week")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    **How to read this heatmap:**
    - 🟢 **Green**: Low spending days (budget-friendly)
    - 🟡 **Yellow**: Moderate spending days
    - 🔴 **Red**: High spending days (watch out!)
    """)
    
    # Day order
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Create heatmap data by day and category
    heatmap_data = df.groupby(["Day", "Category"])["Amount"].sum().reset_index()
    
    # Pivot for better visualization
    heatmap_pivot = heatmap_data.pivot(index="Category", columns="Day", values="Amount").fillna(0)
    
    # Reorder columns
    heatmap_pivot = heatmap_pivot[[day for day in day_order if day in heatmap_pivot.columns]]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=heatmap_pivot.columns,
        y=heatmap_pivot.index,
        colorscale="RdYlGn_r",
        text=np.round(heatmap_pivot.values, 0),
        texttemplate="₹%{text:.0f}",
        textfont={"size": 10},
        hovertemplate="<b>%{y}</b><br>%{x}<br>Amount: ₹%{z:.0f}<extra></extra>",
        colorbar=dict(title="Spending (₹)")
    ))
    
    fig.update_layout(
        title="Spending Heatmap: Amount by Category and Day of Week",
        xaxis_title="Day of Week",
        yaxis_title="Category",
        height=500,
        template="plotly_white"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Daily spending summary
    st.subheader("Daily Spending Summary")
    
    daily_spend = df.groupby("Day")["Amount"].agg(["sum", "mean", "count"]).reset_index()
    daily_spend["Day"] = pd.Categorical(daily_spend["Day"], categories=day_order, ordered=True)
    daily_spend = daily_spend.sort_values("Day")
    
    fig = px.bar(
        daily_spend,
        x="Day",
        y="sum",
        color="sum",
        color_continuous_scale="RdYlGn_r",
        hover_data={"sum": ":.0f", "mean": ":.0f", "count": True},
        labels={"sum": "Total Spending (₹)", "Day": "Day of Week", "mean": "Avg Transaction", "count": "Transactions"},
        title="Total Daily Spending Pattern"
    )
    
    fig.update_layout(height=400, template="plotly_white", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== FINANCIAL INSIGHTS & RECOMMENDATIONS ==========
    st.markdown("<div class='header-section'>", unsafe_allow_html=True)
    st.header("🧠 AI Financial Advisor - Smart Insights")
    st.markdown("</div>", unsafe_allow_html=True)
    
    insights = []
    recommendations = []
    
    # Generate insights
    if want_spend > need_spend * 0.5:
        insights.append("⚠️ High discretionary spending detected - exceeds 50% of needs.")
        recommendations.append("Consider reviewing discretionary purchases to optimize budget allocation.")
    
    if investment < total_spend * 0.1:
        insights.append("📊 Investment allocation is below recommended 10-20% threshold.")
        recommendations.append("Increase investment contributions to build long-term wealth.")
    else:
        insights.append("✅ Investment allocation is within recommended range!")
    
    top_category = cat.idxmax()
    top_category_amount = cat.max()
    top_category_pct = (top_category_amount / total_spend) * 100
    insights.append(f"🏷️ Highest spending category: **{top_category}** (₹{top_category_amount:,.0f}, {top_category_pct:.1f}%)")
    
    avg_daily = (df.groupby("Date")["Amount"].sum().mean())
    insights.append(f"📅 Average daily spend: **₹{avg_daily:,.0f}**")
    
    # Day-based insight
    busiest_day = daily_spend.loc[daily_spend["sum"].idxmax()]
    insights.append(f"📍 Highest spending day: **{busiest_day['Day']}** (₹{busiest_day['sum']:,.0f})")
    
    if want_spend / total_spend > 0.6:
        recommendations.append("Prioritize needs over wants. Current split favors discretionary spending.")
    
    # Display insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Key Findings")
        for insight in insights:
            st.info(insight)
    
    with col2:
        st.subheader("💡 Recommendations")
        for i, rec in enumerate(recommendations, 1):
            st.success(f"**{i}.** {rec}")


