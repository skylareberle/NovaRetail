import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide")

st.title("NovaRetail Customer Intelligence Dashboard")
st.subheader("Revenue, Segment Performance, and Strategic Growth Insights")

# STEP 3 — Load and Prepare Data
try:
    df = pd.read_excel("NR_dataset.xlsx")
except FileNotFoundError:
    st.error("Dataset file not found in repository.")
    st.stop()
except Exception as e:
    st.error("Error loading dataset.")
    st.stop()

# Normalize column names
df.columns = (
    df.columns.str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
)

# Logical required fields
required_fields = [
    "label",
    "customerid",
    "transactionid",
    "transactiondate",
    "productcategory",
    "purchaseamount",
    "customeragegroup",
    "customergender",
    "customerregion",
    "customersatisfaction",
    "retailchannel",
]

missing_fields = [col for col in required_fields if col not in df.columns]

if missing_fields:
    st.error(f"Missing required logical fields: {missing_fields}")
    st.write(df.columns)
    st.stop()

# Datatype conversions
try:
    df["purchaseamount"] = pd.to_numeric(df["purchaseamount"], errors="coerce")
    df["transactiondate"] = pd.to_datetime(df["transactiondate"], errors="coerce")
except Exception:
    st.error("Invalid datatype conversion detected.")
    st.stop()

# Drop rows with null purchase amounts
df = df.dropna(subset=["purchaseamount"])

# Create derived fields
df["year"] = df["transactiondate"].dt.year
df["month"] = df["transactiondate"].dt.month

# STEP 4 — Sidebar Filters
st.sidebar.header("Filters")

def multiselect_filter(column_name, label_name):
    options = sorted(df[column_name].dropna().unique())
    options = ["All"] + options
    selected = st.sidebar.multiselect(label_name, options, default=["All"])
    return selected

label_filter = multiselect_filter("label", "Customer Segment")
region_filter = multiselect_filter("customerregion", "Customer Region")
category_filter = multiselect_filter("productcategory", "Product Category")
channel_filter = multiselect_filter("retailchannel", "Retail Channel")
age_filter = multiselect_filter("customeragegroup", "Customer Age Group")

# STEP 5 — Filtering Logic
filtered_df = df.copy()

def apply_filter(dataframe, column, selected_values):
    if "All" in selected_values:
        return dataframe
    return dataframe[dataframe[column].isin(selected_values)]

filtered_df = apply_filter(filtered_df, "label", label_filter)
filtered_df = apply_filter(filtered_df, "customerregion", region_filter)
filtered_df = apply_filter(filtered_df, "productcategory", category_filter)
filtered_df = apply_filter(filtered_df, "retailchannel", channel_filter)
filtered_df = apply_filter(filtered_df, "customeragegroup", age_filter)

if filtered_df.empty:
    st.warning("No data available for selected filters.")
    st.stop()

# STEP 6 — KPI Section
total_revenue = filtered_df["purchaseamount"].sum()
avg_purchase = filtered_df["purchaseamount"].mean()
total_transactions = filtered_df["transactionid"].nunique()

growth_revenue = filtered_df[
    filtered_df["label"].str.lower().str.contains("growth", na=False)
]["purchaseamount"].sum()

decline_revenue = filtered_df[
    filtered_df["label"].str.lower().str.contains("decline", na=False)
]["purchaseamount"].sum()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Average Purchase Value", f"${avg_purchase:,.2f}")
col3.metric("Total Transactions", f"{total_transactions:,}")
col4.metric("Revenue from Growth Segment", f"${growth_revenue:,.2f}")
col5.metric("Revenue from Decline Segment", f"${decline_revenue:,.2f}")

# STEP 7 — Aggregation Logic
rev_by_segment = (
    filtered_df.groupby("label", as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="purchaseamount", ascending=False)
)

rev_by_region = (
    filtered_df.groupby("customerregion", as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="purchaseamount", ascending=False)
)

rev_by_category = (
    filtered_df.groupby("productcategory", as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="purchaseamount", ascending=False)
)

rev_by_channel = (
    filtered_df.groupby("retailchannel", as_index=False)["purchaseamount"]
    .sum()
    .sort_values(by="purchaseamount", ascending=False)
)

satisfaction_by_segment = (
    filtered_df.groupby("label", as_index=False)["customersatisfaction"]
    .mean()
)

# STEP 8 — Visualizations

fig1 = px.bar(
    rev_by_segment,
    x="label",
    y="purchaseamount",
    title="Revenue by Customer Segment",
)
fig1.update_layout(template="plotly_white")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(
    rev_by_region,
    x="customerregion",
    y="purchaseamount",
    title="Revenue by Region",
)
fig2.update_layout(template="plotly_white")
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.pie(
    rev_by_channel,
    names="retailchannel",
    values="purchaseamount",
    hole=0.4,
    title="Revenue by Retail Channel",
)
fig3.update_layout(template="plotly_white")
st.plotly_chart(fig3, use_container_width=True)

fig4 = px.bar(
    rev_by_category,
    x="productcategory",
    y="purchaseamount",
    title="Revenue by Product Category",
)
fig4.update_layout(template="plotly_white")
st.plotly_chart(fig4, use_container_width=True)

fig5 = px.bar(
    satisfaction_by_segment,
    x="label",
    y="customersatisfaction",
    title="Average Satisfaction by Segment",
)
fig5.update_layout(template="plotly_white")
st.plotly_chart(fig5, use_container_width=True)

# STEP 9 — Early Warning Indicator
decline_percentage = (decline_revenue / total_revenue) * 100 if total_revenue > 0 else 0

st.subheader("Early Warning Indicator")

if decline_percentage > 25:
    st.error(f"Decline Segment Revenue is {decline_percentage:.2f}% of total revenue.")
else:
    st.success(f"Decline Segment Revenue is {decline_percentage:.2f}% of total revenue.")

# STEP 10 — Filtered Data Table
display_columns = [
    "transactiondate",
    "customerid",
    "transactionid",
    "label",
    "productcategory",
    "purchaseamount",
    "customerregion",
    "retailchannel",
    "customersatisfaction",
]

display_columns = [col for col in display_columns if col in filtered_df.columns]

st.subheader("Filtered Transaction Data")
st.dataframe(filtered_df[display_columns].reset_index(drop=True), use_container_width=True)
