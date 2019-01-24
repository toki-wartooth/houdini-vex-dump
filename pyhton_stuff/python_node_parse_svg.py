from re import split
from locale import atof
import xml.dom.minidom as minidom
import struct
import math
import sys
import re

import svg.path
from svg.path import parse_path


# ========================================
# Utility  
# ========================================
def hexToRGB(hexstring):  
    hexstring = hexstring.replace("#", "")  # strip hash
    # Case for hex triplet
    if len(hexstring) == 3:
        hexstring = "".join([x*2 for x in hexstring])
    rgbcol = struct.unpack('BBB', hexstring.decode('hex'))
    rgbcol = [x / 255.0 for x in rgbcol]
    return rgbcol
    
def RGBtoHex(rgbarray):   
    rgbarray = [x * 255.0 for x in rgbarray]
    hex = "#" + struct.pack('BBB',*rgbarray).encode('hex')    
    return hex

# Set prim attributes - prim is the newly created Hou geo, polygon is the imported svg path
def setAttributes(path, prim):
    prim.setAttribValue("prid", ID)    
    # set fill clr
    try:
        f = path.getAttribute("fill")
        fill = hexToRGB(f)
    except:
        fill = [-1.0,-1.0,-1.0]
    prim.setAttribValue("fill", fill)
    # set fill alpha
    try:
        alpha = float(path.getAttribute("opacity"))
    except:
        alpha = 1.0
    prim.setAttribValue("Alpha", alpha) 
    # set stroke clr
    try:
        f = path.getAttribute("stroke").replace('#', '')
        stroke = hexToRGB(f)
    except:
        stroke = [-1.0,-1.0,-1.0]
    prim.setAttribValue("stroke", stroke)    
    # set pscale? (stroke)
    try:
        strokewidth = float(path.getAttribute("stroke-width"))   
    except:
        strokewidth = 0.0
    prim.setAttribValue("pscale", strokewidth)
    
    # try set idname
    try:
        idname = str(path.getAttribute("id"))
    except:
        idname = "error"
    prim.setAttribValue("id_name", idname)
    
    # try set idname
    # try:
    #     clalas = str(path.getAttribute("class"))
    # except:
    #     clalas = "error"
    # prim.setAttribValue("class", clalas)    
    try:
        l_name = str(path.getAttribute("layername"))
    except:
        l_name = "error_layername"
    prim.setAttribValue("layer_name", l_name)

# =======================================
# TODO
# Groups </g>
# More error checks
# =======================================
ID = 0 # global identifier, incremented for each added shape/path (compound paths have a single id)

node = hou.pwd()
geo = node.geometry()
p = hou.evalParm("../path")

#definition = hou.node("..").type().definition()
#read = definition.sections()['TestSVG.svg'].contents()
# print read
#doc = minidom.parseString(read)

#with open(p, 'r') as myfile:
#    f = myfile.read()
#    #.replace('\n', '').replace('\r', '')
#    print f
    
#with open(p, 'rb+') as f:
#    content = f.read()
#    print content
#    f.seek(0)
#    f.write(content.replace(b'\r', b''))
#    f.write(content.replace(b'\n', b''))    
#    f.truncate()    

doc = minidom.parse(p)

# ==========================
# ATTEMPT  number 1 TO TRANSFER LAYER NAMES TO POLYGONS
# ==========================
g_items = doc.getElementsByTagName("g")
for itemm in g_items:
    layer_name = itemm.getAttribute("id") 
    for n in itemm.childNodes[1::2]: # every even item
        n.setAttribute("layername", layer_name)

        # print(n.getAttribute("layername"))


#>>> a[1::2]
#[2, 4, 6, 8]
#>>> a[::2]
#[1, 3, 5, 7, 9]

# ==========================
# POLYGONS AND RECTS AND CIRCLES
# ==========================
polygons = doc.getElementsByTagName('polygon')
for idx, polygon in enumerate(polygons):
    prim = geo.createPolygon()
    setAttributes(polygon, prim)
    ID += 1    
        
    # create points
    ptsstring = polygon.getAttribute("points").strip() 
    points = split("[\s,]", " ".join(ptsstring.split()))  # remove multiple spaces and extract coords  
    i=0
    while i < len(points):
        pp = geo.createPoint()
        pp.setPosition((atof(points[i]), -atof(points[i+1]),0))
        prim.addVertex(pp)
        i = i + 2
        
# Rect
rects = doc.getElementsByTagName('rect')    
for idx, rect in enumerate(rects):
    prim = geo.createPolygon()
    setAttributes(rect, prim)    
    ID += 1    
    # get rect values
    x = atof(rect.getAttribute("x"))
    y = atof(rect.getAttribute("y"))
    width = atof(rect.getAttribute("width"))
    height = atof(rect.getAttribute("height"))
    points = [[x, -y], [x+width,-y],[x+width,-y-height], [x, -y-height]]
    for pt in points:        
        a = geo.createPoint()
        a.setPosition((pt[0], pt[1], 0))
        prim.addVertex(a)        
     
# Circle
circles = doc.getElementsByTagName('circle')    
for idx, circle in enumerate(circles):
    prim = geo.createBezierCurve(12, True, order=4)
    setAttributes(circle, prim)    
    ID += 1    
    # get circle values
    cx = atof(circle.getAttribute("cx"))
    cy = -atof(circle.getAttribute("cy"))
    r = atof(circle.getAttribute("r"))
    
    ctrl = 0.552284749831 # bezier circle
    points = []
    # clockwise from right pt?
    points.append(hou.Vector3(cx + r, cy, 0))    
    points.append(hou.Vector3(cx + r, cy + r*ctrl, 0))    
    points.append(hou.Vector3(cx + r*ctrl, cy + r, 0))  
    points.append(hou.Vector3(cx, cy + r, 0))    
    points.append(hou.Vector3(cx - r*ctrl, cy + r, 0))    
    points.append(hou.Vector3(cx - r, cy + r*ctrl, 0))  
    points.append(hou.Vector3(cx - r, cy, 0))    
    points.append(hou.Vector3(cx - r, cy - r*ctrl, 0))    
    points.append(hou.Vector3(cx - r*ctrl, cy - r, 0))  
    points.append(hou.Vector3(cx , cy - r, 0))    
    points.append(hou.Vector3(cx + r*ctrl, cy - r, 0))    
    points.append(hou.Vector3(cx + r, cy - r*ctrl, 0))      
    for i, v in enumerate(prim.vertices()):
        p = v.point()
        p.setPosition(points[i])          
        
# ==========================
# LINES AND POLYLINES
# ==========================
lines = doc.getElementsByTagName('line')    
for idx, line in enumerate(lines):
    prim = geo.createPolygon()
    prim.setIsClosed(False)
    setAttributes(line, prim)    
    ID += 1    
    
    # get line values
    x1 = line.getAttribute("x1")
    y1 = line.getAttribute("y1")
    x2 = line.getAttribute("x2")
    y2 = line.getAttribute("y2")
    a = geo.createPoint()
    a.setPosition((atof(x1), -atof(y1),0))
    prim.addVertex(a)
    b = geo.createPoint()
    b.setPosition((atof(x2), -atof(y2),0))
    prim.addVertex(b)

polylines = doc.getElementsByTagName('polyline')  
for idx, polyline in enumerate(polylines):
    prim = geo.createPolygon()
    prim.setIsClosed(False)
    setAttributes(polyline, prim)    
    ID += 1 
    
    ptsstring = polyline.getAttribute("points").strip()
    points = split("[\s,]", " ".join(ptsstring.split()))
    i = 0
    while i < len(points):
        pp = geo.createPoint()
        pp.setPosition((atof(points[i]), -atof(points[i+1]),0))
        prim.addVertex(pp)
        i = i + 2    
        
# ==========================
# PATHS (Cubic Bezier)
# ==========================
paths = doc.getElementsByTagName('path')
for idx, path in enumerate(paths):
    ID += 1
    d = path.getAttribute('d')
    
    # super hack to insert Z before any M which isnt the first...?
    start = d[0:2]
    d = d[2:]
    d = re.sub('M', 'ZM', d)
    d = start + d
    
    segs = parse_path(d) 
    
    # path splitting
    # do we also need to Split with others delims etc...
    # split with 'z' or 'Z'?
    delim = "Z"
    a = d.split(delim)
    if(len(a) > 1):
        compound = [e+delim for e in a if e] # split but also keep the z's. Closed bez case
    else:
        compound = a # open bezier case        
        
    ID += 1
    for shape in compound:
        pathObj = parse_path(shape) 
        if(len(pathObj) == 0):
            continue
        
        #print pathObj
        # Creates single segment Prims for paths which contain mixed segments (can polypath later after conversion from bezier) 
        # Sometimes paths which 
        allbez = all(isinstance(x, svg.path.CubicBezier) for x in pathObj)
        allline = all(isinstance(x, svg.path.Line) for x in pathObj)
        allquad = all(isinstance(x, svg.path.QuadraticBezier) for x in pathObj)
        force = hou.evalParm("../force_single")
        if (not allbez or allline or allquad) or force:
            # print "mismatched segments - creating prims for each single segment path element"        
            for part in pathObj:
                if isinstance(part, svg.path.Line):
                    prim = geo.createPolygon()
                    prim.setIsClosed(False)                    
                    setAttributes(path, prim)    
                    a = geo.createPoint()
                    a.setPosition(hou.Vector3(part.start.real, -part.start.imag, 0.0))
                    prim.addVertex(a)
                    a = geo.createPoint()
                    a.setPosition(hou.Vector3(part.end.real, -part.end.imag, 0.0))
                    prim.addVertex(a)                     
                elif isinstance(part, svg.path.CubicBezier) or isinstance(part, svg.path.QuadraticBezier):
                    prim = geo.createBezierCurve(4, False, order=4)  
                    setAttributes(path, prim)                    
                    # create ptlist based on cubic/quadratic segment
                    point_list = (part.start, part.control1, part.control2, part.end) if isinstance(part, svg.path.CubicBezier) else (part.start, part.control, part.control, part.end)
                    points = ()                        
                    for p in point_list:
                        points += (hou.Vector3(p.real, -p.imag, 0.0),)                      
                    for i, v in enumerate(prim.vertices()):
                        v.point().setPosition(points[i])   
                else:
                    print "invalid path segment - skipping"
        # Creates a single Cubic Bezier curve from paths with consistent segments
        else:        
            is_closed = pathObj.closed
            if(is_closed):
                prim = geo.createBezierCurve(len(pathObj) * 3, True, order=4)
            else:
                prim = geo.createBezierCurve(len(pathObj) * 3 + 1, False, order=4)   
            setAttributes(path, prim) # set clr, stroke etc
                    
            points = ()
            for part in pathObj:
                start = part.start
                end = part.end
                point_list = (part.start,)
                if isinstance(part, svg.path.path.Line):
                    point_list += (part.start, part.end)
                if isinstance(part, svg.path.path.CubicBezier):
                    point_list += (part.control1, part.control2)
                    if not is_closed: # if open, also add the endpoint
                        point_list += (part.end,)     
                if isinstance(part, svg.path.path.QuadraticBezier): # broken?
                    point_list += (part.control, part.control)
                    if not is_closed: # if open, also add the endpoint
                        point_list += (part.end,)                          
                for p in point_list:
                    pos = hou.Vector3(p.real, -p.imag, 0.0)
                    points += (pos,)
                                 
            for i, v in enumerate(prim.vertices()):
                v.point().setPosition(points[i])