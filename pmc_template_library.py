"""Editable slides from the approved PMC master, never a screenshot of the deck.

The repository's original test bundle already contains the approved 86-slide
presentation. Selected slide XML matches the later uploaded reference; differences
are saved dates and font packaging. No source client copy, embedded fonts, notes,
unused slides, sample prices or client logos are carried into exports.
"""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import posixpath
import re
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree as E

VERSION = 'pmc-master-v1'
ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / 'PMC_Intelligence_Local_Test_FIXED (1).zip'
MEMBER = 'PMC_Intelligence_Local_Test_FIXED/master/PMC_Master_Strategy.pptx'
MASTER_SHA256 = '5235c0d4977c26481d971f6c2c65c07ca838407eda8f5c3ba583f3ef293d61e4'
NS = {'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
PARSER = E.XMLParser(resolve_entities=False, no_network=True, remove_blank_text=False)

def spec(source, slots=None, remove=(), fixed=False, table=None):
    return {'source':source, 'slots':slots or {}, 'remove':list(remove), 'fixed':fixed, 'table':table}

# Slots: key -> (shape id, max characters). Unlisted copy is agency-approved,
# immutable copy. Coordinates, vector artwork, themes and generic imagery remain.
LAYOUTS = {
 'cover':spec(1, {'title':(5,180)}, remove=(4,42,43)),
 'positioning':spec(2, fixed=True),
 'agency_locations':spec(3, fixed=True),
 'agency_approach':spec(4, fixed=True),
 'executive':spec(5, {'title':(36,70),'copy':(37,1500)}),
 'divider':spec(6, {'title':(81,60)}),
 'department':spec(7, {'department':(41,65),'title':(45,85),'copy':(46,2800)}),
 'search':spec(15, {'intro':(54,480),'campaigns':(53,1700),'priorities':(55,1350),'measurement':(37,1000)}),
 'pmax':spec(16, {'intro':(41,720),'asset_groups':(45,1600),'signals':(46,600),'kpis':(48,420),'secondary':(51,260)}),
 'paid_social':spec(17, {'intro':(41,460),'audiences':(51,1800),'creative':(42,1300),'experience':(45,1100)}),
 'ctv':spec(18, {'intro':(41,520),'audiences':(38,1250),'audience_note':(47,230),'measurement':(58,230)}),
 'seo':spec(22, {'title':(55,65),'headline':(4,105),'subtitle':(5,130),
     'focus_1':(10,40),'focus_2':(11,40),'focus_3':(12,40),
     'local_1':(21,120),'local_2':(22,115),'pages_title':(29,45),'pages_1':(30,120),'pages_2':(31,115),
     'actions_title':(41,45),'actions_1':(42,115),'actions_2':(43,115),
     'services':(45,170),'outcome_1':(48,40),'outcome_2':(51,40),'outcome_3':(54,40)}),
 'seo_execution':spec(23, {'title':(58,65),'content':(14,105),'reporting':(32,100),'approval':(41,35),'guardrail':(45,130)}),
 'creative':spec(29, {'title':(46,220),'copy':(40,2200)}),
 'website':spec(32, {'client':(49,180),'copy':(45,1400)}),
 'website_recommendations':spec(33, {'title':(47,220),'copy':(45,2900)}),
 'investment':spec(56, {'title':(6,260)}, table=4),
 'closing':spec(86, fixed=True),
}


def xml(data): return E.fromstring(data, parser=PARSER)
def serial(root): return E.tostring(root, encoding='UTF-8', xml_declaration=True, standalone=True)
def q(prefix, tag): return '{' + NS[prefix] + '}' + tag

@lru_cache(maxsize=1)
def source_parts():
    if not BUNDLE.is_file(): raise ValueError('The approved PMC template bundle is not installed.')
    with ZipFile(BUNDLE) as bundle:
        info = bundle.getinfo(MEMBER)
        if info.file_size > 25*1024*1024: raise ValueError('Template exceeds the permitted size.')
        data = bundle.read(MEMBER)
    if sha256(data).hexdigest() != MASTER_SHA256:
        raise ValueError('PMC template version does not match the reviewed master. Do not export until it is reviewed.')
    with ZipFile(BytesIO(data)) as archive:
        return {name:archive.read(name) for name in archive.namelist()}

def template_status():
    try:
        source_parts()
        return {'ready':True, 'version':VERSION, 'reference_slides':86,
                'layouts':len(LAYOUTS), 'renderer':'editable-master-slides'}
    except (ValueError, OSError, KeyError):
        return {'ready':False,'version':VERSION,'message':'Approved PMC master unavailable or changed; contact the PMC administrator.'}


def find_shape(root, shape_id):
    hits = root.xpath('.//p:cNvPr[@id=$id]', namespaces=NS, id=str(shape_id))
    if len(hits) != 1: raise ValueError('PMC template shape mapping no longer matches the master.')
    return hits[0].getparent().getparent()


def set_text(shape, value):
    """Replace text while retaining template paragraph/run styling and geometry."""
    frames = shape.xpath('./p:txBody | ./a:txBody', namespaces=NS)
    if not frames: raise ValueError('Mapped template field is not a text frame.')
    frame = frames[0]
    original = frame.findall(q('a','p'))
    styled = [p for p in original if ''.join(p.itertext()).strip()]
    fallback = (styled or original)[-1] if (styled or original) else E.Element(q('a','p'))
    for p in original: frame.remove(p)
    for i, line in enumerate(value.replace('\r\n','\n').replace('\r','\n').split('\n')):
        base = original[i] if i < len(original) else fallback
        paragraph = E.Element(q('a','p'))
        properties = base.find(q('a','pPr'))
        if properties is not None: paragraph.append(deepcopy(properties))
        styles = base.xpath('./a:r/a:rPr | ./a:fld/a:rPr | ./a:endParaRPr', namespaces=NS)
        if not styles: styles = fallback.xpath('./a:r/a:rPr | ./a:endParaRPr', namespaces=NS)
        run = E.SubElement(paragraph,q('a','r'))
        if styles:
            rpr = deepcopy(styles[0]); rpr.tag = q('a','rPr')
            for link in rpr.xpath('./a:hlinkClick | ./a:hlinkMouseOver',namespaces=NS): rpr.remove(link)
            run.append(rpr)
        E.SubElement(run,q('a','t')).text = line or ''
        frame.append(paragraph)



def format_dynamic(shape, body=False, size=22):
    """Use the master’s Outfit body/teal heading styles, not source-client
    paragraph positions. New headings must not inherit unrelated bullet styles."""
    frame=shape.find(q('p','txBody'))
    if frame is None:return
    for p in frame.findall(q('a','p')):
        value=''.join(p.xpath('.//a:t/text()',namespaces=NS))
        pr=p.find(q('a','pPr'))
        if pr is None:pr=E.Element(q('a','pPr'));p.insert(0,pr)
        for child in list(pr):
            if E.QName(child).localname in ('lnSpc','spcBef','spcAft','buChar','buAutoNum','buFont'):pr.remove(child)
        spacing=E.SubElement(pr,q('a','lnSpc'));E.SubElement(spacing,q('a','spcPct'),val='115000')
        for props in p.xpath('./a:r/a:rPr',namespaces=NS):
            if props.find(q('a','latin')) is None:E.SubElement(props,q('a','latin'),typeface='Outfit')
        if body:
            pr.set('marL','0');pr.set('indent','0')
            heading=value.isupper() and len(value)<70 and not value.startswith('•')
            for props in p.xpath('./a:r/a:rPr',namespaces=NS):
                props.set('sz',str(round((size+2 if heading else size)*100)))
                props.set('b','1' if heading else '0')
                for fill in list(props):
                    if E.QName(fill).localname in ('solidFill','gradFill','noFill'):props.remove(fill)
                fill=E.SubElement(props,q('a','solidFill'));E.SubElement(fill,q('a','srgbClr'),val='008C9B' if heading else '18252D')



def fit_title_width(shape):
    """Constrain editable headings to their original title row, using a
    conservative bold-glyph estimate before the vertical fit check."""
    ext=shape.find('.//'+q('a','xfrm')+'/'+q('a','ext'))
    if ext is None:return
    width=int(ext.get('cx'))/12700-18
    weights={'W':1.05,'M':.98,'I':.36,'J':.56,' ': .34,'/':.42,'-':.42,'.':.30}
    for paragraph in shape.xpath('./p:txBody/a:p',namespaces=NS):
        value=''.join(paragraph.xpath('.//a:t/text()',namespaces=NS))
        units=sum(weights.get(ch,.79 if ch.isupper() else .62) for ch in value)
        cap=width/max(1,units)
        for prop in paragraph.xpath('./a:r/a:rPr[@sz]',namespaces=NS):
            prop.set('sz',str(min(int(prop.get('sz')),int(cap*100))))


def _fit_copy(shape, text, minimum=15):
    """Conservative character/line estimate; shrink within a readable range only.

    The same exact text is exported; never truncate a long field. It is rejected
    when it cannot fit at the minimum font size, prompting an explicit split/edit.
    """
    frame = shape.find(q('p','txBody'))
    if frame is None: return
    ext = shape.find('.//' + q('a','xfrm') + '/' + q('a','ext'))
    if ext is None: return
    width = int(ext.get('cx','0'))/12700; height = int(ext.get('cy','0'))/12700
    if not width or not height: return
    body = frame.find(q('a','bodyPr'))
    if body is not None:
        width -= (int(body.get('lIns','91440'))+int(body.get('rIns','91440')))/12700
        height -= (int(body.get('tIns','45720'))+int(body.get('bIns','45720')))/12700
    sizes = [int(v)/100 for v in frame.xpath('.//a:rPr/@sz',namespaces=NS)]
    if not sizes: return
    largest = max(sizes)
    minimum = min(minimum, max(11, min(sizes)*.85))
    import math
    def needed(size):
        chars=max(1,int(width/(size*.56)))
        return sum(max(1,math.ceil(len(line)/chars)) for line in text.split('\n'))*size*1.15
    size=largest
    while size > minimum and needed(size)>height: size-=.5
    if needed(size)>height: raise ValueError('Slide copy is too long for the PMC layout. Shorten this field or split the content across slides.')
    if size < largest:
        ratio=size/largest
        for props in frame.xpath('.//a:rPr[@sz] | .//a:endParaRPr[@sz]',namespaces=NS):
            props.set('sz',str(max(int(minimum*100),int(int(props.get('sz'))*ratio))))
    if body is not None:
        for child in list(body):
            if E.QName(child).localname in ('spAutoFit','normAutofit','noAutofit'): body.remove(child)
        E.SubElement(body,q('a','noAutofit'))


def set_table(shape, rows):
    table = shape.find('.//' + q('a','tbl'))
    originals = table.findall(q('a','tr'))
    if len(originals)<2: raise ValueError('Approved investment table is unavailable.')
    total_height=sum(int(row.get('h')) for row in originals)
    columns=table.find(q('a','tblGrid')).findall(q('a','gridCol'))
    full_width=sum(int(col.get('w')) for col in columns)
    for col,fraction in zip(columns,(.56,.16,.16,.12)):col.set('w',str(round(full_width*fraction)))
    for row in originals: table.remove(row)
    header_height=int(.52*914400)
    body_height=(total_height-header_height)//max(1,len(rows)-1)
    for i, values in enumerate(rows):
        row=deepcopy(originals[0 if i==0 else 1])
        row.set('h',str(header_height if i==0 else body_height))
        cells=row.findall(q('a','tc'))
        for column,cell,value in zip(columns,cells,values):
            set_text(cell,str(value))
            for props in cell.xpath('.//a:rPr | .//a:endParaRPr',namespaces=NS):
                props.set('sz','1500' if i==0 else '1700')
                props.set('b','1' if i==0 else '0')
            for pr in cell.xpath('.//a:pPr',namespaces=NS):
                for el in list(pr):
                    if E.QName(el).localname in ('buChar','buAutoNum','buBlip','spcBef','spcAft','lnSpc'): pr.remove(el)
            tcpr=cell.find(q('a','tcPr'))
            if tcpr is not None: tcpr.set('anchor','ctr')
            # Reject rather than clip a densely edited narrow table cell.
            import math
            usable_width=int(column.get('w'))/12700-20
            usable_height=int(row.get('h'))/12700-12
            font=15 if i==0 else 17
            def cell_height(size):
                capacity=max(1,int(usable_width/(size*.56)))
                return sum(max(1,math.ceil(len(line)/capacity)) for line in str(value).split('\n'))*size*1.15
            while font>14 and cell_height(font)>usable_height:font-=.5
            if cell_height(font)>usable_height:
                raise ValueError('Investment table copy is too long for its cell. Shorten this cell or split the investment across slides.')
            for props in cell.xpath('.//a:rPr | .//a:endParaRPr',namespaces=NS):props.set('sz',str(round(font*100)))
        table.append(row)


def validate_slide(item):
    if not isinstance(item,dict): raise ValueError('Each slide must be an object.')
    key=item.get('template_key')
    if key not in LAYOUTS: raise ValueError('Unknown PMC slide layout.')
    fields=item.get('fields',{})
    if not isinstance(fields,dict) or set(fields)!=set(LAYOUTS[key]['slots']):
        raise ValueError('PMC slide fields do not match the approved layout.')
    for field,(_,limit) in LAYOUTS[key]['slots'].items():
        value=fields[field]
        if not isinstance(value,str) or len(value)>limit or '\x00' in value:
            raise ValueError('Slide field '+field+' exceeds its '+str(limit)+'-character allowance.')
    if LAYOUTS[key]['table']:
        rows=item.get('rows')
        if not isinstance(rows,list) or not 2<=len(rows)<=9: raise ValueError('Investment slides need a header and 1–8 rows.')
        for row in rows:
            if not isinstance(row,list) or len(row)!=4 or any(not isinstance(v,str) or len(v)>400 for v in row):
                raise ValueError('Investment rows need four text cells, each up to 400 characters.')


def make_slide(key, fields, title=None, department=None, rows=None):
    info=LAYOUTS[key]
    item={'type':'pmc_template','template_key':key,'template_version':VERSION,
          'source_slide':info['source'],'title':title or key.replace('_',' ').title(),
          'fields':fields,'field_limits':{k:v[1] for k,v in info['slots'].items()},
          'include':True,'fixed_copy':info['fixed']}
    if department: item['department']=department
    if rows is not None: item['rows']=rows
    validate_slide(item)
    item['body']=preview_text(item)
    return item


def prepared_slide(item, parts):
    validate_slide(item)
    info=LAYOUTS[item['template_key']]; source=info['source']
    root=xml(parts[f'ppt/slides/slide{source}.xml'])
    relations=xml(parts[f'ppt/slides/_rels/slide{source}.xml.rels'])
    for shape_id in info['remove']:
        shape=find_shape(root,shape_id);shape.getparent().remove(shape)
    if item['template_key']=='cover':
        # Replace the restaurant's cover photo with the master’s own agency
        # rocket artwork. Never reuse a sample client's logo or product photo.
        picture=find_shape(root,52)
        find_shape(root,5).find('.//'+q('a','xfrm')+'/'+q('a','ext')).set('cx',str(round(11.7*914400)))
        rocket_rels=xml(parts['ppt/slides/_rels/slide2.xml.rels'])
        image=next(r for r in rocket_rels if r.get('Type','').endswith('/image'))
        rel=E.SubElement(relations,'{'+REL+'}Relationship',Id='rIdPMCRocket',
                         Type=image.get('Type'),Target=image.get('Target'))
        picture.find('.//'+q('a','blip')).set(q('r','embed'),rel.get('Id'))
        from PIL import Image
        image_path=posixpath.normpath(posixpath.join('ppt/slides',image.get('Target')))
        with Image.open(BytesIO(parts[image_path])) as artwork:
            original_ratio=artwork.width/artwork.height
        ext=picture.find('.//'+q('a','xfrm')+'/'+q('a','ext'))
        ratio=int(ext.get('cx'))/int(ext.get('cy'))
        fill=picture.find(q('p','blipFill'))
        for crop in fill.findall(q('a','srcRect')):fill.remove(crop)
        crop=E.Element(q('a','srcRect'))
        if original_ratio>ratio:
            inset=round((1-ratio/original_ratio)*50000);crop.set('l',str(inset));crop.set('r',str(inset))
        else:
            inset=round((1-original_ratio/ratio)*50000);crop.set('t',str(inset));crop.set('b',str(inset))
        fill.insert(1,crop)
    if item['template_key']=='department':
        side=find_shape(root,41).find('.//'+q('a','xfrm'))
        side.find(q('a','off')).set('x',str(round(.35*914400)))
        side.find(q('a','ext')).set('cx',str(round(5.0*914400)))
    if item['template_key']=='paid_social':
        for sid,width in [(42,5.0),(45,5.75)]:
            find_shape(root,sid).find('.//'+q('a','xfrm')+'/'+q('a','ext')).set('cx',str(round(width*914400)))
    if item['template_key']=='ctv':
        for sid in (47,58):
            find_shape(root,sid).find('.//'+q('a','xfrm')+'/'+q('a','ext')).set('cy',str(round(.60*914400)))
    if item['template_key']=='pmax':
        # Constrain source boxes extending past the edge to their two columns.
        for sid,width in [(45,9.6),(46,9.6),(48,4.65),(51,5.2)]:
            ext=find_shape(root,sid).find('.//'+q('a','xfrm')+'/'+q('a','ext'))
            ext.set('cx',str(round(width*914400)))
        for sid,x,y,h in [(45,9.68,3.18,2.7),(46,9.68,6.15,2.0)]:
            transform=find_shape(root,sid).find('.//'+q('a','xfrm'))
            transform.find(q('a','off')).set('x',str(round(x*914400)))
            transform.find(q('a','off')).set('y',str(round(y*914400)))
            transform.find(q('a','ext')).set('cy',str(round(h*914400)))
    for name,(shape_id,_) in info['slots'].items():
        shape=find_shape(root,shape_id);set_text(shape,item['fields'][name])
        body_fields={'copy','campaigns','priorities','measurement','asset_groups','signals','kpis','secondary','audiences','creative','experience'}
        format_dynamic(shape,body=name in body_fields,size=24 if item['template_key']=='executive' else 22)
        if name in ('title','client','department') and item['template_key'] not in ('divider','cover'):fit_title_width(shape)
        try:_fit_copy(shape,item['fields'][name])
        except ValueError as exc:raise ValueError(item['template_key']+' / '+name+': '+str(exc)) from exc
    if info['table']: set_table(find_shape(root,info['table']),item['rows'])
    for el in root.xpath('.//p:timing | .//p:extLst | .//a:hlinkClick | .//a:hlinkMouseOver',namespaces=NS):
        el.getparent().remove(el)
    for el in root.xpath('.//p:cNvPr',namespaces=NS):
        el.attrib.pop('descr',None);el.attrib.pop('title',None)
    used=set(root.xpath('//@r:embed | //@r:link',namespaces=NS))
    for rel in list(relations):
        typ=rel.get('Type','').rsplit('/',1)[-1]
        if rel.get('TargetMode')=='External' or typ not in ('slideLayout','image') or (typ=='image' and rel.get('Id') not in used):
            relations.remove(rel)
    return serial(root),serial(relations)


def preview_text(item):
    data,_=prepared_slide(item,source_parts())
    root=xml(data)
    texts=[]
    for frame in root.xpath('.//p:txBody | .//a:tc/a:txBody',namespaces=NS):
        text='\n'.join(''.join(p.xpath('.//a:t/text()',namespaces=NS)) for p in frame.findall(q('a','p'))).strip()
        if text and '© COPYRIGHT' not in text and text!='PMCMEDIAGROUP.COM': texts.append(text)
    return '\n\n'.join(texts)


def render_master(slides):
    """Create an allowlisted package: only selected slides and reachable assets."""
    selected=[s for s in slides if s.get('include',True) is not False]
    if not selected or len(selected)>120: raise ValueError('Choose 1–120 slides for export.')
    parts=source_parts(); candidates=dict(parts)
    pres=xml(parts['ppt/presentation.xml'])
    allowed={'sldMasterIdLst','sldIdLst','sldSz','notesSz','defaultTextStyle'}
    for child in list(pres):
        if E.QName(child).localname not in allowed: pres.remove(child)
    ids=pres.find(q('p','sldIdLst'))
    for child in list(ids): ids.remove(child)
    rels=xml(parts['ppt/_rels/presentation.xml.rels'])
    for rel in list(rels):
        if rel.get('Type','').rsplit('/',1)[-1] not in ('slideMaster','theme','presProps','viewProps','tableStyles'): rels.remove(rel)
    for i,item in enumerate(selected,1):
        slide,slide_rels=prepared_slide(item,parts)
        candidates[f'ppt/slides/slide{i}.xml']=slide
        candidates[f'ppt/slides/_rels/slide{i}.xml.rels']=slide_rels
        rid='rIdPMC'+str(i)
        E.SubElement(ids,q('p','sldId'),id=str(255+i),attrib={q('r','id'):rid})
        E.SubElement(rels,'{'+REL+'}Relationship',Id=rid,Type=NS['r']+'/slide',Target=f'slides/slide{i}.xml')
    candidates['ppt/presentation.xml']=serial(pres)
    candidates['ppt/_rels/presentation.xml.rels']=serial(rels)
    candidates['docProps/core.xml']=b'<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>PMC Marketing Strategy</dc:title><dc:creator>PMC Media Group</dc:creator></cp:coreProperties>'
    candidates['docProps/app.xml']=f'<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>PMC Intelligence</Application><Slides>{len(selected)}</Slides></Properties>'.encode()
    root_rels=E.Element('{'+REL+'}Relationships',nsmap={None:REL})
    for rid,typ,target in [('rId1',NS['r']+'/officeDocument','ppt/presentation.xml'),('rId2','http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties','docProps/core.xml'),('rId3',NS['r']+'/extended-properties','docProps/app.xml')]:
        E.SubElement(root_rels,'{'+REL+'}Relationship',Id=rid,Type=typ,Target=target)
    candidates['_rels/.rels']=serial(root_rels)
    output={};queue=[''];seen=set()
    forbidden={'notesSlide','notesMaster','commentAuthors','comments','tags','font','oleObject','package','changesInfo','thumbnail','hyperlink'}
    while queue:
        name=queue.pop(0)
        if name in seen: continue
        seen.add(name)
        if name:
            if name not in candidates: raise ValueError('Template contains a missing asset: '+name)
            data=candidates[name]
            if name.startswith(('ppt/slideLayouts/','ppt/slideMasters/')) and name.endswith('.xml'):
                doc=xml(data)
                for el in doc.xpath('.//a:fld | .//a:hlinkClick | .//a:hlinkMouseOver',namespaces=NS): el.getparent().remove(el)
                data=serial(doc)
            output[name]=data
        dirname,filename=posixpath.split(name)
        relname=posixpath.join(dirname,'_rels',filename+'.rels') if name else '_rels/.rels'
        if relname not in candidates: continue
        relationships=xml(candidates[relname])
        for rel in list(relationships):
            typ=rel.get('Type','').rsplit('/',1)[-1]
            if rel.get('TargetMode')=='External' or typ in forbidden:
                relationships.remove(rel);continue
            target=posixpath.normpath(posixpath.join(dirname,rel.get('Target',''))).lstrip('/')
            if target.startswith('../'): raise ValueError('Unsafe template relationship.')
            queue.append(target)
        output[relname]=serial(relationships)
    content_types=xml(parts['[Content_Types].xml'])
    for el in list(content_types):
        if E.QName(el).localname=='Override' and el.get('PartName','').lstrip('/') not in output: content_types.remove(el)
        if E.QName(el).localname=='Default' and el.get('Extension') in ('fntdata','odttf'): content_types.remove(el)
    output['[Content_Types].xml']=serial(content_types)
    stream=BytesIO()
    with ZipFile(stream,'w',ZIP_DEFLATED) as archive:
        for name,data in output.items(): archive.writestr(name,data)
    stream.seek(0)
    return stream
