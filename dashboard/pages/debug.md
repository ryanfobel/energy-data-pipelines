---
title: Debug
---

# Debug

```sql all_tables
SELECT * FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
```

<DataTable data={all_tables}/>
