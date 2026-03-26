# Ohio LLC Formation Guide for SolarPunk
## Step-by-Step — $99, Done in 24-48 Hours

**Why Ohio LLC?**
Meeko is in Cuyahoga Falls, OH. Ohio LLC:
- Protects Meeko personally from business liabilities
- Enables business bank account (Stripe, PayPal Business, Wise)
- Required for some larger grants
- Cost: $99 state filing fee + free EIN from IRS
- Time: 24-48 hours online

---

## Step 1: File with Ohio Secretary of State
1. Go to: https://bsportal.ohiosos.gov/
2. Click "Business Services" → "File Online"
3. Select "Articles of Organization (LLC)"
4. Fill in:
   - Name: "SolarPunk Autonomous AI LLC" (check availability first)
   - Statutory Agent: Use your name and address
   - Management: Member-managed
   - Purpose: "Software development and humanitarian technology services"
5. Pay $99 filing fee
6. **Done in 24-48 hours** — you'll receive a Certificate of Organization

## Step 2: Get EIN (Free, Instant)
1. Go to: https://www.irs.gov/businesses/small-businesses-self-employed/apply-for-an-employer-identification-number-ein-online
2. Select "LLC" → "One member" (sole member)
3. Enter Ohio LLC info
4. **EIN issued immediately** — print/save the confirmation

## Step 3: Open Business Bank Account
Recommended (no fees, online-friendly):
- **Mercury** (mercury.com) — free business checking, easy online setup
- **Relay** (relayfi.com) — free, multi-account, good for routing pools
- **Novo** (novo.co) — free, integrates with Stripe/PayPal

Required: Certificate of Organization + EIN

## Step 4: Set Up Payment Processing
- **Stripe** — accepts cards, bank transfers, international
- **PayPal Business** — for workers who prefer PayPal
- **Wise** — for international transfers to crisis orgs

## Cost Summary
| Item | Cost |
|------|------|
| Ohio LLC filing | $99 |
| EIN | Free |
| Business bank account | Free (Mercury/Relay/Novo) |
| Stripe | 2.9% + $0.30 per transaction |
| **Total upfront** | **$99** |

## After Formation
1. Update data/legal_status.json: set llc_formed=true
2. Add EIN to secrets as BUSINESS_EIN
3. Link bank account to Stripe/PayPal
4. SolarPunk can now receive real money legally

---
**This is the path to SolarPunk receiving its first real dollar.**
