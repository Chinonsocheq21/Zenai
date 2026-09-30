# ZenAI — Lucidchart diagrams

**How to use these.** Lucidchart renders Mermaid natively. In a Lucidchart doc:
**Insert → Diagram as code → Mermaid**, paste one block below, and it draws real
draggable shapes you can restyle. One diagram per Lucid doc (or per page).
Supported types are flowchart, sequence, class, state, C4, gantt and ER — all four
below are inside that set.

Keep these blocks as the source of truth in the repo. When the architecture changes,
edit the code and re-paste rather than dragging boxes around — that's the whole point
of diagram-as-code, and it means the map is never stale at a presentation.

---

## 1 · System architecture — the ten agents, tiered

This is the diagram for slide 3 of every progress report. It keeps all ten agents the
team named in Progress Report 1, but puts them in layers so it's obvious what runs on
every turn, what runs sometimes, and what runs over weeks.

```mermaid
flowchart TB
    subgraph UI["Student"]
        S["Student message"]
    end

    subgraph RAIL["TIER 0 · Safety rail — runs on EVERY turn"]
        CRISIS["Crisis & Safety Agent<br/>trained risk classifier<br/>optimised for RECALL"]
        PRIV["Privacy Agent<br/>PII redaction · consent<br/>· retention policy"]
    end

    subgraph CORE["TIER 1 · Core loop"]
        ORCH["Orchestrator<br/>routes · retries · traces"]
        MOOD["Mood Check-In Agent<br/>trained distress classifier"]
        CONV["Conversation Agent<br/>ACT / CBT protocol"]
        FID["★ Fidelity Monitor ★<br/>scores every reply against<br/>the ACT processes<br/>blocks drift · regenerates"]
        MEM["Memory & Personalization<br/>student-controlled"]
    end

    subgraph SPEC["TIER 2 · Specialists — routed to, not always on"]
        ACAD["Academic Stress Agent"]
        RELIEF["Stress-Relief Agent"]
        SCHED["Wellness Schedule Agent"]
        REF["Resource & Referral Agent"]
    end

    subgraph LONG["TIER 3 · Longitudinal"]
        PROG["Progress Agent<br/>trends over weeks"]
    end

    DB[("Postgres + pgvector<br/>sessions · turns · mood<br/>fidelity_scores · escalations")]

    S --> PRIV
    PRIV --> CRISIS
    CRISIS -->|"risk detected"| ESC["ESCALATE<br/>campus counseling centre<br/>+ 988 · human handoff<br/>conversation STOPS"]
    CRISIS -->|"no risk"| ORCH
    ORCH --> MOOD
    MOOD --> CONV
    ORCH -.routes to.-> ACAD
    ORCH -.routes to.-> RELIEF
    ORCH -.routes to.-> SCHED
    ORCH -.routes to.-> REF
    ACAD --> CONV
    RELIEF --> CONV
    SCHED --> CONV
    REF --> CONV
    MEM <--> CONV
    CONV --> FID
    FID -->|"passes"| OUT["Reply to student"]
    FID -->|"drift: advice / diagnosis /<br/>false reassurance"| CONV
    OUT --> PROG
    MOOD --> DB
    FID --> DB
    PROG --> DB
    MEM <--> DB
    CRISIS --> DB

    classDef safety fill:#fde2e2,stroke:#c0392b,stroke-width:2px
    classDef novel fill:#fff3cd,stroke:#b8860b,stroke-width:3px
    classDef store fill:#e8eef7,stroke:#2c3e50
    class CRISIS,PRIV,ESC safety
    class FID novel
    class DB store
```

> **The yellow box is the contribution.** Everything else exists in some form in
> Woebot, Wysa, Youper or Ash. The Fidelity Monitor does not.

---

## 2 · One turn, end to end

Use this when someone asks *"but how does it actually work?"* — it answers in one
picture, and it makes the safety-first ordering obvious.

```mermaid
sequenceDiagram
    autonumber
    actor St as Student
    participant P as Privacy Agent
    participant C as Crisis & Safety
    participant O as Orchestrator
    participant M as Mood Check-In
    participant K as Memory
    participant V as Conversation (ACT)
    participant F as Fidelity Monitor
    participant D as Database

    St->>P: "I have three exams and I can't sleep"
    P->>P: redact PII, check consent scope
    P->>C: sanitised text
    C->>C: risk classifier (recall-optimised)
    alt risk detected
        C->>St: campus counseling + 988, human handoff
        C->>D: log escalation
        Note over C,St: conversation STOPS here.<br/>No therapy content is generated.
    else no risk
        C->>O: cleared
        O->>M: classify distress
        M->>D: write mood point
        M->>O: {overwhelm 0.81, sleep 0.74}
        O->>K: fetch relevant history (consented only)
        K->>O: prior values work, what helped before
        O->>V: generate, ACT protocol + context
        V->>F: candidate reply
        F->>F: score vs 6 ACT processes
        alt drift detected
            F->>V: reject — "advice-giving", regenerate
            V->>F: second candidate
        end
        F->>D: log fidelity score + attempts
        F->>St: reply
    end
```

---

## 3 · Data model

```mermaid
erDiagram
    STUDENT ||--o{ SESSION : has
    STUDENT ||--o{ CONSENT : grants
    STUDENT ||--o{ MEMORY_ITEM : owns
    SESSION ||--o{ TURN : contains
    TURN ||--|| MOOD_POINT : produces
    TURN ||--|| FIDELITY_SCORE : scored_by
    TURN ||--o{ ESCALATION : may_trigger
    STUDENT ||--o{ PROGRESS_SNAPSHOT : accumulates

    STUDENT {
        int id PK
        string pseudonym
        date created_at
    }
    CONSENT {
        int id PK
        string scope
        bool granted
        date changed_at
    }
    SESSION {
        int id PK
        int student_id FK
        datetime started_at
    }
    TURN {
        int id PK
        int session_id FK
        text student_text_redacted
        text reply
        int regeneration_count
        float latency_ms
    }
    MOOD_POINT {
        int id PK
        int turn_id FK
        string primary_emotion
        float distress_score
        json full_distribution
    }
    FIDELITY_SCORE {
        int id PK
        int turn_id FK
        float acceptance
        float defusion
        float present_moment
        float self_as_context
        float values
        float committed_action
        bool passed
        string drift_type
    }
    ESCALATION {
        int id PK
        int turn_id FK
        float risk_score
        string action_taken
        datetime at
    }
    MEMORY_ITEM {
        int id PK
        int student_id FK
        text content
        string scope
        bool student_deletable
    }
    PROGRESS_SNAPSHOT {
        int id PK
        int student_id FK
        date week
        float avg_distress
        json themes
    }
```

---

## 4 · Semester timeline

```mermaid
gantt
    title ZenAI — Sep 30 to Dec 3
    dateFormat YYYY-MM-DD
    axisFormat %b %d

    section Foundation
    Repo, Docker, schema, CI        :m0, 2026-09-30, 5d
    Agent contracts frozen          :milestone, 2026-10-04, 0d

    section Models (the midterm)
    Data prep, GoEmotions + ED      :2026-10-04, 4d
    Distress classifier             :2026-10-06, 5d
    Crisis classifier (recall)      :crit, 2026-10-06, 6d
    Eval harness + metrics          :2026-10-10, 3d
    MIDTERM PRESENTATION            :milestone, crit, 2026-10-15, 0d

    section Conversation and fidelity
    ACT protocol + Conversation     :2026-10-16, 8d
    Fidelity Monitor                :crit, 2026-10-20, 8d
    Drift experiment E1             :2026-10-28, 5d
    PROGRESS REPORT 3               :milestone, crit, 2026-11-05, 0d

    section Product
    Specialist agents               :2026-11-05, 8d
    Memory, Privacy, Progress       :2026-11-08, 8d
    Front end (Figma to React)      :2026-11-14, 10d

    section Close
    Evidence, report, README        :2026-11-24, 7d
    Rehearsal                       :2026-12-01, 2d
    FINAL PRESENTATION              :milestone, crit, 2026-12-03, 0d
```
