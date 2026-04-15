# DivvyUp API Guide

Base URL: `http://localhost:8000` (dev) — set `VITE_API_URL` for production.

All protected endpoints require an `Authorization: Bearer <token>` header.
Errors always return `{ "detail": "message" }`.

---

## Authentication

### POST /auth/token
Log in and receive a JWT.

> **Important:** This endpoint uses OAuth2 form encoding, NOT JSON.
> Send `Content-Type: application/x-www-form-urlencoded` with field `username` (not `email`).

**Request (form body)**
```
username=user@example.com&password=secret
```

**Response**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

Token expires after **24 hours**. Store it in `localStorage` and attach it to every subsequent request.

---

## Users

### POST /users/
Register a new account. No auth required.

**Request**
```json
{
  "email": "user@example.com",
  "password": "secret",
  "display_name": "Jane",
  "phone": "+1234567890",      // optional
  "base_currency": "USD"       // optional, default "USD"
}
```

**Response** — `UserRead`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "Jane",
  "avatar_emoji": "😀",
  "phone": null,
  "venmo_handle": null,
  "paypal_email": null,
  "base_currency": "USD",
  "created_at": "2026-04-07T..."
}
```

### GET /users/me
Get the currently logged-in user. **Auth required.**

**Response** — `UserRead` (same shape as above)

### GET /users/{user_uuid}
Get a specific user by UUID. **Auth required.**

**Response** — `UserRead`

### GET /users/search?email=...
Search users by email (partial match, case-insensitive). **Auth required.**
Returns up to 10 results. Excludes the current user.

**Response** — `list[UserRead]`

### PATCH /users/me
Update the current user's profile. **Auth required.**
Only include fields you want to change.

**Request**
```json
{
  "display_name": "Jane Smith",
  "avatar_emoji": "🥸",
  "phone": "+1234567890",
  "venmo_handle": "janesmith",
  "paypal_email": "jane@paypal.com",
  "base_currency": "EUR"
}
```

**Response** — `UserRead`

### DELETE /users/me
Delete the current user's account. **Auth required.**

> Will return **403** if the user is still an admin of any group.
> They must transfer ownership or delete those groups first.
> Regular group memberships are cleaned up automatically.

**Response** — 204 No Content

---

## Groups

### POST /groups/
Create a new group. **Auth required.**
Creator is automatically added as admin.

**Request**
```json
{
  "name": "Apartment",
  "description": "Monthly shared expenses",  // optional
  "base_currency": "USD"                      // optional, default "USD"
}
```

**Response** — `GroupRead`
```json
{
  "id": "uuid",
  "name": "Apartment",
  "description": "Monthly shared expenses",
  "invite_code": "A3XK9B2F",
  "base_currency": "USD",
  "created_by": "uuid",
  "created_at": "2026-04-07T..."
}
```

### POST /groups/join
Join a group using an invite code. **Auth required.**

**Request**
```json
{
  "invite_code": "A3XK9B2F"
}
```

**Response** — `GroupRead` for the group that was joined.

Errors:
- `404` — invalid invite code
- `400` — already a member

### GET /groups/
List all groups the current user belongs to. **Auth required.**

**Response** — `list[GroupRead]`

### GET /groups/{group_uuid}
Get a single group. **Auth required. Must be a member.**

**Response** — `GroupRead`

### GET /groups/{group_uuid}/balances
Get net balances for all members of a group. **Auth required. Must be a member.**

Positive `net_balance` = this user is owed money.
Negative `net_balance` = this user owes money.
Accounts for all non-deleted expenses and all **completed** settlements.

**Response**
```json
[
  { "user_id": "uuid", "net_balance": "20.00" },
  { "user_id": "uuid", "net_balance": "-20.00" }
]
```

### PATCH /groups/{group_uuid}
Update group details. **Auth required. Admin only.**

**Request** — any subset of:
```json
{
  "name": "New Name",
  "description": "Updated description",
  "base_currency": "EUR"
}
```

**Response** — `GroupRead`

### DELETE /groups/{group_uuid}
Delete a group and all its data. **Auth required. Admin only.**

**Response** — 204 No Content

---

## Group Members

### GET /groups/{group_uuid}/members
List all members of a group. **Auth required. Must be a member.**

**Response** — `list[GroupMemberRead]`
```json
[
  {
    "group_id": "uuid",
    "user_id": "uuid",
    "role": "admin",
    "joined_at": "2026-04-07T...",
    "display_name": "Jane",
    "email": "jane@example.com",
    "avatar_url": null
  }
]
```

### GET /groups/{group_uuid}/members/{user_uuid}
Get a specific group member. **Auth required.**

**Response** — `GroupMemberRead`

### DELETE /groups/{group_uuid}/members
Leave a group. **Auth required.**

> Admins cannot leave. Transfer ownership first.

**Response** — 204 No Content

### DELETE /groups/{group_uuid}/members/{user_uuid}
Remove another member from a group. **Auth required. Admin only.**

> Admins cannot remove themselves this way. Use the transfer + leave flow.

**Response** — 204 No Content

### PATCH /groups/{group_uuid}/members/{user_uuid}/transfer
Transfer admin ownership to another member. **Auth required. Admin only.**

**Response** — `{ "message": "Ownership of ... has been transferred to ..." }`

---

## Expenses

All expense endpoints require group membership.

### POST /groups/{group_uuid}/expenses/
Create an expense. **Auth required. Must be a member.**

The current user is set as `paid_by`. Splits are calculated automatically based on `split_type`.

#### Split types

**`equal`** (default) — divide evenly among all non-payer members. No extra fields needed.
```json
{
  "description": "Dinner",
  "amount": "60.00",
  "base_amount": "60.00",
  "expense_date": "2026-04-07",
  "split_type": "equal"
}
```

**`exact`** — specify each non-payer's exact dollar amount. Amounts must sum to `base_amount`.
```json
{
  "description": "Dinner",
  "amount": "60.00",
  "base_amount": "60.00",
  "expense_date": "2026-04-07",
  "split_type": "exact",
  "member_splits": [
    { "user_id": "<uuid>", "amount": "40.00" },
    { "user_id": "<uuid>", "amount": "20.00" }
  ]
}
```

**`percentage`** — specify each non-payer's share as a percentage. Percentages must sum to 100.
```json
{
  "description": "Dinner",
  "amount": "60.00",
  "base_amount": "60.00",
  "expense_date": "2026-04-07",
  "split_type": "percentage",
  "member_splits": [
    { "user_id": "<uuid>", "percentage": "66.67" },
    { "user_id": "<uuid>", "percentage": "33.33" }
  ]
}
```

> `amount` is the original currency amount. `base_amount` is the converted USD amount used for balance math. If no currency conversion, they are the same.
> `exchange_rate` (default `1`), `category_id` (default `1`), and `notes` are all optional.

**Response** — `ExpenseRead`
```json
{
  "id": "uuid",
  "group_id": "uuid",
  "paid_by": "uuid",
  "paid_by_name": "Jane",
  "description": "Dinner",
  "amount": "60.00",
  "currency": "USD",
  "base_amount": "60.00",
  "category_id": 1,
  "split_type": "equal",
  "expense_date": "2026-04-07",
  "notes": null,
  "is_deleted": false,
  "created_at": "2026-04-07T..."
}
```

### GET /groups/{group_uuid}/expenses/
List all active expenses in a group. **Auth required. Must be a member.**
Soft-deleted expenses are excluded. Each expense includes `paid_by_name`.

**Response** — `list[ExpenseRead]`

### GET /groups/{group_uuid}/expenses/{expense_uuid}
Get a single expense. **Auth required. Must be a member.**

**Response** — `ExpenseRead`

### GET /groups/{group_uuid}/expenses/{expense_uuid}/splits
Get how an expense is split across members. **Auth required. Must be a member.**

**Response** — `list[ExpenseSplitRead]`
```json
[
  {
    "id": "uuid",
    "expense_id": "uuid",
    "user_id": "uuid",
    "share_amount": "20.00",
    "share_pct": null,
    "is_settled": false,
    "settled_at": null
  }
]
```

### PATCH /groups/{group_uuid}/expenses/{expense_uuid}
Update an expense. **Auth required. Creator or group admin only.**

> Splits are automatically recalculated if `base_amount`, `split_type`, or `member_splits` is included in the request.

**Request** — any subset of:
```json
{
  "description": "Updated name",
  "amount": "75.00",
  "base_amount": "75.00",
  "currency": "USD",
  "exchange_rate": "1",
  "category_id": 2,
  "split_type": "exact",
  "expense_date": "2026-04-07",
  "notes": "Updated note",
  "member_splits": [
    { "user_id": "<uuid>", "amount": "50.00" },
    { "user_id": "<uuid>", "amount": "25.00" }
  ]
}
```

**Response** — `ExpenseRead`

### DELETE /groups/{group_uuid}/expenses/{expense_uuid}
Soft-delete an expense. **Auth required. Creator or group admin only.**

> This sets `is_deleted = true`. The expense is hidden from all reads and excluded from balances. No data is permanently lost.

**Response** — 204 No Content

---

## Settlements

A settlement represents a direct payment from one member to another to clear a debt.
Lifecycle: `pending` → `completed` (payee confirms) or `cancelled` (either party cancels).

Only **completed** settlements affect the balance calculation.

### POST /groups/{group_uuid}/settlements/{payee_uuid}
Record a payment to another group member. **Auth required. Must be a member.**

**Request**
```json
{
  "amount": "20.00",
  "currency": "USD",
  "provider": "venmo",        // optional: "cash" | "venmo" | "paypal" | "other"
  "provider_ref_id": "abc123", // optional
  "note": "For dinner"         // optional
}
```

**Response** — `SettlementRead`
```json
{
  "id": "uuid",
  "group_id": "uuid",
  "payer_id": "uuid",
  "payee_id": "uuid",
  "amount": "20.00",
  "currency": "USD",
  "status": "pending",
  "provider": "venmo",
  "provider_ref_id": null,
  "settled_at": null,
  "created_at": "2026-04-07T..."
}
```

### GET /groups/{group_uuid}/settlements/
List all settlements in a group. **Auth required. Must be a member.**

**Response** — `list[SettlementRead]`

### GET /groups/{group_uuid}/settlements/{settlement_uuid}
Get a single settlement. **Auth required. Must be a member.**

**Response** — `SettlementRead`

### PATCH /groups/{group_uuid}/settlements/{settlement_uuid}/confirm
Confirm a payment was received. **Auth required. Payee only.**

> Sets status to `completed` and records `settled_at`. Balance is updated immediately.

**Response** — `SettlementRead`

### PATCH /groups/{group_uuid}/settlements/{settlement_uuid}/cancel
Cancel a pending settlement. **Auth required. Payer or payee.**

> Only works if status is still `pending`.

**Response** — `SettlementRead`

---

## Recurring Expenses

Recurring expenses auto-generate real expenses on a schedule via a cron job.

### POST /groups/{group_uuid}/recurring/
Create a recurring expense. **Auth required. Must be a member.**

**Request**
```json
{
  "description": "Monthly Rent",
  "amount": "1200.00",
  "currency": "USD",
  "base_amount": "1200.00",
  "exchange_rate": "1",
  "category_id": 4,
  "split_type": "equal",
  "interval": "monthly",     // "daily" | "weekly" | "biweekly" | "monthly" | "yearly"
  "start_date": "2026-05-01",
  "end_date": "2027-05-01"   // optional
}
```

**Response** — `RecurringExpenseRead`

### GET /groups/{group_uuid}/recurring/
List all recurring expenses for a group. **Auth required. Must be a member.**

**Response** — `list[RecurringExpenseRead]`

### GET /groups/{group_uuid}/recurring/{recurring_uuid}
Get a single recurring expense. **Auth required. Must be a member.**

**Response** — `RecurringExpenseRead`

### PATCH /groups/{group_uuid}/recurring/{recurring_uuid}
Update a recurring expense. **Auth required. Creator or group admin only.**

**Request** — any subset of:
```json
{
  "description": "Updated",
  "amount": "1300.00",
  "base_amount": "1300.00",
  "currency": "USD",
  "exchange_rate": "1",
  "category_id": 4,
  "split_type": "equal",
  "end_date": "2027-12-01",
  "is_active": false
}
```

**Response** — `RecurringExpenseRead`

### DELETE /groups/{group_uuid}/recurring/{recurring_uuid}
Deactivate a recurring expense. **Auth required. Creator or group admin only.**

> Sets `is_active = false`. No future expenses will be generated.

**Response** — 204 No Content

### POST /recurring/generate
Trigger the cron job manually. Generates expenses for all active recurring expenses due today or earlier.

> Requires `X-Cron-Secret: <value>` header if `CRON_SECRET` is set in the environment.
> This is called automatically by Render's cron scheduler — the frontend does not need to call this.

**Response**
```json
{ "message": "Generated 3 expense(s)." }
```

---

## Comments

### POST /groups/{group_uuid}/expenses/{expense_uuid}/comments/
Add a comment to an expense. **Auth required. Must be a group member.**

**Request**
```json
{ "body": "Should we split this differently?" }
```

**Response** — `CommentRead`
```json
{
  "id": "uuid",
  "expense_id": "uuid",
  "user_id": "uuid",
  "body": "Should we split this differently?",
  "created_at": "2026-04-07T..."
}
```

### GET /groups/{group_uuid}/expenses/{expense_uuid}/comments/
List all comments on an expense. **Auth required. Must be a group member.**

**Response** — `list[CommentRead]`

### GET /groups/{group_uuid}/expenses/{expense_uuid}/comments/{comment_uuid}
Get a single comment. **Auth required.**

**Response** — `CommentRead`

### DELETE /groups/{group_uuid}/expenses/{expense_uuid}/comments/{comment_uuid}
Delete a comment. **Auth required. Comment author only.**

**Response** — 204 No Content

---

## Notifications

### GET /notifications/
Get all notifications for the current user. **Auth required.**

**Response** — `list[NotificationRead]`

### GET /notifications/{notification_uuid}
Get a single notification. **Auth required.**

**Response** — `NotificationRead`

### DELETE /notifications/
Delete all notifications for the current user. **Auth required.**

**Response** — 204 No Content

### DELETE /notifications/{notification_uuid}
Delete a single notification. **Auth required.**

**Response** — 204 No Content

---

## Categories

### GET /categories/
Get all available expense categories. **Auth required.**

**Response**
```json
[
  { "id": 1, "name": "Groceries",      "icon": "🛒" },
  { "id": 2, "name": "Food & Drink",  "icon": "🍔" },
  { "id": 3, "name": "Transport",     "icon": "🚗" },
  { "id": 4, "name": "Housing",       "icon": "🏠" },
  { "id": 5, "name": "Entertainment", "icon": "🎬" },
  { "id": 6, "name": "Shopping",      "icon": "🛍️" },
  { "id": 7, "name": "Travel",        "icon": "✈️" },
  { "id": 8, "name": "Utilities",     "icon": "💡" },
  { "id": 9, "name": "Health",        "icon": "💊" },
  { "id": 10, "name": "Other",        "icon": "🗂️" }
]
```

The default `category_id` for all expense and recurring expense creates is `1` (Misc).

---

## Common Patterns

### Typical login flow
```js
// 1. Login
POST /auth/token  (form-encoded, field is "username" not "email")

// 2. Get current user info
GET /users/me

// 3. Get user's groups
GET /groups/
```

### Typical group flow
```js
// Create a group (you become admin)
POST /groups/

// Share the invite_code from the response with others
// Others join with:
POST /groups/join  { "invite_code": "..." }

// See who's in the group
GET /groups/{uuid}/members

// See who owes what
GET /groups/{uuid}/balances
```

### Typical expense flow
```js
// Add an expense (you are the payer, splits are auto-calculated)
POST /groups/{uuid}/expenses/

// See the splits
GET /groups/{uuid}/expenses/{uuid}/splits

// When someone pays you back, record it
POST /groups/{uuid}/settlements/{payee_uuid}

// Payee confirms receipt
PATCH /groups/{uuid}/settlements/{uuid}/confirm

// Check updated balances
GET /groups/{uuid}/balances
```

### HTTP status codes used
| Code | Meaning |
|------|---------|
| 200  | Success |
| 204  | Success, no content (deletes) |
| 400  | Bad request / validation error |
| 401  | Not authenticated (missing or expired token) |
| 403  | Forbidden (authenticated but not authorized) |
| 404  | Resource not found |
| 500  | Server error |
---

## Friends

Friends are a directional contacts list — adding someone puts them in your list. They don't need to reciprocate. Balance is calculated across all groups you share with that person.

### POST /friends/{user_uuid}
Add a user to your friends list. **Auth required.**

Errors:
- `400` — adding yourself, or already friends
- `404` — user not found

**Response** — 201
```json
{ "message": "uuid has been added to your friends list." }
```

### GET /friends/
List all your friends with balances. **Auth required.**

**Response** — `list[FriendRead]`
```json
[
  {
    "id": "uuid",
    "email": "friend@example.com",
    "display_name": "Alex",
    "avatar_emoji": "🤫",
    "added_at": "2026-04-07T...",
    "balance": "20.00"
  }
]
```

`balance` — positive means they owe you, negative means you owe them. Calculated across all shared groups, adjusted for completed settlements.

### GET /friends/{user_uuid}
Get a single friend with their balance. **Auth required.**

**Response** — `FriendRead` (same shape as list above)

### DELETE /friends/{user_uuid}
Remove a friend from your list. **Auth required.**

**Response** — 204 No Content

---

## Users — Search

### GET /users/search?email=...
Search for users by email (partial match, case-insensitive). **Auth required.**
Returns up to 10 results, never includes the current user.

**Example:** `GET /users/search?email=jane`

**Response** — `list[UserRead]`

Typical flow: search by email to find a user's UUID, then call `POST /friends/{user_uuid}`.
