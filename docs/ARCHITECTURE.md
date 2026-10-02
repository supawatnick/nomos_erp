# Architecture

## Context
NOMOS ERP is a multi-tenant SaaS ERP with two primary interaction channels: Web and LINE.

```
Web App ----\
             -> FastAPI -> Application Services -> Domain -> PostgreSQL
LINE Webhook-/
                         -> Queue/Workers (async work)
                         -> Audit/Event Log
```

## Boundaries
- Presentation: Next.js UI, LINE webhook/message formatting
- Application: use cases, transactions, authorization orchestration
- Domain: inventory and ERP business rules
- Infrastructure: PostgreSQL, Redis, LINE adapters, observability

## Rule
No channel owns business logic. A receive-stock action from Web and LINE calls the same use case.

## Deployment
Start with Docker Compose. Keep services stateless where possible so deployment can move to Kubernetes without redesigning business logic.
