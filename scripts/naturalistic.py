"""Naturalistic vector birds with exact, visible concept-layer geometry.

The specimen is invented, not a claim to depict one real bird species.
"""
from pathlib import Path
import random

W, H = 720, 480
BILL = 'M 470 128 C 488 128 503 134 516 142 C 499 145 486 150 470 154 C 474 145 474 136 470 128 Z'
CROWN = 'M 393 115 C 393 96 408 82 428 82 C 453 82 470 106 470 127 L 467 133 C 448 112 419 105 393 115 Z'
WING = 'M 277 194 C 304 174 340 174 365 174 C 395 174 420 188 423 212 C 423 243 367 270 293 279 C 276 264 266 238 266 214 C 266 205 270 199 277 194 Z'
BODY = 'M 285 211 C 296 181 349 156 391 148 C 412 140 427 156 440 174 C 452 195 443 220 438 243 C 430 286 414 320 389 335 C 369 346 330 328 308 310 C 283 287 273 246 285 211 Z'
HEAD = 'M 393 151 C 380 132 387 103 406 90 C 427 75 454 90 467 109 C 483 130 478 153 462 168 C 448 181 414 177 402 162 Z'
SPECS = [('bill','yellow bill',[470,128,46,26],BILL),('crown','red crown patch',[393,82,77,51],CROWN),('wing','blue wing patch',[266,174,157,105],WING)]
CONFIGS = [
    ('01-reference','Reference bird',[1,1,1],0,0,False,'All three concepts are present.'),
    ('02-neutral-bill','Change only the bill',[0,1,1],0,0,False,'Yellow bill becomes neutral; the authored class changes.'),
    ('03-neutral-crown','Change only the crown',[1,0,1],0,0,False,'Red crown becomes neutral; the authored class changes.'),
    ('04-neutral-wing','Change only the wing',[1,1,0],0,0,False,'Blue wing becomes neutral; the authored class stays the same.'),
    ('05-moved-bird','Move the same bird',[1,1,1],62,-24,False,'The bird and its supporting branch move; concepts stay the same.'),
    ('06-red-distractor','Put red in the background',[1,0,1],0,0,True,'A red background leaf does not make a red crown.'),
]


def gradient(name, colors, x2='85%', y2='100%'):
    return f'<linearGradient id="{name}" x1="10%" y1="0%" x2="{x2}" y2="{y2}">'+''.join(f'<stop offset="{i/(len(colors)-1):.3f}" stop-color="{color}"/>' for i,color in enumerate(colors))+'</linearGradient>'


def generate(root):
    directory=root/'images/svg-naturalistic'
    masks=directory/'masks';masks.mkdir(parents=True,exist_ok=True)
    result=[]
    for name,title,bits,dx,dy,distractor,note in CONFIGS:
        rng=random.Random(714)
        prefix=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        svg=[prefix,f'<title>Naturalistic vector study — {title}</title>','<defs>',
             gradient('background',['#ced0b6','#8d9b7b','#566e58'],'95%','100%'),
             gradient('body',['#e0d7bb','#b8af91','#827f69','#605f4e']),
             gradient('head',['#ded4b7','#bfb08e','#8c8064']),
             gradient('tail',['#818872','#545e50','#3d493e']),
             gradient('branch',['#93866a','#625b46','#494c3c']),
             gradient('bill-paint',['#ead481','#c2a643','#816b2d'] if bits[0] else ['#ccc5b5','#928c7b','#625e51']),
             gradient('crown-paint',['#c8846c','#a74e3d','#6b342a'] if bits[1] else ['#d1c3a3','#a09277','#736b56']),
             gradient('wing-paint',['#9aaeb3','#65848d','#3d6473','#304c58'] if bits[2] else ['#b5b3a1','#8c8d7f','#696e61','#474e44']),
             '<radialGradient id="eye"><stop offset="0" stop-color="#111e19"/><stop offset=".8" stop-color="#1b261c"/><stop offset="1" stop-color="#766947"/></radialGradient>',
             '<filter id="blur"><feGaussianBlur stdDeviation="14"/></filter>',
             f'<clipPath id="body-clip"><path d="{BODY}"/></clipPath>',
             f'<clipPath id="head-clip"><path d="{HEAD}"/></clipPath>']
        for part,_,_,path in SPECS:svg.append(f'<clipPath id="{part}-clip"><path d="{path}"/></clipPath>')
        svg.extend(['</defs>','<rect width="720" height="480" fill="url(#background)"/>','<g filter="url(#blur)" opacity=".30">'])
        for _ in range(19):
            x,y,r=rng.randint(-30,760),rng.randint(-30,510),rng.randint(14,62)
            svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{rng.choice(["#eee7c8","#ece9d0","#617b5b"])}"/>')
        svg.extend(['</g>', '<path d="M 54 480 Q 112 194 81 0 M 657 480 Q 611 240 686 0" stroke="#697d5c" stroke-width="12" opacity=".15" fill="none"/>'])
        if distractor:
            svg.append('<path d="M 572 82 C 600 52 632 47 651 44 C 651 73 624 97 594 99 C 584 99 577 91 572 82 Z" fill="#a74e3d"/>')
        svg.append(f'<g transform="translate({dx} {dy})">')
        # A gnarled perch, with the same geometry in all concept-only interventions.
        svg.extend(['<path d="M 18 418 C 143 415 205 389 317 383 C 439 376 517 362 687 382" fill="none" stroke="url(#branch)" stroke-width="17" stroke-linecap="round"/>',
                    '<path d="M 24 413 C 143 410 205 384 317 378 C 439 371 517 357 685 377" fill="none" stroke="#b0a17d" stroke-width="2" opacity=".8"/>',
                    '<path d="M 529 370 Q 553 344 592 332" fill="none" stroke="#6e684e" stroke-width="7" stroke-linecap="round"/>'])
        for j in range(50):
            x=28+j*13;y=411-(x-28)*.065
            svg.append(f'<path d="M {x} {y:.1f} l 6 3 l -3 2" stroke="#443f32" opacity=".25" fill="none" stroke-width="1.1"/>')
        # Long overlapping tail feathers, visible shafts and tapered vanes.
        for j in range(6):
            x=300+j*7;tipx=167+j*8;tipy=395-j*3
            svg.append(f'<path d="M {x} 268 C {x-26} 305 {tipx+20} {tipy-21} {tipx} {tipy} C {tipx+18} {tipy+5} {x+9} 310 {x+19} 283 Z" fill="url(#tail)" stroke="#a4a18b" stroke-width=".7"/>')
            svg.append(f'<path d="M {x+8} 280 Q {x-49} 337 {tipx+4} {tipy-3}" stroke="#b5b398" opacity=".48" stroke-width=".8" fill="none"/>')
        # Feet and claws. These lie behind the body, but in front of the perch.
        for x,y in [(352,315),(387,322)]:
            svg.append(f'<path d="M {x} {y} l -1 26 l 10 34 M {x+9} 375 q -17 -2 -27 9 q -2 7 2 8 M {x+9} 375 q 8 -3 18 5 q 4 6 1 11 M {x+10} 375 q 16 -10 27 -3" stroke="#6c6553" stroke-width="4" stroke-linecap="round" fill="none"/>')
            svg.append(f'<path d="M {x-1} {y+9} l 6 -1 M {x-1} {y+15} l 6 -1 M {x+2} {y+24} l 5 -1 M {x+4} {y+31} l 5 -1" stroke="#bcb095" stroke-width="1.4" fill="none"/>')
        svg.extend([f'<path d="{BODY}" fill="url(#body)"/>',f'<path d="{HEAD}" fill="url(#head)"/>','<g clip-path="url(#body-clip)">'])
        # Hundreds of small feather barbs follow the breast and belly rather than a flat cartoon fill.
        for _ in range(440):
            x,y=rng.uniform(280,444),rng.uniform(160,337)
            length=rng.uniform(3,10)
            svg.append(f'<path d="M {x:.2f} {y:.2f} q 1.5 {length*.8:.2f} -2 {length:.2f}" stroke="{rng.choice(["#f0e8cb","#e4dabc","#514e3e"])}" stroke-width="{rng.uniform(.35,.9):.2f}" opacity="{rng.uniform(.13,.4):.2f}" fill="none"/>')
        svg.append('</g><g clip-path="url(#head-clip)">')
        for _ in range(185):
            x,y=rng.uniform(386,478),rng.uniform(84,174)
            svg.append(f'<path d="M {x:.2f} {y:.2f} q 4 1 7 3" stroke="{rng.choice(["#ece3c3","#685b42"])}" stroke-width=".55" opacity=".30" fill="none"/>')
        svg.append('</g>')
        concepts,parts=[],[]
        for idx,(part,label,bbox,path) in enumerate(SPECS):
            svg.extend([f'<g id="{part}" clip-path="url(#{part}-clip)">',f'<path d="{path}" fill="url(#{part}-paint)"/>'])
            if part=='wing':
                for j in range(13):
                    sx=293+j*8;sy=194+j*.5;ex=278+j*6;ey=267-j*1.2
                    svg.append(f'<path d="M {sx} {sy} C {sx+20} {sy+4} {ex+13} {ey-5} {ex} {ey} C {ex-3} {ey-5} {sx-2} {sy+18} {sx} {sy} Z" fill="#c6c9b8" fill-opacity=".12" stroke="#243d3d" stroke-opacity=".28" stroke-width=".9"/>')
                    svg.append(f'<path d="M {sx+4} {sy+7} Q {sx+5} {sy+29} {ex+2} {ey-2}" stroke="#d9d8c0" stroke-width=".65" opacity=".50" fill="none"/>')
                for row in range(4):
                    for col in range(11-row):
                        x=283+col*10+row*4;y=184+row*10
                        svg.append(f'<path d="M {x} {y} q 8 0 7 7 q -4 4 -9 1" stroke="#dad8bd" stroke-opacity=".40" stroke-width=".75" fill="#d4d4bc" fill-opacity=".055"/>')
            elif part=='crown':
                for j in range(64):
                    x,y=rng.uniform(391,471),rng.uniform(82,134)
                    svg.append(f'<path d="M {x:.2f} {y:.2f} q 4 2 7 5" fill="none" stroke="{rng.choice(["#f1dbc0","#3c3327"])}" opacity=".25" stroke-width=".65"/>')
            else:
                svg.extend(['<path d="M 471 142 Q 491 143 516 142" stroke="#51432f" stroke-width=".8" opacity=".7" fill="none"/>','<path d="M 478 133 Q 488 131 498 136" stroke="#f5ebc4" stroke-width="1.2" opacity=".65" fill="none"/>','<ellipse cx="479" cy="137" rx="2.3" ry="1.2" fill="#4c4432"/>'])
            svg.append('</g>')
            box=[bbox[0]+dx,bbox[1]+dy,*bbox[2:]]
            geom={'part':part,'bbox_xywh':box,'bbox_normalized_xywh':[round(box[0]/W,6),round(box[1]/H,6),round(box[2]/W,6),round(box[3]/H,6)],
                  'kind':'exact_svg_geometry','path_d':path,'translation':[dx,dy],
                  'definition':'Tight vector bounds of a filled Bezier silhouette; gradient and feather detail are clipped to this silhouette. All target silhouettes are fully visible.'}
            parts.append(geom)
            mask_path=masks/f'{name}-{part}.svg'
            mask=prefix+f'<rect width="{W}" height="{H}" fill="black"/>'
            if bits[idx]:mask+=f'<g transform="translate({dx} {dy})"><path d="{path}" fill="white"/></g>'
            mask_path.write_text(mask+'</svg>')
            concepts.append({'id':part,'name':label.replace(' ','_'),'label':label,'present':bits[idx],'observable':True,'certainty':'known by construction',
                             'ground_truth_concept_boxes':[geom] if bits[idx] else [],'part_geometry':geom,'proxy_boxes':[],'support_keypoints':[],
                             'mask_path':str(mask_path.relative_to(root)),'localization_status':'exact_visible_svg_geometry' if bits[idx] else 'concept_absent'})
        # Eye and cheek stay separate from the three concept silhouettes.
        svg.extend(['<path d="M 427 145 Q 437 135 453 135 Q 462 135 466 140 Q 450 139 437 151 Z" fill="#e2d5b1" opacity=".7"/>',
                    '<ellipse cx="450" cy="147" rx="7.3" ry="7.9" fill="#78694b"/>',
                    '<ellipse cx="450" cy="147" rx="5.7" ry="6.3" fill="url(#eye)"/>',
                    '<circle cx="448" cy="145" r="1.7" fill="#faf7df" opacity=".9"/>',
                    '<path d="M 433 162 Q 445 169 462 162" stroke="#776b50" stroke-width="1.1" opacity=".45" fill="none"/>',
                    '</g></svg>'])
        image_path=directory/(name+'.svg');image_path.write_text('\n'.join(svg))
        result.append({'id':'naturalistic-'+name,'kind':'svg','style':'naturalistic','title':title,'note':note,
                       'image_path':str(image_path.relative_to(root)),'width':W,'height':H,'class_label':'A' if bits[0] and bits[1] else 'B',
                       'rule':'A iff yellow bill AND red crown patch; otherwise B. Blue wing is irrelevant.',
                       'concept_vector':bits,'concept_order':['yellow_bill','red_crown_patch','blue_wing_patch'],
                       'parts':parts,'concepts':concepts,'bird_bbox_xywh':None,
                       'bird_bbox_kind':'not_exported; target concept geometry is exact',
                       'distractors':[{'name':'red background leaf','bbox_xywh':[572,44,79,55]}] if distractor else [],
                       'evidence':'ILLUSTRATIVE: naturalistic authored SVG, exact concept geometry, invented specimen and class rule'})
    return result
