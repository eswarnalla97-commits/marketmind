import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from database.db_manager import query_df

def run_apriori_mining(min_support=0.02, min_confidence=0.25, sort_by='lift', category=None):
    """
    Executes Apriori Market Basket Analysis on actual warehouse transaction data.
    
    Parameters:
    - min_support: Minimum frequency threshold (0.01 - 0.5)
    - min_confidence: Minimum conditional probability (0.1 - 1.0)
    - sort_by: Column to order rules by ('lift', 'confidence', 'support')
    - category: Optional category filter
    
    Returns:
    - Dictionary containing metrics, frequent itemsets, rules, and top product pairs.
    """
    query = """
        SELECT 
            o.InvoiceNo,
            p.ProductName,
            p.Category,
            f.Quantity
        FROM FactSales f
        JOIN DimOrder o ON f.OrderKey = o.OrderKey
        JOIN DimProduct p ON f.ProductKey = p.ProductKey
        WHERE f.Quantity > 0
    """
    params = []
    if category and category.lower() != 'all':
        query += " AND p.Category = ?"
        params.append(category)

    df_sales = query_df(query, params if params else None)

    if df_sales.empty:
        return {
            "success": False,
            "message": "No transaction records found in data warehouse.",
            "total_transactions": 0,
            "rules_count": 0,
            "itemsets_count": 0,
            "rules": [],
            "top_combinations": [],
            "summary": {}
        }

    # Count total distinct transactions
    total_transactions = df_sales['InvoiceNo'].nunique()
    if total_transactions < 2:
        return {
            "success": False,
            "message": "Insufficient transactions for association mining (at least 2 orders required).",
            "total_transactions": total_transactions,
            "rules_count": 0,
            "itemsets_count": 0,
            "rules": [],
            "top_combinations": [],
            "summary": {}
        }

    # Create Transaction Basket (One-hot encoded)
    # Pivot InvoiceNo x ProductName
    basket = (df_sales.groupby(['InvoiceNo', 'ProductName'])['Quantity']
              .sum()
              .unstack()
              .fillna(0))
    basket_encoded = basket.map(lambda x: True if x > 0 else False)

    # Ensure min_support is bounded
    min_sup = max(0.005, min(float(min_support), 0.9))
    min_conf = max(0.05, min(float(min_confidence), 1.0))

    try:
        # Run Apriori
        frequent_itemsets = apriori(basket_encoded, min_support=min_sup, use_colnames=True)
    except Exception as e:
        return {
            "success": False,
            "message": f"Apriori algorithm error: {str(e)}",
            "total_transactions": total_transactions,
            "rules_count": 0,
            "itemsets_count": 0,
            "rules": [],
            "top_combinations": [],
            "summary": {}
        }

    if frequent_itemsets.empty:
        return {
            "success": True,
            "message": f"No frequent itemsets found with minimum support {min_sup * 100:.1f}%. Try lowering min_support.",
            "total_transactions": total_transactions,
            "rules_count": 0,
            "itemsets_count": 0,
            "rules": [],
            "top_combinations": [],
            "summary": {
                "total_transactions": total_transactions,
                "min_support": min_sup,
                "min_confidence": min_conf,
                "frequent_itemsets_found": 0,
                "rules_generated": 0,
                "max_lift": 0.0
            }
        }

    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))

    # Top Combinations (itemsets of size >= 2)
    top_combos = []
    combos_df = frequent_itemsets[frequent_itemsets['length'] >= 2].sort_values(by='support', ascending=False).head(10)
    for _, row in combos_df.iterrows():
        items_list = list(row['itemsets'])
        top_combos.append({
            "items": items_list,
            "items_str": " + ".join(items_list),
            "support": round(float(row['support']), 4),
            "support_pct": round(float(row['support']) * 100, 2),
            "transaction_count": int(round(float(row['support']) * total_transactions))
        })

    # Generate Association Rules
    rules_list = []
    max_lift = 0.0

    try:
        rules_df = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_conf)
        
        if not rules_df.empty:
            # Sort rules
            valid_sort = sort_by if sort_by in ['lift', 'confidence', 'support'] else 'lift'
            rules_df = rules_df.sort_values(by=valid_sort, ascending=False)
            max_lift = round(float(rules_df['lift'].max()), 2)

            for idx, r in rules_df.iterrows():
                antecedents = list(r['antecedents'])
                consequents = list(r['consequents'])
                ant_str = ", ".join(antecedents)
                con_str = ", ".join(consequents)
                sup = round(float(r['support']), 4)
                conf = round(float(r['confidence']), 4)
                lift = round(float(r['lift']), 2)

                # Generate plain English explanation
                if lift > 1.2:
                    lift_desc = f"{lift}x more likely"
                elif lift >= 0.9:
                    lift_desc = "equally as likely"
                else:
                    lift_desc = f"less likely (lift {lift})"

                explanation = (
                    f"Shoppers buying '{ant_str}' are {lift_desc} to also purchase '{con_str}' "
                    f"({conf * 100:.1f}% confidence across {sup * 100:.1f}% of all transactions)."
                )

                rules_list.append({
                    "id": idx + 1,
                    "antecedents": antecedents,
                    "antecedents_str": ant_str,
                    "consequents": consequents,
                    "consequents_str": con_str,
                    "support": sup,
                    "support_pct": round(sup * 100, 2),
                    "confidence": conf,
                    "confidence_pct": round(conf * 100, 2),
                    "lift": lift,
                    "explanation": explanation
                })
    except Exception:
        rules_list = []

    return {
        "success": True,
        "message": f"Successfully mined {len(rules_list)} association rules and {len(frequent_itemsets)} frequent itemsets.",
        "total_transactions": total_transactions,
        "rules_count": len(rules_list),
        "itemsets_count": len(frequent_itemsets),
        "rules": rules_list[:50],  # Return top 50 rules
        "top_combinations": top_combos,
        "summary": {
            "total_transactions": total_transactions,
            "min_support": min_sup,
            "min_confidence": min_conf,
            "frequent_itemsets_found": len(frequent_itemsets),
            "rules_generated": len(rules_list),
            "max_lift": max_lift
        }
    }
