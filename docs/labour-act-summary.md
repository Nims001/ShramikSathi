# The Labour Act, 2017 (2074) — Structured Summary for App Design

*Organized by violation-detection category rather than strictly by chapter, so it maps onto what your app needs to check. Section numbers refer to the original Act — cite these back to users when flagging a violation.*

---

## 1. Who the Act Covers

- **Labour**: anyone doing physical or intellectual work for an employer, under any job title (§2x).
- **Employer**: any person/enterprise employing labour — includes managers and labour suppliers (§2m).
- **Excluded**: Nepal Army, Police, Armed Police, National Investigation Department; civil servants (governed separately) (§180).
- **Apprentices/trainees** (Ch. 4) are *not* counted as "labour" unless the apprenticeship deviates from the approved curriculum — worth flagging, since this is a common misclassification trick.

### Employment types (§10) — first thing your app should ask
| Type | Definition |
|---|---|
| Regular | Anything not in the categories below |
| Work-based | Tied to a specific task |
| Time-based | Tied to a fixed period |
| Casual | ≤7 days of work within one month |
| Part-time | ≤35 hours/week |

Misclassifying a regular worker as "casual" or "part-time" to dodge benefits is a realistic violation pattern to detect.

---

## 2. Working Hours & Overtime (Ch. 7) — highly checkable

| Rule | Threshold | Section |
|---|---|---|
| Max daily hours | 8 hrs/day | §28(1) |
| Max weekly hours | 48 hrs/week | §28(1) |
| Mandatory rest | 30 min after 5 continuous hours | §28(2) |
| Max overtime | 4 hrs/day, 24 hrs/week | §30(1) |
| Overtime pay rate | 1.5× basic remuneration | §31(1) |
| Compelling overtime | Prohibited except to prevent serious harm/loss | §29 |
| Night transport for women | Required if shift starts before sunrise/after sunset | §33 |

**App logic**: if `hours_worked > 8/day or > 48/week` and `overtime_pay < 1.5× rate` → flag violation. If `weekly_overtime > 24` → flag separately (illegal even if paid).

---

## 3. Wages & Remuneration (Ch. 8)

| Rule | Detail | Section |
|---|---|---|
| Payment interval | Max 1 month between payments | §35(2) |
| Short-term/casual pay | Within 3 days of work completion (or immediately for casual) | §35(1) |
| Annual increment | ≥ half a day's remuneration per year after 1 year of service | §36 |
| Festival expense | 1 month's basic remuneration/year, proportional if <1 year served | §37 |
| Illegal deductions | Anything not in the §38(1) list (tax, PF, court order, agreed service costs, absence, proven loss/damage, collective agreement items, union fees, loan repayment) | §38 |
| Equal pay | No sex-based discrimination for equal-value work | §7 |
| Minimum wage | Set every 2 years by Ministry via Minimum Remuneration Fixation Committee | §106–107 |

**App logic**: any deduction not matching the §38(1) whitelist is a flaggable violation. This is a good concrete rule since the list is closed/enumerated.

---

## 4. Leave Entitlements (Ch. 9) — good for a "leave calculator" feature

| Leave type | Entitlement | Notes | Section |
|---|---|---|---|
| Weekly | 1 day/month min | | §40 |
| Public | 13 days/year (14 for women, incl. Intl Women Labour Day) | | §41 |
| Home leave | 1 day per 20 days worked | Accumulate up to 90 days | §43, §49 |
| Sick leave | 12 days/year, proportional if <1 yr | Medical certificate required if >3 consecutive days | §44 |
| Maternity | 14 weeks total | 2 wks before–6 wks after delivery compulsory; full pay only for 60 days | §45 |
| Paternity/maternity-care | 15 days paid | For male labour when wife delivers | §45(7) |
| Mourning | 13 days, full pay | Death of spouse/parent/parent-in-law etc. | §48 |
| Accumulated leave payout | Cash value on separation or death | | §49(2) |

**Right vs. facility**: sick, mourning, and maternity leave are *rights* (cannot be refused); all other leave is a "facility" the employer can withhold with stated reason (§51). Useful distinction for how urgently your app flags a denial.

---

## 5. Social Security — Provident Fund, Gratuity, Insurance (Ch. 10)

| Benefit | Employer/labour contribution | Section |
|---|---|---|
| Provident Fund | Employer deducts 10% of basic remuneration from labour + adds 10% employer match → deposits to Social Security Fund | §52 |
| Gratuity | 8.33% of basic remuneration/month, employer-funded | §53 |
| Medical insurance | Min. NPR 100,000/year, premium split pro rata | §54 |
| Accidental insurance | Min. NPR 700,000, fully employer-funded | §55 |

If employer fails to deposit PF/gratuity, they owe the labour an **equivalent cash amount** directly (§52(6), §53(6)) — good fallback rule for your detector when Social Security Fund isn't reachable.

---

## 6. Termination, Notice & Retrenchment (Ch. 21)

| Situation | Rule | Section |
|---|---|---|
| Notice period | 1 day (<4 wks employment) / 7 days (4wks–1yr) / 30 days (>1 yr) | §144 |
| No notice given | Employer owes pay equal to notice-period remuneration | §144(2) |
| Probation | Up to 6 months | §13 |
| Compulsory retirement | Age 58 (regular employment) | §147 |
| Retrenchment order | Foreign labour → most-punished → weakest performers → most recently hired, last | §145(5) |
| Retrenchment compensation | 1 month's basic pay per year of service (pro-rated if <1 yr) | §145(7) |
| Final settlement | All dues paid within 15 days of termination | §148 |
| Health-based termination protection | Cannot terminate during hospital treatment for work-related injury/disease; home treatment protected up to 1 year | §143 |

---

## 7. Discrimination, Harassment & Forced Labour (Ch. 2, §132)

- **Prohibited discrimination grounds**: religion, colour, sex, caste, tribe, origin, language, ideological conviction (§6). Exceptions: role-appropriate preference, easier work for pregnant workers (no pay cut), preference for disabled workers in suitable roles.
- **Forced labour**: prohibited outright (§4); penalty up to 2 years imprisonment / NPR 500,000 fine + double compensation (§164(1)).
- **Sexual harassment**: employer can dismiss the harasser; if employer/CEO is the harasser, victim/union/family can file directly (§132).
- **Child labour**: prohibited where contrary to law (§5) — note the Act itself doesn't set the minimum age (that's in separate child labour legislation — worth a note/disclaimer in your app).

---

## 8. Occupational Safety & Health (Ch. 12)

- Employers must formulate a safety & health policy (§68), form a **safety committee** if ≥20 labours (§74), and report any accident/injury/death immediately to the Labour Office (§79).
- Labour can refuse dangerous work and stop it unilaterally if immediate danger and no supervisor is reachable (§76).
- Retaliation against a worker for safety complaints, committee membership, or work-stoppage is explicitly barred (§75) — a "protected activity" flag worth building in.

---

## 9. Foreign Labour (Ch. 6) — if you support migrant workers

- Work permit required from the Department of Labour before hiring foreign labour (§22); employer must first advertise locally and show no qualified Nepali applicant.
- Employment contract with a foreign labour must be in a language they understand, or English (§25).
- Foreign labour can repatriate wages in convertible currency (§26).

---

## 10. Enforcement & Complaint Pathways — maps directly to your "legal recourse" feature

| Body | Role | Deadline to act |
|---|---|---|
| **Labour Office** | First point of contact; individual claims, mediation, inspection | Settle individual claim within 15–21 days (§113–115) |
| **Department of Labour** | Handles bigger fines (unlicensed labour suppliers, foreign labour, discrimination, missing contracts) | — |
| **Labour Court** | Appeals from Office/Department decisions; forced labour, injury/death cases | Appeal within 35 days (§165) |
| **Supreme Court** | Final appeal from Labour Court | Within 35 days (§161) |

**Filing routes for a labour**:
1. Written application to employer first (§113) → 15 days to respond.
2. If no response/no agreement → application to Labour Office for mediation (§114) → 21 days.
3. If unresolved → Office decides on the evidence (§115).
4. Appeal any decision to Labour Court within 35 days (§165).
5. General complaint deadline: **6 months from the date of the violation** (§162) — important to surface as a countdown in your app.

### Penalty quick-reference (Ch. 23, §163) — useful for a "what happens if I report this" screen
| Violation | Fine |
|---|---|
| Unlicensed labour supply / hiring through one | Up to NPR 200,000 |
| Foreign labour without permit | Up to NPR 200,000 + NPR 5,000/month ongoing |
| Discrimination in employment | Up to NPR 100,000 |
| No appointment letter/contract | Up to NPR 500,000 (NPR 10,000/labour) |
| Below-minimum wage or illegal deduction | Repay amount + up to 2× compensation |
| Forced labour (Labour Court) | Up to 2 yrs imprisonment / NPR 500,000 + 2× compensation |

---

## 11. Provisions Specific to Informal/Vulnerable Workers — directly relevant to your target users

- **Domestic labour** (§88): separate minimum wage can be set; food/shelter costs may be deducted from pay if provided by employer.
- **Construction labour** (§85): employer must provide tools, temporary housing if needed, clean water, safety gear.
- **Transport labour** (§86): overtime at 1.5× if >8 hrs/day; two-driver rule for long routes; no alcohol within 12 hrs of driving.
- **Seasonal enterprises** (§89): workers get 25% of remuneration during off-season closure.
- **Tea estate labour** (§84): quarters, first aid, and access to daily goods obligations.

These sector-specific chapters are probably your highest-value detection surface, since informal-sector workers (your stated target, per the ActionAid/NMES/Truth Advocacy study) cluster in construction, domestic work, and transport.

---

## 12. A Practical Note for Your App

The Act repeatedly says "as prescribed" (कानून द्वारा तोकिए बमोजिम) — meaning the *implementing Regulations*, not this Act itself, set exact procedures for many things (e.g., exact retrenchment notice formats, apprentice curriculum approval, domestic worker leave specifics). If you want bulletproof compliance flags, you may eventually need the **Labour Rules/Regulations** alongside this Act — the Act sets the floor, the Rules set the mechanics. Worth a caveat in your app's disclaimers ("this Act sets minimum standards; some procedural details are set by regulation").

Also worth building in explicitly: **§3(2)** — *any contract term below what this Act guarantees is automatically void to that extent*, regardless of what the worker signed. That's a strong, simple rule you can surface prominently: "even if your contract says otherwise, the law wins."

---

*Section numbers throughout refer to The Labour Act, 2017 (2074) as authenticated 4 September 2017.*
