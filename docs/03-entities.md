# Entities

## Enums

|enum | values |
|Platform|github gitlab bitbucket azure_devops other
|TicketType|case feature request issue
|Priority|low medium high
|TicketStatus|open in_progress blocked done closed
|Channel|telegram
|ReminderStatus|scheduled sent failed cancelled

```
PROJECT {
    uuid id PK
    string name
    string slug UK
    enum platform
    string repo_url
    string description
    boolean is_active
    datetime created_at
    datetime updated_at
}

TICKET {
    uuid id PK
    uuid project_id FK
    enum type
    string title
    string description
    enum priority
    enum status
    string external_ref
    datetime due_at
    datetime created_at
    datetime updated_at
}

SUBTASK {
    uuid id PK
    uuid ticket_id FK
    string title
    boolean is_done
    integer position
}

REMINDER {
    uuid id PK
    uuid ticket_id FK
    uuid user_id FK
    datetime remind_at
    enum channel
    string message
    enum status
    integer attempts
    datetime sent_at
}

USER {
    uuid id PK
    string name
    integer telegram_chat_id UK
    boolean is_active
    datetime created_at
}

OTP_CODE {
    uuid id PK
    integer telegram_chat_id FK
    string code_hash
    datetime expires_at
    datetime consumed_at
    integer attempts
}
```
