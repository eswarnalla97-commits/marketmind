import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from database.db_manager import query_df

def run_customer_segmentation(k_clusters=4):
    """
    Executes K-Means Customer Segmentation on real warehouse metrics:
    Features: Recency (days), Frequency (orders), Monetary (total spend), AvgOrderValue (AOV).
    Features are scaled with StandardScaler before clustering.
    """
    k = max(2, min(int(k_clusters), 6))

    query = """
        SELECT 
            c.CustomerID,
            c.CustomerName,
            c.Country,
            COUNT(DISTINCT f.OrderKey) AS Frequency,
            SUM(f.Quantity) AS TotalUnits,
            ROUND(SUM(f.TotalAmount), 2) AS Monetary,
            ROUND(AVG(f.TotalAmount), 2) AS AvgOrderValue,
            MAX(d.FullDate) AS LastPurchaseDate
        FROM DimCustomer c
        JOIN FactSales f ON c.CustomerKey = f.CustomerKey
        JOIN DimDate d ON f.DateKey = d.DateKey
        GROUP BY c.CustomerID, c.CustomerName, c.Country
        HAVING Monetary > 0
    """
    df_cust = query_df(query)

    if df_cust.empty or len(df_cust) < k:
        return {
            "success": False,
            "message": f"Insufficient customer records ({len(df_cust)}) for {k} clusters.",
            "k_clusters": k,
            "total_customers": len(df_cust),
            "clusters": [],
            "customers": [],
            "scatter_data": []
        }

    # Calculate Recency: Days since reference max date
    df_cust['LastPurchaseDate'] = pd.to_datetime(df_cust['LastPurchaseDate'])
    max_date = df_cust['LastPurchaseDate'].max()
    df_cust['Recency'] = (max_date - df_cust['LastPurchaseDate']).dt.days

    # Features for clustering
    feature_cols = ['Recency', 'Frequency', 'Monetary', 'AvgOrderValue']
    X = df_cust[feature_cols].copy()

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Apply K-Means
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    df_cust['Cluster'] = kmeans.fit_predict(X_scaled)

    # Compute Cluster Profiles
    cluster_profiles = []
    cluster_grouped = df_cust.groupby('Cluster')

    # Rank clusters by Average Monetary to give intelligent business labels
    cluster_monetary_ranks = cluster_grouped['Monetary'].mean().sort_values(ascending=False).index.tolist()

    persona_templates = [
        {"name": "Champions / Elite", "badge": "bg-success", "desc": "Highest lifetime spend, frequent recent purchases, best brand advocates."},
        {"name": "Loyal Customers", "badge": "bg-primary", "desc": "Steady transaction frequency, consistent spending, highly engaged."},
        {"name": "Potential / Growth", "badge": "bg-info", "desc": "Moderate spenders with growing frequency, potential to become loyalists."},
        {"name": "At-Risk / Lapsed", "badge": "bg-warning", "desc": "Above-average spend previously, but high recency (long time since last order)."},
        {"name": "Occasional / New", "badge": "bg-secondary", "desc": "Low transaction count and low spend; newer or one-off shoppers."},
        {"name": "Bargain Hunters", "badge": "bg-dark", "desc": "Price-sensitive buyers with low order values and high interval gaps."}
    ]

    cluster_labels = {}
    for rank_idx, cluster_id in enumerate(cluster_monetary_ranks):
        assigned_persona = persona_templates[rank_idx % len(persona_templates)]
        cluster_labels[cluster_id] = assigned_persona

    total_customers_count = len(df_cust)

    for cluster_id in range(k):
        c_sub = df_cust[df_cust['Cluster'] == cluster_id]
        persona = cluster_labels.get(cluster_id, persona_templates[0])
        count = len(c_sub)
        pct = round((count / total_customers_count) * 100, 1)

        cluster_profiles.append({
            "cluster_id": cluster_id,
            "name": persona["name"],
            "badge": persona["badge"],
            "description": persona["desc"],
            "customer_count": count,
            "percentage": pct,
            "avg_spend": round(float(c_sub['Monetary'].mean()), 2),
            "avg_frequency": round(float(c_sub['Frequency'].mean()), 1),
            "avg_recency": round(float(c_sub['Recency'].mean()), 1),
            "avg_aov": round(float(c_sub['AvgOrderValue'].mean()), 2),
            "total_cluster_spend": round(float(c_sub['Monetary'].sum()), 2)
        })

    # Add persona info to each row
    df_cust['SegmentName'] = df_cust['Cluster'].apply(lambda c: cluster_labels[c]['name'])
    df_cust['BadgeClass'] = df_cust['Cluster'].apply(lambda c: cluster_labels[c]['badge'])

    # Format customer list for table
    customer_list = []
    df_sorted = df_cust.sort_values(by='Monetary', ascending=False)
    for _, row in df_sorted.iterrows():
        customer_list.append({
            "customer_id": str(row['CustomerID']),
            "country": str(row['Country']),
            "frequency": int(row['Frequency']),
            "monetary": float(round(row['Monetary'], 2)),
            "aov": float(round(row['AvgOrderValue'], 2)),
            "recency": int(row['Recency']),
            "cluster_id": int(row['Cluster']),
            "segment_name": row['SegmentName'],
            "badge_class": row['BadgeClass']
        })

    # Prepare scatter plot points (Spend vs Frequency with cluster assignment)
    scatter_points = []
    for _, row in df_cust.iterrows():
        scatter_points.append({
            "x": float(round(row['Frequency'], 1)),
            "y": float(round(row['Monetary'], 2)),
            "cluster": int(row['Cluster']),
            "customer_id": str(row['CustomerID']),
            "segment": row['SegmentName']
        })

    return {
        "success": True,
        "k_clusters": k,
        "total_customers": total_customers_count,
        "clusters": cluster_profiles,
        "customers": customer_list,
        "scatter_data": scatter_points,
        "summary": {
            "total_customers": total_customers_count,
            "k_clusters": k,
            "total_spend": round(float(df_cust['Monetary'].sum()), 2),
            "avg_spend_overall": round(float(df_cust['Monetary'].mean()), 2),
            "avg_orders_overall": round(float(df_cust['Frequency'].mean()), 1)
        }
    }
