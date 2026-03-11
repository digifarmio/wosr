# WOSR Underwriting — Task Context

## Urgency
**HIGH** — Meeting tomorrow (2026-03-11) at 3 PM. Nils says "we need something asap this week."

## What This Is
Corteva wants to extend the **Emergence Guarantee** program from **corn** to **Winter Oilseed Rape (WOSR)** across Central/Eastern Europe. We already built the corn underwriting model for Romania (via ChatGPT + Docker). Now we need to adapt it for WOSR.

## Key Contacts
- **Nils Helset** (CEO) — driving the commercial side
- **Matti Tiainen** (matti.tiainen@frontera.ag) — Frontera Ag, coordinating with Corteva
- **Antoine & Etienne** — Descartes (reinsurance/underwriting partner)

## Two Immediate Tasks

### Task 1: Reply to Descartes (TODAY — urgent)
Descartes (Antoine & Etienne) sent an email that needs a response. Previous Descartes correspondence (Feb 25) was about:
- Data mismatch concerns (GeoJSON vs Excel methodology)
- Two separate models: county-level Excel historical analysis vs field-level Docker emergence detection
- Validation limitations pre-2018

Context from Feb 25 email exchange:
- Konstantin drafted a response addressing the data mismatch (two separate models with different methodologies)
- Used both ChatGPT and Claude to refine the response
- Nils validated via ChatGPT's Frontera project channel
- The email was sent, Descartes replied (Feb 27) with "hopefully good news and moving forward"
- Now there's a NEW Descartes email (received Mar 9) that needs review and response

### Task 2: WOSR Underwriting for Romania + 6 Countries
Adapt the corn emergence guarantee methodology to WOSR.

**Countries (in priority order):**
1. Romania (start here — reuse corn methodology)
2. Moldova
3. Poland
4. Ukraine
5. Czech Republic
6. Slovakia
7. Hungary

**Peril Packages (WOSR-specific):**
- **Standard Package**: Non-germination only (50%/100%) due to drought and crust
- **Full Package**: Non-germination (100%) + hail + storm + heavy rain + frost (winter+spring) + possible drought in vegetation period

**Key Differences from Corn:**
- More perils in WOSR than corn (frost is major — winter+spring)
- WOSR premium pricing is ~3x corn (WOSR: 20-24% vs corn: 7-7.6%)
- Average loss ratio for WOSR (5 years): 12.66%
- Nils suggests: "start with calculating autumn replant risk and then spring emergence after"

**Approach:**
- Reuse the corn methodology document as template
- Adapt for WOSR-specific data and Romania first
- Incorporate Marsh/Descartes/Liberty Mutual feedback from corn process
- Run the model for all 7 countries
- Share results via Claude Cowork (Nils setting up — adding Morris, Ben, Bube, Matti)

## Existing Work & Resources

### ChatGPT Conversations (Frontera GPT Project)
- Corn/WOSR Excel results for Romania: https://chatgpt.com/g/g-p-68873fafbbf88191b23263fe7836051b-frontera/shared/c/69af037f-47dc-832a-9368-a5f105a28c87
- Descartes email review: https://chatgpt.com/g/g-p-68873fafbbf88191b23263fe7836051b-frontera/shared/c/69145dcc-2c88-8326-a990-dfec1b3c1689
- Descartes validation: https://chatgpt.com/share/e/6969ec98-6ae4-8005-ae37-959ab25e85ac

### Google Drive Documents (key ones)
- **WOSR and Corn Pricing Premium notes** — in Corteva docs (GDrive)
- **Definitive Actuarial Methodology for Historical Loss Ratio Calculation** — multiple versions (2025-11-14, 2026-01-15, 2026-01-19)
- **30-Year Historical Losses Prediction RO** (report, 2025-10-16)
- **Insurance Premium Pricing | Romania 2026** (multiple versions with Marsh)
- **Premium Risk Pricing Exercise (07.09.2025)**
- **Claims Loss Calculation Exercise - Final**
- **FARM Replanting Insurance Specification** (technical spec, 2025-10-21)
- **WOSR claims data spreadsheet**: https://docs.google.com/spreadsheets/d/1rDgY_ObppGBQZYTa4K-dVNhWohlcXBl9/edit

### GDrive Profiles (dpro knowledge base)
- `/home/ubuntu/dpro/data/gdrive/profiles/clients/corteva.md` — 95 lines, full doc inventory
- `/home/ubuntu/dpro/data/gdrive/profiles/clients/frontera.md` — 100 lines, full doc inventory
- `/home/ubuntu/dpro/data/gdrive/profiles/clients/marsh.md` — 60+ lines, all Marsh meeting notes
- `/home/ubuntu/dpro/data/gdrive/profiles/contracts/frontera-x-corteva-agreement-process.md` — EUR 1.7M structure

### Corteva Deal Summary
- **Program Fee**: EUR/USD 450,000 (2026 season, Romania corn)
- **Broader Structure**: EUR 1,700,000 (Option A — validated approach)
- **Pilot Area**: 100,000 hectares, southern Romania, corn (Lumiposa treated hybrids)
- **Platform**: https://frontera.digifarm.io/en
- **Pricing**: USD 2/hectare for emergence detection access
- **Expiry**: 2026-12-31 (program year)
- **Status**: Many draft agreement versions, no final signed version yet

### Reinsurance Partners
- **Marsh** — Primary broker, extensive meeting history (Jul-Nov 2025)
- **Munich Re** — Reinsurer, follow-up meetings in Sep 2025
- **Descartes (Antoine, Etienne)** — Underwriting/validation partner, reviewing Docker methodology
- **Liberty Mutual** — Referenced in WOSR discussions
- **Hannover Re** — Named in agreement process doc

## Nils's Full Slack Messages (Mar 9-10, 2026)

### Mar 9, 16:17 CET
> Hey how's it going? did you have a nice weekend?! I saw the email from Descartes just now - would you be able to have a look?

### Mar 9, 18:10 CET
> Hey btw just spoke with Matti and we need to do the same underwriting process for winter oilseed rape for Romania as Corteva wants to put together the program for it

### Mar 9, 18:11 CET
> So considering what Descartes has replied with and the process would you be able to help me put together the same docs basically and docker for WOSR for Romania to start with and then

### Mar 9, 18:13 CET
> So basically Moldova, Poland, Ukraine, Czech Republic, Slovakia and Hungary

### Mar 9, 18:14 CET
> But maybe the first thing we need to do is check if can re-use the methodology document and WOSR data for Romania first?

### Mar 9, 18:21 CET
> I'm flying back from Morocco we did Katie's 40th here and won't be back until later tonight - one thing you could maybe help me with is getting the AI agent chat we used for the final corn and WOSR and see if we can (a) share with matti (his email is: matti.tiainen@frontera.ag) and also (b) easier maybe to export to Claude and use the co working functionality so we can collaborate on it together? I tried creating a co working account but didn't work for me

### Mar 9, 18:23 CET
> Is this the last ChatGPT channel we had when we did excel results for Romania on corn? [ChatGPT link]
> Or did we have another one?

### Mar 9, 18:47 CET
> Actually thinking about it would be best if you're able to run all the countries in Claude for the WOSR using the model we built in Romania with adjustments + feedback based on what we have gone through with Marsh/Descartes and Liberty Mutual - and then I was thinking maybe it would be good to have a joint group channel in Claude co work with the data or results etc that you me and Matti can collaborate on?

### Mar 9, 18:52 CET
> Basically the perils/causes would be a bit different and more in WOSR than in corn (I sent email but it would be):
> 1 – standard which includes only non germination (50%/100%) because of drought and crust.
> 2 – Full package including non germination (100%) + hail, storm, heavy rain, frost (winter+spring) + possible drought in the vegetation period.

### Mar 9, 18:57 CET
> Sorry for all the messages just starting stressing a bit as I spoke with Matti and we need something asap this week for them basically but if you're able to help me with this think it through etc that would be amazing

### Mar 9, 19:35 CET
> Hey, sorry. I have some idea also. We have Tess's birthday, I'll come back soon [Konstantin]

### Mar 9, 19:55 CET
> Amazing thank you and happy birthday to Tess!

### Mar 9, 19:56 CET
> I think we can start with calculating autumn replant risk and then spring emergence after maybe :)

### Mar 10, 10:23 CET
> Hey hows it going? Could you help me with the WOSR stuff? sorry we just got confirmation the meeting is tomorrow at 3 pm, so we should have some stuff to present, and also today this morning if possible we should get back to Descartes and Etienne if possible

### Mar 10, 10:23 CET
> I also signed up for Claude cowork and included Morris + Ben and Bube since they requested access so will import the memory from ChatGPT shortly so maybe we can use cowork for the WOSR stuff

### Mar 10, 10:49 CET
> Yeah, let's do that. Thinking. Working on Descartes now [Konstantin]

### Mar 10, 10:49 CET
> Thank you! [Nils]

### Mar 10, 13:43 CET
> btw, do you see this chat? [screenshot] on frontera gpt project? I've drafted the email [Konstantin]

## Suggested Work Plan

### Priority 1 (Today): Descartes Email Response
1. Read the latest Descartes email (check Gmail or ask Nils to forward)
2. Draft response using context from previous exchanges
3. Send to Nils for review before sending

### Priority 2 (Today/Tomorrow): WOSR Romania Analysis
1. Access the WOSR claims data spreadsheet (5 years of data available)
2. Review the corn actuarial methodology document
3. Adapt methodology for WOSR perils (add frost, different thresholds)
4. Calculate autumn replant risk first, then spring emergence
5. Generate historical loss ratio analysis for Romania WOSR

### Priority 3 (This Week): Expand to 6 More Countries
1. After Romania model validated, adapt for Moldova, Poland, Ukraine, Czech Republic, Slovakia, Hungary
2. Adjust for country-specific climate/crop data
3. Compile results for all 7 countries

### Priority 4: Collaboration Setup
1. Set up Claude Cowork channel with Nils, Matti, Morris, Ben, Bube
2. Import ChatGPT conversation context
3. Share WOSR results and methodology docs

## Technical Notes
- The corn Docker image contains emergence detection logic (not the Excel county-level model)
- Excel model = historical county-level loss estimation (35-year horizon)
- Docker model = field-level emergence detection using satellite imagery
- These are two complementary but methodologically different approaches
- Descartes has been reviewing the Docker methodology for production readiness
- Key concern: replicability of Excel results from 2018 data
