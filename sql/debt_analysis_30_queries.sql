USE international_debt_analysis;

/*
International Debt Analysis - 30 assignment queries
Requires MySQL 8.0+ for window functions and CTEs.

IMPORTANT DATA NOTE:
The observations table contains many different indicators and years. These can
represent different measures (stocks, disbursements, repayments, interest, etc.).
Summing all indicators and all years together is only a sum of recorded values,
not a valid economic measure of “global debt”. For meaningful debt-stock analysis,
filter to a single debt-stock indicator and a single year. Comments are included
where the assignment's requested total can be misleading.
*/

-- ==============================
-- BASIC QUERIES (1-10)
-- ==============================

-- 1. Retrieve all distinct country names from the dataset.
SELECT DISTINCT country_name
FROM countries
ORDER BY country_name;

-- 2. Count the total number of countries available in the observations.
SELECT COUNT(DISTINCT country_code) AS total_countries
FROM debt_observations;

-- 3. Find the total number of indicators present in the observations.
SELECT COUNT(DISTINCT indicator_code) AS total_indicators
FROM debt_observations;

-- 4. Display the first 10 records of the dataset.
SELECT country_code, indicator_code, year, debt_value
FROM debt_observations
ORDER BY country_code, indicator_code, year
LIMIT 10;

-- 5. Calculate total global debt.
-- Assignment-style total: sum of every recorded value. Since indicators/years
-- may measure different things, use one debt-stock indicator and one year for
-- an economically interpretable global debt total instead (example below).
SELECT SUM(debt_value) AS sum_of_all_recorded_values_not_comparable_debt
FROM debt_observations
WHERE debt_value IS NOT NULL;

-- Recommended interpretable version: global total for one indicator and year.
-- Replace the indicator code/year with the intended debt-stock measure and year.
-- SELECT year, SUM(debt_value) AS global_debt_stock
-- FROM debt_observations
-- WHERE indicator_code = 'DT.DOD.DECT.CD' AND year = 2024
-- GROUP BY year;

-- 6. List all unique indicator names.
SELECT DISTINCT indicator_name
FROM debt_indicators
ORDER BY indicator_name;

-- 7. Find the number of records for each country.
SELECT c.country_name, COUNT(*) AS record_count
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
GROUP BY c.country_code, c.country_name
ORDER BY record_count DESC;

-- 8. Display records where debt value is greater than 1 billion USD.
SELECT country_code, indicator_code, year, debt_value
FROM debt_observations
WHERE debt_value > 1000000000
ORDER BY debt_value DESC;

-- 9. Find minimum, maximum, and average recorded debt value.
SELECT MIN(debt_value) AS minimum_value,
       MAX(debt_value) AS maximum_value,
       AVG(debt_value) AS average_value
FROM debt_observations
WHERE debt_value IS NOT NULL;

-- 10. Count total records in the dataset.
SELECT COUNT(*) AS total_records
FROM debt_observations;

-- ==============================
-- INTERMEDIATE QUERIES (11-20)
-- ==============================

-- 11. Find the total recorded value for each country.
-- This is a raw aggregation across indicators and years, not a debt-stock total.
SELECT c.country_name, SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY total_recorded_value DESC;

-- 12. Display the top 10 countries with the highest total recorded value.
SELECT c.country_name, SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY total_recorded_value DESC
LIMIT 10;

-- 13. Find the average recorded value per country.
SELECT c.country_name, AVG(o.debt_value) AS average_recorded_value
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY average_recorded_value DESC;

-- 14. Calculate total recorded value for each indicator.
SELECT d.indicator_code, d.indicator_name,
       SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN debt_indicators d ON d.indicator_code = o.indicator_code
WHERE o.debt_value IS NOT NULL
GROUP BY d.indicator_code, d.indicator_name
ORDER BY total_recorded_value DESC;

-- 15. Identify the indicator with the highest total recorded value.
SELECT d.indicator_code, d.indicator_name,
       SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN debt_indicators d ON d.indicator_code = o.indicator_code
WHERE o.debt_value IS NOT NULL
GROUP BY d.indicator_code, d.indicator_name
ORDER BY total_recorded_value DESC
LIMIT 1;

-- 16. Find the country with the lowest total recorded value.
SELECT c.country_name, SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY total_recorded_value ASC
LIMIT 1;

-- 17. Calculate total value for each country and indicator combination.
SELECT c.country_name, d.indicator_name,
       SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
JOIN debt_indicators d ON d.indicator_code = o.indicator_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name, d.indicator_code, d.indicator_name
ORDER BY total_recorded_value DESC;

-- 18. Count how many distinct indicators each country has.
SELECT c.country_name,
       COUNT(DISTINCT o.indicator_code) AS indicator_count
FROM countries c
JOIN debt_observations o ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
ORDER BY indicator_count DESC;

-- 19. Countries whose total recorded value is above the average country total.
WITH country_totals AS (
    SELECT country_code, SUM(debt_value) AS total_value
    FROM debt_observations
    WHERE debt_value IS NOT NULL
    GROUP BY country_code
)
SELECT c.country_name, ct.total_value
FROM country_totals ct
JOIN countries c ON c.country_code = ct.country_code
WHERE ct.total_value > (SELECT AVG(total_value) FROM country_totals)
ORDER BY ct.total_value DESC;

-- 20. Rank countries based on total recorded value (highest to lowest).
WITH country_totals AS (
    SELECT country_code, SUM(debt_value) AS total_value
    FROM debt_observations
    WHERE debt_value IS NOT NULL
    GROUP BY country_code
)
SELECT c.country_name, ct.total_value,
       RANK() OVER (ORDER BY ct.total_value DESC) AS country_rank
FROM country_totals ct
JOIN countries c ON c.country_code = ct.country_code
ORDER BY country_rank, c.country_name;

-- ==============================
-- ADVANCED QUERIES (21-30)
-- ==============================

-- 21. Find the top 5 indicators contributing most by total recorded value.
SELECT d.indicator_code, d.indicator_name,
       SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN debt_indicators d ON d.indicator_code = o.indicator_code
WHERE o.debt_value IS NOT NULL
GROUP BY d.indicator_code, d.indicator_name
ORDER BY total_recorded_value DESC
LIMIT 5;

-- 22. Calculate each country's percentage contribution to all recorded values.
-- This is an assignment-style calculation; values across indicators/years may
-- not be economically comparable, so interpret it with caution.
WITH country_totals AS (
    SELECT country_code, SUM(debt_value) AS country_total
    FROM debt_observations
    WHERE debt_value IS NOT NULL
    GROUP BY country_code
), all_total AS (
    SELECT SUM(debt_value) AS grand_total
    FROM debt_observations
    WHERE debt_value IS NOT NULL
)
SELECT c.country_name, ct.country_total,
       ROUND(100.0 * ct.country_total / NULLIF(at.grand_total, 0), 2)
           AS percentage_contribution
FROM country_totals ct
JOIN countries c ON c.country_code = ct.country_code
CROSS JOIN all_total at
ORDER BY percentage_contribution DESC;

-- 23. Identify the top 3 countries for each indicator by total recorded value.
WITH country_indicator_totals AS (
    SELECT o.country_code, o.indicator_code,
           SUM(o.debt_value) AS total_value
    FROM debt_observations o
    WHERE o.debt_value IS NOT NULL
    GROUP BY o.country_code, o.indicator_code
), ranked AS (
    SELECT cit.country_code, c.country_name,
           cit.indicator_code, d.indicator_name, cit.total_value,
           ROW_NUMBER() OVER (
               PARTITION BY cit.indicator_code
               ORDER BY cit.total_value DESC
           ) AS indicator_country_rank
    FROM country_indicator_totals cit
    JOIN countries c ON c.country_code = cit.country_code
    JOIN debt_indicators d ON d.indicator_code = cit.indicator_code
)
SELECT indicator_name, country_name, total_value, indicator_country_rank
FROM ranked
WHERE indicator_country_rank <= 3
ORDER BY indicator_name, indicator_country_rank;

-- 24. Difference between maximum and minimum recorded value for each country.
SELECT c.country_name,
       MAX(o.debt_value) AS maximum_value,
       MIN(o.debt_value) AS minimum_value,
       MAX(o.debt_value) - MIN(o.debt_value) AS max_min_difference
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY max_min_difference DESC;

-- 25. Create a view for the top 10 countries by total recorded value.
-- The aggregation across all indicators/years is assignment-style, not a
-- comparable economic debt-stock measure.
CREATE OR REPLACE VIEW top_10_countries_by_recorded_value AS
SELECT c.country_code, c.country_name,
       SUM(o.debt_value) AS total_recorded_value
FROM debt_observations o
JOIN countries c ON c.country_code = o.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY total_recorded_value DESC
LIMIT 10;

-- Display the view.
SELECT *
FROM top_10_countries_by_recorded_value
ORDER BY total_recorded_value DESC;

-- 26. Categorize countries into High, Medium, and Low Debt.
-- Example thresholds are in USD and should be adapted to a single debt-stock
-- indicator/year for a meaningful debt classification.
WITH country_debt AS (
    SELECT o.country_code, SUM(o.debt_value) AS total_value
    FROM debt_observations o
    WHERE o.debt_value IS NOT NULL
      AND o.indicator_code = 'DT.DOD.DECT.CD'
      AND o.year = (SELECT MAX(year) FROM debt_observations
                    WHERE indicator_code = 'DT.DOD.DECT.CD')
    GROUP BY o.country_code
)
SELECT c.country_name, cd.total_value,
       CASE
           WHEN cd.total_value >= 100000000000 THEN 'High Debt'
           WHEN cd.total_value >= 10000000000 THEN 'Medium Debt'
           ELSE 'Low Debt'
       END AS debt_category
FROM country_debt cd
JOIN countries c ON c.country_code = cd.country_code
ORDER BY cd.total_value DESC;

-- 27. Calculate cumulative recorded value per country using a window function.
-- Values are aggregated by year first, then cumulatively summed.
WITH country_year_totals AS (
    SELECT country_code, year, SUM(debt_value) AS yearly_total
    FROM debt_observations
    WHERE debt_value IS NOT NULL
    GROUP BY country_code, year
)
SELECT c.country_name, cyt.year, cyt.yearly_total,
       SUM(cyt.yearly_total) OVER (
           PARTITION BY cyt.country_code
           ORDER BY cyt.year
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS cumulative_recorded_value
FROM country_year_totals cyt
JOIN countries c ON c.country_code = cyt.country_code
ORDER BY c.country_name, cyt.year;

-- 28. Find indicators whose average is higher than the overall observation average.
SELECT d.indicator_code, d.indicator_name,
       AVG(o.debt_value) AS indicator_average
FROM debt_observations o
JOIN debt_indicators d ON d.indicator_code = o.indicator_code
WHERE o.debt_value IS NOT NULL
GROUP BY d.indicator_code, d.indicator_name
HAVING AVG(o.debt_value) > (
    SELECT AVG(debt_value)
    FROM debt_observations
    WHERE debt_value IS NOT NULL
)
ORDER BY indicator_average DESC;

-- 29. Identify countries contributing more than 5% of all recorded values.
-- This is an assignment-style metric and is not an economically comparable
-- debt share unless restricted to one indicator and one year.
WITH country_totals AS (
    SELECT country_code, SUM(debt_value) AS country_total
    FROM debt_observations
    WHERE debt_value IS NOT NULL
    GROUP BY country_code
), grand_total AS (
    SELECT SUM(debt_value) AS total_value
    FROM debt_observations
    WHERE debt_value IS NOT NULL
)
SELECT c.country_name, ct.country_total,
       ROUND(100.0 * ct.country_total / NULLIF(gt.total_value, 0), 2)
           AS percentage_contribution
FROM country_totals ct
JOIN countries c ON c.country_code = ct.country_code
CROSS JOIN grand_total gt
WHERE 100.0 * ct.country_total / NULLIF(gt.total_value, 0) > 5
ORDER BY percentage_contribution DESC;

-- 30. Find the most dominant indicator for each country by total recorded value.
WITH country_indicator_totals AS (
    SELECT country_code, indicator_code, SUM(debt_value) AS total_value
    FROM debt_observations
    WHERE debt_value IS NOT NULL
    GROUP BY country_code, indicator_code
), ranked_indicators AS (
    SELECT cit.country_code, cit.indicator_code, cit.total_value,
           ROW_NUMBER() OVER (
               PARTITION BY cit.country_code
               ORDER BY cit.total_value DESC
           ) AS indicator_rank
    FROM country_indicator_totals cit
)
SELECT c.country_name, d.indicator_name, ri.total_value
FROM ranked_indicators ri
JOIN countries c ON c.country_code = ri.country_code
JOIN debt_indicators d ON d.indicator_code = ri.indicator_code
WHERE ri.indicator_rank = 1
ORDER BY c.country_name;
