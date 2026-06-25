
SELECT f.fund_name, f.fund_house, a.aum
FROM fact_aum a
JOIN dim_fund f ON a.amfi_code = f.amfi_code
ORDER BY a.aum DESC
LIMIT 5;


SELECT strftime('%Y-%m', date) AS month, ROUND(AVG(nav), 4) AS avg_nav
FROM fact_nav
WHERE amfi_code = 125497
GROUP BY month
ORDER BY month;


SELECT strftime('%Y', date) AS transaction_year, SUM(amount) AS total_sip_amount,
       COUNT(transaction_id) AS total_sip_count
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY transaction_year
ORDER BY transaction_year;


SELECT state, COUNT(transaction_id) AS transaction_count, SUM(amount) AS total_investment
FROM fact_transactions
GROUP BY state
ORDER BY total_investment DESC;


SELECT f.fund_name, p.expense_ratio, p.return_3y
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio < 1.0 AND p.anomaly_flag = 0
ORDER BY p.return_3y DESC;


SELECT 
    SUM(CASE WHEN transaction_type IN ('SIP', 'LUMPSUM') THEN amount ELSE 0 END) - 
    SUM(CASE WHEN transaction_type = 'REDEMPTION' THEN amount ELSE 0 END) AS net_inflow_inr
FROM fact_transactions;


SELECT f.fund_house, f.category, ROUND(AVG(p.return_5y), 2) AS mean_5y_return
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
GROUP BY f.fund_house, f.category
ORDER BY mean_5y_return DESC;

SELECT kyc_status, COUNT(*) AS total_records, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_transactions), 2) AS percentage_contribution
FROM fact_transactions
GROUP BY kyc_status;

SELECT f.fund_name, MAX(n.nav) AS peak_nav, MIN(n.nav) AS floor_nav,
       (MAX(n.nav) - MIN(n.nav)) AS total_spread
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code
ORDER BY total_spread DESC
LIMIT 10;

SELECT f.fund_name, p.return_1y, p.return_3y, p.return_5y
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.anomaly_flag = 1;