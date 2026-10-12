"""Photographic SVG composites: exact authored edit masks, approximate anatomy."""
import base64
from pathlib import Path

SHAPES=[
    ('bill','yellow bill patch',[(254,112),(266,109),(280,122),(271,127),(257,131),(249,125)]),
    ('crown','red crown patch',[(208,97),(220,91),(240,90),(257,97),(267,107),(262,110),(245,109),(229,104),(215,103),(202,111),(204,100)]),
    ('wing','blue wing patch',[(156,201),(177,207),(193,207),(214,199),(234,195),(257,182),(272,171),(275,192),(267,218),(249,239),(216,263),(186,276),(158,286),(132,294),(120,280),(126,259),(141,236),(149,214)])
]
MATRICES={'bill':[(.90,.2),(.68,.15),(.18,.02)],'crown':[(.64,.18),(.26,.06),(.20,.04)],'wing':[(.34,.06),(.58,.08),(.80,.12)]}


def generate(root):
    source='images/cub/047.American_Goldfinch/American_Goldfinch_0017_32272.jpg'
    photo='data:image/jpeg;base64,'+base64.b64encode((root/source).read_bytes()).decode()
    directory=root/'images/svg-photographic';(directory/'masks').mkdir(parents=True,exist_ok=True)
    settings=[('01-reference','Photographic reference',[1,1,1],0,0,False),
              ('02-neutral-bill','Change only the bill',[0,1,1],0,0,False),
              ('03-neutral-crown','Change only the crown',[1,0,1],0,0,False),
              ('04-neutral-wing','Change only the wing',[1,1,0],0,0,False),
              ('05-moved-photo','Move the photograph',[1,1,1],30,-20,False),
              ('06-red-distractor','Red background distractor',[1,0,1],0,0,True)]
    result=[]
    for name,title,bits,dx,dy,distractor in settings:
        prefix='<svg xmlns="http://www.w3.org/2000/svg" width="400" height="500" viewBox="0 0 400 500">'
        svg=[prefix,f'<title>{title}: grayscale CUB photo with authored color masks</title>','<defs>',
             f'<image id="photo" href="{photo}" width="400" height="500"/>',
             '<filter id="gray" color-interpolation-filters="sRGB"><feColorMatrix type="saturate" values="0"/></filter>']
        for part,_,points in SHAPES:
            ps=' '.join(f'{x},{y}' for x,y in points)
            matrix=[]
            for scale,offset in MATRICES[part]:matrix.extend([.2126*scale,.7152*scale,.0722*scale,0,offset])
            matrix.extend([0,0,0,1,0])
            svg.extend([f'<clipPath id="{part}-clip"><polygon points="{ps}"/></clipPath>',
                        f'<filter id="{part}-tint" color-interpolation-filters="sRGB"><feColorMatrix type="matrix" values="'+ ' '.join(str(v) for v in matrix)+'"/></filter>'])
        svg.extend(['</defs>','<rect width="400" height="500" fill="#d4d4d0"/>',f'<g transform="translate({dx} {dy})">','<use href="#photo" filter="url(#gray)"/>'])
        concepts,parts=[],[]
        for (part,label,points),bit in zip(SHAPES,bits):
            ps=' '.join(f'{x},{y}' for x,y in points)
            if bit:svg.append(f'<g id="{part}" clip-path="url(#{part}-clip)"><use href="#photo" filter="url(#{part}-tint)"/></g>')
            xs,ys=zip(*points);box=[min(xs)+dx,min(ys)+dy,max(xs)-min(xs),max(ys)-min(ys)]
            geom={'part':part,'bbox_xywh':box,'bbox_normalized_xywh':[round(box[0]/400,6),round(box[1]/500,6),round(box[2]/400,6),round(box[3]/500,6)],
                  'kind':'exact_authored_recoloring_mask','polygon':points,'translation':[dx,dy],
                  'definition':'Exact bounds of a designed color-edit mask. The mask was traced approximately by the assistant; it is not independently validated anatomical segmentation.'}
            parts.append(geom)
            maskpath=directory/'masks'/f'{name}-{part}.svg'
            maskpath.write_text(prefix+'<rect width="400" height="500" fill="black"/>'+(f'<g transform="translate({dx} {dy})"><polygon points="{ps}" fill="white"/></g>' if bit else '')+'</svg>')
            concepts.append({'id':part,'name':label.replace(' ','_'),'label':label,'present':bit,'observable':True,'certainty':'known authored color edit',
                             'ground_truth_concept_boxes':[geom] if bit else [],'part_geometry':geom,'proxy_boxes':[],'support_keypoints':[],
                             'mask_path':str(maskpath.relative_to(root)),'localization_status':'exact_edit_mask_approximate_anatomical_fit'})
        svg.append('</g>')
        if distractor:svg.append('<circle cx="330" cy="60" r="18" fill="#a94e42"/>')
        svg.append('</svg>');path=directory/(name+'.svg');path.write_text('\n'.join(svg))
        result.append({'id':'photographic-'+name,'kind':'svg','style':'photographic_composite','title':title,
                       'note':'Real photo texture with designed recoloring masks; exact edit geometry, approximate anatomical tracing.'+(' The entire photo layer moves by (+30, −20), not the bird alone.' if dx else ''),
                       'image_path':str(path.relative_to(root)),'width':400,'height':500,'source_image_path':source,'source_cub_image_id':2651,
                       'class_label':'A' if bits[0] and bits[1] else 'B','rule':'A iff yellow bill patch AND red crown patch; otherwise B.',
                       'concept_vector':bits,'concept_order':['yellow_bill_patch','red_crown_patch','blue_wing_patch'],'parts':parts,'concepts':concepts,
                       'bird_bbox_xywh':None,'distractors':[{'name':'red background circle','bbox_xywh':[312,42,36,36]}] if distractor else [],
                       'evidence':'CONSTRUCTED PHOTO COMPOSITE: original CUB texture; exact authored edit masks, not independent anatomical ground truth'})
    return result
