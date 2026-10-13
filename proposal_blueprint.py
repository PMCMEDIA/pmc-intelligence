"""One saved project -> PMC master slide plan -> editable preview and export.

This maps actual saved recommendations, not a new LLM connection. Drafts expose
missing inputs, never reuse the sample clients' prices, demographics or metrics.
"""
import re
from decimal import Decimal, InvalidOperation
from pmc_template_library import make_slide, template_status, VERSION

ORDER=['Production','Digital Media','SEO / AEO','Organic Social','Creative / Website','PR / Communications','Measurement']


def amount(value):
    try:
        result=Decimal(str(value))
        return result if result.is_finite() and result>=0 else None
    except (InvalidOperation,TypeError,ValueError): return None

def money(value):
    number=amount(value)
    return '${:,.0f}'.format(number) if number is not None else 'To confirm'

def text(value): return str(value or '').strip()
def bullets(items): return '\n'.join('• '+text(v) for v in items if text(v))

def section(project,name):
    strategy=project.get('strategy') or {}; d=dict((strategy.get('department_sections') or {}).get(name) or {})
    detail=(project.get('department_details') or {}).get(name) or {}
    d.update({k:v for k,v in detail.items() if k in ('objective','deliverables','notes','timing')})
    if 'kpis' in detail: d['success']=detail['kpis']
    d['recommendations']=list((strategy.get('departments') or {}).get(name) or [])
    return d

def chunks(value,limit):
    """Split long copy at a paragraph or word boundary; never drop content."""
    value=text(value)
    if not value:return ['Needs confirmation.']
    result=[]
    while len(value)>limit:
        stop=value.rfind('\n',0,limit)
        if stop<limit//3:stop=value.rfind(' ',0,limit)
        if stop<1:stop=limit
        result.append(value[:stop]);value=value[stop:].lstrip('\n ')
    if value:result.append(value)
    return result

def channel_names(project):
    rows=(project.get('tactic_allocations') or {}).get('Digital Media') or []
    # An explicitly scoped tactic list is the source of truth. Excluded/zero
    # allocation channels do not acquire deliverables from a generic suggestion.
    if rows:
        names=[text(r.get('name')).lower() for r in rows if r.get('include',True) is not False and (r.get('percent') is None or (amount(r.get('percent')) or 0)>0)]
    else:names=[text(r).lower() for r in section(project,'Digital Media')['recommendations']]
    found=[]
    for key,hints in [('search',('google search','search ads','paid search','search marketing','search')),('pmax',('performance max','pmax')),('paid_social',('paid social','meta ads','social advertising')),('ctv',('performance media','ctv','streaming'))]:
        if any(any(re.search(r'(?<!\w)'+re.escape(h)+r'(?!\w)',n) for h in hints) for n in names):found.append(key)
    return found


def required_assets(project):
    """PMC's supplied channel requirements, not platform policy or a quote."""
    result=[]; channels=channel_names(project)
    if 'ctv' in channels: result.append('Performance Media / CTV: :30 commercial master and :15 cutdown.')
    if 'paid_social' in channels: result.append('Paid Social: :30 video and :15 vertical version; test variations scoped separately.')
    if 'pmax' in channels: result.append('Performance Max: :15 or :30 video; confirm additional orientations and imagery.')
    deps=(project.get('strategy') or {}).get('departments') or {}
    if 'Organic Social' in deps:
        scope=text(section(project,'Organic Social').get('deliverables'))
        result.append('Organic Social: '+(scope or 'derive original video and photography from the approved reel cadence and content plan.'))
    if project.get('website_pricing') or project.get('website_analysis'):
        result.append('Website: confirm whether original photography, staff/facility imagery or website video is required.')
    if result:result.append('Production review: combine compatible masters/cutdowns and shoot needs; do not count shared assets or filming twice. Shoot, edit, licensing and revision costs need approved Production rates.')
    return result


def _department_copy(d):
    blocks=[]
    for label,key in [('OBJECTIVE','objective'),('STRATEGIC RESPONSE','response'),('WHY IT MATTERS','rationale')]:
        if text(d.get(key)):blocks.append(label+'\n'+text(d[key]))
    if d['recommendations']:blocks.append('RECOMMENDED TACTICS\n'+bullets(d['recommendations']))
    for label,key in [('SCOPED DELIVERABLES','deliverables'),('EXPECTED OUTCOME','outcome'),('SUCCESS CRITERIA','success')]:
        if text(d.get(key)):blocks.append(label+'\n'+text(d[key]))
    return '\n\n'.join(blocks)


def default_outline(project):
    if not template_status()['ready']: raise ValueError('The approved PMC master is unavailable. Existing saved decks remain accessible; restore the master before rebuilding.')
    p=project; client=text(p.get('client')) or 'Client'; strategy=p.get('strategy') or {}
    departments=strategy.get('departments') or {}; slides=[]
    def put(key,fields,title=None,department=None,rows=None):
        slide=make_slide(key,fields,title,department,rows);slides.append(slide);return slide
    def narrative(title,copy,department=None):
        for i,part in enumerate(chunks(copy,1200)):
            heading=title if i==0 else title+' (continued)'
            put('executive',{'title':heading.upper(),'copy':part},heading,department)
    def department_pages(name,d,heading=None):
        for i,part in enumerate(chunks(_department_copy(d),2300)):
            title=heading or name.upper()+' STRATEGY'
            if i:title+=' (continued)'
            put('department',{'department':name.upper(),'title':title,'copy':part},title,name)

    put('cover',{'title':client+'\nMarketing Proposal'},client+' · Marketing Proposal')
    for key,title in [('positioning','PMC Positioning'),('agency_locations','PMC Locations'),('agency_approach','Our Collaborative Approach')]:put(key,{},title)
    narrative('Executive Summary',text(strategy.get('executive')) or 'Client-specific executive strategy needs confirmation.')
    if 'Production' in departments:
        put('divider',{'title':'CINEMATIC PRESENCE'},'Cinematic Presence','Production')
        d=section(p,'Production'); department_pages('Production',d,'CINEMATIC STRATEGY')
        assets=required_assets(p)
        if assets:
            for part in chunks(bullets(assets),2300):put('department',{'department':'CINEMATIC PRODUCTION','title':'CHANNEL-DRIVEN ASSET REQUIREMENTS','copy':part},'Required Production Assets','Production')
    channels=channel_names(p)
    if 'Digital Media' in departments:
        put('divider',{'title':'DIGITAL DISRUPTION'},'Digital Disruption','Digital Media')
        d=section(p,'Digital Media');department_pages('Digital Media',d,'DIGITAL STRATEGY')
        # Channel scope uses explicit saved information. Missing geographic,
        # service and audience details remain gaps instead of stock personas.
        intent=text(p.get('goal')) or 'the confirmed business objective'
        scope=text(d.get('deliverables')) or 'Priority services, markets, landing pages and launch scope need confirmation.'
        if len(scope)>550:scope='See the full scoped deliverables in the Digital Strategy section. Apply those approved priorities to this channel.'
        if len(intent)>300:intent='Support the complete business objective recorded in the Executive Summary.'
        success=text(d.get('success')) or 'Define qualified conversions and confirm measurement before launch.'
        if len(success)>750:success='See the full Digital Strategy success criteria. Confirm channel-level measurement before launch.'
        response=text(d.get('response') or d.get('objective'))
        if len(response)>850:response='See the complete strategic response in the Digital Strategy section. Retain those approved priorities for this channel.'
        if 'search' in channels:
            put('search',{'intro':intent,
                'campaigns':'CAMPAIGN STRUCTURE\n'+scope,
                'priorities':'STRATEGIC PRIORITIES\n'+response,
                'measurement':'MEASURABLE KPIs\n'+success},'Google Ads','Digital Media')
        if 'pmax' in channels:
            put('pmax',{'intro':intent,'asset_groups':'ASSET GROUPS & PRIORITIES\n'+scope,
                'signals':'AUDIENCE SIGNALS\nConfirm approved first-party data, relevant intent signals and geographic scope. No inferred customer lists or demographics.',
                'kpis':'MEASURABLE KPIs\n'+(success if len(success)<360 else 'See the Digital Strategy success criteria. Preserve all detailed measures there.'),
                'secondary':'CREATIVE REQUIREMENTS\n:15 or :30 video. Confirm orientations and supporting imagery with Production.'},'Google Performance Max','Digital Media')
        if 'paid_social' in channels:
            put('paid_social',{'intro':intent,
                'audiences':'AUDIENCE & MARKET SCOPE\n'+scope,
                'creative':'STRATEGIC RESPONSE\n'+response,
                'experience':'MEASURABLE KPIs\n'+success+'\n\nPRODUCTION\n:30 video plus :15 vertical version; consolidate compatible assets.'},'Paid Social Media','Digital Media')
        if 'ctv' in channels:
            put('ctv',{'intro':intent,'audiences':'AUDIENCE-FIRST PLAN\n'+scope,
                'audience_note':'Use the confirmed service area and audience priorities. Eligibility and targeting signals require review.',
                'measurement':'Confirm verified visits and qualified conversions. :30 + :15 creative is required; do not invent reach or lead forecasts.'},'Performance Media','Digital Media')
        competition=(p.get('competitive_intelligence') or {}).get('candidates') or []
        if competition:
            narrative('Competitive Landscape', 'PUBLIC-SEARCH CANDIDATES · NOT VERIFIED COMPETITORS\n\n'+ '\n\n'.join(text(c.get('title'))+'\n'+text(c.get('url')) for c in competition)+'\n\nValidate market relevance and source evidence before presenting competitor claims.','Digital Media')
        outlook=p.get('campaign_outlook') or {}
        if outlook:
            narrative('Measurement & Forecast Review','FORECAST STATUS\nThe existing model uses planning assumptions. Independently sourced industry benchmarks, investment period and defensible client economics must be confirmed before client-ready KPI or ROI scenarios are included.\n\nSaved scenario values are not automatically copied into this PMC template draft.','Digital Media')
    if 'SEO / AEO' in departments:
        d=section(p,'SEO / AEO')
        # Detailed recommendations stay intact in their own master-layout slide.
        # The three-card overview and four-stage execution slide match the source.
        put('seo',{'title':'SEO / AEO STRATEGY','headline':'Stronger search visibility. A clearer path to action.',
            'subtitle':'Client-specific priorities are detailed in the following strategy section.',
            'focus_1':'CONFIRM SERVICE AREA','focus_2':'PRIORITY PAGES','focus_3':'SEARCH + AI DISCOVERY',
            'local_1':'Review business profiles, local listings and authentic reviews.',
            'local_2':'Confirm the searches and markets most relevant to the business.',
            'pages_title':'Strengthen priority pages','pages_1':'Evaluate service pages, supporting evidence and internal links.',
            'pages_2':'Use the approved strategy to prioritize content and page updates.',
            'actions_title':'Drive qualified actions','actions_1':'Review technical and navigation barriers before expanding traffic.',
            'actions_2':'Make the confirmed conversion actions simple and trackable.',
            'services':'Priority services and keyword opportunities require a verified client-specific review.',
            'outcome_1':'Qualified organic traffic','outcome_2':'Qualified conversions','outcome_3':'Search + AI visibility'},'SEO / AEO Overview','SEO / AEO')
        department_pages('SEO / AEO',d,'SEO / AEO RECOMMENDATIONS')
        put('seo_execution',{'title':'SEO / AEO EXECUTION','content':'Find content gaps. Draft\narticles, FAQs and\npriority-page copy.',
            'reporting':'Monitor search and AI\nvisibility. Connect reporting\nto qualified actions.',
            'approval':'Client approval','guardrail':'Client approval before publishing. No confidential client or customer information in AI prompts.'},'SEO / AEO Execution','SEO / AEO')
    if 'Organic Social' in departments:
        put('divider',{'title':'SOCIAL MEDIA\nIMPACT'},'Social Media Impact','Organic Social')
        d=section(p,'Organic Social');department_pages('Organic Social',d,'HARNESS THE POWER OF SOCIAL MEDIA')
        scope=text(d.get('deliverables')) or 'Platforms and posting cadence need confirmation. State the recommended frequency as “up to” the approved number of posts.'
        social='PLATFORMS & FREQUENCY\n'+scope+'\n\nCONTENT PILLARS\n'+bullets(d['recommendations'])+'\n\nCONTENT TYPES\nConfirm the mix of Reels, carousels, static graphics and photography. Scope YouTube separately when included.\n\nPRODUCTION ALIGNMENT\nDerive filming, editing and original photography from the agreed content cadence. Existing audience counts and posting activity require a source.'
        for part in chunks(social,2300):put('department',{'department':'SOCIAL MEDIA MANAGEMENT','title':'PLATFORMS, CADENCE & CONTENT','copy':part},'Social Deliverables','Organic Social')
    if 'Creative / Website' in departments:
        d=section(p,'Creative / Website')
        put('divider',{'title':'DESIGN\nREVOLUTION'},'Design Revolution','Creative / Website')
        for part in chunks(_department_copy(d),1900):put('creative',{'title':client+' · Creative Direction','copy':part},'Creative Design Strategy','Creative / Website')
        put('divider',{'title':'WEBSITE EXPERIENCE'},'Website Experience','Creative / Website')
        for part in chunks('\n\n'.join(filter(None,[text(d.get('objective')),text(d.get('response'))])),1150):put('website',{'client':client,'copy':part},'Website Design & Development','Creative / Website')
        w=p.get('website_pricing') or {};a=p.get('website_analysis') or {}
        pages=amount(w.get('pages'))
        recommendations=['OUR RECOMMENDATIONS FOR BUILDING A SUCCESSFUL WEBSITE ARE BASED ON THE FOLLOWING:']
        recommendations.append('BILLABLE SCOPE\n'+('Develop up to '+format(pages,'g')+' billable pages, subject to final sitemap approval.' if pages else 'Confirm billable development pages after reviewing the sitemap. Public URLs are not automatically billable pages.'))
        if text(w.get('notes')): recommendations.append('SCOPE NOTES\n'+text(w['notes']))
        if a:
            recommendations.append('AVAILABLE WEBSITE DISCOVERY\n'+str(a.get('url_count',0))+' public URLs identified. Homepage and XML sitemap review only; this is not a full crawl or verified feature audit.')
            if a.get('recommendations'):recommendations.append('FUNCTIONALITY TO EVALUATE\n'+bullets(text(x.get('feature'))+' — '+text(x.get('reason')) for x in a['recommendations']))
        else:recommendations.append('WEBSITE DISCOVERY\nNo website scope scan is saved. Use Scan website & competitors in Advanced Builder to collect the preliminary findings.')
        recommendations.append('CONVERSION EXPERIENCE\n'+bullets(d['recommendations']))
        for part in chunks('\n\n'.join(recommendations),2400):put('website_recommendations',{'title':client+' Website','copy':part},'Website Recommendations','Creative / Website')
    for name in departments:
        if name not in ORDER[:5]:department_pages(name,section(p,name),name.upper())
    # Tables are newly populated from saved amounts. No sample-client contract
    # clauses, setup charges, agency fees or investment tiers are inferred.
    w=p.get('website_pricing') or {}
    if w and any((amount(w.get(k)) or 0)>0 for k in ('pages','discovery','templates','technical')):
        n=lambda k:amount(w.get(k)) or Decimal(0)
        rate=amount(w.get('page_rate'));rate=Decimal(850) if rate is None else rate
        dev=n('pages')*rate;design=n('templates')*n('mockup_rate');total=max(Decimal(0),n('discovery')+design+dev+n('technical')-n('adjustment'))
        rows=[['Website Deliverables','Pay Structure','Investment','Review'],
            ['Discovery & sitemap','One-time',money(n('discovery')),'Scope review'],
            ['Mockups & wireframing ('+str(w.get('templates',0))+' unique templates)','One-time',money(design),'Scope review'],
            [str(w.get('pages',0))+' billable development pages × '+money(rate),'One-time',money(dev),'Page count review'],
            ['Additional technical functionality','One-time',money(n('technical')),'Technical review'],
            ['Discount / adjustment','One-time','−'+money(n('adjustment')),'Pricing review'],
            ['Proposed website total','One-time',money(total),'Not a separate recurring media cost']]
        put('investment',{'title':client+'\nWebsite Framework & Investment'},'Website Investment','Creative / Website',rows)
    allocations=[r for r in p.get('investment_allocations',[]) if (amount(r.get('amount')) or 0)>0]
    if allocations:
        for start in range(0,len(allocations),8):
            rows=[['Marketing Deliverables','Pay Structure','Investment','Review']]
            rows.extend([text(r.get('department')),text(r.get('period')) or 'Period to confirm',money(r.get('amount')),'Proposed allocation'] for r in allocations[start:start+8])
            put('investment',{'title':client+'\nMarketing Growth Investment Framework'},'Marketing Investment',rows=rows)
    else:narrative('Investment Framework','BUDGET GUIDANCE\n'+text(p.get('budget') or 'To confirm')+'\n\nDepartment and channel allocations require confirmation. Production pricing requires approved shoot/edit rates. No sample-deck prices or automatic percentage allocation has been substituted.')
    put('closing',{},'Let’s Build Something Extraordinary')
    return slides
