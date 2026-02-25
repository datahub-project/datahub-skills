# Identity Platforms Sources

**Source Type:** API-Based

## Overview

Identity platforms like Okta, Azure AD, and Google Workspace provide user and group information through REST APIs.

## What to Extract

- **Users** (CorpUser) - User accounts and profiles
- **Groups** (CorpGroup) - Security groups and organizational units
- **Group Membership** - User-to-group relationships

## Required Aspects

| Aspect            | Required        | Description                                        |
| ----------------- | --------------- | -------------------------------------------------- |
| `corpUserInfo`    | ✅ ALWAYS       | User profile info (name, email, title, department) |
| `corpGroupInfo`   | ✅ ALWAYS       | Group info (name, description, email)              |
| `groupMembership` | ✅ IF AVAILABLE | User's group memberships                           |
| `status`          | 🔄 AUTO         | Auto-generated for all entities                    |

## Implementation Guide

→ **See [API-Based Sources Guide](../api.md)** for implementation details

## Special Considerations

- **Privacy**: Handle PII (Personally Identifiable Information) appropriately
- **Pagination**: User/group lists can be very large
- **Rate Limiting**: Identity APIs often have strict rate limits

## Example Sources in DataHub

- `src/datahub/ingestion/source/okta.py`
- `src/datahub/ingestion/source/azure_ad.py`
