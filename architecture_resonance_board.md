# Architecture Resonance Board – E-Commerce Django Project

## High-Level Architecture

- **Presentation Layer:** Django Templates + Bootstrap 5 (UI, forms, pages)
- **Business Logic Layer:** Django Views + Service functions (cart, order processing, validation)
- **Data Layer:** Django Models & ORM (queries, relationships)
- **Persistence Layer:** MariaDB (XAMPP) via PyMySQL

**User Flow:**  
Browser → URL → View → Model/Service → DB → Rendered Template

---

## Risks & Mitigations

1. **Stock Concurrency / Overselling**  
   - *Risk:* Two users purchase last items at same time, causing negative stock.
   - *Mitigation:* Use @transaction.atomic and select_for_update() in checkout to lock product rows and ensure atomic updates.

2. **AI Hallucination in Code Generation**
   - *Risk:* LLM creates invalid or insecure Django code (bad fields, logic bugs, unsafe auth).
   - *Mitigation:* Mandatory mental execution (manual, line-by-line logic review), maintain ME.log.md for suspected LLM errors, commit refactorings as [ME].

3. **Cart & Session Security (Unauthenticated Users)**
   - *Risk:* Session hijack or expiry leads to cart loss or tampering.
   - *Mitigation:* Use Django’s secure session framework, enable SESSION_COOKIE_SECURE & HTTPS for prod, merge/anonymize cart on login, expire sessions properly.

4. **Image/File Upload Security (future)**
   - *Risk:* Malicious or huge file uploads could exploit server or eat space.
   - *Mitigation:* Validate file type/size, use Django FileField with proper validators and storage settings.

---

## Key Decisions

- Use Django 4.2.16 for MariaDB 10.4 compatibility (due to Windows/XAMPP dev environment)
- PyMySQL as DB backend (works on Windows/XAMPP)
- Mental execution and curation is required for all LLM-generated code; any “template” or boilerplate must be verified
- Use “ME.log.md” to note and correct any hallucinated or suspicious lines

---
# Architecture Resonance Board – E-Commerce Project

## High-Level Architecture
- Presentation: Django Templates + Bootstrap
- Business Logic: Views + Services
- Data Access: Models + ORM
- Persistence: MariaDB (XAMPP) via PyMySQL

## Risks (≥3)
1. Race condition on stock → overselling
   Mitigation: @transaction.atomic on checkout
2. AI hallucinations in generated code
   Mitigation: Mental execution + ME.log.md + [ME] commits
3. Anonymous cart lost on session expiry
   Mitigation: Merge session to DB cart on login

## Decisions
- Django 4.2.16 for MariaDB 10.4 compatibility
- PyMySQL for Windows install ease

Next: Product detail view