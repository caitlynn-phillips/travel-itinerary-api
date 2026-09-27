# Travel Itinerary Planning & Booking API — Planning Document

## ERD (entity relationships)

```
User (accounts) ──1:1──> Budget is via Itinerary, not User
User ──1:M──> Itinerary (owner)
User ──M:M──> Itinerary (collaborators, through Collaboration)
Itinerary ──1:M──> DailyPlan
Itinerary ──1:1──> Budget
Itinerary ──1:M──> Expense
Itinerary ──1:M──> Booking
Itinerary ──M:1──> Destination
DailyPlan ──M:M──> Activity
Destination ──1:M──> Accommodation
Destination ──1:M──> Activity
Destination ──1:M──> Review
Accommodation ──1:M──> Booking, Review
Activity ──1:M──> Booking, Review
Booking ──M:1──> User, Itinerary, (Accommodation | Activity)
Review ──M:1──> User, (Destination | Accommodation | Activity)
Collaboration (through model) ──M:1──> Itinerary, User (+ role)
```

Core apps: `accounts`, `destinations`, `itineraries` (Itinerary, DailyPlan, Collaboration), `bookings` (Accommodation, Activity, Booking), `reviews` (Review), `budgets` (Budget, Expense).

## API endpoint list (v1, JSON, paginated where listed)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/accounts/register/` | Register user, returns JWT pair |
| POST | `/api/v1/accounts/login/` | Login, returns JWT pair |
| POST | `/api/v1/accounts/token/refresh/` | Refresh access token |
| GET/PATCH | `/api/v1/accounts/profile/` | View/update own profile |
| POST | `/api/v1/accounts/password/change/` | Change password |
| POST | `/api/v1/accounts/password/reset/`, `/password/reset/confirm/` | Reset flow |
| GET | `/api/v1/destinations/` (ViewSet) | Browse/search/filter destinations |
| GET | `/api/v1/destinations/{id}/popular_activities/`, `/weather_info/` | Custom actions |
| GET/POST | `/api/v1/itineraries/` (ViewSet) | List own+shared / create itinerary |
| GET/PATCH/DELETE | `/api/v1/itineraries/{id}/` | Retrieve/update/delete |
| POST/GET | `/api/v1/itineraries/{id}/duplicate/`, `/share/`, `/export_pdf/`, `/upcoming/` | Custom actions |
| GET/POST | `/api/v1/itineraries/search/` (FBV) | Custom ranked search |
| GET | `/api/v1/itineraries/{id}/report/` (FBV) | Aggregated trip report |
| POST | `/api/v1/itineraries/bulk-update/` (FBV) | Bulk booking updates |
| POST/PATCH/DELETE | `/api/v1/itineraries/{id}/collaborators/` (CBV) | Manage collaborators |
| CRUD | `/api/v1/bookings/` (ViewSet) | Accommodation/activity bookings |
| POST | `/api/v1/bookings/{id}/confirm/`, `/cancel/` | Custom actions |
| CRUD | `/api/v1/reviews/` (ViewSet) | Reviews/ratings |
| GET | `/api/v1/budgets/`, `/expenses/` | Budget + expense tracking |
| GET | `/api/v1/analytics/`, `/analytics/budget_summary/` | Trip analytics ViewSet |
| GET | `/api/docs/`, `/api/redoc/` | Swagger / ReDoc |

## Authentication flow

1. Client registers or logs in → receives `access` (1 hr) + `refresh` (7 day) JWTs.
2. `access` token sent as `Authorization: Bearer <token>` on every request.
3. On 401 expiry, client calls `token/refresh/` for a new access token (rotation enabled).
4. Password reset uses a signed token emailed to the user, confirmed via `password/reset/confirm/`.

## Permission matrix

| Action | Owner | Collaborator (editor) | Collaborator (viewer) | Anonymous |
|---|---|---|---|---|
| View public destination | ✔ | ✔ | ✔ | ✔ |
| View own/shared itinerary | ✔ | ✔ | ✔ | ✘ |
| Edit itinerary | ✔ | ✔ | ✘ | ✘ |
| Delete itinerary | ✔ | ✘ | ✘ | ✘ |
| Manage collaborators | ✔ | ✘ | ✘ | ✘ |
| Create/cancel own booking | ✔ | ✔ | ✘ | ✘ |
| Write review | ✔ (authenticated) | ✔ | ✔ | ✘ |

Enforced via `IsAuthenticated`, `IsTripOwner`, `IsTripOwnerOrCollaborator`, `CanEditItinerary`, `IsBookingOwner`.

## URL structure

Everything is namespaced and versioned: `/api/v1/<app>/...`, with `app_name` set per app and ViewSets registered on one shared `DefaultRouter`. Nested resources (e.g. collaborators under an itinerary, expenses under a budget) use path converters like `<int:trip_id>`.

## Testing strategy

- **Models**: field validation, `clean()` rules (date ordering, single-target reviews), custom methods (`add_collaborator`, `budget_remaining`).
- **Serializers**: nested output, `validate`/`validate_<field>`, create/update overrides.
- **Views**: one `APITestCase` per app covering CRUD, auth-required (401), and cross-user access (404/403), using `force_authenticate` and factory-built fixtures in `setUp`.
- **Permissions**: dedicated `PermissionTestCase` per role (owner/editor/viewer) against a shared itinerary fixture.
- Target: 25+ tests, >75% coverage via `pytest --cov=.`.
