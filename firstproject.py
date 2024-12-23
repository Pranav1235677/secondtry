import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from faker import Faker
import random
import calendar

# Initialize Faker
fake = Faker()

# Function to generate simulated dataset for a given month
def generate_data(month):
    categories = [
        "Food", "Transportation", "Bills", "Groceries", "Entertainment",
        "Investments", "School FEES", "College FEES", "Fruits & Vegetables",
        "Stationery", "Subscriptions", "Sports & Fitness", "Home Essentials"
    ]
    payment_modes = ["Cash", "Online", "Credit Card", "Debit Card", "Wallet", "Net Banking", "UPI"]
    data = []
    for _ in range(100):
        date = fake.date_between_dates(
            date_start=pd.Timestamp(f"2024-{month:02d}-01"),
            date_end=pd.Timestamp(f"2024-{month:02d}-{calendar.monthrange(2024, month)[1]}")
        )
        data.append({
            "Date": date,
            "Category": random.choice(categories),
            "Payment_Mode": random.choice(payment_modes),
            "Description": random.choice([
                "Investment in mutual funds", "Paid school fees", "Bought groceries",
                "Dining out with family", "Purchased new stationery",
                "Monthly subscription fee", "Gym membership renewal",
                "Home improvement essentials"
            ]),
            "Amount_Paid": round(random.uniform(10.0, 500.0), 2),
            "Cashback": round(random.uniform(0.0, 20.0), 2),
            "Month": calendar.month_name[month]
        })
    return pd.DataFrame(data)

# Function to initialize the SQLite database with 12 monthly tables
def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    for month in range(1, 13):
        month_name = calendar.month_name[month]
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {month_name} (
                Date TEXT,
                Category TEXT,
                Payment_Mode TEXT,
                Description TEXT,
                Amount_Paid REAL,
                Cashback REAL,
                Month TEXT
            )
        """)
    conn.commit()
    conn.close()

# Function to load data into the corresponding monthly table
def load_data_to_db(data, month):
    conn = sqlite3.connect('expenses.db')
    month_name = calendar.month_name[month]
    data.to_sql(month_name, conn, if_exists='append', index=False)
    conn.close()

# Function to query data from all or specific monthly tables
def query_data(query):
    conn = sqlite3.connect('expenses.db')
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result

# Predefined SQL Queries
SQL_QUERIES = {
    "Total Amount Spent per Category": "SELECT Category, SUM(Amount_Paid) AS Total_Spent FROM expenses GROUP BY Category",
    "Monthly Spending Breakdown": "SELECT Month, SUM(Amount_Paid) AS Total_Spent FROM expenses GROUP BY Month",
    "Top 5 Highest Expenses": "SELECT * FROM expenses ORDER BY Amount_Paid DESC LIMIT 5",
    "Cash vs Online Transactions": "SELECT Payment_Mode, COUNT(*) AS Transaction_Count, SUM(Amount_Paid) AS Total_Spent FROM expenses GROUP BY Payment_Mode",
    "Average Cashback by Category": "SELECT Category, AVG(Cashback) AS Avg_Cashback FROM expenses GROUP BY Category",
    "Spending Trends Over Time": "SELECT Date, SUM(Amount_Paid) AS Daily_Spent FROM expenses GROUP BY Date ORDER BY Date",
    "Top Spending Days": "SELECT Date, SUM(Amount_Paid) AS Total_Spent FROM expenses GROUP BY Date ORDER BY Total_Spent DESC LIMIT 10",
    "Average Spending by Month": "SELECT Month, AVG(Amount_Paid) AS Avg_Spending FROM expenses GROUP BY Month",
    "Category Breakdown for January": "SELECT Category, SUM(Amount_Paid) AS Total_Spent FROM January GROUP BY Category",
    "Highest Cashback Transactions": "SELECT * FROM expenses ORDER BY Cashback DESC LIMIT 5",
    "Transactions Above 300": "SELECT * FROM expenses WHERE Amount_Paid > 300 ORDER BY Amount_Paid DESC",
    "Most Frequently Used Payment Mode": "SELECT Payment_Mode, COUNT(*) AS Usage_Count FROM expenses GROUP BY Payment_Mode ORDER BY Usage_Count DESC LIMIT 1",
    "Least Spent Categories": "SELECT Category, SUM(Amount_Paid) AS Total_Spent FROM expenses GROUP BY Category ORDER BY Total_Spent ASC LIMIT 5",
    "Daily Average Spending": "SELECT Date, AVG(Amount_Paid) AS Avg_Spending FROM expenses GROUP BY Date ORDER BY Date",
    "Weekly Spending Trends": "SELECT strftime('%W', Date) AS Week_Number, SUM(Amount_Paid) AS Weekly_Spent FROM expenses GROUP BY Week_Number",
    "Category-Wise Transaction Count": "SELECT Category, COUNT(*) AS Transaction_Count FROM expenses GROUP BY Category ORDER BY Transaction_Count DESC"
}

# Streamlit Application
st.title("Personal Expense Tracker")

# Sidebar options
option = st.sidebar.selectbox(
    "Choose an option",
    ["Generate Data", "View Data", "Visualize Insights", "Run SQL Query", "Predefined SQL Queries"]
)

if option == "Generate Data":
    st.subheader("Generate Expense Data")
    month = st.selectbox("Select a month to generate data:", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
    if st.button("Generate"):
        data = generate_data(month)
        load_data_to_db(data, month)
        st.success(f"Data for {calendar.month_name[month]} generated and loaded into the database!")
        st.dataframe(data.head())

elif option == "View Data":
    st.subheader("View Expense Data")
    month = st.selectbox("Select a month to view data:", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
    query = f"SELECT * FROM {calendar.month_name[month]}"
    data = query_data(query)
    st.dataframe(data)

elif option == "Visualize Insights":
    st.subheader("Spending Insights")
    query = "SELECT Category, SUM(Amount_Paid) as Total_Spent FROM expenses GROUP BY Category"
    data = query_data(query)
    st.bar_chart(data.set_index("Category"))

    # Pie Chart
    fig, ax = plt.subplots()
    ax.pie(data["Total_Spent"], labels=data["Category"], autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    st.pyplot(fig)

elif option == "Run SQL Query":
    st.subheader("Run Custom SQL Query")
    query = st.text_area("Enter your SQL query:")
    if st.button("Execute"):
        try:
            data = query_data(query)
            st.dataframe(data)
        except Exception as e:
            st.error(f"An error occurred: {e}")

elif option == "Predefined SQL Queries":
    st.subheader("Predefined SQL Queries")
    query_name = st.selectbox("Select a query to run", list(SQL_QUERIES.keys()))
    query = SQL_QUERIES[query_name]
    if st.button("Run Query"):
        data = query_data(query)
        st.dataframe(data)
        if query_name == "Spending Trends Over Time":
            st.line_chart(data.set_index("Date"))
        elif query_name in ["Total Amount Spent per Category", "Cash vs Online Transactions"]:
            st.bar_chart(data.set_index(data.columns[0]))

# Initialize the database
init_db()