# Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Itinerary : owns
    User ||--o{ Collaboration : "collaborates via"
    User ||--o{ Booking : makes
    User ||--o{ Review : writes
    Itinerary ||--o{ Collaboration : "shared via"
    Itinerary ||--o{ DailyPlan : "planned in"
    Itinerary ||--|| Budget : has
    Itinerary ||--o{ Expense : tracks
    Itinerary ||--o{ Booking : contains
    DailyPlan }o--o{ Activity : includes
    Destination ||--o{ Itinerary : "is visited in"
    Destination ||--o{ Accommodation : offers
    Destination ||--o{ Activity : offers
    Destination |o--o{ Review : "reviewed in"
    Accommodation |o--o{ Booking : "booked in"
    Accommodation |o--o{ Review : "reviewed in"
    Activity |o--o{ Booking : "booked in"
    Activity |o--o{ Review : "reviewed in"

    User {
        string username
        string email
    }
    Destination {
        string name
        string country
    }
    Itinerary {
        string title
        date start_date
        date end_date
        decimal budget
        string status
    }
    Collaboration {
        string role
    }
    Booking {
        decimal price
        string status
    }
    Review {
        int rating
        string title
    }
```

Notes:

- Collaboration is the through model for the many-to-many between User and Itinerary (`Itinerary.collaborators`).
- A Booking points to either an Accommodation or an Activity, and a Review points to exactly one of Destination, Accommodation, or Activity (enforced in each model's `clean()`), so those links are optional.
