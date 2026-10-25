
USE international_debt_analysis;

-- 1. Overall database summary
SELECT
    COUNT(*) AS total_observations,
    COUNT(DISTINCT country_code) AS total_countries,
    COUNT(DISTINCT indicator_code) AS total_indicators,
    MIN(year) AS first_year,
    MAX(year) AS latest_year
FROM debt_observations;

-- 2. Latest available year in the dataset
SELECT MAX(year) AS latest_year
FROM debt_observations;

-- 3. Observation counts by year
SELECT
    year,
    COUNT(*) AS observation_count
FROM debt_observations
GROUP BY year
ORDER BY year;

-- 4. Top 10 countries by total recorded debt value
SELECT
    c.country_name,
    SUM(o.debt_value) AS total_debt_value
FROM debt_observations o
JOIN countries c
    ON o.country_code = c.country_code
JOIN debt_indicators d
    ON o.indicator_code = d.indicator_code
WHERE o.debt_value IS NOT NULL
  AND d.indicator_name LIKE 'External debt stocks%'
  AND d.indicator_name NOT LIKE '%change%'
GROUP BY c.country_code, c.country_name
ORDER BY total_debt_value DESC
LIMIT 10;

-- 5. Top 10 indicators by observation count
SELECT
    d.indicator_name,
    COUNT(*) AS observation_count
FROM debt_observations o
JOIN debt_indicators d
    ON o.indicator_code = d.indicator_code
GROUP BY d.indicator_code, d.indicator_name
ORDER BY observation_count DESC
LIMIT 10;

-- 6. Average recorded debt value by year
SELECT
    year,
    ROUND(AVG(debt_value), 2) AS average_debt_value
FROM debt_observations
WHERE debt_value IS NOT NULL
GROUP BY year
ORDER BY year;

-- 7. Missing debt values by year
SELECT
    year,
    COUNT(*) AS total_rows,
    SUM(debt_value IS NULL) AS missing_debt_values
FROM debt_observations
GROUP BY year
ORDER BY year;

-- 8. Latest observations for review
SELECT
    c.country_name,
    d.indicator_name,
    o.year,
    o.debt_value
FROM debt_observations o
JOIN countries c
    ON o.country_code = c.country_code
JOIN debt_indicators d
    ON o.indicator_code = d.indicator_code
ORDER BY o.year DESC
LIMIT 20;
-- 9. Retrieve all distinct country names
SELECT DISTINCT country_name
FROM countries
ORDER BY country_name;

-- 10. Count total countries
SELECT COUNT(*) AS total_countries
FROM countries;

-- 11. Count total indicators
SELECT COUNT(*) AS total_indicators
FROM debt_indicators;

-- 12. Display first 10 records
SELECT *
FROM debt_observations
LIMIT 10;

-- 13. Calculate total global debt
SELECT SUM(debt_value) AS total_global_debt
FROM debt_observations;

-- 14. List unique indicator names
SELECT DISTINCT indicator_name
FROM debt_indicators
ORDER BY indicator_name;

-- 15. Number of records for each country
SELECT c.country_name, COUNT(*) AS record_count
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
ORDER BY record_count DESC;

-- 16. Records where debt value exceeds 1 billion
SELECT *
FROM debt_observations
WHERE debt_value > 1000000000;

-- 17. Minimum, maximum and average debt values
SELECT MIN(debt_value) AS minimum_debt,
       MAX(debt_value) AS maximum_debt,
       AVG(debt_value) AS average_debt
FROM debt_observations;

-- 18. Total records
SELECT COUNT(*) AS total_records
FROM debt_observations;

-- 19. Total debt value for each country
SELECT c.country_name, SUM(o.debt_value) AS total_debt
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
ORDER BY total_debt DESC;

-- 20. Top 10 countries by total recorded value
SELECT c.country_name, SUM(o.debt_value) AS total_debt
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
WHERE o.debt_value IS NOT NULL
GROUP BY c.country_code, c.country_name
ORDER BY total_debt DESC
LIMIT 10;

-- 21. Average debt value per country
SELECT c.country_name, AVG(o.debt_value) AS average_debt
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
ORDER BY average_debt DESC;

-- 22. Total debt value for each indicator
SELECT d.indicator_name, SUM(o.debt_value) AS total_debt
FROM debt_observations o
JOIN debt_indicators d ON o.indicator_code = d.indicator_code
GROUP BY d.indicator_code, d.indicator_name
ORDER BY total_debt DESC;

-- 23. Indicator with the highest total recorded value
SELECT d.indicator_name, SUM(o.debt_value) AS total_value
FROM debt_observations o
JOIN debt_indicators d ON o.indicator_code = d.indicator_code
GROUP BY d.indicator_code, d.indicator_name
ORDER BY total_value DESC
LIMIT 1;

-- 24. Country with the lowest total recorded value
SELECT c.country_name, SUM(o.debt_value) AS total_value
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
ORDER BY total_value ASC
LIMIT 1;

-- 25. Total value by country and indicator
SELECT c.country_name, d.indicator_name,
       SUM(o.debt_value) AS total_value
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
JOIN debt_indicators d ON o.indicator_code = d.indicator_code
GROUP BY c.country_code, c.country_name,
         d.indicator_code, d.indicator_name
ORDER BY total_value DESC;

-- 26. Number of indicators for each country
SELECT c.country_name,
       COUNT(DISTINCT o.indicator_code) AS indicator_count
FROM countries c
JOIN debt_observations o ON c.country_code = o.country_code
GROUP BY c.country_code, c.country_name
ORDER BY indicator_count DESC;

-- 27. Countries above the global average observation value
SELECT c.country_name, AVG(o.debt_value) AS average_value
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
HAVING AVG(o.debt_value) > (
    SELECT AVG(debt_value)
    FROM debt_observations
);

-- 28. Rank countries by total recorded value
SELECT country_name, total_value,
       RANK() OVER (ORDER BY total_value DESC) AS debt_rank
FROM (
    SELECT c.country_name, SUM(o.debt_value) AS total_value
    FROM debt_observations o
    JOIN countries c ON o.country_code = c.country_code
    GROUP BY c.country_code, c.country_name
) AS country_totals;

-- 29. Top 5 indicators by total recorded value
SELECT d.indicator_name, SUM(o.debt_value) AS total_value
FROM debt_observations o
JOIN debt_indicators d ON o.indicator_code = d.indicator_code
GROUP BY d.indicator_code, d.indicator_name
ORDER BY total_value DESC
LIMIT 5;

-- 30. Percentage contribution by country to total recorded value
SELECT c.country_name,
       SUM(o.debt_value) AS country_total,
       ROUND(
           100.0 * SUM(o.debt_value) /
           NULLIF((SELECT SUM(debt_value)
                   FROM debt_observations), 0),
           2
       ) AS percentage_contribution
FROM debt_observations o
JOIN countries c ON o.country_code = c.country_code
GROUP BY c.country_code, c.country_name
ORDER BY percentage_contribution DESC;