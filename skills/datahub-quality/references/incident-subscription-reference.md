# Incident & Subscription Reference

---

## Incidents

### Raise an incident

```graphql
mutation {
  raiseIncident(input: {
    type: FRESHNESS
    title: "Orders table is stale"
    description: "Last update was 12 hours ago, expected every 6 hours"
    resourceUrn: "<DATASET_URN>"
    priority: HIGH
    status: { state: ACTIVE, stage: TRIAGE }
    assigneeUrns: ["urn:li:corpuser:oncall"]
  })
}
```

Returns the incident URN as a string.

Multi-asset incidents: use `resourceUrns` (list) instead of `resourceUrn` (single).

### Update incident status

```graphql
mutation {
  updateIncidentStatus(
    urn: "<INCIDENT_URN>"
    input: {
      state: RESOLVED
      stage: FIXED
      message: "Backfill completed successfully"
    }
  )
}
```

### Update incident details

```graphql
mutation {
  updateIncident(
    urn: "<INCIDENT_URN>"
    input: {
      title: "Updated title"
      priority: CRITICAL
      status: { state: ACTIVE, stage: INVESTIGATION }
      assigneeUrns: ["urn:li:corpuser:jdoe", "urn:li:corpuser:oncall"]
    }
  )
}
```

### Incident types (`IncidentType`)

| Type | Use case |
| --- | --- |
| `FRESHNESS` | Data is stale |
| `VOLUME` | Row count anomaly |
| `FIELD` | Column-level quality issue |
| `SQL` | Custom SQL check failure |
| `DATA_SCHEMA` | Unexpected schema change |
| `OPERATIONAL` | Pipeline or infrastructure failure |
| `CUSTOM` | Anything else (set `customType` string) |
| `DATASET_COLUMN` | Issue with a specific column |
| `DATASET_ROWS` | Issue with specific rows |

### Incident priorities (`IncidentPriority`)

`CRITICAL` > `HIGH` > `MEDIUM` > `LOW`

### Incident states (`IncidentState`)

| State | Meaning |
| --- | --- |
| `ACTIVE` | Incident is open and needs attention |
| `RESOLVED` | Incident has been closed |

### Incident stages (`IncidentStage`)

| Stage | Meaning |
| --- | --- |
| `TRIAGE` | Just raised, needs assessment |
| `INVESTIGATION` | Being investigated |
| `WORK_IN_PROGRESS` | Fix is underway |
| `FIXED` | Root cause addressed |
| `NO_ACTION_REQUIRED` | Determined to not need a fix |

### Incident source types (`IncidentSourceType`)

| Type | Meaning |
| --- | --- |
| `MANUAL` | Raised by a user |
| `ASSERTION_FAILURE` | Auto-raised by a failing assertion |

---

## Querying Incidents

### On a dataset

```graphql
query {
  dataset(urn: "<DATASET_URN>") {
    incidents(state: ACTIVE, start: 0, count: 20) {
      total
      incidents {
        urn
        incidentType
        title
        description
        priority
        incidentStatus { state stage message lastUpdated { time } }
        source { type source { urn } }
        created { time actor }
        assignees { ... on CorpUser { username } ... on CorpGroup { name } }
      }
    }
  }
}
```

Filter parameters on `incidents()`:

| Parameter | Type | Notes |
| --- | --- | --- |
| `state` | `IncidentState` | `ACTIVE` or `RESOLVED` |
| `stage` | `IncidentStage` | Filter by stage |
| `priority` | `IncidentPriority` | Filter by priority |
| `assigneeUrns` | `[String!]` | Filter by assignees |
| `start` | `Int` | Pagination offset |
| `count` | `Int` | Page size (default 20) |

### By URN

```graphql
query {
  entity(urn: "<INCIDENT_URN>") {
    ... on Incident {
      urn
      incidentType
      title
      description
      priority
      incidentStatus { state stage message }
      entity { urn type ... on Dataset { properties { name } platform { name } } }
      source { type }
      created { time actor }
    }
  }
}
```

---

## Subscriptions

### Create a subscription

```graphql
mutation {
  createSubscription(input: {
    entityUrn: "<ENTITY_URN>"
    subscriptionTypes: [ENTITY_CHANGE]
    entityChangeTypes: [
      { entityChangeType: ASSERTION_FAILED }
      { entityChangeType: INCIDENT_RAISED }
    ]
    notificationConfig: {
      notificationSettings: {
        sinkTypes: [SLACK]
        slackSettings: { channels: ["#data-quality"] }
      }
    }
  }) { subscriptionUrn }
}
```

### Subscription types (`SubscriptionType`)

| Type | Scope |
| --- | --- |
| `ENTITY_CHANGE` | Direct changes on the entity |
| `UPSTREAM_ENTITY_CHANGE` | Changes on upstream dependencies |

### Quality-relevant change types (`EntityChangeType`)

| Change type | Trigger |
| --- | --- |
| `ASSERTION_PASSED` | Assertion succeeded |
| `ASSERTION_FAILED` | Assertion failed |
| `ASSERTION_ERROR` | Assertion errored |
| `INCIDENT_RAISED` | Incident opened |
| `INCIDENT_RESOLVED` | Incident closed |

### Filtering to specific assertions

```graphql
entityChangeTypes: [
  {
    entityChangeType: ASSERTION_FAILED
    filter: { includeAssertions: ["<ASSERTION_URN_1>", "<ASSERTION_URN_2>"] }
  }
]
```

### Notification channels

**Slack:**
```graphql
notificationConfig: {
  notificationSettings: {
    sinkTypes: [SLACK]
    slackSettings: {
      userHandle: "@jdoe"           # DM to user
      channels: ["#data-quality"]   # or post to channel(s)
    }
  }
}
```

**Email:**
```graphql
notificationConfig: {
  notificationSettings: {
    sinkTypes: [EMAIL]
    emailSettings: { email: "oncall@company.com" }
  }
}
```

**Microsoft Teams:**
```graphql
notificationConfig: {
  notificationSettings: {
    sinkTypes: [TEAMS]
    teamsSettings: {
      channels: [{ id: "<TEAMS_CHANNEL_ID>", name: "Data Quality" }]
    }
  }
}
```

**Multiple channels simultaneously:**
```graphql
notificationConfig: {
  notificationSettings: {
    sinkTypes: [SLACK, EMAIL]
    slackSettings: { channels: ["#data-quality"] }
    emailSettings: { email: "oncall@company.com" }
  }
}
```

### Group subscriptions

Subscribe a group (all members get notified):

```graphql
mutation {
  createSubscription(input: {
    entityUrn: "<ENTITY_URN>"
    groupUrn: "urn:li:corpGroup:data-engineering"
    subscriptionTypes: [ENTITY_CHANGE]
    entityChangeTypes: [
      { entityChangeType: ASSERTION_FAILED }
      { entityChangeType: INCIDENT_RAISED }
    ]
    notificationConfig: {
      notificationSettings: {
        sinkTypes: [SLACK]
        slackSettings: { channels: ["#data-eng-alerts"] }
      }
    }
  }) { subscriptionUrn }
}
```

### Update a subscription

```graphql
mutation {
  updateSubscription(input: {
    subscriptionUrn: "<SUBSCRIPTION_URN>"
    entityChangeTypes: [
      { entityChangeType: ASSERTION_FAILED }
      { entityChangeType: ASSERTION_ERROR }
      { entityChangeType: INCIDENT_RAISED }
      { entityChangeType: INCIDENT_RESOLVED }
    ]
    notificationConfig: {
      notificationSettings: {
        sinkTypes: [SLACK, EMAIL]
        slackSettings: { channels: ["#data-quality"] }
        emailSettings: { email: "team@company.com" }
      }
    }
  }) { subscriptionUrn }
}
```

### Delete a subscription

```graphql
mutation {
  deleteSubscription(input: {
    subscriptionUrn: "<SUBSCRIPTION_URN>"
  })
}
```

### Query subscriptions

```graphql
# List your subscriptions
query {
  listSubscriptions(input: { start: 0, count: 20 }) {
    total
    subscriptions {
      subscriptionUrn
      entity { urn type ... on Dataset { properties { name } platform { name } } }
      subscriptionTypes
      entityChangeTypes { entityChangeType filter { includeAssertions } }
      notificationConfig {
        notificationSettings {
          sinkTypes
          slackSettings { channels }
          emailSettings { email }
        }
      }
    }
  }
}

# Who is subscribed to an entity
query {
  getEntitySubscriptionSummary(input: { entityUrn: "<ENTITY_URN>" }) {
    isUserSubscribed
    isUserSubscribedViaGroup
    userSubscriptionCount
    groupSubscriptionCount
    subscribedUsers { username }
    subscribedGroups { name }
  }
}

# Get a specific subscription
query {
  getSubscription(input: { entityUrn: "<ENTITY_URN>" }) {
    subscription {
      subscriptionUrn
      subscriptionTypes
      entityChangeTypes { entityChangeType }
    }
  }
}
```
