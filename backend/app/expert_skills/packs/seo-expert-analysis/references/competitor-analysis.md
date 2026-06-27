# Competitor Analysis Methodology (No Backlink DB)

## What we CAN do
- Infer **primary keywords** from URL, title, H1, meta, industry vertical
- Identify **3–5 named competitors** from public market knowledge + SERP-style reasoning
- Compare **content breadth**: service pages, blog depth, location pages, pricing transparency
- Analyze **presentation patterns**: trust signals, CTAs, schema types, page templates
- Score **content gaps**: topics they rank for conceptually that target lacks

## What we CANNOT do
- Ahrefs/Moz/SEMrush backlink counts or DA/DR
- Exact ranking positions without live SERP API
- Traffic estimates from third-party databases

## Competitor identification process
1. **Auto-extract** seed keywords from live homepage crawl (title, meta, H1–H3, body text, bigrams)
2. Run web context search: `{brand} {top keywords} competitors`
3. Ask: "Who would rank for [keyword] in [geo/industry]?"
3. Prefer direct business competitors over Wikipedia/aggregators
4. For each competitor note: page count signals, content types, technical polish

## Content gap framework
| Gap type | Example | Opportunity |
|---|---|---|
| Topic | Competitor has /pricing, target doesn't | Add pricing page |
| Depth | Competitor 2000-word guides, target 300-word stubs | Expand pillar content |
| Local | Competitor has city landing pages | Add geo pages |
| Trust | Competitor shows certifications, target doesn't | Add credentials section |
| Technical | Competitor fast LCP, target 15s+ | Performance sprint |

## Competitive scoring (0–15 in overall score)
- 13–15: Clear content/technical edge over identified competitors
- 9–12: Parity with minor gaps
- 5–8: Behind on 2+ dimensions
- 0–4: Significant competitive disadvantage