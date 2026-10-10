# ML Training Guide & Dataset Instructions

Welcome! This guide details the structure of the training data and how to use it for your Machine Learning models. 

## 📂 Dataset Location
All necessary training data has been automatically generated, merged with real-world public data, and forcefully pushed to this repository.
You can find all **10 CSV files** ready for ingestion in the following directory:
`Code/data/raw/`

## 📊 Dataset Overview (Hybrid Data)
We are using a **Hybrid Dataset**. We took real, high-variance public datasets (London Smart Meter energy data and UCI Online Retail transactions) and joined them using a unified `customer_id` format (`CUST-0001` to `CUST-5000`). 
For the tables that didn't exist in the public datasets (e.g., Vehicles, Digital Usage, Green Products), we used our existing synthetic data generator to accurately fill in the gaps.

You have the following 8 core feature tables available for training:
1. `customers.csv`: Demographics, age, income, and latent variables.
2. `transactions.csv`: Individual transactional events mapped from the UCI Retail dataset.
3. `energy_usage.csv`: Monthly energy (electricity and synthetic gas) derived from the LCL Smart Meter dataset.
4. `digital_usage.csv`: App logins, website visits, and digital engagement metrics.
5. `vehicles.csv`: Customer vehicle profiles (EV vs. ICE, mileage).
6. `products.csv`: Current traditional banking products held by the customer.
7. `green_products.csv`: Current green products held.
8. `emissions_factors.csv`: Global emissions factors for carbon calculations.

## 🎯 Target Labels (What you are predicting)
For supervised learning, the "ground truth" target variables have already been generated based on the personas and transactions. They are located in:

* **`take_up_labels.csv`**: Use this to train your **Green Product Recommendation Model**. It contains a boolean flag (`took_up_green_product`) indicating if a customer is likely to purchase a green product.
* **`transaction_labels.csv`**: Use this to train your **Transaction Categoriser**. It maps each `transaction_id` (from the UCI Retail set) to a specific spending category (e.g., "Other", "Groceries", "Transport").

## 🚀 Steps to Start Training
1. **Pull the latest changes:** 
   Ensure you are on the `main` branch and have the latest hybrid datasets.
   ```bash
   git pull origin main
   ```
2. **Load the data into your ML script:**
   You can load the files using pandas. Make sure to use `customer_id` to join demographic, vehicle, and energy data, and `transaction_id` to join transaction data with its labels.
   ```python
   import pandas as pd
   
   # Example: Loading customer demographics and their green product targets
   customers_df = pd.read_csv("Code/data/raw/customers.csv")
   labels_df = pd.read_csv("Code/data/raw/take_up_labels.csv")
   
   # Merge on customer_id
   train_df = pd.merge(customers_df, labels_df, on="customer_id")
   ```

3. **Validation:** 
   Please use the `Code/gold_set.csv` file to perform a final, blind evaluation of your Transaction Categoriser to ensure its accuracy before we finalize the submission!

Happy training! If you need any of the schemas modified, just let the team know.
