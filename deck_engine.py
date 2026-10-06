from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from io import BytesIO

NAVY=RGBColor(11,23,36); TEAL=RGBColor(22,183,200); MUTED=RGBColor(93,111,124); WHITE=RGBColor(255,255,255); LIGHT=RGBColor(244,247,249)

def _rgb(v,fallback):
    try:
        h=(v or "").replace("#",""); return RGBColor(int(h[:2],16),int(h[2:4],16),int(h[4:6],16))
    except: return fallback

def default_outline(p):
    out=[{"title":str(p.get("client","Client"))+" Strategy","body":"Integrated Marketing Strategy\nPrepared by PMC Media Group","type":"cover","include":True},{"title":"Executive Direction","body":p.get("strategy",{}).get("executive",""),"type":"content","include":True}]
    facts=p.get("strategy",{}).get("facts",[])[:6]; out.append({"title":"Research + Discovery","body":"\n".join(["• "+str(x.get("label"))+": "+str(x.get("value")) for x in facts]),"type":"content","include":True})
    for name,recs in p.get("strategy",{}).get("departments",{}).items():
        d=p.get("department_details",{}).get(name,{}); body=[]
        if d.get("objective"): body.append("OBJECTIVE\n"+d["objective"])
        if recs: body.append("RECOMMENDATIONS\n"+"\n".join(["• "+x for x in recs]))
        if d.get("deliverables"): body.append("DELIVERABLES\n"+d["deliverables"])
        if d.get("kpis"): body.append("SUCCESS CRITERIA\n"+d["kpis"])
        out.append({"title":name,"body":"\n\n".join(body),"type":"department","include":True})
    if p.get("investment_allocations"): out.append({"title":"Investment Framework","body":"","type":"investment","include":True})
    if p.get("tactic_allocations"): out.extend([{"title":"Channel + Tactic Plan","body":"","type":"channels","include":True},{"title":"Measurement + Success Framework","body":"","type":"measurement","include":True}])
    out.append({"title":"Next Steps","body":"• Confirm launch priorities and timing\n• Finalize production and implementation requirements\n• Activate measurement and reporting plan","type":"closing","include":True}); return out

def text(slide,x,y,w,h,value,size=15,color=MUTED,bold=False):
    box=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=box.text_frame; tf.word_wrap=True; tf.clear()
    for i,line in enumerate(str(value or "").split("\n")):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.text=line; p.font.size=Pt(size); p.font.color.rgb=color; p.font.bold=bold; p.space_after=Pt(6)
    return box

def build_pptx(p):
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    brand=p.get("deck_branding",{}); brand_color=_rgb(brand.get("accent_color"),TEAL); treatment=brand.get("treatment","pmc")
    for item in (p.get("deck_outline") or default_outline(p)):
        if item.get("include",True) is False: continue
        typ=item.get("type","content"); dark=typ in ("cover","closing"); slide=prs.slides.add_slide(prs.slide_layouts[6])
        bg=slide.background.fill; bg.solid(); bg.fore_color.rgb=NAVY if dark else WHITE
        accent_shape=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(.65),Inches(.65),Inches(.12),Inches(.72)); accent_shape.fill.solid(); accent_shape.fill.fore_color.rgb=brand_color; accent_shape.line.fill.background()
        text(slide,1,.62,11.5,.8,item.get("title",""),34 if typ=="cover" else 27,WHITE if dark else NAVY,True)
        text(slide,1,7.02,11,.22,("PMC Intelligence" if treatment!="client" else str(p.get("client","Client"))),8,brand_color)
        if typ=="investment":
            inv=[x for x in p.get("investment_allocations",[]) if float(x.get("amount",0))>0]
            if inv:
                data=ChartData(); data.categories=[x.get("department","") for x in inv]; data.add_series("Investment",[float(x.get("amount",0)) for x in inv])
                chart=slide.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT,Inches(.9),Inches(1.55),Inches(5.25),Inches(4.9),data).chart; chart.has_legend=True; chart.legend.position=XL_LEGEND_POSITION.BOTTOM; chart.legend.include_in_layout=False
                y=1.65
                for x in inv:
                    text(slide,6.65,y,3.5,.35,x.get("department",""),13,NAVY,True); text(slide,10.1,y,1,.35,str(x.get("percent",0))+"%",13,brand_color,True); text(slide,11.1,y,1.2,.35,"$"+format(float(x.get("amount",0)),",.0f"),13,MUTED); y+=.55
        elif typ=="channels":
            y=1.55
            for dept,items in p.get("tactic_allocations",{}).items():
                text(slide,1,y,3.2,.3,dept.upper(),11,brand_color,True); y+=.34
                for x in items[:5]:
                    pct=float(x.get("percent",0)); text(slide,1.1,y,3.4,.3,x.get("name",""),13,NAVY,True)
                    bar=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(4.55),Inches(y+.04),Inches(5.4),Inches(.15)); bar.fill.solid(); bar.fill.fore_color.rgb=LIGHT; bar.line.fill.background()
                    fill=slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(4.55),Inches(y+.04),Inches(5.4*min(pct,100)/100),Inches(.15)); fill.fill.solid(); fill.fill.fore_color.rgb=brand_color; fill.line.fill.background()
                    text(slide,10.15,y,1,.3,str(x.get("percent",0))+"%",12,MUTED,True); y+=.38
                y+=.12
        elif typ=="measurement":
            y=1.55
            for dept,items in p.get("tactic_allocations",{}).items():
                text(slide,1,y,3.1,.3,dept.upper(),11,brand_color,True); y+=.34
                for x in items[:5]: text(slide,1.15,y,3.5,.3,x.get("name",""),13,NAVY,True); text(slide,4.8,y,7.2,.3,x.get("kpi") or "Success criteria TBD",13,MUTED); y+=.38
                y+=.12
        elif typ=="department":
            body=item.get("body",""); text(slide,1,1.55,11.1,4.95,body,15,MUTED)
        else:
            text(slide,1,1.7,11.2,4.9,item.get("body",""),16,RGBColor(205,220,228) if dark else MUTED)
    out=BytesIO(); prs.save(out); out.seek(0); return out
