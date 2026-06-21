# System Architecture

AI-SlowMatch is a prototype architecture. The current implementation is a minimal FastAPI backend with deterministic services and a mock AI provider. A frontend is intentionally deferred to Phase 3 under `apps/web` so the safety model and API contracts can stabilize first.

## High-Level System Diagram

```mermaid
flowchart TB
    User["User"]
    API["FastAPI API"]
    Consent["ConsentManager"]
    Safety["SafetyPolicy"]
    Risk["ScamRiskAnalyzer"]
    Ladder["TrustLadderEngine"]
    Journal["JournalSummarizer"]
    AI["LLMClient interface"]
    Mock["MockAIProvider"]
    Docs["Education and governance docs"]

    User --> API
    API --> Consent
    API --> Safety
    API --> Risk
    API --> Ladder
    API --> Journal
    Risk --> AI
    Journal --> AI
    AI --> Mock
    User --> Docs
```

## Data Flow Diagram

```mermaid
flowchart LR
    Input["Submitted text or journal events"]
    ConsentCheck["Explicit consent check"]
    SafetyCheck["Abuse-request safety check"]
    Analyzer["Risk, ladder, or journal service"]
    Response["Uncertainty-aware response"]
    Retention["No database in Phase 0-2"]

    Input --> ConsentCheck
    ConsentCheck --> SafetyCheck
    SafetyCheck --> Analyzer
    Analyzer --> Response
    Analyzer -. "future storage only with explicit retention policy" .-> Retention
```

## Trust Ladder State Machine

```mermaid
stateDiagram-v2
    [*] --> UNKNOWN_STRANGER
    UNKNOWN_STRANGER --> LOW_PRESSURE_CHAT: low-pressure conversation
    LOW_PRESSURE_CHAT --> REPEATED_CONSISTENT_INTERACTION: repeated normal interaction
    REPEATED_CONSISTENT_INTERACTION --> BOUNDARY_RESPECT_VERIFIED: boundaries respected and identity checked
    BOUNDARY_RESPECT_VERIFIED --> SAFETY_CHECKED_OFFLINE_MEETING: safety checklist for public meeting
    SAFETY_CHECKED_OFFLINE_MEETING --> DEEPER_RELATIONSHIP_EXPLORATION: slow mutual discussion

    LOW_PRESSURE_CHAT --> UNKNOWN_STRANGER: high-risk signal
    REPEATED_CONSISTENT_INTERACTION --> LOW_PRESSURE_CHAT: boundary pressure
    BOUNDARY_RESPECT_VERIFIED --> LOW_PRESSURE_CHAT: inconsistent verification
```

## AI Risk-Analysis Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant A as FastAPI
    participant C as ConsentManager
    participant S as SafetyPolicy
    participant R as ScamRiskAnalyzer
    participant L as LLMClient
    participant M as MockAIProvider

    U->>A: POST /risk/analyze
    A->>C: ensure consent
    C-->>A: allowed
    A->>S: block abuse requests
    S-->>A: allowed
    A->>R: analyze conversation
    R->>L: generate_structured
    L->>M: mock response
    M-->>L: deterministic output
    R-->>A: risk signals and next steps
    A-->>U: non-accusatory risk-support response
```

## Frontend Plan

No frontend is created in this phase. A future `apps/web` dashboard should be small and utilitarian:

- paste conversation text;
- show risk signals, uncertainty, and next steps;
- show trust ladder stage and safety checklist;
- support local-only journal entries;
- expose delete/export controls before persistent storage is introduced.
