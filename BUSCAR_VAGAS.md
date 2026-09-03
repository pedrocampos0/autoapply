# BUSCAR_VAGAS.md

## Skill Name

`BUSCAR_VAGAS`

## Purpose

Run the complete **AutoApply job-search and Gmail reporting workflow**.

The skill must:
- Search for current jobs matching the candidate profile.
- Prioritize remote opportunities compatible with a candidate based in Brazil.
- Estimate compatibility.
- Enforce hard exclusions.
- Deduplicate against every previous AutoApply report.
- Report **only genuinely new vacancies**.
- Keep confirmed applications separate from jobs that were only discovered.
- Generate a concise report with direct job links.
- Deliver the report through Gmail when explicitly requested.

Accuracy is more important than volume.

---

# 1. Target Roles

Prioritize:
- Senior Software Engineer
- Senior Full Stack Engineer
- Senior Full-Stack Developer
- Senior Backend Engineer
- Senior Python Engineer
- Senior TypeScript Engineer
- Senior Node.js Engineer
- Senior React Engineer
- Senior AI Engineer
- Senior Applied AI Engineer
- Senior Generative AI Engineer
- Senior LLM Engineer
- Senior AI Software Engineer
- AI Application Engineer
- AI Platform Engineer
- Software Engineer, AI
- Software Engineer, GenAI
- Software Engineer, LLM
- Staff Software Engineer
- Staff Backend Engineer
- Staff Full Stack Engineer
- Lead Software Engineer when strongly hands-on
- Principal Software Engineer when technically compatible
- Forward Deployed Engineer / Solutions Engineer only when primarily software-engineering focused

Avoid roles that are mainly people management.

---

# 2. Candidate Defaults

Use these defaults:
- **Location:** Brazil
- **English:** C1 / Advanced
- **Availability:** Can start within 7 days
- **Preferred model:** Remote
- **Target seniority:** Senior+
- **Contractor / PJ minimum:** USD 4,000/month
- **Annual contractor equivalent:** approximately USD 48,000/year
- **Brazil CLT reference floor:** BRL 20,000 gross/month

Rules:
- If the published salary floor is higher than the default, use the higher published floor.
- Do not reject a strong job only because compensation is unpublished.
- Reject explicitly under-floor compensation unless there is an exceptional documented reason.

---

# 3. Priority Technical Stack

## Core
- Python
- TypeScript
- JavaScript
- Node.js
- React
- AWS
- PostgreSQL
- REST APIs
- Distributed systems
- Microservices
- Docker
- Kubernetes
- CI/CD

## AI / GenAI
Give strong positive weight to:
- LLMs
- Generative AI
- RAG
- LangChain
- LangGraph
- OpenAI APIs
- Anthropic / Claude
- Mistral
- Gemini
- Vector databases
- Embeddings
- Semantic search
- Agentic workflows
- AI agents
- Prompt engineering
- AI automation
- OCR / Document AI
- LLM evaluation
- Production AI pipelines

## AWS
Positive signals:
- EKS
- Lambda
- SQS
- SNS
- ECS
- EC2
- RDS
- Aurora PostgreSQL
- S3
- CloudWatch
- IAM
- EventBridge

## Frontend
Positive signals:
- React
- TypeScript
- Next.js
- Modern frontend architecture
- Component-driven development
- REST / GraphQL integration

---

# 4. Geographic Eligibility

The candidate is based in **Brazil**.

## Strongly preferred
- Remote Brazil
- Brazil remote
- Remote LATAM
- Latin America remote
- Remote Americas when Brazil is accepted
- Worldwide remote
- Global remote
- Anywhere
- Work from anywhere
- International contractor
- Global contractor
- EOR compatible with Brazil
- International hiring explicitly including Brazil

## Potentially acceptable
A role may remain eligible when:
- The company is based in the US, Canada, or Europe but hires globally.
- The role clearly states worldwide/international remote hiring.
- The employer uses a contractor model compatible with international candidates.

## Reject
- US-only residence
- US work authorization required with no international option
- Canada-only
- EU-only / Europe-only when Brazil is excluded
- UK-only
- Mandatory relocation outside Brazil
- Hybrid or on-site attendance outside Brazil
- Incompatible security clearance
- Incompatible citizenship requirement
- Timezone/location restriction that clearly excludes Brazil

For city-specific jobs inside Brazil, verify that the city/location requirement is actually compatible.

---

# 5. Mandatory Search Sources

Search broadly across:

1. Micro1 Talent Jobs
2. GitHub `backend-br/vagas` Issues
3. Combine Global Recruitment
4. Indeed Brasil
5. PowerToFly
6. We Work Remotely
7. Wellfound
8. Remotive
9. FlexJobs
10. Working Nomads
11. NoDesk
12. LinkedIn Jobs via web search
13. Remote OK
14. Himalayas
15. Jobgether
16. Arc.dev

Also search direct company and ATS pages:
- Company Careers pages
- Lever
- Greenhouse
- Ashby
- Workable
- SmartRecruiters
- Workday when indexable
- BambooHR when indexable
- Recruitee
- Jobvite

When an aggregator and the employer both list the same role, prefer the **official employer page** as canonical.

---

# 6. Search Query Strategy

Use multiple query variants. Examples:

- `"Senior Software Engineer" Python React remote Brazil`
- `"Senior Software Engineer" Python AWS remote LATAM`
- `"Senior Full Stack Engineer" Python TypeScript remote LATAM`
- `"Senior Full Stack Engineer" React Node.js Brazil`
- `"Senior Backend Engineer" Python AWS remote`
- `"Senior Python Engineer" remote Brazil`
- `"Senior Python Engineer" remote LATAM`
- `"Senior AI Engineer" LLM remote LATAM`
- `"Generative AI Engineer" Python remote Brazil`
- `"Applied AI Engineer" remote Americas`
- `"LLM Engineer" Python RAG remote`
- `"Software Engineer AI" Python React remote`
- `"Senior Node.js Engineer" remote LATAM`
- `"Senior TypeScript Engineer" remote Brazil`
- `"Staff Software Engineer" Python remote LATAM`
- `"Full Stack Engineer" React Python AWS remote`
- `"Backend Engineer" Python PostgreSQL AWS remote Brazil`
- `"LangChain" engineer remote`
- `"RAG" Python engineer remote`
- `"AI Engineer" Python LLM Brazil`
- `"Software Engineer" LangGraph remote`

Rotate geography/employment keywords:
- Brazil
- Brasil
- LATAM
- Latin America
- Americas
- worldwide
- global
- anywhere
- remote
- international
- contractor
- global contractor
- work from anywhere

Search title variants because equivalent jobs often use different titles.

---

# 7. Recency Rules

Prioritize:
1. Last 24 hours
2. Last 3 days
3. Last 7 days
4. Last 14 days
5. Up to 30 days only when still clearly open and highly compatible

Check when available:
- Publication date
- Update date
- Application status
- Whether the page still exists
- Whether applications are still accepted

Reject:
- Expired jobs
- Removed jobs
- Closed jobs
- Broken/dead application pages
- Old generic talent pools masquerading as active vacancies

---

# 8. Hard Exclusions

Exclude if:
- Estimated compatibility is below 55%.
- Academic transcript is mandatory.
- Detailed academic history/transcript is a mandatory application artifact.
- Brazil is not eligible.
- Local work authorization is incompatible.
- Mandatory relocation outside Brazil is required.
- Hybrid/on-site presence outside Brazil is required.
- Role is internship or junior.
- Role is closed/removed.
- Published compensation is below the applicable floor.
- Listing is only a generic talent pool.
- Listing appears to be spam or cannot be verified.
- Role is primarily mobile, embedded, firmware, hardware, or game development with poor overlap.
- Role is primarily BI/reporting/data analyst.
- Role is pure academic/research data science with insufficient software engineering.
- Role is primarily management rather than hands-on engineering.
- Required stack is substantially incompatible.

Known exclusion:
- Do not include **Sezzle Senior Software Engineer (Brazil)** while its academic transcript requirement remains mandatory.

---

# 9. Match Threshold

Only report:

`MATCH >= 55%`

The percentage must reflect the complete vacancy, not title similarity alone.

---

# 10. Suggested Match Scoring

## Core technical stack — 35
- Python: +8
- TypeScript / JavaScript: +5
- Node.js: +5
- React: +5
- AWS: +5
- PostgreSQL / SQL: +3
- Docker / Kubernetes: +2
- APIs / Microservices / Distributed Systems: +2

## AI / LLM alignment — 15
- LLM / GenAI: +5
- RAG: +3
- LangChain / LangGraph: +2
- Agents / agentic workflows: +2
- OpenAI / Anthropic / Mistral / Gemini: +1
- Vector DB / embeddings: +1
- OCR / document AI / AI automation: +1

## Seniority and scope — 15
- Senior clearly aligned: +10
- Staff/Lead/Principal technical fit: up to +10
- Architecture / ownership: +3
- Technical mentoring: +2

## Location/hiring compatibility — 20
- Brazil explicitly accepted: +20
- LATAM: +18
- Worldwide/global: +18
- Americas with Brazil accepted: +16
- Credible international contractor compatibility: +15

## Domain/responsibility fit — 10
Positive examples:
- Backend/API ownership
- Full-stack product engineering
- Cloud architecture
- Distributed systems
- AI product engineering
- Automation
- Production LLM systems
- Document processing
- Technical ownership

## Compensation — 5
- Clearly above target: full points
- At target: positive
- Unknown: neutral
- Explicitly below floor: reject

Normalize final score to 100%.

---

# 11. Qualitative Review

Before inclusion, verify:
1. Important must-have requirements are reasonably met.
2. Missing skills are secondary/learnable.
3. Seniority is realistic.
4. Brazil is eligible.
5. Remote model is compatible.
6. Compensation is acceptable or unknown.
7. Vacancy is active.
8. No mandatory transcript exists.
9. Vacancy never appeared in a previous AutoApply report.
10. Role meaningfully uses the candidate's strongest stack.

A role must pass both quantitative and qualitative review.

---

# 12. Mandatory Deduplication

The report must contain **only vacancies never shown in any prior AutoApply report**.

Before every report:
1. Retrieve/search prior AutoApply reports.
2. Build a historical job index.
3. Compare every new discovery to history.
4. Remove every previously reported vacancy even if still active.
5. Never recycle old jobs because the current search produced few results.

## Primary identity
Use:

`normalized_company + normalized_job_title + canonical_url_or_job_id`

Also compare:
- Employer ATS job ID
- Lever requisition ID
- Greenhouse job ID
- Ashby job ID
- LinkedIn job ID
- Original careers URL
- Source job ID

## Fuzzy duplicates
Treat as duplicate when:
- Same company and essentially same title.
- Aggregator redirects to the same employer application.
- URLs differ only by tracking parameters.
- Same description appears across several boards.
- Job ID is identical.
- Canonical employer posting is identical.

Strip common tracking parameters such as:
- `utm_source`
- `utm_medium`
- `utm_campaign`
- `utm_content`
- `utm_term`
- Non-identifying referral tokens

A repost is not automatically new. Require evidence of a genuinely new requisition or materially different role.

---

# 13. Gmail Is Part of Search History

Previous AutoApply Gmail reports are part of deduplication history.

Before generating a new report, search Gmail using terms such as:
- `AutoApply`
- `"AutoApply" report`
- `"job report"`
- `"vagas"`
- Prior report subject conventions
- Company names or job IDs when validating a suspected duplicate

Inspect enough messages to determine whether the company/title/URL/job ID has already been reported.

Do not rely only on the current chat when Gmail contains older reports.

---

# 14. Canonical Internal Job Record

Normalize each candidate vacancy into:

```text
company:
title:
canonical_title:
location:
remote_scope:
employment_type:
salary:
currency:
salary_period:
source:
source_url:
canonical_url:
job_id:
published_date:
last_verified_date:
technologies:
ai_keywords:
must_have_requirements:
nice_to_have_requirements:
transcript_required:
brazil_eligible:
active:
match_score:
match_reason:
duplicate:
duplicate_reference:
application_status:
application_confirmation:
```

---

# 15. Application Status Integrity

Never state that an application was submitted without **verifiable confirmation**.

Acceptable evidence:
- Submission success page
- Confirmation email
- ATS explicitly showing submitted/applied
- Another unambiguous confirmation

Do not infer submission only because:
- Form was opened
- Fields were filled
- Resume was uploaded
- Submit button was clicked without confirmation
- Browser interaction appeared to finish

Recommended statuses:
- `CONFIRMED_APPLIED`
- `ACTIVE_NOT_APPLIED`
- `APPLICATION_STARTED_NOT_CONFIRMED`
- `INCOMPATIBLE`
- `CLOSED`
- `DUPLICATE_PREVIOUS_REPORT`

---

# 16. Report Inclusion Policy

The primary report includes only **new eligible jobs**:
- Active
- Brazil-compatible
- Match >=55%
- Not excluded
- Never previously reported

Keep confirmed applications separate from active jobs without confirmed submission.

Do not include in the main list:
- Previously reported jobs
- Closed jobs
- Incompatible jobs
- Jobs below 55%
- Transcript-required jobs

A diagnostics summary may include exclusion counts.

---

# 17. Recommended Email Report

```markdown
# AutoApply Job Report — YYYY-MM-DD

Search completed: YYYY-MM-DD HH:MM America/Sao_Paulo

## Summary
- New eligible jobs: X
- Confirmed applications: X
- Active jobs not confirmed as applied: X
- Duplicates removed: X
- Incompatible / closed jobs filtered: X

## New Eligible Jobs

### 1. Company — Role
- Match: XX%
- Location: ...
- Remote eligibility: ...
- Employment type: ...
- Compensation: ...
- Main stack: ...
- Why it matches: ...
- Status: ACTIVE_NOT_APPLIED / CONFIRMED_APPLIED
- Source: ...
- Direct job link: ...

## Confirmed Applications
Only include applications with verifiable submission confirmation.

## Notes
- Jobs requiring academic transcripts were excluded.
- Previously reported vacancies were removed.
- Only jobs with estimated compatibility >=55% were retained.
```

If there are no new eligible jobs, **do not repeat old jobs**.

Use a short zero-result report:

```markdown
# AutoApply Job Report — YYYY-MM-DD

No new eligible vacancies were found in this search cycle.

Previously reported jobs were excluded.

Filters applied:
- Brazil-compatible remote roles
- Senior Software Engineering / Full Stack / Backend / AI
- Match >=55%
- No mandatory academic transcript
- Compensation constraints when published
```

---

# 18. Required Fields Per Reported Job

Whenever available:
- Company
- Role
- Match %
- Location
- Remote scope
- Employment type
- Compensation
- Relevant technologies
- Main responsibilities
- Key requirements
- Short match explanation
- Source
- Direct canonical URL
- Publication date
- Application status

Keep the report concise and easy to scan.

---

# 19. Source Validation

For each vacancy:
1. Prefer official company page.
2. Find canonical employer page when discovered through an aggregator.
3. Verify application URL works.
4. Confirm title and company.
5. Check location restrictions.
6. Check mandatory requirements.
7. Search for transcript/academic-history requirements.
8. Check compensation when published.
9. Check active status.
10. Deduplicate before reporting.

Never invent:
- Salary
- Location eligibility
- Job ID
- Application status
- Technologies
- Submission confirmation

Unknown information must remain `unknown`.

---

# 20. Search Breadth vs Precision

Search broadly and report narrowly.

Desired behavior:
- High recall in discovery
- High precision in final filtering
- Strict deduplication
- Strict eligibility verification
- Concise final report

If 100 listings are discovered and 3 pass all rules, report 3.

If zero pass, report zero.

Never lower the 55% threshold to fill the report.

---

# 21. Gmail Delivery Workflow

When the user explicitly asks to deliver the report via Gmail:

1. Determine the recipient from explicit user instructions or established AutoApply Gmail history.
2. **Never invent an email address.**
3. Generate the report before sending.
4. Preferred subject: `AutoApply Job Report — YYYY-MM-DD`
5. Preserve direct clickable job links.
6. Keep the summary at the top.
7. Use compact sections for each vacancy.
8. If the user asks to review first, create a Gmail draft.
9. If the user explicitly asks to send now, send through Gmail.
10. Only state that the email was sent after Gmail confirms success.
11. If Gmail fails, report the failure accurately.
12. Search/read historical Gmail reports first whenever needed for deduplication.

Preferred subject alternatives:
- `AutoApply — New Job Opportunities — YYYY-MM-DD`
- `AutoApply Job Report — YYYY-MM-DD — Rerun`

Never use a subject implying completed applications unless submission was actually confirmed.

---

# 22. Gmail Quality Rules

The email must:
- Be readable on desktop and mobile.
- Put the most important information first.
- Include direct URLs.
- Avoid excessive prose.
- Clearly separate confirmed applications from unsubmitted opportunities.
- Never present a duplicate as new.
- Never present an incompatible vacancy as recommended.
- Clearly state when there are zero new jobs.
- Never claim successful application without proof.

---

# 23. Optional Per-Vacancy Application Package

When application materials are requested, one folder per vacancy may contain:
- Tailored CV/resume
- English cover letter
- `JOB_INFO.txt`

Suggested `JOB_INFO.txt`:

```text
Company:
Role:
Job URL:
Source:
Location:
Remote eligibility:
Employment type:
Compensation:
Match score:
Key technologies:
Important requirements:
Application status:
Application confirmation:
Notes:
```

This package is separate from the Gmail report unless attachments are explicitly requested.

---

# 24. Resume and Cover Letter Rules

When generating application materials:
- Tailor them to the vacancy.
- Keep every factual claim grounded in the real resume/experience.
- Emphasize Python, TypeScript, Node.js, React, AWS, PostgreSQL, AI/LLM, RAG, LangChain, cloud, distributed systems, APIs, automation, and production engineering when relevant.
- Use English for international applications unless Portuguese is clearly required.
- Never fabricate technologies, employers, achievements, education, or certifications.

---

# 25. Preferred Execution Order

## Phase 1 — Load History
- Search prior AutoApply reports.
- Search Gmail history when reports were emailed.
- Extract company/title/URL/job IDs.
- Build the deduplication index.

## Phase 2 — Broad Discovery
Search:
- Remote job boards
- LATAM/Brazil boards
- LinkedIn web-indexed listings
- GitHub communities
- Recruiting platforms
- Direct ATS/company career pages

## Phase 3 — Normalize
Create canonical job records.

## Phase 4 — Remove Obvious Failures
Remove:
- Closed
- Location-incompatible
- Junior/intern
- Transcript-required
- Compensation-below-floor
- Obvious duplicates

## Phase 5 — Match Scoring
Calculate compatibility and reject below 55%.

## Phase 6 — Deep Verification
For remaining jobs:
- Open original listing
- Confirm location
- Confirm active status
- Confirm important requirements
- Confirm URL
- Confirm salary when present
- Confirm no transcript requirement

## Phase 7 — Historical Deduplication
Run final duplicate checks against all previous reports.

## Phase 8 — Application Status
Separate:
- Confirmed applied
- Active/not confirmed
- Application started but not confirmed

## Phase 9 — Generate Report
Report only new eligible vacancies.

## Phase 10 — Gmail Delivery
Draft or send according to the user's instruction.

---

# 26. Decision Rules

- If `match < 55%` → exclude.
- If academic transcript is mandatory → exclude.
- If Brazil is not eligible → exclude.
- If closed/expired → exclude.
- If explicit compensation is below floor → exclude.
- If previously present in any AutoApply report → exclude from new-jobs report.
- If submission is not verifiably confirmed → do not mark as applied.
- If no new jobs pass → send a zero-new-jobs report.
- If board listing and employer listing are the same role → prefer employer canonical URL.
- If information is uncertain → mark it unknown; never guess.

---

# 27. Internal Run Metrics

Retain when possible:
- Sources searched
- Search timestamp
- Raw discoveries
- Duplicates removed
- Excluded by location
- Excluded by compensation
- Excluded by transcript
- Excluded by compatibility
- Closed/expired count
- New eligible vacancies
- Confirmed applications

These may be summarized in the report.

---

# 28. Final Quality Checklist

Before delivery verify:

- [ ] Every reported job is active.
- [ ] Every job is compatible with a Brazil-based candidate.
- [ ] Every job has match >=55%.
- [ ] No job requires a mandatory academic transcript.
- [ ] No job is knowingly below the compensation floor.
- [ ] No job appeared in a previous AutoApply report.
- [ ] Aggregator duplicates were collapsed.
- [ ] Official employer URLs were preferred where available.
- [ ] Every job link is correct.
- [ ] No unconfirmed application is marked submitted.
- [ ] Confirmed applications are separated from active opportunities.
- [ ] Report contains only genuinely new opportunities.
- [ ] Gmail recipient was not guessed.
- [ ] Email is only reported as sent after Gmail confirms success.

---

# 29. Operating Priority

Use this priority order:

1. **Eligibility**
2. **Newness**
3. **Technical fit**
4. **Location compatibility**
5. **Compensation**
6. **Recency**
7. **Source reliability**
8. **Actionability**

Optimize for useful, genuinely new opportunities rather than volume.

---

# 30. Compact Execution Prompt

> Execute a complete AutoApply search round. Find current remote jobs or jobs compatible with a candidate based in Brazil for Senior Software Engineer, Full Stack, Backend, AI Engineer, and closely related positions. Prioritize Python, TypeScript/Node.js, React, AWS, AI/LLMs/RAG/LangChain and related production engineering technologies. Search the standard AutoApply sources plus direct company careers/Lever/Greenhouse/Ashby pages. Include only jobs with estimated compatibility of at least 55%. Exclude roles requiring academic transcripts, incompatible residence/work authorization, expired/closed jobs, incompatible roles, and compensation explicitly below the applicable floor. Check all previous AutoApply reports, including relevant Gmail history, and report only vacancies that have never appeared before, using company + title + canonical URL/job ID plus fuzzy matching to prevent duplicates. Never mark an application as submitted without verifiable confirmation. Generate a concise report with direct links, separating confirmed applications from active jobs without confirmed submission. If there are no new eligible jobs, produce a short zero-new-jobs report without repeating old vacancies. When explicitly requested, deliver the report via Gmail using the established recipient/history and only claim success after Gmail confirms delivery.
