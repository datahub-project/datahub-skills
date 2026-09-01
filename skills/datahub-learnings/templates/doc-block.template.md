# Documentation Block Template

Rendered from the structured property (source of truth) on every retain write, never
hand-composed, never partially patched. Full rules: `protocol/SPEC.md` §5.2.

```markdown
<!-- agent-memory:begin -->

## Agent learnings

_Distilled by agents via the agent-memory protocol. Machine-generated — do not hand-edit; edits will be overwritten on the next write._

### `<kind>` — `<field-name-or-"table">` (confidence: <level>)

**Claim:** <claim text>
**Evidence:** <evidence text>
**Learned by** `<agent-name>/<session-id>` on <YYYY-MM-DD> — id `<uuid>`

### `<kind>` — `<field-name-or-"table">` (confidence: <level>, DISPUTED — see id <conflicting-id>)

**Claim:** <claim text — unchanged even though disputed>
**Evidence:** <evidence text — unchanged even though disputed>
**Learned by** `<agent-name>/<session-id>` on <YYYY-MM-DD> — id `<uuid>`

### `<kind>` — `<field-name-or-"table">` (confidence: <level>, CONFLICT — contradicts id <disputed-id>)

**Claim:** <claim stating the contradiction plainly>
**Evidence:** <evidence text>
**Learned by** `<agent-name>/<session-id>` on <YYYY-MM-DD> — id `<uuid>`
<!-- agent-memory:end -->
```

Conflict headings say "contradicts", never "supersedes" or "replaces". An unresolved
conflict prefers neither side (SPEC.md §8).

## Splice logic (apply every write, not just the first)

```python
BEGIN = "<!-- agent-memory:begin -->"
END = "<!-- agent-memory:end -->"

def splice(current_description, rendered_block):
    current_description = current_description or ""
    if BEGIN in current_description and END in current_description:
        pre = current_description.split(BEGIN)[0]
        post = current_description.split(END)[1]
        return pre + rendered_block + post          # replace in place
    sep = "\n\n" if current_description else ""
    return current_description + sep + rendered_block  # first write: append
```

Then `update_description(entity_urn=..., operation="replace", description=splice(current, rendered_block))`.
Verified empirically: applying this twice in a row (once to establish the block, once
with different content) leaves exactly one `<!-- agent-memory:begin -->` occurrence,
never two.

## Ordering and rules

1. Entries ordered by `learned_at` descending, ties broken by `kind` alphabetically (SPEC.md §5.2 rule 3).
2. One `###` heading per learning: `` `kind` — `field-or-"table"` (confidence: level) `` (rule 4).
3. `status: disputed` or `status: conflict` entries render the status visibly in the heading (rule 5).
4. The block is a full regeneration of every current, non-superseded learning: writing the same learning set twice must produce byte-identical block content (rule 6).
