# Future Features & Ideas

> **Last Updated:** November 24, 2025
> 
> **Purpose:** This document captures potential features for evaluation AFTER Month 10. These are NOT committed to the 12-month roadmap. We'll evaluate each based on client demand, ROI, and strategic value.
> 
> **Philosophy:** Capture ideas without scope creep. Stay focused on core bookkeeping/payroll.

---

## Status Key

- 🟢 **APPROVED:** Will build (moved to roadmap)
- 🟡 **CONSIDERING:** Evaluating value
- 🔴 **REJECTED:** Out of scope / Not worth it
- ⚪ **IDEA:** Captured for future review

---

## Portal Enhancements

### 🟡 Expense Claims System

**What:** Employees submit expenses via portal, employer approves, integrates with payroll

**Why:** Some clients process expense reimbursements through payroll

**Features:**
- Upload receipt (photo or file)
- AI extracts amount, date, category
- Employer approval workflow
- VAT reclaim calculation
- Integration with payroll

**Effort:** 4-5 days

**Decision Point:** Month 10 - Check if 3+ beta clients need this

**Questions to answer:**
- Do clients actually process expenses through payroll?
- Do they have existing expense systems (Expensify, etc.)?
- Is the build time worth it?
- Can they just email receipts instead?

**Notes:** Only build if genuine client need. Many businesses use dedicated expense software.

---

### 🟢 CSV Bulk Upload (Timesheets)

**What:** Employers upload timesheet data via CSV file instead of manual entry

**Why:** Clients with 10+ employees waste time on manual entry

**Features:**
- CSV template download
- Drag-and-drop upload
- Data validation (catches errors)
- Bulk import to system
- Error reporting

**Effort:** 2 days

**Decision:** APPROVED - Add to Month 8

**Priority:** High (big time saver for larger clients)

**Notes:** Absolutely worth building. Makes system scalable.

---

### ⚪ Advanced Pension Calculator

**What:** AI suggests optimal pension contributions with projections

**Why:** Unique value-add, helps employees, positions us as advisors

**Features:**
- Current vs. optimized comparison
- Retirement projection calculator
- Tax relief visualization
- "What if" scenarios
- Personalized recommendations

**Example:**
> "Bobby, increasing from 5% to 8% costs you only £18/month after tax relief, but adds £15,000 to your retirement pot. Worth it?"

**Effort:** 3-4 days

**Decision Point:** Month 11 - If time allows

**Priority:** Medium (nice differentiation, but not essential)

**Notes:** Could be a killer feature. Makes us look like financial advisors.

---

### 🔴 Staff Scheduling / Rotas

**What:** Shift scheduling, rota management, availability tracking

**Why:** Clients ask for it

**Effort:** 20+ days (complex domain)

**Decision:** REJECTED - Out of scope

**Reason:**
- Not bookkeeping/payroll (happens BEFORE payroll)
- Clients have better tools (Planday, Rota Cloud, Deputy)
- Complex domain (fairness, legality, rules)
- Maintenance nightmare
- Scope creep

**Alternative:** Integrate with existing scheduling tools (import approved hours)

**Notes:** This would turn us into HR software. Stay in our lane.

---

### ⚪ White-Label Portal Branding

**What:** Custom branding per client (colors, logo, domain)

**Why:** Premium service offering, professional appearance

**Features:**
- Client uploads logo
- Choose brand colors
- Custom domain (portal.clientname.com)
- Personalized emails
- White-label everything

**Effort:** 5-7 days

**Decision Point:** Month 12 or Year 2

**Priority:** Medium (premium tier differentiation)

**Pricing:** Charge £40-50/month extra for white-label

**Notes:** Good for premium tier. Not essential for launch.

---

### ⚪ Year-End Gamification

**What:** Fun, engaging summary of employee's financial year

**Why:** Employee engagement, differentiation, makes portal sticky

**Features:**
- "Your 2025 in Numbers" dashboard
- Earnings breakdown with visualizations
- Achievements/milestones
- Pension growth visualization
- Shareable summary (LinkedIn, optional)

**Example:**
> "🎉 2025 Achievements:
> - Earned £24,500
> - Saved £1,200 in pension
> - Zero sick days (healthy!)
> - Used all holiday (balanced!)
> 
> 🎯 2026 Goals:
> - Increase pension to 8%
> - Save £500 in tax optimization"

**Effort:** 3-4 days

**Decision Point:** Month 11 (if time allows)

**Priority:** Low (fun but not essential)

**Notes:** Could go viral. Employees might share on social media.

---

### ⚪ Interactive Payslip Walkthrough

**What:** First-time users get guided tour of their payslip

**Why:** Reduce "What does this mean?" questions

**Features:**
- Tooltip tour of payslip
- "Tap any item to learn more"
- Video explainers
- Quiz to test understanding
- Completion badge

**Effort:** 2-3 days

**Decision Point:** Month 11

**Priority:** Low-Medium (educational, nice touch)

**Notes:** Could reduce support questions significantly.

---

## AI Features

### 🟡 Fraud Detection

**What:** AI flags suspicious transactions automatically

**Why:** Protect clients, add value, demonstrate AI capability

**Features:**
- Pattern detection (unusual amounts, new suppliers)
- Duplicate invoice detection
- Velocity checks (too many similar transactions)
- Known fraud pattern matching
- Confidence scoring
- Alert employer immediately

**Example Alerts:**
> "⚠️ Potential fraud detected:
> £5,000 payment to new supplier 'Quick Services Ltd'
> - First transaction with this supplier
> - Amount 10x larger than typical
> - Supplier name matches common fraud pattern
> - Recommend: Verify before processing"

**Effort:** 5-7 days

**Decision Point:** Month 9-10 (if time allows)

**Priority:** High (valuable feature, not too complex)

**Notes:** This is a genuine differentiator. Could save clients thousands.

---

### ⚪ Smart Invoice Matching

**What:** Auto-match invoices to bank transactions

**Why:** Save massive reconciliation time

**Features:**
- AI matches invoice to transaction
- Handles partial payments
- Detects early payment discounts
- Flags mismatches
- Learns from corrections

**Effort:** 7-10 days (complex logic)

**Decision Point:** Year 2

**Priority:** Medium (good idea, but complex)

**Notes:** Xero/QB do some of this. Only build if we can do it BETTER.

---

### ⚪ Predictive Cash Flow

**What:** AI predicts cash flow issues before they happen

**Why:** Proactive service, valuable insights

**Features:**
- Analyze historical patterns
- Predict upcoming expenses
- Warn of low cash scenarios
- Suggest timing optimizations
- Seasonal adjustment predictions

**Example:**
> "⚠️ Cash Flow Warning:
> Based on historical patterns, you'll likely face a cash crunch in March:
> - Large VAT payment due (£8,500)
> - Typically low revenue month
> - Payroll still due (£12,000)
> 
> Suggestions:
> - Chase outstanding invoices now
> - Consider payment plan with HMRC
> - Delay non-essential purchases"

**Effort:** 10-15 days (needs historical data, complex)

**Decision Point:** Year 2 (need 12+ months data)

**Priority:** Low (complex, needs scale)

**Notes:** Amazing feature but needs lots of data to work well.

---

### ⚪ AI Tax Optimization Suggestions

**What:** AI suggests tax-saving opportunities

**Why:** High-value advisory service

**Features:**
- Scan transactions for missed deductions
- Suggest optimal expense timing
- Identify tax relief opportunities
- Compare entity structures
- Pension contribution optimization

**Example:**
> "💡 Tax Saving Opportunity:
> You've spent £2,400 on business equipment this year.
> 
> If you buy that £500 laptop you're considering BEFORE April 5th:
> - You can claim Annual Investment Allowance
> - Reduces taxable profit by £2,900
> - Saves ~£551 in corporation tax
> - Payback period: Immediate
> 
> Recommend: Purchase before year-end."

**Effort:** 15+ days (complex domain, liability concerns)

**Decision Point:** Year 2+ (need qualified tax expert oversight)

**Priority:** Low (high liability, need proper credentials)

**Notes:** This is accountant territory. Be careful about unauthorized tax advice.

---

## Employee Portal Features

### 🟡 Take-Home Calculator (Enhanced)

**What:** Interactive "what-if" calculator for employees

**Why:** Helps employees understand pay changes

**Features:**
- Slider: Adjust hours/salary
- Real-time take-home calculation
- Tax bracket visualization
- NI threshold impacts
- Pension contribution effects
- Student loan repayment impact

**Example:**
> "If you work 25 hours/week instead of 20:
> - Gross: +£280/month
> - Take home: +£229/month
> - Pension: +£14/month (you keep building retirement!)
> - Tax impact: Slight increase (still in basic rate)
> 
> Worth the extra 5 hours? You decide!"

**Effort:** 2-3 days

**Decision Point:** Month 9

**Priority:** Medium (good engagement feature)

**Notes:** Already planned for Month 9. Confirming it's valuable.

---

### ⚪ Financial Wellness Tools

**What:** Budget suggestions, savings tips, financial education

**Why:** Employee value-add, differentiation

**Features:**
- Budget calculator (50/30/20 rule)
- Savings goal tracker
- Debt payoff calculator
- Benefits eligibility checker
- Financial literacy content

**Example:**
> "💡 Based on your £1,680/month income:
> 
> Suggested Budget:
> - Essentials (50%): £840 (rent, bills, food)
> - Lifestyle (30%): £504 (fun, hobbies, eating out)
> - Savings (20%): £336 (emergency fund + goals)
> 
> You're already saving 5% in pension (£84).
> Try to save another £250/month for emergencies.
> 
> Goal: £3,000 emergency fund = 12 months away!"

**Effort:** 5-7 days

**Decision Point:** Year 2

**Priority:** Low (nice-to-have, not core)

**Notes:** Could partner with financial wellness apps instead of building.

---

### ⚪ Push Notifications (Mobile App)

**What:** Native mobile app with push notifications

**Why:** Better engagement than email

**Features:**
- "Payslip ready" notifications
- "Holiday request approved"
- "Tax code changed"
- "Important update from employer"
- Customizable notification preferences

**Effort:** 30+ days (full mobile app)

**Decision Point:** Year 2 (after web portal proven)

**Priority:** Low (need web portal solid first)

**Notes:** Huge undertaking. Only if web portal is massive success.

---

## Integrations

### 🟡 Slack Integration

**What:** Notifications and updates via Slack

**Why:** Some clients prefer Slack communication

**Features:**
- Payroll approval requests in Slack
- Employee notifications (optional)
- Quick responses via Slack
- Status updates
- Alert notifications

**Effort:** 2-3 days

**Decision Point:** Month 11 (if 3+ clients request)

**Priority:** Low-Medium (depends on demand)

**Notes:** Easy to build IF clients want it. Don't build speculatively.

---

### ⚪ WhatsApp Notifications

**What:** Send notifications via WhatsApp

**Why:** Better reach for some employees (higher open rate)

**Features:**
- Payslip ready notifications
- Holiday request updates
- Important reminders
- Opt-in only (GDPR compliant)
- Costs per message (WhatsApp Business API)

**Effort:** 3-4 days + ongoing API costs

**Decision Point:** Year 2

**Priority:** Low (cool but costs add up)

**Notes:** WhatsApp Business API has costs. Need to evaluate ROI.

---

### 🔴 Custom Inventory Sync

**What:** Sync inventory data, stock levels, ordering

**Why:** Client requested it

**Decision:** REJECTED

**Reason:**
- Xero and QuickBooks already do this well
- Complex domain (stock management, warehousing)
- Not bookkeeping/payroll related
- Reinventing the wheel
- Scope creep

**Alternative:** Use Xero/QB's inventory features. That's what they're for.

**Notes:** Don't compete with platforms you're integrating with.

---

### ⚪ Google Calendar Sync (Payroll Deadlines)

**What:** Auto-add payroll deadlines to employer's Google Calendar

**Why:** Helps employers remember important dates

**Features:**
- Payroll processing deadlines
- VAT return dates
- PAYE submission deadlines
- Year-end reminders
- Holiday deadline alerts
- Auto-updates if dates change

**Effort:** 2-3 days

**Decision Point:** Month 8-9 (fits well with holiday feature)

**Priority:** Medium (useful, not too complex)

**Notes:** We already planned basic calendar integration. This extends it.

---

## Business Features

### ⚪ Multi-Currency Support

**What:** Handle foreign currency payroll and transactions

**Why:** International clients or UK businesses with overseas employees

**Features:**
- Multi-currency payroll
- Exchange rate handling
- Foreign tax implications
- Reporting in GBP equivalent
- Multiple bank accounts

**Effort:** 10+ days (complex, many edge cases)

**Decision Point:** Only if actively needed

**Priority:** Very Low (UK-focused practice)

**Notes:** Complex. Only build if we specifically target international clients.

---

### ⚪ Multi-Entity Management

**What:** Manage multiple companies under one account

**Why:** Clients with multiple businesses

**Features:**
- Switch between entities easily
- Consolidated reporting
- Cross-entity insights
- Separate data security
- Group-level dashboards

**Effort:** 7-10 days

**Decision Point:** Year 2 (after single-entity perfect)

**Priority:** Medium (good for growth)

**Notes:** Some clients will have multiple businesses. Plan for it eventually.

---

### ⚪ Accountant Collaboration Tools

**What:** Let client's year-end accountant access system

**Why:** Smooth year-end process

**Features:**
- Read-only access for external accountant
- Export data in standard formats
- Audit trail access
- Commenting on transactions
- Year-end checklist

**Effort:** 5-7 days

**Decision Point:** Month 11-12 (before first year-end)

**Priority:** Medium (will be needed for year-end)

**Notes:** Useful. Many clients use separate accountants for year-end.

---

### 🟡 Client Onboarding Wizard

**What:** Step-by-step guided setup for new clients

**Why:** Reduce onboarding time, improve first impression

**Features:**
- Welcome walkthrough
- API connection setup
- Employee import
- Settings configuration
- Test payroll run
- Training videos
- Progress tracker

**Effort:** 4-5 days

**Decision Point:** Month 11 (before real clients)

**Priority:** High (first impression matters!)

**Notes:** Worth building. Makes us look professional and reduces support time.

---

## Platform Extensions

### ⚪ Sage Integration

**What:** Add Sage 50cloud as third platform

**Why:** 15% UK market share (total coverage: 110%)

**Effort:** 3-4 weeks (new platform adapter)

**Decision Point:** Year 2 (after Xero + QB proven)

**Priority:** Medium (good growth opportunity)

**Notes:** Follow same adapter pattern. Should be straightforward.

---

### ⚪ FreeAgent Integration

**What:** Add FreeAgent as fourth platform

**Why:** Popular with freelancers/small businesses in UK

**Effort:** 3-4 weeks

**Decision Point:** Year 2+

**Priority:** Low-Medium (nice to have)

**Notes:** Smaller market share but loyal user base.

---

### ⚪ Receipt Bank / Dext Integration

**What:** Import receipts from Receipt Bank/Dext

**Why:** Many clients already use these tools

**Effort:** 3-5 days (API integration)

**Decision Point:** Year 2 (if clients use it)

**Priority:** Low (only if demand exists)

**Notes:** We're building our own upload. Only integrate if clients insist.

---

## Ideas Parking Lot

Random ideas to evaluate someday (unfiltered):

- Voice input for expense submission
- Receipt scanning via phone camera (AR overlay)
- Automated payslip translation (for non-English employees)
- Employee referral program tracking
- Tax code change alerts (proactive notifications)
- Pension contribution matching game (make it fun!)
- Financial goal-setting and tracking
- Overtime pattern analysis (flag burnout risks)
- Holiday usage analytics (who's not taking enough?)
- Team collaboration features (internal messaging)
- Client portal themes (let employers customize look)
- Benchmark reports (compare to similar businesses)
- Carbon footprint tracking (business travel expenses)
- Charity giving via payroll (easy donations)
- Employee discounts marketplace
- Learning management system (track training)
- Anonymous employee feedback
- Mental health check-ins
- Referral rewards program
- Integration with UK gov Gateway
- Auto-generate director's loan accounts
- CIS reverse charge handling
- Construction Industry Scheme support
- Apprenticeship levy calculator
- National Living Wage compliance checker
- Gender pay gap reporting
- Off-payroll working (IR35) checker

**Note:** These are raw ideas. Most won't get built. That's okay!

---

## Evaluation Criteria

When deciding whether to promote from IDEA → APPROVED:

### Ask These Questions:

1. **Client Demand:** Do 3+ clients actively request this?
2. **Core Business:** Does it directly support bookkeeping/payroll?
3. **Effort:** Is effort < 1 week to build?
4. **AI Advantage:** Does it leverage our AI advantage?
5. **Alternatives:** Can't clients solve this another way?
6. **ROI:** Will it save time or generate revenue?
7. **Scope:** Keeps us focused on bookkeeping (not HR/other)?
8. **Maintenance:** Low maintenance burden?

### Scoring:

- **6-8 YES:** Strongly consider building
- **4-5 YES:** Maybe defer to Year 2
- **2-3 YES:** Probably not worth it
- **0-1 YES:** Definitely reject

### Example Evaluation:

**Feature:** CSV Bulk Upload

1. Client Demand: ✅ (clients with 10+ employees need this)
2. Core Business: ✅ (directly supports payroll input)
3. Effort: ✅ (2 days to build)
4. AI Advantage: ❌ (not AI-related)
5. Alternatives: ❌ (manual entry is painful)
6. ROI: ✅ (saves hours per payroll run)
7. Scope: ✅ (clearly payroll-related)
8. Maintenance: ✅ (simple, stable)

**Score: 6/8** → **APPROVED!** ✅

---

## Review Schedule

### Month 10: First Review
- Evaluate all 🟡 CONSIDERING features
- Check beta client feedback
- Prioritize top 3-5 for Months 11-12
- Move approved items to roadmap

### Month 12: Second Review
- Review for Year 2 roadmap
- Check which ideas clients actually requested
- Deprioritize unused ideas
- Plan Year 2 feature set

### Quarterly (Year 2+): Ongoing Reviews
- Evaluate new requests from clients
- Review analytics (which features used most?)
- Retire unused features
- Plan next quarter

---

## How to Use This Document

### For You (Building):
- When you think "wouldn't it be cool if..." → Add to this doc
- Don't add to roadmap immediately
- Capture the idea, evaluate later
- Stay focused on committed roadmap

### For Claude Code:
- This doc is for REFERENCE only
- Do NOT implement these features unless told
- They're ideas, not instructions
- Focus on MULTI_PLATFORM_ROADMAP.md instead

### For Decision-Making:
- Use evaluation criteria strictly
- Be ruthless about scope creep
- Remember: we're bookkeepers, not HR software
- Quality over quantity

---

## ⚠️ Important Reminders

**DON'T:**
- ❌ Build features "just in case"
- ❌ Add features because they're cool
- ❌ Compete with established tools
- ❌ Lose focus on core business
- ❌ Over-engineer early
- ❌ Say yes to everything

**DO:**
- ✅ Capture every idea here
- ✅ Evaluate based on real client need
- ✅ Build what directly supports payroll/accounting
- ✅ Stay focused on 12-month roadmap
- ✅ Quality over quantity
- ✅ Launch with core features working brilliantly

---

## Success Metrics

**If this document is working well:**
- Ideas captured (not forgotten)
- Roadmap stays focused (not bloated)
- Features built have clear ROI
- Clients actually use what we build
- No feature regret ("why did we build that?")

**If this document isn't working:**
- Roadmap keeps changing
- Building features nobody uses
- Scope creep happening
- Time wasted on "cool but useless"

---

## Final Note

**Remember:** Every feature has a cost.

- Time to build
- Time to maintain
- Time to support
- Time to document
- Complexity added to system

**Ask:** "Is this feature worth all those costs?"

**Usually the answer is:** "Not yet. Maybe Year 2."

**And that's okay!** 

**Better to do 10 things brilliantly than 50 things poorly.** 🎯

---

**Let's stay focused. Let's build smart. Let's launch strong.** 🚀
