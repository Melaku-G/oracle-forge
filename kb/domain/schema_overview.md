# DAB Schema Overview

> KB v2 — Domain Layer | Oracle Forge
> Status: STUB — populate with actual schema as each dataset is loaded.
> Load this file at every session (listed in AGENT.md always-load).

---

## How to Use This File

For each dataset loaded, add an entry below following the template.
Pull schema details by running: `list_db` on each database, then `SELECT * LIMIT 3` on each table.

---

## Template

```
### [dataset_name]
Databases: [db1_name] ([system]) + [db2_name] ([system])
Domain: [what this dataset is about]

[db1_name]:
  [table_name]: [col1 (type)], [col2 (type)], ...

[db2_name]:
  [table_name]: [col1 (type)], [col2 (type)], ...

Join key: [col in db1] ↔ [col in db2] — [note any format difference]
```

---

## Datasets

_(Add entries here as each dataset is loaded. Start with Yelp.)_
