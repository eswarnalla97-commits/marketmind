import os
import random
import datetime
import pandas as pd

def generate_sample_data(output_path="d:/marketmind/data/sample_transactions.csv"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    random.seed(42)

    # Realistic catalog with Indian Rupee (INR - ₹) pricing
    categories_and_products = {
        "Electronics & Gadgets": [
            ("E101", "Mechanical Gaming Keyboard", 2999.00),
            ("E102", "Wireless Ergonomic Mouse", 1499.00),
            ("E103", "USB-C 7-in-1 Multiport Hub", 1899.00),
            ("E104", "Active Noise-Cancelling Headphones", 5999.00),
            ("E105", "1080p Full-HD Streaming Webcam", 2499.00),
            ("E106", "Aluminum Ergonomic Laptop Stand", 1299.00),
            ("E107", "Fast Wireless Charging Pad 15W", 899.00),
            ("E108", "Portable High-Speed SSD 1TB", 6499.00)
        ],
        "Home & Kitchen": [
            ("H201", "Traditional Brass Filter Coffee Maker", 850.00),
            ("H202", "Stainless Steel Reusable Coffee Mesh", 399.00),
            ("H203", "Ceramic Artisan Chai & Coffee Cups (Set of 6)", 749.00),
            ("H204", "Electric Rapid Boil Kettle 1.5L", 1699.00),
            ("H205", "Digital Kitchen Food & Spice Scale", 699.00),
            ("H206", "Silicone Baking & Roti Mat", 449.00)
        ],
        "Fitness & Wellness": [
            ("F301", "Eco Ayurvedic Cork Yoga Mat", 1599.00),
            ("F302", "Fabric Resistance Loop Bands (Set of 3)", 599.00),
            ("F303", "Insulated Stainless Steel Bottle 1L", 899.00),
            ("F304", "High-Density Muscle Foam Roller", 799.00),
            ("F305", "Speed Skipping Jump Rope", 349.00)
        ],
        "Apparel & Fashion": [
            ("A401", "Pure Organic Cotton T-Shirt", 799.00),
            ("A402", "Winter Fleece Zip-Up Hoodie", 1999.00),
            ("A403", "Waterproof Urban Laptop Backpack", 2299.00),
            ("A404", "Genuine RFID Leather Wallet", 1199.00),
            ("A405", "Breathable Bamboo Socks (Pack of 3)", 449.00)
        ],
        "Office & Stationery": [
            ("O501", "Hardcover Ruled Journal Notebook", 499.00),
            ("O502", "Precision Rollerball Gel Pens (Set of 10)", 299.00),
            ("O503", "Extended Vegan Leather Desk Blotter", 999.00),
            ("O504", "Ergonomic Memory Foam Wrist Rest", 599.00)
        ]
    }

    # Frequent bundles in Indian retail
    frequent_pairs = [
        (("H201", "Traditional Brass Filter Coffee Maker", 850.00, "Home & Kitchen"), 
         ("H202", "Stainless Steel Reusable Coffee Mesh", 399.00, "Home & Kitchen")),
        (("H201", "Traditional Brass Filter Coffee Maker", 850.00, "Home & Kitchen"), 
         ("H203", "Ceramic Artisan Chai & Coffee Cups (Set of 6)", 749.00, "Home & Kitchen")),
        (("E101", "Mechanical Gaming Keyboard", 2999.00, "Electronics & Gadgets"), 
         ("E102", "Wireless Ergonomic Mouse", 1499.00, "Electronics & Gadgets")),
        (("E101", "Mechanical Gaming Keyboard", 2999.00, "Electronics & Gadgets"), 
         ("E106", "Aluminum Ergonomic Laptop Stand", 1299.00, "Electronics & Gadgets")),
        (("F301", "Eco Ayurvedic Cork Yoga Mat", 1599.00, "Fitness & Wellness"), 
         ("F302", "Fabric Resistance Loop Bands (Set of 3)", 599.00, "Fitness & Wellness")),
        (("F301", "Eco Ayurvedic Cork Yoga Mat", 1599.00, "Fitness & Wellness"), 
         ("F303", "Insulated Stainless Steel Bottle 1L", 899.00, "Fitness & Wellness")),
        (("O501", "Hardcover Ruled Journal Notebook", 499.00, "Office & Stationery"), 
         ("O502", "Precision Rollerball Gel Pens (Set of 10)", 299.00, "Office & Stationery")),
        (("A401", "Pure Organic Cotton T-Shirt", 799.00, "Apparel & Fashion"), 
         ("A402", "Winter Fleece Zip-Up Hoodie", 1999.00, "Apparel & Fashion"))
    ]

    # Major Indian States & Union Territories
    indian_regions = [
        "Maharashtra", "Karnataka", "Delhi NCR", "Tamil Nadu", 
        "Telangana", "Gujarat", "Uttar Pradesh", "West Bengal", 
        "Kerala", "Rajasthan"
    ]
    region_weights = [0.22, 0.18, 0.15, 0.12, 0.10, 0.08, 0.06, 0.04, 0.03, 0.02]

    # 160 customer profiles across Indian states
    customers = []
    for c_id in range(1001, 1161):
        c_state = random.choices(indian_regions, weights=region_weights)[0]
        tier = random.choices(["vip", "loyal", "regular", "churned", "new"], weights=[0.10, 0.25, 0.35, 0.15, 0.15])[0]
        customers.append({
            "id": f"IND-CUST-{c_id}",
            "country": c_state,  # Using State as the geographic dimension for Indian retail
            "tier": tier
        })

    start_date = datetime.date(2024, 1, 1)
    rows = []
    invoice_counter = 70000

    for cust in customers:
        tier = cust["tier"]
        if tier == "vip":
            order_counts = random.randint(7, 12)
            date_range = (1, 360)
        elif tier == "loyal":
            order_counts = random.randint(4, 7)
            date_range = (1, 355)
        elif tier == "regular":
            order_counts = random.randint(2, 4)
            date_range = (30, 340)
        elif tier == "churned":
            order_counts = random.randint(2, 4)
            date_range = (1, 120)
        else: # new
            order_counts = 1
            date_range = (280, 365)

        for _ in range(order_counts):
            invoice_counter += 1
            inv_no = f"INV-IN-{invoice_counter}"
            day_offset = random.randint(date_range[0], date_range[1])
            order_date = start_date + datetime.timedelta(days=day_offset)
            date_str = order_date.strftime("%Y-%m-%d")

            basket_items = []
            # Probability of co-purchased retail bundle
            if random.random() < 0.55:
                pair = random.choice(frequent_pairs)
                item_a, item_b = pair
                qty_a = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
                qty_b = random.choices([1, 2], weights=[0.85, 0.15])[0]
                basket_items.append((item_a[0], item_a[1], item_a[3], qty_a, item_a[2]))
                basket_items.append((item_b[0], item_b[1], item_b[3], qty_b, item_b[2]))

            extra_items_count = random.choices([0, 1, 2], weights=[0.5, 0.35, 0.15])[0]
            existing_pids = {item[0] for item in basket_items}

            all_cat_keys = list(categories_and_products.keys())
            for _ in range(extra_items_count):
                cat = random.choice(all_cat_keys)
                p_tuple = random.choice(categories_and_products[cat])
                if p_tuple[0] not in existing_pids:
                    qty = random.choices([1, 2, 3, 4], weights=[0.75, 0.18, 0.05, 0.02])[0]
                    basket_items.append((p_tuple[0], p_tuple[1], cat, qty, p_tuple[2]))
                    existing_pids.add(p_tuple[0])

            if not basket_items:
                cat = random.choice(all_cat_keys)
                p_tuple = random.choice(categories_and_products[cat])
                qty = random.choices([1, 2], weights=[0.85, 0.15])[0]
                basket_items.append((p_tuple[0], p_tuple[1], cat, qty, p_tuple[2]))

            for pid, pname, cat, qty, price in basket_items:
                rows.append({
                    "InvoiceNo": inv_no,
                    "InvoiceDate": date_str,
                    "CustomerID": cust["id"],
                    "ProductID": pid,
                    "ProductName": pname,
                    "Category": cat,
                    "Quantity": qty,
                    "UnitPrice": price,
                    "Country": cust["country"]
                })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} transactions in Indian Currency (INR) at {output_path}")

    # Indian Standard CSV Template
    template_path = "d:/marketmind/data/sample_template.csv"
    template_df = pd.DataFrame([
        {
            "InvoiceNo": "INV-IN-80001",
            "InvoiceDate": "2024-06-15",
            "CustomerID": "IND-CUST-2001",
            "ProductID": "E101",
            "ProductName": "Mechanical Gaming Keyboard",
            "Category": "Electronics & Gadgets",
            "Quantity": 1,
            "UnitPrice": 2999.00,
            "Country": "Maharashtra"
        },
        {
            "InvoiceNo": "INV-IN-80001",
            "InvoiceDate": "2024-06-15",
            "CustomerID": "IND-CUST-2001",
            "ProductID": "E102",
            "ProductName": "Wireless Ergonomic Mouse",
            "Category": "Electronics & Gadgets",
            "Quantity": 1,
            "UnitPrice": 1499.00,
            "Country": "Maharashtra"
        },
        {
            "InvoiceNo": "INV-IN-80002",
            "InvoiceDate": "2024-06-16",
            "CustomerID": "IND-CUST-2002",
            "ProductID": "H201",
            "ProductName": "Traditional Brass Filter Coffee Maker",
            "Category": "Home & Kitchen",
            "Quantity": 1,
            "UnitPrice": 850.00,
            "Country": "Karnataka"
        },
        {
            "InvoiceNo": "INV-IN-80002",
            "InvoiceDate": "2024-06-16",
            "CustomerID": "IND-CUST-2002",
            "ProductID": "H202",
            "ProductName": "Stainless Steel Reusable Coffee Mesh",
            "Category": "Home & Kitchen",
            "Quantity": 2,
            "UnitPrice": 399.00,
            "Country": "Karnataka"
        },
        {
            "InvoiceNo": "INV-IN-80003",
            "InvoiceDate": "2024-06-17",
            "CustomerID": "IND-CUST-2003",
            "ProductID": "F301",
            "ProductName": "Eco Ayurvedic Cork Yoga Mat",
            "Category": "Fitness & Wellness",
            "Quantity": 1,
            "UnitPrice": 1599.00,
            "Country": "Delhi NCR"
        }
    ])
    template_df.to_csv(template_path, index=False)
    print(f"Generated Indian standard template CSV at {template_path}")

if __name__ == "__main__":
    generate_sample_data()
