# DAX Measures cho Dashboard PowerBI

Tài liệu này tách riêng toàn bộ DAX measures dùng cho file PowerBI 5 màn hình của bài Data Explorers 2026.

## Nguyên tắc chung

- `fact_sales` là fact table trung tâm.
- Nên tạo `Date` table riêng và nối `Date[Date] -> fact_sales[order_date]`.
- Không gọi T1/2026 so với T3/2025 là MoM.
- Tách rõ `Calendar MoM %` và `Previous Available Growth %`.

## 1. Basic KPI

```dax
Total Revenue = SUM(fact_sales[line_total])

Total Quantity = SUM(fact_sales[quantity])

Total Orders = DISTINCTCOUNT(fact_sales[so_number])

Active Dealers = DISTINCTCOUNT(fact_sales[customer_code])

Avg Revenue per Order = DIVIDE([Total Revenue], [Total Orders])

Avg Revenue per Dealer = DIVIDE([Total Revenue], [Active Dealers])
```

## 2. Calendar MoM

```dax
Revenue Calendar MoM % =
VAR cur = [Total Revenue]
VAR prev =
    CALCULATE(
        [Total Revenue],
        DATEADD('Date'[Date], -1, MONTH)
    )
RETURN
DIVIDE(cur - prev, prev)
```

Lưu ý:

- T1/2026 sẽ `BLANK()` vì thiếu T12/2025.
- Đây là hành vi đúng, không phải lỗi.

## 3. Previous Available Growth

```dax
Revenue Previous Available Period =
VAR curPeriod = MAX(fact_sales[fiscal_year]) * 12 + MAX(fact_sales[fiscal_month])
VAR prevPeriod =
    MAXX(
        FILTER(
            ALL(fact_sales[fiscal_year], fact_sales[fiscal_month]),
            fact_sales[fiscal_year] * 12 + fact_sales[fiscal_month] < curPeriod
        ),
        fact_sales[fiscal_year] * 12 + fact_sales[fiscal_month]
    )
RETURN
CALCULATE(
    [Total Revenue],
    FILTER(
        ALL(fact_sales),
        fact_sales[fiscal_year] * 12 + fact_sales[fiscal_month] = prevPeriod
    )
)
```

```dax
Revenue Previous Available Growth % =
VAR cur = [Total Revenue]
VAR prev = [Revenue Previous Available Period]
RETURN
DIVIDE(cur - prev, prev)
```

## 4. YoY

```dax
Revenue YoY % =
VAR curYear = MAX(fact_sales[fiscal_year])
VAR curMonth = MAX(fact_sales[fiscal_month])
VAR cur = [Total Revenue]
VAR prev =
    CALCULATE(
        [Total Revenue],
        REMOVEFILTERS(fact_sales[fiscal_year], fact_sales[fiscal_month]),
        fact_sales[fiscal_year] = curYear - 1,
        fact_sales[fiscal_month] = curMonth
    )
RETURN
DIVIDE(cur - prev, prev)
```

## 5. Q1 và T3

```dax
Revenue Q1 2025 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2025, fact_sales[fiscal_quarter] = 1)

Revenue Q1 2026 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2026, fact_sales[fiscal_quarter] = 1)

Growth Q1 YoY =
DIVIDE([Revenue Q1 2026] - [Revenue Q1 2025], [Revenue Q1 2025])

Revenue T3 2025 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2025, fact_sales[fiscal_month] = 3)

Revenue T3 2026 =
CALCULATE([Total Revenue], fact_sales[fiscal_year] = 2026, fact_sales[fiscal_month] = 3)

Growth T3 YoY =
DIVIDE([Revenue T3 2026] - [Revenue T3 2025], [Revenue T3 2025])
```

## 6. Pareto

```dax
Revenue Share Top 20pct =
VAR dealerTable =
    ADDCOLUMNS(
        ALLSELECTED(fact_sales[customer_code]),
        "DealerRevenue", [Total Revenue]
    )
VAR topNValue =
    ROUNDUP(COUNTROWS(dealerTable) * 0.2, 0)
VAR topDealers =
    TOPN(topNValue, dealerTable, [DealerRevenue], DESC)
VAR topRevenue =
    SUMX(topDealers, [DealerRevenue])
RETURN
DIVIDE(topRevenue, [Total Revenue])
```

## 7. Churn

```dax
Churn Risk Dealers =
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_code]),
    FILTER(
        VALUES(fact_sales[customer_code]),
        CALCULATE(MAX(fact_sales[order_date])) < DATE(2026, 1, 1)
    )
)
```

```dax
Lost Dealers 180d =
CALCULATE(
    DISTINCTCOUNT(fact_sales[customer_code]),
    FILTER(
        VALUES(fact_sales[customer_code]),
        DATE(2026, 3, 31) - CALCULATE(MAX(fact_sales[order_date])) > 180
    )
)
```

## 8. Group Share

```dax
Group Revenue Share =
DIVIDE(
    [Total Revenue],
    CALCULATE([Total Revenue], ALLSELECTED(fact_sales[group_code]))
)
```

## 9. Planning Target

```dax
Target Revenue Q2 2026 = [Revenue Q1 2026] * 1.10

Target Qty Q2 2026 =
CALCULATE([Total Quantity], fact_sales[fiscal_year] = 2026, fact_sales[fiscal_quarter] = 1) * 1.10
```

Ghi chú:

- Target +10% là giả định business để trình bày planning.
- Không được ghi đây là forecast model chính thức.
