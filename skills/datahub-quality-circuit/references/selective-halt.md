# Selective halt patterns

## Forking pipeline

When one stage fans out to multiple marts, quality issues often hit **only one branch**.

```
raw ──→ staging ──┬──→ mart_A   (impacted)
                  └──→ mart_B   (healthy)
```

**Do:** quarantine `mart_A` (and optionally `staging` if it still feeds only bad paths that cannot be filtered).  
**Don't:** quarantine `mart_B` “to be safe” without evidence.

## Linear pipeline

```
raw ──→ staging ──→ mart
```

Impact often cascades fully — still document hop distance and owners.

## Sample data note

Official DataHub sample **healthcare** plants quality issues (negative billing, invalid ages, date swaps). Load via dataset ingest + lineage scripts — not `datahub datapack load healthcare`. Datapacks such as `showcase-ecommerce` / `bootstrap` are separate.
