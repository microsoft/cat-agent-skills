# Azure Retail Prices API

## Purpose

Query current public Azure list prices without a new app registration.

## Official basis

Microsoft documents the Azure Retail Prices API as an unauthenticated interface. Prices are retail prices. According to the documentation, non-USD values are intended for budget estimation. Savings plan prices are included in the preview version.

Documentation:
https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices

Base endpoint:
https://prices.azure.com/api/retail/prices

Preview endpoint:
https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview

## Query rules

1. Filter as narrowly as possible on `serviceName`, `armRegionName`, `armSkuName`, price type, and if needed product or meter.
2. Respect case sensitivity of filter values.
3. Retrieve all pages via `NextPageLink` when a complete result set is required.
4. Use only matching active results.
5. Check `unitOfMeasure`, `currencyCode`, `type`, `reservationTerm`, `effectiveStartDate`, and primary meter region status.
6. Resolve multiple matching meters on business grounds; do not blindly sum them or take the first result.
7. Do not present retail prices as customer-specific contract prices or invoice forecasts.

## Typical fields

- `currencyCode`
- `retailPrice`
- `unitPrice`
- `armRegionName`
- `location`
- `effectiveStartDate`
- `meterId`
- `meterName`
- `productName`
- `skuName`
- `serviceName`
- `serviceFamily`
- `unitOfMeasure`
- `type`
- `isPrimaryMeterRegion`
- `armSkuName`
- `reservationTerm`
- `savingsPlan`

## Error handling

- No results: check filters and official names, then loosen selectively.
- Ambiguous results: stop the calculation and clarify SKU, operating system, tier, redundancy, or meter.
- API unreachable: do not estimate prices; output open line items and prepared search parameters.
- Currency mismatch: disclose the USD value and the required exchange-rate conversion.
