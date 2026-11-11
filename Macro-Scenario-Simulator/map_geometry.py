"""Bundled Natural Earth boundaries and Mercator projection; no network or GIS library."""
import json
import math
from pathlib import Path

BOUNDS=(-180,15,180,80)  # west, south, east, north

def clip_ring(points,bounds=BOUNDS):
    """Sutherland–Hodgman polygon clipping in lon/lat before projection."""
    result=[tuple(p[:2]) for p in points]
    for axis,edge,lower in [(0,bounds[0],True),(0,bounds[2],False),(1,bounds[1],True),(1,bounds[3],False)]:
        old=result;result=[]
        if not old: break
        previous=old[-1]; prev_inside=previous[axis]>=edge if lower else previous[axis]<=edge
        for current in old:
            inside=current[axis]>=edge if lower else current[axis]<=edge
            if inside != prev_inside:
                t=(edge-previous[axis])/(current[axis]-previous[axis])
                result.append(tuple(previous[j]+t*(current[j]-previous[j]) for j in (0,1)))
            if inside: result.append(current)
            previous=current;prev_inside=inside
    return result

def project(lon,lat):
    lat=max(-85,min(85,lat))
    return lon, -math.degrees(math.log(math.tan(math.pi/4+math.radians(lat)/2)))

def load_boundaries():
    features=json.loads((Path(__file__).parent/'data/europe.geojson').read_text())
    result=[]
    for f in features:
        g=f['geometry'];polygons=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
        rings=[]
        for polygon in polygons:
            # Exterior rings only; this small-scale map omits inland-water holes.
            ring=clip_ring(polygon[0])
            if len(ring)>=3: rings.append([project(*p) for p in ring])
        if rings: result.append(dict(name=f['name'],iso=f['iso'],rings=rings))
    return result

def viewport(width,height):
    left,top=project(BOUNDS[0],BOUNDS[3]);right,bottom=project(BOUNDS[2],BOUNDS[1])
    scale=min((width-32)/(right-left),(height-24)/(bottom-top))
    return scale,(width-scale*(left+right))/2,(height-scale*(top+bottom))/2
