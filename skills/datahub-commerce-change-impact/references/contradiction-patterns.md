# Contradiction patterns

Five families cover most commerce drift. For each: what to compare, what it
costs when wrong, and the trap that makes it easy to miss.

---

## 1. Price parity

**Compare** the authoritative price against every customer-visible price:
checkout, storefront, product feeds, marketplace listings, advertising claims,
and machine-readable manifests.

**Cost** Either the merchant honours the advertised price and loses the
difference on every unit, or refuses and takes a landing-page-mismatch penalty,
item disapproval, or a complaint. Both outcomes are worse than the change never
having been made.

**Trap** Feeds are frequently *pinned* — a value hardcoded during an incident to
get a rejected feed accepted, then never unpinned. The transformation is working
correctly; it is faithfully emitting the override. Compare emitted output, not
transformation logic.

---

## 2. Inventory safety

**Compare** sellable units against every commitment: bundles, kits, pre-orders,
subscription allocations, marketplace quantity.

Sellable units is rarely raw on-hand. Subtract reservations and safety stock:

```
sellable = on_hand - reserved - safety_stock
```

For bundles, the constraint is the scarcest component:

```
buildable = min(sellable(component) // units_per_bundle for each component)
```

**Cost** Overselling is the most expensive contradiction because the customer
has already paid. It produces cancellations, refunds, support contacts and
marketplace seller-metric damage that outlasts the incident.

**Trap** A bundle commitment set when stock was plentiful stays valid-looking
long after the component ran down. Nothing recomputes it unless something does.

---

## 3. Promotion integrity

**Compare** each active promotion's price basis against the current
authoritative price. Also check date windows, eligibility, stacking, and whether
the promoted item is actually in stock.

**Cost** A promotion anchored to a superseded price overstates the saving. If
the basis is presented to the customer as a reference price, that is a
misleading-savings claim, which is regulated in most markets.

**Trap** The promotion still computes correctly — it applies exactly the
percentage it was configured with. Only the anchor is wrong, so nothing errors.

---

## 4. Machine-readable freshness

**Compare** agent- and partner-facing manifests — structured product feeds,
shopping-agent manifests, partner APIs — against current price, availability,
status, variants and policy.

**Cost** These are quoted verbatim by systems with no human in the loop. A stale
manifest is not a page a customer might misread; it is a wrong fact stated
confidently by a third party before the customer ever reaches the store.

**Trap** They are usually the least-monitored surface, because no internal team
looks at them daily. They are also increasingly the first thing a customer sees.

---

## 5. Policy consistency

**Compare** the authoritative policy — returns window, restocking fee, shipping
commitment, warranty — against the storefront, checkout, feed claims,
promotional copy and manifests.

**Cost** The advertised terms are the ones a customer can hold the merchant to.
A shorter advertised window than the real policy is a consumer-protection
problem; a longer one is an unfunded liability.

**Trap** Policy is often copy rather than data, so it lives in a CMS or a
template and never appears in a data-quality check at all. Its lineage may need
to be recorded manually before this workflow can see it.

---

## Recording a contradiction

Whatever the family, record the same fields, so findings are comparable:

| Field | Why |
| --- | --- |
| expected value | from the authoritative source |
| observed value | from the downstream asset's actual output |
| source URN | what the truth came from |
| downstream URN | what disagrees |
| owner | who can fix it, or explicitly none |
| customer impact | one sentence, no jargon |
| business risk | what it costs if left |
| evidence | the comparison and the lineage path that connected them |

The evidence field is what makes a finding checkable by someone who does not
trust the tool. Keep it.
