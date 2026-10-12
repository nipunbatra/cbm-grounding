"""Small evaluator for the absolute M/L/C/Z paths used in this exercise."""
import math
import re


def segments(path):
    tokens=re.findall(r'[MLCZ]|-?\d+(?:\.\d+)?',path)
    i=0;point=start=None
    while i<len(tokens):
        cmd=tokens[i];i+=1
        if cmd in ('M','L'):
            p=tuple(map(float,tokens[i:i+2]));i+=2
            if cmd=='M':start=p
            else:yield ('L',point,p)
            point=p
        elif cmd=='C':
            coords=list(map(float,tokens[i:i+6]));i+=6
            a,b,p=tuple(coords[:2]),tuple(coords[2:4]),tuple(coords[4:6])
            yield ('C',point,a,b,p);point=p
        elif cmd=='Z':
            yield ('L',point,start);point=start
        else:raise ValueError(cmd)


def evaluate(p0,p1,p2,p3,t):
    return (1-t)**3*p0+3*(1-t)**2*t*p1+3*(1-t)*t*t*p2+t**3*p3


def path_bounds(path):
    points=[]
    for segment in segments(path):
        if segment[0]=='L':points.extend(segment[1:]);continue
        controls=segment[1:];ts={0.,1.}
        for axis in (0,1):
            p0,p1,p2,p3=[p[axis] for p in controls]
            a=-p0+3*p1-3*p2+p3;b=2*(p0-2*p1+p2);c=p1-p0
            if abs(a)<1e-12:
                roots=[] if abs(b)<1e-12 else [-c/b]
            else:
                disc=b*b-4*a*c
                roots=[] if disc<0 else [(-b+math.sqrt(disc))/(2*a),(-b-math.sqrt(disc))/(2*a)]
            ts.update(t for t in roots if 0<t<1)
        points.extend(tuple(evaluate(*(p[axis] for p in controls),t) for axis in (0,1)) for t in ts)
    xs,ys=zip(*points)
    return [min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)]


def path_area(path):
    points=[]
    for s in segments(path):
        if s[0]=='L':points.extend(s[1:]);continue
        points.extend(tuple(evaluate(*(p[axis] for p in s[1:]),t/256) for axis in (0,1)) for t in range(257))
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2
