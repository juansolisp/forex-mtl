#!/usr/bin/env python3
"""
forex-mtl E2E Flow Diagrams PDF
Visual diagrams of every flow, timer, HTTP call, constraint and response.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Circle, Polygon,
    Group, Path
)
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
import math

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm

# ── Colours ──────────────────────────────────────────────────────────────────
C_BG       = colors.HexColor('#0f172a')   # dark navy
C_SURFACE  = colors.HexColor('#1e293b')   # card bg
C_BORDER   = colors.HexColor('#334155')   # card border
C_PURPLE   = colors.HexColor('#7c3aed')
C_PURPLEL  = colors.HexColor('#a78bfa')
C_CYAN     = colors.HexColor('#0891b2')
C_CYANL    = colors.HexColor('#67e8f9')
C_GREEN    = colors.HexColor('#16a34a')
C_GREENL   = colors.HexColor('#86efac')
C_ORANGE   = colors.HexColor('#ea580c')
C_ORANGEL  = colors.HexColor('#fdba74')
C_RED      = colors.HexColor('#dc2626')
C_REDL     = colors.HexColor('#fca5a5')
C_YELLOW   = colors.HexColor('#ca8a04')
C_YELLOWL  = colors.HexColor('#fde047')
C_GRAY     = colors.HexColor('#64748b')
C_GRAYL    = colors.HexColor('#94a3b8')
C_WHITE    = colors.white
C_BLACK    = colors.black
C_TEXT     = colors.HexColor('#f1f5f9')
C_SUBTEXT  = colors.HexColor('#94a3b8')

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

def style(name, parent='Normal', **kw):
    s = ParagraphStyle(name, parent=ss[parent], **kw)
    return s

S_TITLE   = style('Title2',  fontSize=28, leading=34, textColor=C_WHITE,
                  fontName='Helvetica-Bold', spaceAfter=6, alignment=TA_CENTER)
S_SUBTITLE= style('Sub2',    fontSize=13, leading=17, textColor=C_PURPLEL,
                  fontName='Helvetica', spaceAfter=4, alignment=TA_CENTER)
S_H1      = style('H1b',     fontSize=18, leading=22, textColor=C_CYANL,
                  fontName='Helvetica-Bold', spaceBefore=14, spaceAfter=6)
S_H2      = style('H2b',     fontSize=13, leading=17, textColor=C_PURPLEL,
                  fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4)
S_H3      = style('H3b',     fontSize=11, leading=14, textColor=C_ORANGEL,
                  fontName='Helvetica-Bold', spaceBefore=7, spaceAfter=3)
S_BODY    = style('Bodyb',   fontSize=9,  leading=13, textColor=C_TEXT,
                  fontName='Helvetica', spaceAfter=4)
S_SMALL   = style('Smallb',  fontSize=8,  leading=11, textColor=C_SUBTEXT,
                  fontName='Helvetica', spaceAfter=3)
S_CODE    = style('Codeb',   fontSize=8,  leading=11, textColor=C_GREENL,
                  fontName='Courier', spaceAfter=2,
                  backColor=C_SURFACE, leftIndent=8, rightIndent=8,
                  borderPadding=4)
S_CAPTION = style('Capb',    fontSize=8,  leading=11, textColor=C_SUBTEXT,
                  fontName='Helvetica-Oblique', spaceAfter=6, alignment=TA_CENTER)
S_NOTE    = style('Noteb',   fontSize=8,  leading=11, textColor=C_YELLOWL,
                  fontName='Helvetica', spaceAfter=4, leftIndent=10)
S_LABEL   = style('Labelb',  fontSize=7.5, leading=10, textColor=C_SUBTEXT,
                  fontName='Helvetica', spaceAfter=1)

def hr():
    return HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=8, spaceBefore=4)

def sp(h=6):
    return Spacer(1, h)

def h1(t): return Paragraph(t, S_H1)
def h2(t): return Paragraph(t, S_H2)
def h3(t): return Paragraph(t, S_H3)
def body(t): return Paragraph(t, S_BODY)
def small(t): return Paragraph(t, S_SMALL)
def note(t): return Paragraph(f'⚠ {t}', S_NOTE)
def caption(t): return Paragraph(t, S_CAPTION)
def code(t): return Paragraph(t, S_CODE)

# ── Drawing helpers ───────────────────────────────────────────────────────────

def box(d, x, y, w, h, fill=C_SURFACE, stroke=C_BORDER, r=6, sw=1):
    d.add(Rect(x, y, w, h, rx=r, ry=r, fillColor=fill, strokeColor=stroke, strokeWidth=sw))

def label(d, x, y, txt, size=8, color=C_TEXT, bold=False, align='middle'):
    fn = 'Helvetica-Bold' if bold else 'Helvetica'
    d.add(String(x, y, txt, fontSize=size, fillColor=color,
                 fontName=fn, textAnchor=align))

def arrow_right(d, x1, y, x2, color=C_GRAY, label_txt='', lcolor=None, sw=1.5):
    d.add(Line(x1, y, x2-6, y, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x2-6, y+4, x2, y, x2-6, y-4],
                  fillColor=color, strokeColor=color, strokeWidth=0))
    if label_txt:
        mx = (x1+x2)/2
        d.add(String(mx, y+3, label_txt, fontSize=7, fillColor=lcolor or C_SUBTEXT,
                     fontName='Helvetica', textAnchor='middle'))

def arrow_left(d, x1, y, x2, color=C_GRAY, label_txt='', lcolor=None, sw=1.5):
    d.add(Line(x1, y, x2+6, y, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x2+6, y+4, x2, y, x2+6, y-4],
                  fillColor=color, strokeColor=color, strokeWidth=0))
    if label_txt:
        mx = (x1+x2)/2
        d.add(String(mx, y+3, label_txt, fontSize=7, fillColor=lcolor or C_SUBTEXT,
                     fontName='Helvetica', textAnchor='middle'))

def arrow_down(d, x, y1, y2, color=C_GRAY, label_txt='', sw=1.5):
    d.add(Line(x, y1, x, y2+6, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x-4, y2+6, x, y2, x+4, y2+6],
                  fillColor=color, strokeColor=color, strokeWidth=0))
    if label_txt:
        my = (y1+y2)/2
        d.add(String(x+4, my, label_txt, fontSize=7, fillColor=C_SUBTEXT,
                     fontName='Helvetica', textAnchor='start'))

def arrow_up(d, x, y1, y2, color=C_GRAY, label_txt='', sw=1.5):
    d.add(Line(x, y1, x, y2-6, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x-4, y2-6, x, y2, x+4, y2-6],
                  fillColor=color, strokeColor=color, strokeWidth=0))
    if label_txt:
        my = (y1+y2)/2
        d.add(String(x+4, my, label_txt, fontSize=7, fillColor=C_SUBTEXT,
                     fontName='Helvetica', textAnchor='start'))

def dashed_line(d, x1, y1, x2, y2, color=C_GRAY, sw=1):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=sw,
               strokeDashArray=[4, 3]))

def node(d, x, y, w, h, title, subtitle='', fill=C_SURFACE, stroke=C_BORDER,
         title_color=C_WHITE, sub_color=C_SUBTEXT, r=6, icon='', sw=1.5):
    box(d, x, y, w, h, fill=fill, stroke=stroke, r=r, sw=sw)
    ty = y + h/2 + (5 if subtitle else 0)
    if icon:
        label(d, x + w/2 - (len(title)*3.5)/2 - 6, ty, icon, size=10, color=title_color, align='start')
        label(d, x + w/2 - (len(title)*3.5)/2 + 4, ty, title, size=9, color=title_color, bold=True, align='start')
    else:
        label(d, x + w/2, ty, title, size=9, color=title_color, bold=True, align='middle')
    if subtitle:
        label(d, x + w/2, y + h/2 - 8, subtitle, size=7, color=sub_color, align='middle')

# ── Flowable wrapper for Drawing ──────────────────────────────────────────────

class DiagramFlow(Flowable):
    def __init__(self, drawing):
        Flowable.__init__(self)
        self.drawing = drawing
        self.width   = drawing.width
        self.height  = drawing.height

    def draw(self):
        renderPDF.draw(self.drawing, self.canv, 0, 0)

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 1 — System Architecture Overview
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_architecture():
    W, H = 480, 280
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    # ── components ───────────────────────────────────────────────────────────
    # Browser
    node(d,  10, 180, 90, 50, 'Browser', 'localhost:3001',
         fill=colors.HexColor('#1a1a3e'), stroke=C_PURPLE, title_color=C_PURPLEL, sw=2)

    # Frontend (Nginx+React)
    node(d, 130, 180, 100, 50, 'Frontend', 'Nginx + React',
         fill=colors.HexColor('#1a2a3e'), stroke=C_CYAN, title_color=C_CYANL, sw=2)

    # forex-proxy
    node(d, 260, 130, 110, 100, 'forex-proxy', ':9090',
         fill=colors.HexColor('#1a2e1a'), stroke=C_GREEN, title_color=C_GREENL, sw=2)
    label(d, 315, 210, 'Scala / http4s', size=7, color=C_SUBTEXT, align='middle')
    label(d, 315, 198, 'cats-effect 2', size=7, color=C_SUBTEXT, align='middle')

    # One-Frame
    node(d, 390, 180, 80, 50, 'One-Frame', ':18080 (ext)',
         fill=colors.HexColor('#2e1a1a'), stroke=C_ORANGE, title_color=C_ORANGEL, sw=2)

    # Cache (inside forex-proxy)
    box(d, 266, 138, 98, 38, fill=colors.HexColor('#0a1f0a'), stroke=C_GREEN, r=4, sw=1)
    label(d, 315, 162, 'Ref[Map[Pair,Rate]]', size=7, color=C_GREENL, align='middle')
    label(d, 315, 151, '72 pairs in memory', size=6.5, color=C_SUBTEXT, align='middle')

    # ── arrows ───────────────────────────────────────────────────────────────
    # Browser ↔ Frontend
    arrow_right(d, 100, 210, 130, color=C_PURPLE, label_txt='HTTP/SSE', lcolor=C_PURPLEL)
    arrow_left(d,  100, 200, 130, color=C_PURPLE, label_txt='HTML/JSON', lcolor=C_PURPLEL)

    # Frontend ↔ forex-proxy  (proxied by Nginx)
    arrow_right(d, 230, 210, 260, color=C_CYAN, label_txt='proxy_pass', lcolor=C_CYANL)
    arrow_left(d,  230, 200, 260, color=C_CYAN, label_txt='JSON/SSE',   lcolor=C_CYANL)

    # forex-proxy ↔ One-Frame
    arrow_right(d, 370, 210, 390, color=C_ORANGE, label_txt='GET /rates', lcolor=C_ORANGEL)
    arrow_left(d,  370, 200, 390, color=C_ORANGE, label_txt='72 pairs',   lcolor=C_ORANGEL)

    # ── timer badge ──────────────────────────────────────────────────────────
    box(d, 262, 80, 106, 44, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=4)
    label(d, 315, 114, 'Cache Refresh Timer', size=8, color=C_PURPLEL, bold=True, align='middle')
    label(d, 315, 103, 'every 240s (configurable)', size=7, color=C_SUBTEXT, align='middle')
    label(d, 315,  92, '90s – 300s range', size=7, color=C_GRAY, align='middle')
    arrow_up(d, 315, 128, 138, color=C_PURPLE, sw=1)

    # ── labels ───────────────────────────────────────────────────────────────
    label(d, 55,  175, ':3001', size=7, color=C_SUBTEXT, align='middle')
    label(d, 180, 175, ':80 (internal)', size=7, color=C_SUBTEXT, align='middle')

    # ── legend ───────────────────────────────────────────────────────────────
    label(d, 12, 90, 'Legend:', size=7.5, color=C_SUBTEXT, bold=True, align='start')
    box(d, 12, 60, 10, 8, fill=C_PURPLE, stroke=C_PURPLE, r=1)
    label(d, 26, 65, 'Browser/UI', size=7, color=C_SUBTEXT, align='start')
    box(d, 82, 60, 10, 8, fill=C_CYAN, stroke=C_CYAN, r=1)
    label(d, 96, 65, 'Nginx proxy', size=7, color=C_SUBTEXT, align='start')
    box(d, 152, 60, 10, 8, fill=C_GREEN, stroke=C_GREEN, r=1)
    label(d, 166, 65, 'forex-proxy (Scala)', size=7, color=C_SUBTEXT, align='start')
    box(d, 252, 60, 10, 8, fill=C_ORANGE, stroke=C_ORANGE, r=1)
    label(d, 266, 65, 'One-Frame (external)', size=7, color=C_SUBTEXT, align='start')

    label(d, W//2, 28, 'All 3 services run in Docker on the same host network', size=7.5,
          color=C_SUBTEXT, align='middle')
    label(d, W//2, 16, 'Nginx on :3001 proxies /api/* → :9090 and serves static React build',
          size=7, color=C_GRAY, align='middle')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 2 — Rate Request (Happy Path) Sequence
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_rate_request():
    W, H = 480, 340
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    # ── lifeline headers ─────────────────────────────────────────────────────
    cols = [50, 160, 280, 400]
    names = ['Client', 'Nginx\n:3001', 'forex-proxy\n:9090', 'Cache\n(Ref)']
    colors_h = [C_PURPLE, C_CYAN, C_GREEN, C_GREENL]
    for i,(cx,nm,cl) in enumerate(zip(cols, names, colors_h)):
        box(d, cx-35, H-38, 70, 28, fill=C_SURFACE, stroke=cl, r=4, sw=1.5)
        lines = nm.split('\n')
        label(d, cx, H-20, lines[0], size=8, color=cl, bold=True, align='middle')
        if len(lines)>1:
            label(d, cx, H-10, lines[1], size=6.5, color=C_SUBTEXT, align='middle')
        # dashed lifeline
        dashed_line(d, cx, H-38, cx, 10, color=C_BORDER, sw=1)

    # ── sequence steps ───────────────────────────────────────────────────────
    steps = [
        # (y, x1, x2, direction, label, sublabel, color, note)
        (300, 0, 1, 'r', 'GET /rates?from=USD&to=JPY', 'HTTP/1.1', C_PURPLE, ''),
        (280, 1, 2, 'r', 'proxy_pass → :9090/rates?from=USD&to=JPY', '', C_CYAN, ''),
        (260, 2, 3, 'r', 'ref.get', 'O(1) lookup', C_GREEN, ''),
        (240, 3, 2, 'l', 'Rate{price, timestamp}', '< 1ms', C_GREENL, ''),
        (220, 2, 1, 'l', '200 OK  {"from":"USD","to":"JPY","price":...}', '', C_GREEN, ''),
        (200, 1, 0, 'l', '200 OK  JSON + X-Request-ID header', '', C_CYAN, ''),
    ]

    cx_map = cols

    for (y, ci, cj, dr, lbl, sub, cl, nt) in steps:
        x1 = cx_map[ci]
        x2 = cx_map[cj]
        if dr == 'r':
            arrow_right(d, x1+35, y, x2-35, color=cl, sw=1.5)
        else:
            arrow_left(d, x1-35, y, x2+35, color=cl, sw=1.5)
        mx = (x1+x2)/2
        label(d, mx, y+5, lbl, size=7, color=cl, align='middle')
        if sub:
            label(d, mx, y-5, sub, size=6.5, color=C_SUBTEXT, align='middle')

    # ── SSE publish side-effect ───────────────────────────────────────────────
    # arrow from proxy to the side showing event published
    box(d, 340, 210, 110, 22, fill=colors.HexColor('#1a2e1a'), stroke=C_GREEN, r=3)
    label(d, 395, 224, 'eventBus.publish(', size=7, color=C_GREENL, align='middle')
    label(d, 395, 214, '  ProxyRequest event)', size=7, color=C_GREENL, align='middle')
    arrow_right(d, 315, 218, 340, color=C_GREEN, sw=1)

    # ── activation boxes ─────────────────────────────────────────────────────
    box(d, 277, 195, 6, 110, fill=C_GREEN, stroke=C_GREEN, r=1, sw=0)

    # ── step numbers ─────────────────────────────────────────────────────────
    for i,(y,_,_,_,_,_,_,_) in enumerate(steps):
        label(d, 8, y+2, str(i+1), size=7, color=C_SUBTEXT, bold=True, align='middle')

    # ── timing badge ─────────────────────────────────────────────────────────
    box(d, 8, 60, 120, 52, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=4)
    label(d, 68, 100, 'Timing', size=8, color=C_PURPLEL, bold=True, align='middle')
    label(d, 68,  89, 'Cache lookup: < 1ms', size=7, color=C_TEXT, align='middle')
    label(d, 68,  79, 'Total latency: < 5ms', size=7, color=C_TEXT, align='middle')
    label(d, 68,  69, '0 calls to One-Frame', size=7, color=C_GREENL, align='middle')

    # ── constraint badge ─────────────────────────────────────────────────────
    box(d, 140, 60, 130, 52, fill=colors.HexColor('#2e1a1a'), stroke=C_ORANGE, r=4)
    label(d, 205, 100, 'Validation', size=8, color=C_ORANGEL, bold=True, align='middle')
    label(d, 205,  89, '?from= and ?to= required', size=7, color=C_TEXT, align='middle')
    label(d, 205,  79, 'Must be valid currency code', size=7, color=C_TEXT, align='middle')
    label(d, 205,  69, '→ 400 if invalid/missing', size=7, color=C_REDL, align='middle')

    # ── response schema ───────────────────────────────────────────────────────
    box(d, 8, 10, 460, 44, fill=C_SURFACE, stroke=C_BORDER, r=4)
    label(d, 14, 44, 'Response schema:', size=7, color=C_SUBTEXT, bold=True, align='start')
    label(d, 14, 33, '{"from":"USD","to":"JPY","price":134.56,"timestamp":"2026-02-28T22:30:09Z"}',
          size=7, color=C_GREENL, align='start')
    label(d, 14, 22, 'Error 400: {"errors":["Invalid value for: query parameter from"]}',
          size=7, color=C_REDL, align='start')
    label(d, 14, 12, 'Error 500: {"message":"Rate for USD/JPY not in cache"}',
          size=7, color=C_REDL, align='start')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 3 — Cache Refresh Cycle
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_cache_refresh():
    W, H = 480, 360
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    # ── lifeline headers ─────────────────────────────────────────────────────
    cols  = [55, 175, 300, 420]
    names = ['Refresh\nStream', 'OneFrameLive\n(HTTP client)', 'One-Frame\n:18080', 'Cache\n(Ref)']
    clrs  = [C_PURPLE, C_CYAN, C_ORANGE, C_GREEN]
    for cx, nm, cl in zip(cols, names, clrs):
        box(d, cx-42, H-38, 84, 28, fill=C_SURFACE, stroke=cl, r=4, sw=1.5)
        lines = nm.split('\n')
        label(d, cx, H-20, lines[0], size=8, color=cl, bold=True, align='middle')
        if len(lines)>1:
            label(d, cx, H-10, lines[1], size=6.5, color=C_SUBTEXT, align='middle')
        dashed_line(d, cx, H-38, cx, 10, color=C_BORDER, sw=1)

    # ── steps ─────────────────────────────────────────────────────────────────
    # Timer fires
    box(d, 10, 295, 90, 18, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=3)
    label(d, 55, 306, 'Timer fires (240s)', size=7, color=C_PURPLEL, align='middle')
    arrow_down(d, 55, 295, 277, color=C_PURPLE, sw=1.5)

    # doRefresh starts
    label(d, 55, 272, 'doRefresh()', size=7.5, color=C_PURPLE, bold=True, align='middle')

    # Build request
    arrow_right(d, 97, 258, 133, color=C_CYAN, sw=1.5)
    label(d, 115, 262, 'fetchAll(72 pairs)', size=7, color=C_CYANL, align='middle')

    # HTTP call to One-Frame
    arrow_right(d, 217, 244, 258, color=C_ORANGE, sw=1.5)
    label(d, 237, 248, 'GET /rates', size=7, color=C_ORANGEL, align='middle')
    label(d, 237, 238, '?pair=USDJPY&pair=USDEUR...', size=6.5, color=C_SUBTEXT, align='middle')
    label(d, 237, 228, '(72 pairs, 1 request)', size=6.5, color=C_SUBTEXT, align='middle')
    label(d, 237, 218, 'token: 10dc303...', size=6.5, color=C_GRAY, align='middle')

    # Response from One-Frame
    arrow_left(d, 217, 200, 258, color=C_ORANGE, sw=1.5)
    label(d, 237, 204, '200 OK  [{from,to,bid,ask,price,time_stamp}×72]', size=6.5, color=C_ORANGEL, align='middle')

    # Parse
    label(d, 175, 190, 'decode JSON, build Map[Pair→Rate]', size=7, color=C_CYAN, align='middle')

    # Return to refresh stream
    arrow_left(d, 97, 175, 133, color=C_CYAN, sw=1.5)
    label(d, 115, 179, 'Right(List[Rate])', size=7, color=C_CYANL, align='middle')

    # Update cache Ref
    arrow_right(d, 97, 158, 378, color=C_GREEN, sw=1.5)
    label(d, 237, 162, 'ref.set(newMap)  lastRefreshedAtRef.set(now)', size=7, color=C_GREENL, align='middle')

    # Publish event
    box(d, 10, 130, 450, 18, fill=colors.HexColor('#1a2e1a'), stroke=C_GREEN, r=3)
    label(d, 235, 141, 'eventBus.publish( CacheRefresh{pairsCount=72, durationMs, timestamp} )',
          size=7, color=C_GREENL, align='middle')

    # SSE flows to browser
    box(d, 10, 108, 450, 18, fill=colors.HexColor('#1a1a2e'), stroke=C_PURPLE, r=3)
    label(d, 235, 119, '→ SSE: data: {"type":"CacheRefresh","pairsCount":72,"durationMs":312,"timestamp":"..."}',
          size=7, color=C_PURPLEL, align='middle')

    # next sleep
    box(d, 10, 86, 180, 18, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=3)
    label(d, 55, 97, 'sleep(240s)  — next cycle', size=7, color=C_PURPLEL, align='middle')
    arrow_right(d, 97, 95, 190, color=C_PURPLE, sw=1)
    label(d, 150, 99, 'or race with setInterval()', size=6.5, color=C_SUBTEXT, align='middle')

    # ── constraint box ───────────────────────────────────────────────────────
    box(d, 290, 60, 185, 60, fill=colors.HexColor('#2e1a0a'), stroke=C_ORANGE, r=4)
    label(d, 382, 110, 'One-Frame Constraints', size=8, color=C_ORANGEL, bold=True, align='middle')
    label(d, 382,  99, '≤ 1,000 calls / day', size=7.5, color=C_TEXT, align='middle')
    label(d, 382,  89, '240s interval → 360 calls/day', size=7, color=C_GREENL, align='middle')
    label(d, 382,  79, 'SLA: data fresh < 300s', size=7.5, color=C_TEXT, align='middle')
    label(d, 382,  69, 'Buffer: 300-240 = 60s margin', size=7, color=C_CYANL, align='middle')

    # ── error path note ───────────────────────────────────────────────────────
    box(d, 10, 60, 270, 22, fill=colors.HexColor('#2e1a1a'), stroke=C_RED, r=3)
    label(d, 14, 74, 'On error: publish CacheRefreshFailed  |  old data kept  |  stream continues',
          size=7, color=C_REDL, align='start')
    label(d, 14, 64, 'handleErrorWith → never crashes the refresh stream', size=7, color=C_SUBTEXT, align='start')

    # ── step numbers ─────────────────────────────────────────────────────────
    ys = [306, 262, 248, 200, 158, 141, 119, 97]
    for i,y in enumerate(ys):
        label(d, 480-12, y, str(i+1), size=7, color=C_SUBTEXT, bold=True, align='middle')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 4 — SSE / Heartbeat Event Flow
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_sse_heartbeat():
    W, H = 480, 360
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    # ── three columns: Server | SSE wire | Browser ───────────────────────────
    # Server box
    box(d, 8, 60, 150, 278, fill=C_SURFACE, stroke=C_GREEN, r=6, sw=1.5)
    label(d, 83, 328, 'forex-proxy (Server)', size=9, color=C_GREENL, bold=True, align='middle')

    # EventBus
    box(d, 16, 230, 134, 40, fill=colors.HexColor('#0a2e0a'), stroke=C_GREEN, r=4, sw=1)
    label(d, 83, 256, 'EventBus', size=8, color=C_GREENL, bold=True, align='middle')
    label(d, 83, 246, 'fs2.Topic  buf=128', size=7, color=C_SUBTEXT, align='middle')
    label(d, 83, 236, 'CacheRefresh  ProxyRequest  Failed', size=6.5, color=C_SUBTEXT, align='middle')

    # Heartbeat generator
    box(d, 16, 165, 134, 52, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=4, sw=1)
    label(d, 83, 206, 'Heartbeat Stream', size=8, color=C_PURPLEL, bold=True, align='middle')
    label(d, 83, 196, 'per-connection', size=7, color=C_SUBTEXT, align='middle')
    label(d, 83, 186, 'Stream.repeatEval.metered(30s)', size=6.5, color=C_SUBTEXT, align='middle')
    label(d, 83, 176, '{serverTimeMs, lastRefreshedAt}', size=6.5, color=C_PURPLEL, align='middle')

    # merge
    box(d, 50, 138, 66, 22, fill=colors.HexColor('#0f172a'), stroke=C_BORDER, r=3)
    label(d, 83, 151, '  merge()', size=8, color=C_TEXT, bold=True, align='middle')
    arrow_down(d, 83, 165, 160, color=C_PURPLE, sw=1.5)
    arrow_down(d, 83, 230, 160, color=C_GREEN, sw=1.5)

    # SSE encoder
    box(d, 16, 95, 134, 30, fill=C_SURFACE, stroke=C_BORDER, r=4, sw=1)
    label(d, 83, 116, 'SSE Encoder', size=8, color=C_TEXT, bold=True, align='middle')
    label(d, 83, 106, '"data: {...}\\n\\n"', size=7, color=C_CYANL, align='middle')
    arrow_down(d, 83, 138, 125, color=C_GRAY, sw=1.5)

    # ── SSE wire (middle) ─────────────────────────────────────────────────────
    box(d, 172, 60, 110, 278, fill=colors.HexColor('#0f1629'), stroke=C_BORDER, r=6, sw=1)
    label(d, 227, 330, 'SSE Connection', size=9, color=C_CYANL, bold=True, align='middle')
    label(d, 227, 318, 'GET /events  (keep-alive)', size=7, color=C_SUBTEXT, align='middle')
    label(d, 227, 307, 'Content-Type: text/event-stream', size=7, color=C_SUBTEXT, align='middle')

    # wire events listed
    events = [
        (265, 'Heartbeat (t=0)', C_PURPLEL),
        (240, 'ProxyRequest (on each /rates)', C_CYAN),
        (215, 'CacheRefresh (on refresh)', C_GREENL),
        (190, 'CacheRefreshFailed (on error)', C_REDL),
        (165, 'Heartbeat (t=30s)', C_PURPLEL),
        (140, 'Heartbeat (t=60s)', C_PURPLEL),
        (115,  '... (every 30s)', C_GRAY),
        (90,  'CacheRefresh (t=240s)', C_GREENL),
    ]
    for ey, etxt, ecl in events:
        box(d, 178, ey-8, 98, 14, fill=C_SURFACE, stroke=ecl, r=2, sw=0.5)
        label(d, 227, ey, etxt, size=6.5, color=ecl, align='middle')

    # arrows from server → wire
    arrow_right(d, 150, 108, 172, color=C_CYAN, sw=1.5)
    label(d, 161, 112, 'stream', size=6.5, color=C_SUBTEXT, align='middle')

    # ── Browser box ───────────────────────────────────────────────────────────
    box(d, 296, 60, 180, 278, fill=C_SURFACE, stroke=C_PURPLE, r=6, sw=1.5)
    label(d, 386, 330, 'Browser (React)', size=9, color=C_PURPLEL, bold=True, align='middle')

    # useEventStream singleton
    box(d, 304, 270, 164, 52, fill=colors.HexColor('#1a1a3e'), stroke=C_PURPLE, r=4, sw=1)
    label(d, 386, 312, 'useEventStream (singleton)', size=8, color=C_PURPLEL, bold=True, align='middle')
    label(d, 386, 302, 'globalEntries: LogEntry[]', size=7, color=C_TEXT, align='middle')
    label(d, 386, 292, 'MAX_EVENTS = 2000 ring buffer', size=7, color=C_SUBTEXT, align='middle')
    label(d, 386, 282, 'globalClockOffsetMs = serverMs−now', size=7, color=C_SUBTEXT, align='middle')

    # heartbeat listeners
    box(d, 304, 210, 164, 38, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=4, sw=1)
    label(d, 386, 236, 'heartbeatListeners (Set)', size=8, color=C_PURPLEL, bold=True, align='middle')
    label(d, 386, 226, '→ FreshnessBar.addHeartbeatListener', size=7, color=C_SUBTEXT, align='middle')
    label(d, 386, 216, '→ setLastRefreshedAt(hb.lastRefreshedAt)', size=7, color=C_SUBTEXT, align='middle')

    # FreshnessBar
    box(d, 304, 155, 164, 44, fill=colors.HexColor('#1a2e1a'), stroke=C_GREEN, r=4, sw=1)
    label(d, 386, 188, 'FreshnessBar', size=8, color=C_GREENL, bold=True, align='middle')
    label(d, 386, 178, 'ageS = correctedNow − lastRefreshMs', size=7, color=C_TEXT, align='middle')
    label(d, 386, 168, 'correctedNow = Date.now()+clockOffsetMs', size=7, color=C_SUBTEXT, align='middle')
    label(d, 386, 159, 'setInterval 1s tick  +  visibilitychange', size=6.5, color=C_SUBTEXT, align='middle')

    # StatsPanel
    box(d, 304, 110, 164, 36, fill=colors.HexColor('#1a2e1a'), stroke=C_CYAN, r=4, sw=1)
    label(d, 386, 136, 'StatsPanel', size=8, color=C_CYANL, bold=True, align='middle')
    label(d, 386, 126, 'lastCacheRefresh from entries', size=7, color=C_TEXT, align='middle')
    label(d, 386, 116, 'SSE events only (no heartbeat)', size=7, color=C_SUBTEXT, align='middle')

    # RefreshControl
    box(d, 304, 70, 164, 32, fill=colors.HexColor('#2e1a1a'), stroke=C_ORANGE, r=4, sw=1)
    label(d, 386, 94, 'RefreshControl', size=8, color=C_ORANGEL, bold=True, align='middle')
    label(d, 386, 84, 'PUT /config/refresh-interval', size=7, color=C_TEXT, align='middle')
    label(d, 386, 75, '→ setInterval + forceRefresh', size=7, color=C_SUBTEXT, align='middle')

    # arrows SSE wire → browser
    arrow_right(d, 282, 257, 304, color=C_PURPLE, sw=1.5)
    arrow_right(d, 282, 227, 304, color=C_PURPLE, sw=1)
    arrow_right(d, 282, 197, 304, color=C_PURPLE, sw=1)

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 5 — Interval Change Flow
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_interval_change():
    W, H = 480, 320
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    # lifelines
    cols  = [55, 160, 270, 380]
    names = ['Browser\nReact', 'forex-proxy\nHTTP', 'OneFrameCache\nSignallingRef', 'EventBus\n+SSE']
    clrs  = [C_PURPLE, C_GREEN, C_ORANGE, C_CYAN]
    for cx, nm, cl in zip(cols, names, clrs):
        box(d, cx-42, H-38, 84, 28, fill=C_SURFACE, stroke=cl, r=4, sw=1.5)
        lines = nm.split('\n')
        label(d, cx, H-20, lines[0], size=8, color=cl, bold=True, align='middle')
        if len(lines)>1:
            label(d, cx, H-10, lines[1], size=6.5, color=C_SUBTEXT, align='middle')
        dashed_line(d, cx, H-38, cx, 10, color=C_BORDER, sw=1)

    # steps
    y = 268
    # 1. User clicks "2m"
    box(d, 10, y, 90, 16, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=3)
    label(d, 55, y+9, 'User clicks "2m"', size=7, color=C_PURPLEL, align='middle')
    y -= 22

    # 2. PUT request
    arrow_right(d, 97, y, 118, color=C_PURPLE, sw=1.5)
    label(d, 107, y+5, 'PUT /config/refresh-interval', size=7, color=C_PURPLEL, align='middle')
    label(d, 107, y-4, '{"seconds":120}', size=6.5, color=C_SUBTEXT, align='middle')
    y -= 26

    # 3. setInterval
    arrow_right(d, 202, y, 228, color=C_GREEN, sw=1.5)
    label(d, 215, y+5, 'intervalRef.set(120s)', size=7, color=C_GREENL, align='middle')
    y -= 18

    # 4. race resolves OR missed
    box(d, 232, y-6, 136, 22, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=3)
    label(d, 300, y+7, 'Concurrent.race resolves', size=7, color=C_PURPLEL, align='middle')
    label(d, 300, y-2, '(sleep cancelled if listening)', size=6.5, color=C_SUBTEXT, align='middle')
    y -= 24

    # 5. forceRefresh
    arrow_right(d, 202, y, 228, color=C_GREEN, sw=1.5)
    label(d, 215, y+5, 'forceRefresh() — doRefresh()', size=7, color=C_GREENL, align='middle')
    label(d, 215, y-4, 'blocks until complete', size=6.5, color=C_SUBTEXT, align='middle')
    y -= 26

    # 6. One-Frame fetch (inside doRefresh)
    arrow_right(d, 202, y, 228, color=C_ORANGE, sw=1.5)
    label(d, 215, y+5, 'HTTP GET /rates (72 pairs)', size=7, color=C_ORANGEL, align='middle')
    y -= 20

    arrow_left(d, 202, y, 228, color=C_ORANGE, sw=1.5)
    label(d, 215, y+5, '200 OK  72 rates', size=7, color=C_ORANGEL, align='middle')
    y -= 20

    # 7. Publish CacheRefresh
    arrow_right(d, 312, y, 338, color=C_GREEN, sw=1.5)
    label(d, 325, y+5, 'publish(CacheRefresh)', size=7, color=C_GREENL, align='middle')
    y -= 20

    # 8. SSE event to browser
    arrow_left(d, 97, y, 338, color=C_CYAN, sw=1.5)
    label(d, 215, y+5, 'SSE: CacheRefresh → lastRefreshedAt resets to now', size=7, color=C_CYANL, align='middle')
    y -= 22

    # 9. 200 OK returns
    arrow_left(d, 97, y, 118, color=C_GREEN, sw=1.5)
    label(d, 107, y+5, '200 OK {"seconds":120}', size=7, color=C_GREENL, align='middle')
    y -= 18

    # 10. globalInterval update
    box(d, 10, y-8, 90, 16, fill=colors.HexColor('#1a2e1a'), stroke=C_GREEN, r=3)
    label(d, 55, y+0, 'globalInterval=120', size=7, color=C_GREENL, align='middle')
    label(d, 55, y-8, 'FreshnessBar resets', size=7, color=C_CYANL, align='middle')
    y -= 30

    # ── key insight box ───────────────────────────────────────────────────────
    box(d, 10, 10, 460, 42, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=4)
    label(d, 235, 44, 'Key fix: forceRefresh() is called BEFORE Ok() returns', size=8, color=C_PURPLEL, bold=True, align='middle')
    label(d, 235, 33, 'CacheRefresh SSE event arrives at browser at the same moment the button re-enables.', size=7.5, color=C_TEXT, align='middle')
    label(d, 235, 22, 'Eliminates the Concurrent.race miss-window where setInterval fired during doRefresh.', size=7, color=C_SUBTEXT, align='middle')
    label(d, 235, 12, 'At most 2 One-Frame calls (race + forceRefresh) — still well within 1000/day budget.', size=7, color=C_SUBTEXT, align='middle')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 6 — All Timers & Intervals
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_timers():
    W, H = 480, 340
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    label(d, W//2, H-12, 'All Timers & Periodic Calls in the System', size=11, color=C_TEXT,
          bold=True, align='middle')

    timers = [
        # (y, label, period, owner, color, detail)
        (285, 'Cache Refresh',       '240s (default)', 'forex-proxy', C_GREEN,  'configurable 90–300s via PUT /config/refresh-interval'),
        (248, 'Heartbeat (SSE)',      '30s',            'forex-proxy', C_PURPLE, 'per SSE connection  · first emit immediate on connect'),
        (211, 'useRefreshInterval\npolling', '60s',     'Frontend',    C_CYAN,   'GET /config/refresh-interval  · keeps interval in sync'),
        (174, 'FreshnessBar tick',   '1s',             'Frontend',    C_GREENL, 'setInterval(1s)  · updates ageS counter each second'),
        (137, 'visibilitychange\nsnap', 'on tab focus', 'Frontend',   C_ORANGE, 'forces Date.now() read when tab returns from background'),
        (100, 'One-Frame API limit', '86,400s / day',  'One-Frame',   C_REDL,   '≤ 1,000 calls/day  · 240s interval = 360 calls/day'),
        ( 63, 'http4s timeout',      '40s',            'forex-proxy', C_ORANGEL,'request timeout on One-Frame HTTP calls'),
    ]

    for (y, nm, period, owner, cl, detail) in timers:
        # main row
        box(d, 10, y, 460, 30, fill=C_SURFACE, stroke=cl, r=4, sw=1.5)

        # period badge
        box(d, 14, y+8, 80, 16, fill=cl, stroke=cl, r=3)
        label(d, 54, y+18, period, size=8, color=C_BG if cl not in (C_GRAY,C_SUBTEXT) else C_TEXT,
              bold=True, align='middle')

        # timer name
        lines = nm.split('\n')
        label(d, 104, y+22, lines[0], size=8.5, color=cl, bold=True, align='start')
        if len(lines)>1:
            label(d, 104, y+13, lines[1], size=8.5, color=cl, bold=True, align='start')

        # owner tag
        box(d, 380, y+8, 86, 16, fill=C_SURFACE, stroke=C_BORDER, r=3)
        label(d, 423, y+18, owner, size=7.5, color=C_SUBTEXT, align='middle')

        # detail
        label(d, 104, y+5, detail, size=7, color=C_SUBTEXT, align='start')

    # ── timeline visualisation ────────────────────────────────────────────────
    # Not a full timeline, just a note
    box(d, 10, 14, 460, 20, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=4)
    label(d, 235, 26, 'SLA math:  refresh every 240s  +  40s timeout  = 280s worst-case age  <  300s SLA  ✓',
          size=8, color=C_PURPLEL, align='middle')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 7 — HTTP API Reference (all endpoints)
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_api():
    W, H = 480, 420
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    label(d, W//2, H-12, 'HTTP API — All Endpoints', size=11, color=C_TEXT, bold=True, align='middle')

    endpoints = [
        # (method, path, color, params, req_body, resp_200, resp_err, desc)
        ('GET',  '/rates',
         C_GREEN,
         '?from=USD&to=JPY  (required, ISO 4217)',
         '—',
         '{"from":"USD","to":"JPY","price":134.56,"timestamp":"2026-02-28T22:30:09Z"}',
         '400 {"errors":["..."]}  |  500 {"message":"..."}',
         'Proxy lookup. O(1) cache read. 0 One-Frame calls.'),

        ('GET',  '/events',
         C_CYAN,
         '—',
         '—',
         'text/event-stream  (keep-alive)  data: {"type":"CacheRefresh"|"ProxyRequest"|"Heartbeat"|"CacheRefreshFailed",...}',
         'Connection drop on server shutdown',
         'SSE stream. Heartbeat every 30s. Never closes normally.'),

        ('GET',  '/config/refresh-interval',
         C_PURPLE,
         '—',
         '—',
         '{"seconds":240,"message":"current refresh interval is 240s"}',
         '—',
         'Read the current cache refresh interval.'),

        ('PUT',  '/config/refresh-interval',
         C_ORANGE,
         '—',
         '{"seconds":120}',
         '{"seconds":120,"message":"refresh interval updated to 120s — refreshed immediately"}',
         '400 {"seconds":..,"message":"interval must be between 90s and 300s"}',
         'Change interval. Calls forceRefresh() before 200. CacheRefresh SSE guaranteed.'),

        ('POST', '/config/force-refresh',
         C_REDL,
         '—',
         '—',
         '{"message":"cache refreshed","pairsCount":72}',
         '—',
         'Manually trigger immediate cache refresh. Blocks until complete.'),

        ('GET',  '/config/status',
         C_GRAYL,
         '—',
         '—',
         '{"intervalSeconds":240,"lastRefreshedAt":"2026-02-28T22:30:09Z"}',
         '—',
         'Current interval + last refresh timestamp.'),
    ]

    y = H - 35
    for (method, path, cl, params, req, resp200, resp_err, desc) in endpoints:
        h = 56
        box(d, 10, y-h, 460, h, fill=C_SURFACE, stroke=cl, r=4, sw=1.5)

        # method badge
        mcl = {'GET': C_GREEN, 'PUT': C_ORANGE, 'POST': C_REDL}
        box(d, 14, y-h+h//2-8, 36, 16, fill=cl, stroke=cl, r=3)
        label(d, 32, y-h+h//2+2, method, size=8, color=C_BG, bold=True, align='middle')

        # path
        label(d, 58, y-h+h-10, path, size=10, color=cl, bold=True, align='start')

        # desc
        label(d, 58, y-h+h-21, desc, size=7, color=C_SUBTEXT, align='start')

        # params / body
        if params != '—':
            label(d, 58, y-h+h-33, f'Params: {params}', size=7, color=C_CYANL, align='start')
        if req != '—':
            label(d, 58, y-h+h-33, f'Body: {req}', size=7, color=C_CYANL, align='start')

        # response
        label(d, 58, y-h+h-44, f'200: {resp200[:85]}{"…" if len(resp200)>85 else ""}',
              size=7, color=C_GREENL, align='start')
        if resp_err != '—':
            label(d, 58, y-h+h-54+2, f'Err: {resp_err[:80]}{"…" if len(resp_err)>80 else ""}',
                  size=6.5, color=C_REDL, align='start')

        y -= (h + 6)

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 8 — Docker / Network Layout
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_docker():
    W, H = 480, 300
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    label(d, W//2, H-12, 'Docker Compose Network Layout', size=11, color=C_TEXT, bold=True, align='middle')

    # Host border
    box(d, 8, 15, 464, 252, fill=colors.HexColor('#0a0f1a'), stroke=C_BORDER, r=8, sw=1)
    label(d, 240, 255, 'Host machine (localhost)', size=8, color=C_SUBTEXT, align='middle')

    # Docker bridge network
    box(d, 16, 22, 448, 218, fill=colors.HexColor('#0f172a'), stroke=C_GRAY, r=6, sw=1)
    label(d, 240, 232, 'Docker bridge network (forex-mtl_default)', size=8, color=C_GRAY, align='middle')

    # one-frame container
    box(d, 24, 140, 130, 92, fill=colors.HexColor('#2e1a0a'), stroke=C_ORANGE, r=6, sw=2)
    label(d, 89, 222, 'one-frame', size=9, color=C_ORANGEL, bold=True, align='middle')
    label(d, 89, 210, 'paidyinc/one-frame', size=7, color=C_SUBTEXT, align='middle')
    label(d, 89, 198, 'internal: :8080', size=8, color=C_ORANGE, align='middle')
    label(d, 89, 186, 'host: :18080', size=8, color=C_ORANGEL, align='middle')
    label(d, 89, 174, '≤1000 calls/day limit', size=7, color=C_REDL, align='middle')
    label(d, 89, 162, 'rates API endpoint', size=7, color=C_SUBTEXT, align='middle')
    label(d, 89, 151, 'token auth (header)', size=7, color=C_SUBTEXT, align='middle')

    # forex-proxy container
    box(d, 175, 100, 140, 132, fill=colors.HexColor('#0a2e0a'), stroke=C_GREEN, r=6, sw=2)
    label(d, 245, 222, 'forex-proxy', size=9, color=C_GREENL, bold=True, align='middle')
    label(d, 245, 210, 'scala/sbt multi-stage', size=7, color=C_SUBTEXT, align='middle')
    label(d, 245, 198, 'internal: :9090', size=8, color=C_GREEN, align='middle')
    label(d, 245, 186, 'host: :9090', size=8, color=C_GREENL, align='middle')
    label(d, 245, 174, 'ONE_FRAME_URL=', size=7, color=C_SUBTEXT, align='middle')
    label(d, 245, 163, '  http://one-frame:8080', size=7, color=C_CYANL, align='middle')
    label(d, 245, 152, 'ONE_FRAME_TOKEN=10dc...', size=7, color=C_SUBTEXT, align='middle')
    label(d, 245, 141, 'APP_HTTP_PORT=9090', size=7, color=C_SUBTEXT, align='middle')
    label(d, 245, 130, 'depends_on: one-frame', size=7, color=C_GRAY, align='middle')
    label(d, 245, 119, 'In-memory cache (Ref)', size=7, color=C_GREENL, align='middle')
    label(d, 245, 109, 'EventBus (fs2 Topic)', size=7, color=C_SUBTEXT, align='middle')

    # frontend container
    box(d, 335, 140, 130, 92, fill=colors.HexColor('#1a1a2e'), stroke=C_PURPLE, r=6, sw=2)
    label(d, 400, 222, 'frontend', size=9, color=C_PURPLEL, bold=True, align='middle')
    label(d, 400, 210, 'node build → nginx', size=7, color=C_SUBTEXT, align='middle')
    label(d, 400, 198, 'internal: :80', size=8, color=C_PURPLE, align='middle')
    label(d, 400, 186, 'host: :3001', size=8, color=C_PURPLEL, align='middle')
    label(d, 400, 174, 'Nginx proxy_pass', size=7, color=C_CYANL, align='middle')
    label(d, 400, 162, '/api/ → forex-proxy:9090', size=7, color=C_CYANL, align='middle')
    label(d, 400, 151, 'depends_on: forex-proxy', size=7, color=C_GRAY, align='middle')
    label(d, 400, 140, '+ one-frame', size=7, color=C_GRAY, align='middle')

    # internal arrow one-frame ↔ forex-proxy
    arrow_right(d, 154, 190, 175, color=C_ORANGE, label_txt='HTTP :8080', lcolor=C_ORANGEL, sw=1.5)
    arrow_left(d,  154, 180, 175, color=C_ORANGE, label_txt='72 rates',   lcolor=C_ORANGEL, sw=1.5)

    # internal arrow forex-proxy ↔ frontend
    arrow_right(d, 315, 190, 335, color=C_CYAN, label_txt=':9090', lcolor=C_CYANL, sw=1.5)
    arrow_left(d,  315, 180, 335, color=C_CYAN, label_txt='JSON/SSE', lcolor=C_CYANL, sw=1.5)

    # host port labels
    label(d, 89,  32, '↑ :18080', size=7, color=C_ORANGEL, align='middle')
    label(d, 245, 32, '↑ :9090',  size=7, color=C_GREENL,  align='middle')
    label(d, 400, 32, '↑ :3001',  size=7, color=C_PURPLEL, align='middle')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 9 — FreshnessBar State Machine
# ═══════════════════════════════════════════════════════════════════════════════

def diagram_freshness_state():
    W, H = 480, 300
    d = Drawing(W, H)
    d.add(Rect(0, 0, W, H, fillColor=C_BG, strokeColor=C_BG))

    label(d, W//2, H-12, 'FreshnessBar — State & Colour Logic', size=11, color=C_TEXT, bold=True, align='middle')

    # ── State machine ─────────────────────────────────────────────────────────
    # State: WAITING
    box(d, 10, 210, 100, 44, fill=C_SURFACE, stroke=C_GRAY, r=6, sw=1.5)
    label(d, 60, 242, 'WAITING', size=9, color=C_GRAY, bold=True, align='middle')
    label(d, 60, 231, 'ageS = null', size=7.5, color=C_SUBTEXT, align='middle')
    label(d, 60, 221, 'shows "—"', size=7, color=C_SUBTEXT, align='middle')

    # State: FRESH
    box(d, 140, 210, 100, 44, fill=colors.HexColor('#0a2e0a'), stroke=C_GREEN, r=6, sw=2)
    label(d, 190, 242, 'FRESH', size=9, color=C_GREENL, bold=True, align='middle')
    label(d, 190, 231, '0 ≤ ageS < 75%', size=7.5, color=C_SUBTEXT, align='middle')
    label(d, 190, 221, '■ green bar', size=7, color=C_GREENL, align='middle')

    # State: WARN
    box(d, 260, 210, 100, 44, fill=colors.HexColor('#2e2a0a'), stroke=C_YELLOW, r=6, sw=2)
    label(d, 310, 242, 'WARN', size=9, color=C_YELLOWL, bold=True, align='middle')
    label(d, 310, 231, '75% ≤ ageS < 90%', size=7.5, color=C_SUBTEXT, align='middle')
    label(d, 310, 221, '■ yellow bar', size=7, color=C_YELLOWL, align='middle')

    # State: CRITICAL
    box(d, 370, 210, 100, 44, fill=colors.HexColor('#2e0a0a'), stroke=C_RED, r=6, sw=2)
    label(d, 420, 242, 'CRITICAL', size=9, color=C_REDL, bold=True, align='middle')
    label(d, 420, 231, '90% ≤ ageS < 300s', size=7.5, color=C_SUBTEXT, align='middle')
    label(d, 420, 221, '■ red bar', size=7, color=C_REDL, align='middle')

    # SLA BREACHED
    box(d, 370, 155, 100, 44, fill=colors.HexColor('#3e0a0a'), stroke=C_RED, r=6, sw=2.5)
    label(d, 420, 187, 'SLA BREACHED', size=8, color=C_REDL, bold=True, align='middle')
    label(d, 420, 176, 'ageS ≥ 300s', size=7.5, color=C_SUBTEXT, align='middle')
    label(d, 420, 166, '■ pulsing red', size=7, color=C_REDL, align='middle')

    # Transitions
    arrow_right(d, 110, 232, 140, color=C_GREEN, label_txt='first heartbeat/SSE', lcolor=C_GREENL)
    arrow_right(d, 240, 232, 260, color=C_YELLOW, label_txt='ageS ≥ period×0.75', lcolor=C_YELLOWL)
    arrow_right(d, 360, 232, 370, color=C_RED, label_txt='ageS ≥ period×0.9', lcolor=C_REDL)
    arrow_up(d, 420, 210, 199, color=C_RED, label_txt='ageS ≥ 300s', sw=1.5)
    # Reset arrows
    dashed_line(d, 190, 210, 190, 185, color=C_GREEN, sw=1)
    dashed_line(d, 190, 185, 60, 185, color=C_GREEN, sw=1)
    dashed_line(d, 310, 210, 310, 185, color=C_GREEN, sw=1)
    dashed_line(d, 420, 155, 420, 185, color=C_GREEN, sw=1)
    arrow_down(d, 60, 185, 210, color=C_GREEN, sw=1)
    arrow_down(d, 310, 185, 210, color=C_GREEN, sw=1)
    label(d, 225, 188, 'CacheRefresh SSE  OR  Heartbeat → ageS resets to ~0', size=7, color=C_GREENL, align='middle')

    # ── period calculation ────────────────────────────────────────────────────
    box(d, 10, 110, 340, 88, fill=C_SURFACE, stroke=C_BORDER, r=6)
    label(d, 15, 190, 'Period Calculation', size=9, color=C_PURPLEL, bold=True, align='start')
    label(d, 15, 179, 'period = Math.min(currentInterval, 300)       // bar spans 0 → period', size=8, color=C_TEXT, align='start')
    label(d, 15, 168, 'pct    = Math.min(100, (ageS / period) × 100) // bar width %', size=8, color=C_TEXT, align='start')
    label(d, 15, 157, 'isWarn     = ageS ≥ period × 0.75  &&  ageS < period × 0.9', size=8, color=C_YELLOWL, align='start')
    label(d, 15, 146, 'isCritical = ageS ≥ period × 0.9   &&  ageS < 300', size=8, color=C_REDL, align='start')
    label(d, 15, 135, 'isSlaBreached = ageS ≥ 300', size=8, color=C_REDL, align='start')
    label(d, 15, 124, 'correctedNow  = Date.now() + clockOffsetMs   // clock skew correction', size=8, color=C_CYANL, align='start')
    label(d, 15, 113, 'ageMs = correctedNow − new Date(lastRefreshedAt).getTime()', size=8, color=C_TEXT, align='start')

    # ── anchor sources ────────────────────────────────────────────────────────
    box(d, 360, 110, 110, 88, fill=colors.HexColor('#1e1a2e'), stroke=C_PURPLE, r=6)
    label(d, 415, 190, 'Anchor Sources', size=8.5, color=C_PURPLEL, bold=True, align='middle')
    label(d, 415, 179, '1. SSE CacheRefresh', size=7.5, color=C_GREENL, align='middle')
    label(d, 415, 169, '   (immediate, ms-accurate)', size=7, color=C_SUBTEXT, align='middle')
    label(d, 415, 158, '2. Heartbeat.lastRefreshedAt', size=7.5, color=C_PURPLEL, align='middle')
    label(d, 415, 148, '   (every 30s, survives reload)', size=7, color=C_SUBTEXT, align='middle')
    label(d, 415, 137, '3. null → shows "—"', size=7.5, color=C_GRAY, align='middle')
    label(d, 415, 127, '   (cold start, no refresh)', size=7, color=C_SUBTEXT, align='middle')
    label(d, 415, 116, '  Priority: 1 > 2 > 3', size=7, color=C_PURPLEL, align='middle')

    # ── bottom constraint ────────────────────────────────────────────────────
    box(d, 10, 55, 460, 46, fill=colors.HexColor('#1a2e1a'), stroke=C_GREEN, r=4)
    label(d, 14, 93, 'Example with interval=240s:', size=8, color=C_GREENL, bold=True, align='start')
    label(d, 14, 81, '  Fresh: 0–179s  |  Warn (yellow): 180–215s  |  Critical (red): 216–299s  |  SLA breach: ≥300s', size=7.5, color=C_TEXT, align='start')
    label(d, 14, 70, 'Example with interval=90s:', size=8, color=C_CYANL, bold=True, align='start')
    label(d, 14, 59, '  Fresh: 0–67s  |  Warn: 68–80s  |  Critical: 81–89s  |  SLA breach: ≥300s (SLA cap always 300s)', size=7.5, color=C_TEXT, align='start')

    label(d, W//2, 14, 'setInterval(1s) ticks ageS up every second  ·  visibilitychange snaps now immediately on tab return',
          size=7, color=C_SUBTEXT, align='middle')

    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════

def build_pdf(path):
    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title='forex-mtl E2E Flow Diagrams',
        author='forex-mtl'
    )

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(sp(60))
    story.append(Paragraph('forex-mtl', S_TITLE))
    story.append(Paragraph('End-to-End Flow Diagrams', S_SUBTITLE))
    story.append(sp(4))
    story.append(Paragraph('Visual reference: all flows, timers, HTTP calls, constraints, requests & responses', S_SUBTITLE))
    story.append(sp(20))
    story.append(hr())
    story.append(sp(10))

    toc_items = [
        ('1', 'System Architecture Overview'),
        ('2', 'Rate Request — Happy Path Sequence'),
        ('3', 'Cache Refresh Cycle'),
        ('4', 'SSE & Heartbeat Event Flow'),
        ('5', 'Interval Change Flow (PUT /config/refresh-interval)'),
        ('6', 'All Timers & Periodic Calls'),
        ('7', 'HTTP API Reference — All Endpoints'),
        ('8', 'Docker Compose Network Layout'),
        ('9', 'FreshnessBar State Machine & Colour Logic'),
    ]
    data = [['#', 'Section']] + [[n, t] for n, t in toc_items]
    tbl = Table(data, colWidths=[1.2*cm, 13*cm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), C_PURPLE),
        ('TEXTCOLOR',   (0,0), (-1,0), C_WHITE),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,0), 9),
        ('BACKGROUND',  (0,1), (-1,-1), C_SURFACE),
        ('TEXTCOLOR',   (0,1), (0,-1), C_PURPLEL),
        ('TEXTCOLOR',   (1,1), (1,-1), C_TEXT),
        ('FONTNAME',    (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',    (0,1), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [C_SURFACE, colors.HexColor('#253347')]),
        ('GRID',        (0,0), (-1,-1), 0.5, C_BORDER),
        ('ALIGN',       (0,0), (0,-1), 'CENTER'),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(tbl)

    # ── Section 1 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('1. System Architecture Overview'))
    story.append(body(
        'Three Docker containers communicate over a shared bridge network. '
        'The browser connects only to Nginx (:3001). Nginx serves the React SPA and '
        'proxies all API calls (/rates, /events, /config/*) to forex-proxy (:9090). '
        'forex-proxy holds an in-memory cache of all 72 currency pairs and periodically '
        'refreshes it from One-Frame (:18080).'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_architecture()))
    story.append(caption('Figure 1 — Three-container architecture with internal Docker network and host port mappings'))

    # ── Section 2 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('2. Rate Request — Happy Path Sequence'))
    story.append(body(
        'A client request for a currency rate travels through Nginx → forex-proxy → in-memory cache. '
        'No call to One-Frame is made at request time. The cache returns the rate in < 1ms via a '
        'Map lookup (O(1)). The response includes a side-effect: a ProxyRequest SSE event is published '
        'to the EventBus so connected browser tabs see it in real time.'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_rate_request()))
    story.append(caption('Figure 2 — GET /rates sequence diagram with validation, cache lookup, and SSE side-effect'))

    # ── Section 3 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('3. Cache Refresh Cycle'))
    story.append(body(
        'The refresh stream runs concurrently with the HTTP server (merged in Main.scala). '
        'It fires an initial refresh on startup, then sleeps for the configured interval. '
        'When the interval changes, a Concurrent.race interrupts the sleep immediately. '
        'One-Frame is called with all 72 pairs in a single batch request. On success the '
        'Ref is atomically updated and a CacheRefresh SSE event is published.'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_cache_refresh()))
    story.append(caption('Figure 3 — Cache refresh stream: startup, periodic refresh, One-Frame HTTP call, error handling'))

    # ── Section 4 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('4. SSE & Heartbeat Event Flow'))
    story.append(body(
        'Each browser tab that connects to GET /events gets a long-lived SSE connection. '
        'The server merges two streams per connection: the shared EventBus (CacheRefresh, '
        'ProxyRequest, CacheRefreshFailed) and a per-connection heartbeat stream (every 30s). '
        'The heartbeat carries serverTimeMs for clock-skew correction and lastRefreshedAt '
        'to re-anchor the freshness timer after reconnects or page reloads.'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_sse_heartbeat()))
    story.append(caption('Figure 4 — SSE stream topology: EventBus merge with per-connection heartbeat, browser-side consumers'))

    # ── Section 5 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('5. Interval Change Flow'))
    story.append(body(
        'When the user clicks a preset button (e.g. "2m"), a PUT request is sent. The backend '
        'calls setInterval(120s) to update the SignallingRef, then immediately calls forceRefresh() '
        'which runs doRefresh() directly and blocks until it completes. This guarantees a '
        'CacheRefresh SSE event arrives at the browser at the same moment the 200 response '
        're-enables the button — eliminating the race window in Concurrent.race.'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_interval_change()))
    story.append(caption('Figure 5 — PUT /config/refresh-interval: setInterval + forceRefresh guarantees immediate cache reset'))

    # ── Section 6 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('6. All Timers & Periodic Calls'))
    story.append(body(
        'The system has six distinct timers spanning server and browser. '
        'The most critical is the 240s cache refresh — it must stay below 300s (SLA). '
        'With a 40s One-Frame HTTP timeout, the worst-case data age is 280s, within budget.'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_timers()))
    story.append(caption('Figure 6 — All timers: cache refresh (240s), SSE heartbeat (30s), frontend poll (60s), tick (1s)'))

    # ── Section 7 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('7. HTTP API Reference — All Endpoints'))
    story.append(body(
        'forex-proxy exposes six HTTP endpoints. All are served on port 9090 and proxied '
        'through Nginx on port 3001. The /events endpoint is a persistent SSE stream. '
        'All JSON responses use snake_case keys matching the One-Frame API convention.'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_api()))
    story.append(caption('Figure 7 — Complete HTTP API: method, path, parameters, request body, 200 response, error responses'))

    # ── Section 8 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('8. Docker Compose Network Layout'))
    story.append(body(
        'docker-compose.yml defines three services on a shared bridge network. '
        'Service names are used as DNS hostnames inside the network (one-frame:8080). '
        'Environment variables override application.conf values via HOCON substitution '
        '(${?ONE_FRAME_URL}, ${?ONE_FRAME_TOKEN}, ${?APP_HTTP_PORT}).'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_docker()))
    story.append(caption('Figure 8 — Docker bridge network: container names, internal ports, host-mapped ports, env overrides'))

    # ── Section 9 ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('9. FreshnessBar State Machine & Colour Logic'))
    story.append(body(
        'FreshnessBar tracks cache age in real time. The anchor (lastRefreshedAt) comes from '
        'two sources: SSE CacheRefresh events (immediate, ms-accurate) and Heartbeat.lastRefreshedAt '
        '(every 30s, survives page reload). Age is computed with clock-skew correction. '
        'The bar colour changes at 75% (yellow), 90% (red), and 100% of the SLA (pulsing red).'
    ))
    story.append(sp(4))
    story.append(DiagramFlow(diagram_freshness_state()))
    story.append(caption('Figure 9 — FreshnessBar state transitions, period calculation formulas, and anchor priority'))

    # ── Quick reference table ─────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('Quick Reference'))
    story.append(sp(4))

    qr_data = [
        ['Item', 'Value', 'Reason'],
        ['Currencies supported', '9 (AUD BRL CAD CHF EUR GBP JPY NZD USD)', 'One-Frame API constraint'],
        ['Pairs in cache', '72  (9×8, no self-pairs)', 'All ordered permutations'],
        ['Default refresh interval', '240s (4 minutes)', '360 calls/day ≪ 1,000 limit'],
        ['Min / Max interval', '90s / 300s', 'Rate limit floor / SLA ceiling'],
        ['SLA requirement', '< 300s data age', 'Assignment spec'],
        ['Worst-case data age', '280s (240s sleep + 40s timeout)', '< 300s SLA ✓'],
        ['One-Frame calls/day', '~360 at 240s', '640 calls headroom remaining'],
        ['One-Frame auth', 'Header: token: 10dc303...', 'NOT Bearer — custom scheme'],
        ['One-Frame query format', '?pair=USDJPY&pair=EURJPY...', '72 params, 1 request'],
        ['One-Frame JSON key', 'time_stamp (snake_case)', 'circe withSnakeCaseMemberNames'],
        ['Cache store', 'Ref[F, Map[Rate.Pair, Rate]]', 'Lock-free, CE2 atomic ref'],
        ['EventBus', 'fs2.Topic[F, Option[LogEvent]]', 'Fan-out, buf=128/subscriber'],
        ['SSE heartbeat', 'every 30s per connection', 'NAT keepalive + clock sync'],
        ['Frontend SSE', 'EventSource (singleton)', 'One connection shared across components'],
        ['Clock skew correction', 'clockOffsetMs = serverMs − Date.now()', 'Applied to all age calculations'],
        ['Nginx proxy_read_timeout', '600s', 'Covers 4-min quiet between refreshes'],
        ['forex-proxy port', '9090', 'Avoids conflict with One-Frame :8080'],
        ['Frontend port', '3001', 'Nginx serves SPA + proxies API'],
    ]

    col_w = [(PAGE_W - 2*MARGIN) * f for f in [0.28, 0.42, 0.30]]
    qrt = Table(qr_data, colWidths=col_w)
    qrt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0), C_PURPLE),
        ('TEXTCOLOR',     (0,0), (-1,0), C_WHITE),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0), 8.5),
        ('BACKGROUND',    (0,1), (-1,-1), C_SURFACE),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [C_SURFACE, colors.HexColor('#253347')]),
        ('TEXTCOLOR',     (0,1), (0,-1), C_CYANL),
        ('TEXTCOLOR',     (1,1), (1,-1), C_TEXT),
        ('TEXTCOLOR',     (2,1), (2,-1), C_SUBTEXT),
        ('FONTNAME',      (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1), (-1,-1), 7.5),
        ('GRID',          (0,0), (-1,-1), 0.4, C_BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('WORDWRAP',      (0,0), (-1,-1), True),
    ]))
    story.append(qrt)

    doc.build(story)
    print(f'PDF written → {path}')

if __name__ == '__main__':
    build_pdf('/home/juan/paidy/interview/forex-flows.pdf')
