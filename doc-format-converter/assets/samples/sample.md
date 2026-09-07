# Quarterly Product Update

The **Falcon** release shipped on schedule and *ahead* of the quality bar. This
document is a fixture for verifying the Universal Document Converter — it
exercises headings, inline formatting, lists, a table, code, and CJK text.

## Highlights

- Faster sync engine with `delta-merge` enabled by default
- **32%** fewer support tickets month over month
- New admin dashboard rolled out to all tenants

## Adoption by Region

| Region   | Active Users | Growth |
| -------- | ------------ | ------ |
| Americas | 12,400       | +8%    |
| EMEA     | 9,850        | +12%   |
| APAC     | 7,300        | +21%   |

## Rollout Steps

1. Enable the feature flag for pilot tenants
2. Monitor error budgets for one week
3. Expand to all tenants

## Sample Configuration

```json
{
  "sync": { "mode": "delta-merge", "interval_s": 30 }
}
```

## International Note

日本語のテキストも正しく変換されます。
