# Architecture Resonance Board - E-Commerce Django App

## High-Level Architecture
- Presentation Layer: Django Templates + Bootstrap 5 (UI, forms, pages)
- Application/Business Logic Layer: Views + Services (validation, cart logic, order processing)
- Data Access Layer: Django Models + ORM (queries, relationships)
- Persistence Layer: MariaDB (XAMPP) via PyMySQL

User flow example: Browser → URL → View → Service/Model → DB → Template render.

## Risks Identified (≥3 required)
1. **Stock concurrency / overselling**: Multiple users adding low-stock item to cart simultaneously could cause negative stock.
   Mitigation: Use database transactions (atomic) + optimistic locking on Product.stock.

2. **AI hallucinations in code generation**: LLM may generate incorrect DB fields, insecure auth, or broken flows.
   Mitigation: Mandatory mental execution + curator review on every non-template line; log hallucinations in ME.log.md.

3. **Session security for cart (unauthenticated users)**: Session hijacking or tampering.
   Mitigation: Use Django's secure session framework; enable HTTPS in prod; clear expired sessions.

4. **Image upload security** (if added later): Malicious files, large uploads.
   Mitigation: Validate file types/sizes, use Django's FileField with validators.

Next: Generate models.py spec → Cursor generates code → mental execution → commit [ME].


# Architecture Resonance Board - E-Commerce Django Project

## High-Level Architecture
- Presentation: Templates + Bootstrap (UI)
- Business Logic: Views + Services (cart, order calc)
- Data Access: Models + ORM
- Persistence: XAMPP MariaDB via PyMySQL

Flow: URL → View → Model query → DB → Template

## Risks (≥3)
1. Stock race condition → overselling
   Mitigation: @transaction.atomic on checkout
2. AI hallucinations in code
   Mitigation: Mental execution + ME.log.md + [ME] commits
3. Anonymous cart loss on session expiry
   Mitigation: Merge session to DB on login

## Decisions
- Django 4.2.16 for MariaDB 10.4 compatibility
- PyMySQL for Windows ease