#!/usr/bin/env python3
"""
Rate Limiting & Token Quota Tracking — Industry Standards
Visual PDF with diagrams, comparisons, and Scala/cats-effect implementations.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle, Path
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable

PAGE_W, PAGE_H = A4
MARGIN = 1.8 * cm

# ── Palette ────────────────────────────────────────────────────────────────────
BG       = colors.HexColor('#0f172a')
SURFACE  = colors.HexColor('#1e293b')
SURFACE2 = colors.HexColor('#253347')
BORDER   = colors.HexColor('#334155')
PURPLE   = colors.HexColor('#7c3aed')
PURPLEL  = colors.HexColor('#a78bfa')
CYAN     = colors.HexColor('#0891b2')
CYANL    = colors.HexColor('#67e8f9')
GREEN    = colors.HexColor('#16a34a')
GREENL   = colors.HexColor('#86efac')
ORANGE   = colors.HexColor('#ea580c')
ORANGEL  = colors.HexColor('#fdba74')
RED      = colors.HexColor('#dc2626')
REDL     = colors.HexColor('#fca5a5')
YELLOW   = colors.HexColor('#ca8a04')
YELLOWL  = colors.HexColor('#fde047')
GRAY     = colors.HexColor('#64748b')
GRAYL    = colors.HexColor('#94a3b8')
WHITE    = colors.white
TEXT     = colors.HexColor('#f1f5f9')
SUBTEXT  = colors.HexColor('#94a3b8')
PINK     = colors.HexColor('#ec4899')
PINKL    = colors.HexColor('#f9a8d4')

# ── Styles ────────────────────────────────────────────────────────────────────
ss = getSampleStyleSheet()

def sty(name, **kw):
    return ParagraphStyle(name, parent=ss['Normal'], **kw)

S_COVER  = sty('cover',  fontSize=32, leading=38, textColor=WHITE,
                fontName='Helvetica-Bold', spaceAfter=6, alignment=TA_CENTER)
S_CSUB   = sty('csub',   fontSize=14, leading=18, textColor=PURPLEL,
                fontName='Helvetica', spaceAfter=4, alignment=TA_CENTER)
S_H1     = sty('h1',     fontSize=17, leading=21, textColor=CYANL,
                fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=5)
S_H2     = sty('h2',     fontSize=12, leading=15, textColor=PURPLEL,
                fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=3)
S_H3     = sty('h3',     fontSize=10, leading=13, textColor=ORANGEL,
                fontName='Helvetica-Bold', spaceBefore=5, spaceAfter=2)
S_BODY   = sty('body',   fontSize=9,  leading=13, textColor=TEXT,
                fontName='Helvetica', spaceAfter=4)
S_SMALL  = sty('small',  fontSize=8,  leading=11, textColor=SUBTEXT,
                fontName='Helvetica', spaceAfter=3)
S_CODE   = sty('code',   fontSize=7.5, leading=11, textColor=GREENL,
                fontName='Courier', spaceAfter=2,
                backColor=SURFACE, leftIndent=8, rightIndent=8,
                borderPadding=(4,6,4,6))
S_NOTE   = sty('note',   fontSize=8,  leading=11, textColor=YELLOWL,
                fontName='Helvetica', spaceAfter=4, leftIndent=10)
S_CAP    = sty('cap',    fontSize=8,  leading=11, textColor=SUBTEXT,
                fontName='Helvetica-Oblique', spaceAfter=8, alignment=TA_CENTER)

def hr(): return HRFlowable(width='100%', thickness=0.5, color=BORDER,
                             spaceAfter=6, spaceBefore=3)
def sp(h=6): return Spacer(1, h)
def h1(t): return Paragraph(t, S_H1)
def h2(t): return Paragraph(t, S_H2)
def h3(t): return Paragraph(t, S_H3)
def body(t): return Paragraph(t, S_BODY)
def small(t): return Paragraph(t, S_SMALL)
def note(t): return Paragraph(f'★ {t}', S_NOTE)
def cap(t): return Paragraph(t, S_CAP)
def code(t): return Paragraph(t, S_CODE)

# ── Drawing helpers ────────────────────────────────────────────────────────────
def box(d, x, y, w, h, fill=SURFACE, stroke=BORDER, r=5, sw=1.2):
    d.add(Rect(x, y, w, h, rx=r, ry=r,
               fillColor=fill, strokeColor=stroke, strokeWidth=sw))

def lbl(d, x, y, t, size=8, color=TEXT, bold=False, anchor='middle'):
    fn = 'Helvetica-Bold' if bold else 'Helvetica'
    d.add(String(x, y, t, fontSize=size, fillColor=color,
                 fontName=fn, textAnchor=anchor))

def lbl_code(d, x, y, t, size=7.5, color=GREENL, anchor='start'):
    d.add(String(x, y, t, fontSize=size, fillColor=color,
                 fontName='Courier', textAnchor=anchor))

def arr_r(d, x1, y, x2, color=GRAY, ltext='', lcolor=None, sw=1.5):
    d.add(Line(x1, y, x2-6, y, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x2-7,y+4,x2,y,x2-7,y-4],
                  fillColor=color, strokeColor=color, strokeWidth=0))
    if ltext:
        d.add(String((x1+x2)/2, y+3, ltext, fontSize=7, fillColor=lcolor or SUBTEXT,
                     fontName='Helvetica', textAnchor='middle'))

def arr_l(d, x1, y, x2, color=GRAY, ltext='', lcolor=None, sw=1.5):
    d.add(Line(x1, y, x2+6, y, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x2+7,y+4,x2,y,x2+7,y-4],
                  fillColor=color, strokeColor=color, strokeWidth=0))
    if ltext:
        d.add(String((x1+x2)/2, y+3, ltext, fontSize=7, fillColor=lcolor or SUBTEXT,
                     fontName='Helvetica', textAnchor='middle'))

def arr_u(d, x, y1, y2, color=GRAY, sw=1.5):
    d.add(Line(x, y1, x, y2+6, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x-4,y2+6,x,y2,x+4,y2+6],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def arr_d(d, x, y1, y2, color=GRAY, sw=1.5):
    d.add(Line(x, y1, x, y2-6, strokeColor=color, strokeWidth=sw))
    d.add(Polygon([x-4,y2-6,x,y2,x+4,y2-6],
                  fillColor=color, strokeColor=color, strokeWidth=0))

def dash(d, x1, y1, x2, y2, color=GRAY, sw=1):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=sw,
               strokeDashArray=[4,3]))

class DF(Flowable):
    def __init__(self, drawing):
        Flowable.__init__(self)
        self.drawing = drawing
        self.width   = drawing.width
        self.height  = drawing.height
    def draw(self):
        renderPDF.draw(self.drawing, self.canv, 0, 0)

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 1 — Algorithm Comparison Timeline
# Shows all 4 algorithms responding to the same request burst
# ══════════════════════════════════════════════════════════════════════════════
def diag_algorithms():
    W, H = 480, 360
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Algorithm Comparison — Same 12-request burst, limit=8/window',
        size=10, bold=True, anchor='middle')

    # time axis
    TL = 30   # left margin
    TR = 460  # right end
    TW = TR - TL
    # 12 request marks at t=0..11
    def tx(t): return TL + t * TW / 11

    # ── Row headers ───────────────────────────────────────────────────────────
    rows = [
        (285, 'Fixed Window',      CYAN,   'Hard reset at window boundary — burst risk at edges'),
        (215, 'Sliding Window',    GREEN,  'Interpolated — no cliff, gradual rollover'),
        (145, 'Token Bucket',      PURPLE, 'Refill rate controls burst — allows front-loading'),
        ( 75, 'Leaky Bucket',      ORANGE, 'Constant output rate — no bursting at all'),
    ]

    for (ry, name, cl, desc) in rows:
        box(d, TL-28, ry-12, 26, 60, fill=SURFACE, stroke=cl, r=3, sw=1)
        lbl(d, TL-15, ry+34, name[:5], size=6.5, color=cl, bold=True, anchor='middle')
        lbl(d, TL-15, ry+25, name[5:], size=6.5, color=cl, bold=True, anchor='middle')
        lbl(d, TL, ry-18, desc, size=7, color=SUBTEXT, anchor='start')

    # ── Simulate responses for each algorithm ─────────────────────────────────
    # Fixed Window: limit=8, window=10 units, reset at t=6 in the example
    # Requests 0-7 allowed (0-indexed), request 8-10 rejected, request 11 allowed (new window)
    fixed_allow  = {0,1,2,3,4,5,6,7,11}
    sliding_allow = {0,1,2,3,4,5,6,7,8,9}   # sliding is more permissive at edge
    # Token bucket: starts full (8 tokens), 1 token/unit refill, each req costs 1
    # All 8 are allowed, then token runs out, partial refill by t=11
    token_allow  = {0,1,2,3,4,5,6,7,11}
    # Leaky: 1 req processed per ~1.5 units => only ~7 in window
    leaky_allow  = {0,2,3,5,6,8,9,11}

    algos = [
        (285, fixed_allow,   CYAN,   REDL),
        (215, sliding_allow, GREEN,  REDL),
        (145, token_allow,   PURPLE, REDL),
        ( 75, leaky_allow,   ORANGE, REDL),
    ]

    for (ry, allowed, cl, rcl) in algos:
        # draw timeline bar
        d.add(Line(TL, ry+20, TR, ry+20, strokeColor=BORDER, strokeWidth=0.5))
        for t in range(12):
            x = tx(t)
            if t in allowed:
                d.add(Circle(x, ry+20, 6, fillColor=cl, strokeColor=cl, strokeWidth=0))
                lbl(d, x, ry+17, '✓', size=7, color=BG, anchor='middle')
            else:
                d.add(Circle(x, ry+20, 6, fillColor=rcl, strokeColor=rcl, strokeWidth=0))
                lbl(d, x, ry+17, '✗', size=7, color=BG, anchor='middle')
            lbl(d, x, ry+6, f't{t}', size=6, color=SUBTEXT, anchor='middle')

    # window boundary marker for Fixed Window
    wx = tx(7.5)
    d.add(Line(wx, 260, wx, 270, strokeColor=CYANL, strokeWidth=1.5,
               strokeDashArray=[3,2]))
    lbl(d, wx, 272, 'window', size=6.5, color=CYANL, anchor='middle')
    lbl(d, wx, 264, 'reset', size=6.5, color=CYANL, anchor='middle')

    # burst risk annotation for fixed window
    box(d, tx(7)+8, 292, 70, 22, fill=colors.HexColor('#2e0a0a'), stroke=REDL, r=3, sw=1)
    lbl(d, tx(7)+43, 306, '⚡ boundary burst:', size=7, color=REDL, bold=True, anchor='middle')
    lbl(d, tx(7)+43, 297, 't7+t11 = 2×limit/window', size=6.5, color=REDL, anchor='middle')

    # ── Legend ────────────────────────────────────────────────────────────────
    lx = 12
    for i,(lname,lcl) in enumerate([('Allowed',GREEN),('Rejected',REDL)]):
        d.add(Circle(lx+6, 44, 5, fillColor=lcl, strokeColor=lcl, strokeWidth=0))
        lbl(d, lx+14, 41, lname, size=7.5, color=lcl, anchor='start')
        lx += 70

    lbl(d, W//2, 14, 'Leaky Bucket enforces constant output rate — queued/dropped, not time-windowed rejections',
        size=7, color=SUBTEXT, anchor='middle')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 2 — Token Bucket Deep Dive
# ══════════════════════════════════════════════════════════════════════════════
def diag_token_bucket():
    W, H = 480, 320
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Token Bucket — Mechanics & State', size=10, bold=True, anchor='middle')

    # ── Bucket visual ─────────────────────────────────────────────────────────
    BX, BY, BW, BH = 30, 80, 100, 170
    # bucket outline
    d.add(Rect(BX, BY, BW, BH, rx=4, ry=4,
               fillColor=colors.HexColor('#0a2e1a'), strokeColor=GREEN, strokeWidth=2))
    # fill level (6/10 tokens)
    fill_h = int(BH * 0.6)
    d.add(Rect(BX+2, BY+2, BW-4, fill_h-4, rx=2, ry=2,
               fillColor=colors.HexColor('#16a34a33'), strokeColor=None, strokeWidth=0))
    # token circles inside
    for row in range(3):
        for col in range(2):
            tx2 = BX + 20 + col*30
            ty2 = BY + 15 + row*22
            if row*2+col < 6:
                d.add(Circle(tx2, ty2, 8, fillColor=GREEN, strokeColor=GREENL, strokeWidth=1))
                lbl(d, tx2, ty2-3, '1', size=7, color=BG, bold=True, anchor='middle')
    # empty token outlines
    for i in range(4):
        row = (i+6)//2
        col = (i+6)%2
        tx2 = BX + 20 + col*30
        ty2 = BY + 15 + row*22
        if ty2 < BY+BH-5:
            d.add(Circle(tx2, ty2, 8, fillColor=None, strokeColor=BORDER, strokeWidth=1))

    lbl(d, BX+BW//2, BY-12, 'Bucket', size=8, bold=True, color=GREENL, anchor='middle')
    lbl(d, BX+BW//2, BY+BH+8, 'tokens: 6/10', size=8, color=GREEN, anchor='middle')
    lbl(d, BX+BW//2, BY+BH+18, 'capacity: 10', size=7, color=SUBTEXT, anchor='middle')

    # ── Refill (top) ──────────────────────────────────────────────────────────
    box(d, BX+10, BY+BH+38, 80, 24, fill=SURFACE, stroke=PURPLE, r=4, sw=1.5)
    lbl(d, BX+50, BY+BH+52, 'Refill Process', size=8, color=PURPLEL, bold=True, anchor='middle')
    lbl(d, BX+50, BY+BH+42, '1 token / second', size=7, color=SUBTEXT, anchor='middle')
    arr_u(d, BX+BW//2, BY+BH+38, BY+BH, color=PURPLE, sw=1.5)
    lbl(d, BX+BW//2+5, BY+BH+20, 'refill rate', size=6.5, color=PURPLEL, anchor='start')

    # ── Consume (right) ───────────────────────────────────────────────────────
    arr_r(d, BX+BW, BY+BH//2+30, BX+BW+90, color=RED, sw=2)
    lbl(d, BX+BW+45, BY+BH//2+43, 'consume 1 token', size=7.5, color=REDL, bold=True, anchor='middle')
    lbl(d, BX+BW+45, BY+BH//2+32, 'per request', size=7, color=SUBTEXT, anchor='middle')

    arr_l(d, BX+BW, BY+BH//2-10, BX+BW+90, color=GREEN, sw=1.5)
    lbl(d, BX+BW+45, BY+BH//2-5, 'allow', size=7.5, color=GREENL, anchor='middle')
    lbl(d, BX+BW+45, BY+BH//2-15, '(tokens > 0)', size=7, color=SUBTEXT, anchor='middle')

    # REJECT path
    box(d, BX+BW+100, BY+BH//2+20, 70, 24, fill=colors.HexColor('#2e0a0a'), stroke=REDL, r=4, sw=1.5)
    lbl(d, BX+BW+135, BY+BH//2+34, 'HTTP 429', size=8, color=REDL, bold=True, anchor='middle')
    lbl(d, BX+BW+135, BY+BH//2+24, 'bucket empty', size=7, color=SUBTEXT, anchor='middle')
    arr_r(d, BX+BW+90, BY+BH//2+32, BX+BW+100, color=REDL, sw=1.5)

    # ── State formula ─────────────────────────────────────────────────────────
    box(d, 240, 180, 230, 90, fill=SURFACE, stroke=PURPLE, r=5, sw=1.5)
    lbl(d, 355, 262, 'State per entity', size=8.5, color=PURPLEL, bold=True, anchor='middle')
    lbl_code(d, 248, 250, '(tokens_remaining: Int,', size=8, anchor='start')
    lbl_code(d, 248, 239, ' last_refill_ts:   Long)', size=8, anchor='start')
    lbl(d, 355, 228, 'On each request:', size=7.5, color=SUBTEXT, anchor='middle')
    lbl_code(d, 248, 217, 'elapsed = now - last_refill_ts', size=7.5, anchor='start')
    lbl_code(d, 248, 206, 'tokens  = min(cap, stored + elapsed×rate)', size=7.5, anchor='start')
    lbl_code(d, 248, 195, 'if tokens >= 1: tokens -= 1; allow', size=7.5, anchor='start')
    lbl_code(d, 248, 185, 'else: reject', size=7.5, color=REDL, anchor='start')

    # ── Key properties ────────────────────────────────────────────────────────
    box(d, 240, 60, 230, 110, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
    lbl(d, 355, 162, 'Properties', size=8.5, color=GREENL, bold=True, anchor='middle')
    props = [
        ('✓', 'Allows bursts up to bucket capacity',       GREENL),
        ('✓', 'O(1) check, O(1) state',                   GREENL),
        ('✓', 'Used by Stripe, AWS API GW, Envoy',        GREENL),
        ('△', 'Not natural for "N per day" quota',        YELLOWL),
        ('△', 'Two parameters (cap + rate) to tune',      YELLOWL),
        ('✗', 'Distributed: needs shared store (Redis)',   REDL),
    ]
    for i,(sym,txt,cl) in enumerate(props):
        lbl(d, 248, 152-i*14, sym, size=8, color=cl, bold=True, anchor='start')
        lbl(d, 258, 152-i*14, txt, size=7.5, color=cl, anchor='start')

    # ── Bucket4j / resilience4j ───────────────────────────────────────────────
    box(d, 240, 14, 230, 38, fill=colors.HexColor('#1a1a2e'), stroke=PURPLE, r=4, sw=1)
    lbl(d, 355, 44, 'JVM Libraries', size=8, color=PURPLEL, bold=True, anchor='middle')
    lbl(d, 248, 33, 'Bucket4j — JCache/Redis/Hazelcast backends', size=7.5, color=TEXT, anchor='start')
    lbl(d, 248, 23, 'resilience4j-ratelimiter — AtomicRateLimiter', size=7.5, color=TEXT, anchor='start')

    box(d, 14, 14, 220, 38, fill=colors.HexColor('#0a2e0a'), stroke=GREEN, r=4, sw=1)
    lbl(d, 14+110, 44, 'Scala / cats-effect', size=8, color=GREENL, bold=True, anchor='middle')
    lbl_code(d, 20, 33, 'Ref[F, (Int, Long)]', size=8, anchor='start')
    lbl(d, 20, 23, '  ← CAS-based, wait-free, zero deps', size=7.5, color=SUBTEXT, anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 3 — Sliding Window Counter
# ══════════════════════════════════════════════════════════════════════════════
def diag_sliding_window():
    W, H = 480, 300
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Sliding Window Counter — Interpolated Quota', size=10, bold=True, anchor='middle')

    # ── Timeline with two windows ─────────────────────────────────────────────
    TL, TR, TY = 30, 450, 185
    TW = TR - TL

    # window boxes
    # prev window (day N-1): x=TL .. TL+TW*0.5
    WM = TL + int(TW * 0.55)  # current midnight boundary
    WC = TL + TW              # end of current day

    # prev window (full)
    d.add(Rect(TL, TY-30, WM-TL, 30, rx=0, ry=0,
               fillColor=colors.HexColor('#0a1f2e'), strokeColor=CYAN, strokeWidth=1.5))
    lbl(d, (TL+WM)//2, TY-14, 'Yesterday (window N-1)', size=8, color=CYANL, bold=True, anchor='middle')
    lbl(d, (TL+WM)//2, TY-5, 'count = 700', size=8, color=CYAN, anchor='middle')

    # current window, showing 30% elapsed
    elapsed_x = WM + int((WC-WM)*0.30)
    d.add(Rect(WM, TY-30, WC-WM, 30, rx=0, ry=0,
               fillColor=colors.HexColor('#0a2e1a'), strokeColor=GREEN, strokeWidth=1.5))
    # elapsed portion
    d.add(Rect(WM, TY-30, elapsed_x-WM, 30, rx=0, ry=0,
               fillColor=colors.HexColor('#16a34a22'), strokeColor=None, strokeWidth=0))
    lbl(d, (WM+WC)//2, TY-14, 'Today (window N)', size=8, color=GREENL, bold=True, anchor='middle')
    lbl(d, (WM+WC)//2, TY-5, 'count = 80', size=8, color=GREEN, anchor='middle')

    # elapsed marker
    d.add(Line(elapsed_x, TY-32, elapsed_x, TY+8, strokeColor=YELLOWL, strokeWidth=1.5,
               strokeDashArray=[3,2]))
    lbl(d, elapsed_x, TY+15, 'NOW', size=8, color=YELLOWL, bold=True, anchor='middle')
    lbl(d, elapsed_x, TY+24, '30% elapsed', size=7, color=YELLOWL, anchor='middle')

    # midnight marker
    d.add(Line(WM, TY-35, WM, TY+6, strokeColor=BORDER, strokeWidth=1.5))
    lbl(d, WM, TY+12, '00:00 UTC', size=7, color=SUBTEXT, anchor='middle')

    # ── Sliding calculation box ───────────────────────────────────────────────
    box(d, 30, 100, 420, 72, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
    lbl(d, 240, 164, 'Effective Count Calculation', size=9, color=GREENL, bold=True, anchor='middle')
    lbl_code(d, 38, 153, 'overlap_fraction = 1.0 - 0.30 = 0.70   ← (1 - elapsed%)', size=8.5, anchor='start')
    lbl_code(d, 38, 141, 'effective        = prev_count × overlap_fraction + curr_count', size=8.5, anchor='start')
    lbl_code(d, 38, 129, '               = 700 × 0.70 + 80 = 490 + 80 = 570', size=8.5, color=CYANL, anchor='start')
    lbl_code(d, 38, 118, 'remaining        = 1000 - 570 = 430                          ✓ allow', size=8.5, color=GREENL, anchor='start')
    lbl(d, 38, 107, 'With fixed window: count=80 today (no yesterday context) → would allow 920 more, risky', size=7.5, color=SUBTEXT, anchor='start')

    # ── Redis Lua atomic script ───────────────────────────────────────────────
    box(d, 30, 20, 420, 74, fill=SURFACE, stroke=PURPLE, r=5, sw=1.5)
    lbl(d, 240, 86, 'Redis Lua Script (atomic check + increment)', size=9, color=PURPLEL, bold=True, anchor='middle')
    lines = [
        'local prev    = tonumber(redis.call("GET", KEYS[1])) or 0',
        'local curr    = tonumber(redis.call("GET", KEYS[2])) or 0',
        'local frac    = tonumber(ARGV[1])  -- fraction of window elapsed',
        'local limit   = tonumber(ARGV[2])',
        'if prev*(1-frac)+curr < limit then',
        '    redis.call("INCR", KEYS[2])',
        '    redis.call("EXPIRE", KEYS[2], 172800)  -- 48h TTL',
        '    return {1, math.floor(prev*(1-frac)+curr+1)}  -- allowed, count',
        'else return {0, math.floor(prev*(1-frac)+curr)} end  -- rejected',
    ]
    for i,ln in enumerate(lines):
        lbl_code(d, 38, 75-i*8, ln, size=7.2, color=GREENL if i<4 else (CYANL if i<7 else REDL),
                 anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 4 — Fixed Window Counter
# ══════════════════════════════════════════════════════════════════════════════
def diag_fixed_window():
    W, H = 480, 280
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Fixed Window Counter — Simplest, Boundary-Burst Risk', size=10, bold=True, anchor='middle')

    # ── Window grid ───────────────────────────────────────────────────────────
    days = ['2026-02-26\ncount=892', '2026-02-27\ncount=360', '2026-02-28\ncount=47']
    cols_c = [CYAN, GREEN, PURPLEL]
    for i,(day,cl) in enumerate(zip(days,cols_c)):
        x = 20 + i*155
        box(d, x, 170, 148, 72, fill=SURFACE, stroke=cl, r=4, sw=1.5)
        lines = day.split('\n')
        lbl(d, x+74, 225, lines[0], size=8, color=cl, bold=True, anchor='middle')
        lbl(d, x+74, 212, lines[1], size=9, color=cl, anchor='middle')
        # bar showing fill level
        fill_pct = [0.892, 0.360, 0.047][i]
        bar_w = int(136 * fill_pct)
        d.add(Rect(x+6, 175, bar_w, 16, rx=2, ry=2,
                   fillColor=cl, strokeColor=None, strokeWidth=0))
        d.add(Rect(x+6, 175, 136, 16, rx=2, ry=2,
                   fillColor=None, strokeColor=BORDER, strokeWidth=0.5))
        lbl(d, x+74, 177, f'{int(fill_pct*100)}% used', size=7, color=BG if fill_pct>0.3 else SUBTEXT, anchor='middle')
        if i < 2:
            arr_r(d, x+148, 206, x+155, color=BORDER, sw=1)

    # ── Redis key pattern ─────────────────────────────────────────────────────
    box(d, 20, 108, 440, 52, fill=SURFACE, stroke=CYAN, r=5, sw=1.5)
    lbl(d, 240, 152, 'Redis key pattern — one key per (entity, day)', size=8.5, color=CYANL, bold=True, anchor='middle')
    lbl_code(d, 28, 141, 'key   = f"quota:{api_token}:{today_utc}"', size=8.5, anchor='start')
    lbl_code(d, 28, 130, 'count = INCR(key)                          -- atomic, returns new value', size=8.5, anchor='start')
    lbl_code(d, 28, 119, 'if count == 1: EXPIRE(key, 86400)          -- set TTL on first write', size=8.5, anchor='start')
    lbl_code(d, 28, 109, 'if count > 1000: return HTTP 429 else: allow', size=8.5, color=GREENL, anchor='start')

    # ── Race condition warning and fix ───────────────────────────────────────
    box(d, 20, 50, 210, 52, fill=colors.HexColor('#2e1a0a'), stroke=ORANGEL, r=4, sw=1.5)
    lbl(d, 125, 94, '⚠ Race: INCR+EXPIRE not atomic', size=8, color=ORANGEL, bold=True, anchor='middle')
    lbl(d, 28,  83, 'If process crashes after INCR', size=7.5, color=TEXT, anchor='start')
    lbl(d, 28,  73, 'but before EXPIRE → key never expires', size=7.5, color=TEXT, anchor='start')
    lbl(d, 28,  63, 'Fix: use Lua script (atomic both ops)', size=7.5, color=GREENL, anchor='start')
    lbl(d, 28,  53, 'or: SET key 1 EX 86400 NX on first write', size=7, color=SUBTEXT, anchor='start')

    # boundary burst
    box(d, 248, 50, 212, 52, fill=colors.HexColor('#2e0a0a'), stroke=REDL, r=4, sw=1.5)
    lbl(d, 354, 94, '⚠ Boundary Burst Attack', size=8, color=REDL, bold=True, anchor='middle')
    lbl(d, 256, 83, 't=23:59:59  →  1000 requests  ✓', size=7.5, color=TEXT, anchor='start')
    lbl(d, 256, 73, 't=00:00:01  →  1000 requests  ✓', size=7.5, color=TEXT, anchor='start')
    lbl(d, 256, 63, '= 2000 requests in 2 seconds', size=7.5, color=REDL, anchor='start')
    lbl(d, 256, 53, 'Fix: use Sliding Window instead', size=7, color=ORANGEL, anchor='start')

    # ── When to use ───────────────────────────────────────────────────────────
    box(d, 20, 12, 440, 32, fill=colors.HexColor('#1a2e1a'), stroke=GREEN, r=4)
    lbl(d, 240, 36, '✓ Best for: known daily quota limits (like One-Frame 1000/day) where boundary burst risk is acceptable', size=8, color=GREENL, anchor='middle')
    lbl(d, 240, 26, 'Used by: GitHub (hourly), most API gateways by default. Simple, fast, auditable.', size=7.5, color=SUBTEXT, anchor='middle')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 5 — Leaky Bucket
# ══════════════════════════════════════════════════════════════════════════════
def diag_leaky_bucket():
    W, H = 480, 260
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Leaky Bucket — Traffic Shaper (not quota tracker)', size=10, bold=True, anchor='middle')

    # ── Queue visual ──────────────────────────────────────────────────────────
    QX, QY, QW, QH = 30, 60, 80, 160
    box(d, QX, QY, QW, QH, fill=colors.HexColor('#1a2e0a'), stroke=ORANGE, r=4, sw=2)
    lbl(d, QX+QW//2, QY+QH+10, 'FIFO Queue', size=8, color=ORANGEL, bold=True, anchor='middle')
    lbl(d, QX+QW//2, QY+QH+20, 'capacity=8', size=7, color=SUBTEXT, anchor='middle')

    # requests in queue
    for i in range(6):
        ry = QY + 8 + i*22
        box(d, QX+6, ry, QW-12, 18, fill=ORANGE, stroke=None, r=3, sw=0)
        lbl(d, QX+QW//2, ry+10, f'req #{i+1}', size=7, color=BG, bold=True, anchor='middle')

    # overflow requests
    for i in range(3):
        rx = QX+QW+10 + i*38
        box(d, rx, QY+20, 32, 18, fill=colors.HexColor('#2e0a0a'), stroke=REDL, r=3, sw=1)
        lbl(d, rx+16, QY+30, 'DROP', size=6.5, color=REDL, bold=True, anchor='middle')
        arr_d(d, QX+QW+5+i*8, QY+60-i*10, QY+38-i*10, color=REDL, sw=1)
    lbl(d, QX+QW+70, QY+10, '← overflow → dropped', size=7, color=REDL, anchor='middle')

    # leak arrow (bottom)
    arr_d(d, QX+QW//2, QY, QY-30, color=ORANGEL, sw=2)
    lbl(d, QX+QW//2+5, QY-15, 'drain rate: 1 req/tick', size=7.5, color=ORANGEL, anchor='start')

    # processor
    box(d, QX+10, QY-48, QW-20, 20, fill=SURFACE, stroke=GREEN, r=3, sw=1.5)
    lbl(d, QX+QW//2, QY-35, 'Process', size=8, color=GREENL, bold=True, anchor='middle')
    arr_r(d, QX+QW, QY-38, QX+QW+50, color=GREEN, sw=1.5)
    lbl(d, QX+QW+25, QY-33, 'allow', size=7.5, color=GREENL, anchor='middle')

    # incoming requests (top)
    for i in range(5):
        arr_d(d, QX+10+i*15, QY+QH+50, QY+QH+10, color=CYAN, sw=1.2)
    lbl(d, QX+QW//2, QY+QH+60, 'burst of incoming', size=7, color=CYANL, anchor='middle')
    lbl(d, QX+QW//2, QY+QH+70, 'requests', size=7, color=SUBTEXT, anchor='middle')

    # ── Properties ────────────────────────────────────────────────────────────
    box(d, 240, 140, 230, 100, fill=SURFACE, stroke=ORANGE, r=5, sw=1.5)
    lbl(d, 355, 232, 'Properties', size=8.5, color=ORANGEL, bold=True, anchor='middle')
    props = [
        ('✓', 'Perfectly smooth output rate',         GREENL),
        ('✓', 'DoS resistant — excess simply dropped', GREENL),
        ('✓', 'Used by nginx limit_req, Envoy',       GREENL),
        ('✗', 'No bursting — penalises valid spikes', REDL),
        ('✗', 'Not for N/day quota tracking',         REDL),
        ('✗', 'Queue state lost on restart',          REDL),
        ('✗', 'Distributed needs central coordinator',REDL),
    ]
    for i,(sym,txt,cl) in enumerate(props):
        lbl(d, 248, 222-i*13, sym, size=8, color=cl, bold=True, anchor='start')
        lbl(d, 258, 222-i*13, txt, size=7.5, color=cl, anchor='start')

    # ── When to use ───────────────────────────────────────────────────────────
    box(d, 240, 60, 230, 70, fill=SURFACE, stroke=CYAN, r=5, sw=1.5)
    lbl(d, 355, 122, 'Use Leaky Bucket for:', size=8.5, color=CYANL, bold=True, anchor='middle')
    uses = [
        'Egress traffic shaping (max N req/s to downstream)',
        'CPU/resource protection at ingress',
        'NOT for quota accounting (N calls per day)',
        'Combine with Fixed Window for both',
    ]
    for i,u in enumerate(uses):
        cl = ORANGEL if i>=2 else TEXT
        lbl(d, 248, 112-i*13, ('→ ' if i<2 else '✗ ')+u, size=7.5, color=cl, anchor='start')

    box(d, 240, 14, 230, 38, fill=colors.HexColor('#1a1a2e'), stroke=PURPLE, r=4)
    lbl(d, 355, 44, 'Hybrid pattern (industry)', size=8, color=PURPLEL, bold=True, anchor='middle')
    lbl(d, 248, 33, 'Leaky Bucket (rate shaper) +', size=7.5, color=TEXT, anchor='start')
    lbl(d, 248, 23, 'Fixed Window Counter (quota tracker)', size=7.5, color=TEXT, anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 6 — Redis Distributed Rate Limiting
# ══════════════════════════════════════════════════════════════════════════════
def diag_redis():
    W, H = 480, 320
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Redis — Distributed Rate Limiting (multi-instance)', size=10, bold=True, anchor='middle')

    # ── Multi-instance setup ──────────────────────────────────────────────────
    # Instance boxes
    for i,name in enumerate(['Instance A', 'Instance B', 'Instance C']):
        ix = 14 + i*105
        box(d, ix, 215, 98, 56, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
        lbl(d, ix+49, 258, name, size=8, color=GREENL, bold=True, anchor='middle')
        lbl(d, ix+49, 248, 'forex-proxy', size=7, color=SUBTEXT, anchor='middle')
        lbl(d, ix+49, 238, ':9090 / :9091 / :9092', size=6.5, color=SUBTEXT, anchor='middle')
        lbl(d, ix+49, 228, 'NO local state', size=7, color=ORANGEL, anchor='middle')
        lbl(d, ix+49, 218, 'reads Redis atomically', size=6.5, color=SUBTEXT, anchor='middle')

    # Redis box (central)
    box(d, 180, 140, 120, 62, fill=colors.HexColor('#2e0a0a'), stroke=REDL, r=6, sw=2)
    lbl(d, 240, 192, 'Redis', size=11, color=REDL, bold=True, anchor='middle')
    lbl(d, 240, 180, 'single-threaded executor', size=7.5, color=SUBTEXT, anchor='middle')
    lbl(d, 240, 170, 'Lua scripts = atomic', size=7.5, color=ORANGEL, anchor='middle')
    lbl(d, 240, 160, 'RDB/AOF persistence', size=7.5, color=SUBTEXT, anchor='middle')
    lbl(d, 240, 150, 'quota:{id}:{date} → INT', size=7.5, color=REDL, anchor='middle')

    # arrows: instances → Redis
    for i in range(3):
        ix = 63 + i*105
        arr_d(d, ix, 215, 200, color=GRAY, sw=1.2)
        arr_u(d, ix+10, 200, 215, color=GRAYL, sw=1)

    # ── Hash tag cluster note ─────────────────────────────────────────────────
    box(d, 310, 140, 162, 62, fill=SURFACE, stroke=PURPLE, r=5, sw=1.5)
    lbl(d, 391, 194, 'Cluster Hash Tags', size=8.5, color=PURPLEL, bold=True, anchor='middle')
    lbl_code(d, 318, 183, 'quota:{user123}:2026-02-28', size=7.5, anchor='start')
    lbl(d, 318, 172, '→ {user123} forces same slot', size=7.5, color=SUBTEXT, anchor='start')
    lbl(d, 318, 162, '→ Lua script runs atomically', size=7.5, color=GREENL, anchor='start')
    lbl(d, 318, 152, '→ all keys on same Redis node', size=7.5, color=SUBTEXT, anchor='start')
    lbl(d, 318, 143, 'Without: multi-key Lua = error', size=7, color=REDL, anchor='start')

    # ── Latency comparison ────────────────────────────────────────────────────
    box(d, 14, 90, 290, 42, fill=SURFACE, stroke=CYAN, r=5, sw=1.5)
    lbl(d, 159, 124, 'Latency per quota check', size=8.5, color=CYANL, bold=True, anchor='middle')
    for i,(store,lat,cl) in enumerate([
        ('In-memory Ref (single instance)', '< 1 µs  (CAS)',  GREENL),
        ('Redis (LAN)',                     '1–2 ms  (RTT)',   CYANL),
        ('PostgreSQL',                      '5–20 ms (RTT)',   YELLOWL),
    ]):
        lbl(d, 22, 114-i*12, store+':', size=7.5, color=SUBTEXT, anchor='start')
        lbl(d, 218, 114-i*12, lat, size=8, color=cl, bold=True, anchor='start')

    # ── Key properties ────────────────────────────────────────────────────────
    box(d, 310, 90, 162, 42, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
    lbl(d, 391, 124, 'When to use Redis', size=8.5, color=GREENL, bold=True, anchor='middle')
    lbl(d, 318, 113, '✓ Multiple service instances', size=7.5, color=GREENL, anchor='start')
    lbl(d, 318, 103, '✓ Quota survives any single restart', size=7.5, color=GREENL, anchor='start')
    lbl(d, 318, 93, '✗ Adds infrastructure dependency', size=7.5, color=REDL, anchor='start')

    # ── Lua atomicity proof ───────────────────────────────────────────────────
    box(d, 14, 14, 458, 68, fill=SURFACE, stroke=PURPLE, r=5, sw=1.5)
    lbl(d, 240, 74, 'Why Lua = atomic (not two separate INCR+EXPIRE)', size=8.5, color=PURPLEL, bold=True, anchor='middle')
    lbl(d, 22,  63, 'Redis is single-threaded. Lua scripts execute as one indivisible unit — no other command', size=8, color=TEXT, anchor='start')
    lbl(d, 22,  53, 'can run between the GET and the INCR inside the script. This eliminates the TOCTOU race', size=8, color=TEXT, anchor='start')
    lbl(d, 22,  42, 'where two concurrent requests both read count=999 and both conclude "allow" then both write 1000.', size=8, color=TEXT, anchor='start')
    lbl(d, 22,  31, 'WATCH/MULTI/EXEC transactions also work but Lua is preferred: shorter RTT, less client logic.', size=8, color=SUBTEXT, anchor='start')
    lbl(d, 22,  21, 'Redisson wraps all of this in a JVM-friendly RRateLimiter interface usable from Scala.', size=8, color=SUBTEXT, anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 7 — cats-effect Ref implementation (Scala)
# ══════════════════════════════════════════════════════════════════════════════
def diag_cats_ref():
    W, H = 480, 380
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'cats-effect Ref[F,_] — In-Memory Quota Tracker', size=10, bold=True, anchor='middle')

    # ── CAS diagram ───────────────────────────────────────────────────────────
    # show AtomicReference CAS loop
    box(d, 14, 285, 160, 72, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
    lbl(d, 94, 349, 'Ref[F, QuotaState]', size=8.5, color=GREENL, bold=True, anchor='middle')
    lbl(d, 94, 338, '= AtomicReference[QuotaState]', size=7.5, color=SUBTEXT, anchor='middle')
    lbl(d, 94, 327, 'CAS retry loop (wait-free)', size=7.5, color=CYANL, anchor='middle')
    lbl(d, 94, 316, 'No locks — fibers never block', size=7.5, color=TEXT, anchor='middle')
    lbl(d, 94, 305, 'O(1) amortized under low contention', size=7, color=SUBTEXT, anchor='middle')
    lbl(d, 94, 295, '≈ 50–200 ns per modify call', size=7, color=GREENL, anchor='middle')

    # state box
    box(d, 185, 285, 185, 72, fill=colors.HexColor('#0a2e0a'), stroke=GREEN, r=5, sw=1.5)
    lbl(d, 277, 349, 'QuotaState', size=8.5, color=GREENL, bold=True, anchor='middle')
    lbl_code(d, 193, 337, 'case class QuotaState(', size=8, anchor='start')
    lbl_code(d, 193, 326, '  count: Int,', size=8, anchor='start')
    lbl_code(d, 193, 315, '  date:  LocalDate,', size=8, anchor='start')
    lbl_code(d, 193, 304, '  limit: Int = 1000', size=8, anchor='start')
    lbl_code(d, 193, 293, ')', size=8, anchor='start')

    # Scala implementation
    box(d, 14, 130, 456, 148, fill=SURFACE, stroke=PURPLE, r=5, sw=1.5)
    lbl(d, 240, 270, 'Full cats-effect implementation', size=8.5, color=PURPLEL, bold=True, anchor='middle')
    scala_lines = [
        'def checkAndIncrement: F[QuotaResult] =',
        '  ref.modify { state =>',
        '    val today = LocalDate.now(ZoneOffset.UTC)',
        '    val reset  = if (state.date != today) state.copy(count=0, date=today) else state',
        '    if (reset.count >= reset.limit)',
        '      (reset, QuotaResult.Exceeded(reset.limit, resetAtMidnight(today)))',
        '    else if (reset.count >= reset.limit * 0.8)',
        '      (reset.copy(count=reset.count+1),',
        '       QuotaResult.Warning(remaining=reset.limit-reset.count-1))',
        '    else',
        '      (reset.copy(count=reset.count+1),',
        '       QuotaResult.OK(remaining=reset.limit-reset.count-1))',
        '  }',
    ]
    for i,ln in enumerate(scala_lines):
        cl = GREENL if i<2 else (CYANL if 2<=i<4 else (REDL if 4<=i<6 else (YELLOWL if 6<=i<8 else TEXT)))
        lbl_code(d, 22, 259-i*10, ln, size=7.5, color=cl, anchor='start')

    # ── Persistence via periodic flush ───────────────────────────────────────
    box(d, 14, 70, 220, 52, fill=SURFACE, stroke=ORANGE, r=5, sw=1.5)
    lbl(d, 124, 114, 'Periodic Flush to DB', size=8.5, color=ORANGEL, bold=True, anchor='middle')
    lbl_code(d, 22, 103, 'Stream.fixedDelay(30.seconds)', size=7.5, anchor='start')
    lbl_code(d, 22,  92, '  .evalMap(_ => ref.get)', size=7.5, anchor='start')
    lbl_code(d, 22,  81, '  .evalMap(db.upsertQuota)', size=7.5, anchor='start')
    lbl(d, 22,  72, 'Loss window = flush interval (30s)', size=7, color=SUBTEXT, anchor='start')

    # ── Graceful shutdown ──────────────────────────────────────────────────────
    box(d, 245, 70, 225, 52, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
    lbl(d, 357, 114, 'Graceful Shutdown Flush', size=8.5, color=GREENL, bold=True, anchor='middle')
    lbl_code(d, 253, 103, 'Resource.make(acquire) {', size=7.5, anchor='start')
    lbl_code(d, 253,  92, '  state =>              ', size=7.5, anchor='start')
    lbl_code(d, 253,  81, '    ref.get.flatMap(db.upsertQuota)', size=7.5, anchor='start')
    lbl_code(d, 253,  72, '}                       ', size=7.5, anchor='start')

    # ── Tradeoffs ──────────────────────────────────────────────────────────────
    box(d, 14, 14, 456, 50, fill=SURFACE, stroke=CYAN, r=4, sw=1.5)
    lbl(d, 240, 56, 'When to use in-memory Ref', size=8.5, color=CYANL, bold=True, anchor='middle')
    tradeoffs = [
        ('✓ Single-instance (current forex-proxy architecture)', GREENL),
        ('✓ Zero infrastructure — no Redis, no extra DB table needed', GREENL),
        ('✓ Sub-microsecond quota checks — no latency added to request path', GREENL),
        ('✗ Multi-instance: each Ref is independent — quota is per-instance, not shared', REDL),
        ('✗ SIGKILL loses up to 30s of counts (permissive failure — slight overcounting)', YELLOWL),
    ]
    for i,(t,cl) in enumerate(tradeoffs):
        lbl(d, 22, 46-i*9, t, size=7.5, color=cl, anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 8 — HTTP Rate Limit Headers
# ══════════════════════════════════════════════════════════════════════════════
def diag_headers():
    W, H = 480, 300
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'HTTP Rate Limit Headers — Standards & Response Examples', size=10, bold=True, anchor='middle')

    # ── De facto standard (X-RateLimit-*) ─────────────────────────────────────
    box(d, 14, 200, 220, 78, fill=SURFACE, stroke=CYAN, r=5, sw=1.5)
    lbl(d, 124, 270, 'De Facto Standard (GitHub, etc.)', size=8.5, color=CYANL, bold=True, anchor='middle')
    headers_defacto = [
        'X-RateLimit-Limit:     1000',
        'X-RateLimit-Remaining: 423',
        'X-RateLimit-Reset:     1740787200  ← Unix epoch UTC',
        'X-RateLimit-Used:      577',
        'Retry-After:           54321       ← seconds until reset',
    ]
    for i,h in enumerate(headers_defacto):
        cl = CYANL if 'Limit' in h else (GREENL if 'Remain' in h else (REDL if 'Retry' in h else TEXT))
        lbl_code(d, 22, 260-i*13, h, size=7.5, color=cl, anchor='start')

    # ── IETF Draft ────────────────────────────────────────────────────────────
    box(d, 246, 200, 226, 78, fill=SURFACE, stroke=PURPLE, r=5, sw=1.5)
    lbl(d, 359, 270, 'IETF Draft (emerging standard)', size=8.5, color=PURPLEL, bold=True, anchor='middle')
    headers_ietf = [
        'RateLimit-Policy: "daily";q=1000;w=86400',
        'RateLimit:        "daily";r=423;t=54321',
        '',
        '← Multi-policy (burst + daily):',
        'RateLimit-Policy: "burst";q=100;w=60,',
        '                  "daily";q=1000;w=86400',
        'RateLimit: "burst";r=89;t=42,',
        '           "daily";r=423;t=54321',
    ]
    for i,h in enumerate(headers_ietf):
        cl = PURPLEL if 'Policy' in h else (CYANL if 'RateLimit:' in h or '"burst"' in h or '"daily"' in h else (SUBTEXT if '←' in h else TEXT))
        lbl_code(d, 254, 260-i*10, h, size=7, color=cl, anchor='start')

    # ── 429 response example ──────────────────────────────────────────────────
    box(d, 14, 100, 456, 94, fill=colors.HexColor('#1a0a0a'), stroke=REDL, r=5, sw=1.5)
    lbl(d, 240, 186, 'HTTP 429 Too Many Requests — full response', size=8.5, color=REDL, bold=True, anchor='middle')
    resp_lines = [
        'HTTP/1.1 429 Too Many Requests',
        'Content-Type: application/json',
        'Retry-After: 54321',
        'X-RateLimit-Limit: 1000',
        'X-RateLimit-Remaining: 0',
        'X-RateLimit-Reset: 1740787200',
        '',
        '{"error":"Daily quota of 1000 upstream API calls exhausted.",',
        ' "resets_at":"2026-03-01T00:00:00Z","remaining":0}',
    ]
    for i,ln in enumerate(resp_lines):
        cl = REDL if '429' in ln else (ORANGEL if 'Retry' in ln or 'Reset' in ln else (GREENL if 'Remain' in ln else (CYANL if 'json' in ln or 'error' in ln else TEXT)))
        lbl_code(d, 22, 176-i*10, ln, size=7.5, color=cl, anchor='start')

    # ── http4s snippet ────────────────────────────────────────────────────────
    box(d, 14, 14, 456, 80, fill=SURFACE, stroke=GREEN, r=5, sw=1.5)
    lbl(d, 240, 86, 'http4s — adding quota headers to every response', size=8.5, color=GREENL, bold=True, anchor='middle')
    http4s_lines = [
        'def withQuotaHeaders(resp: Response[F], state: QuotaState): Response[F] =',
        '  resp.putHeaders(',
        '    Header("X-RateLimit-Limit",     state.limit.toString),',
        '    Header("X-RateLimit-Remaining", state.remaining.toString),',
        '    Header("X-RateLimit-Reset",     state.resetEpochSeconds.toString)',
        '  )',
        'val middleware: HttpRoutes[F] => HttpRoutes[F] = routes =>',
        '  Kleisli { req => routes(req).semiflatMap(r => quota.get.map(withQuotaHeaders(r,_))) }',
    ]
    for i,ln in enumerate(http4s_lines):
        lbl_code(d, 22, 76-i*9, ln, size=7.5, color=GREENL if i<6 else PURPLEL, anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 9 — Hard vs Soft Limits & Industry Comparison
# ══════════════════════════════════════════════════════════════════════════════
def diag_soft_hard():
    W, H = 480, 320
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Hard vs Soft Limits + Industry Comparison', size=10, bold=True, anchor='middle')

    # ── Gauge visual ──────────────────────────────────────────────────────────
    # Horizontal bar 0→1000
    BL, BR, BY, BHH = 14, 370, 215, 34
    BW = BR - BL

    # background
    d.add(Rect(BL, BY, BW, BHH, rx=8, ry=8,
               fillColor=SURFACE, strokeColor=BORDER, strokeWidth=1))

    # green zone 0-70%
    gw = int(BW*0.70)
    d.add(Rect(BL+2, BY+2, gw-4, BHH-4, rx=6, ry=6,
               fillColor=colors.HexColor('#16a34a44'), strokeColor=None, strokeWidth=0))
    # yellow zone 70-90%
    yw_s = BL+2+gw-4
    yw = int(BW*0.20)-2
    d.add(Rect(yw_s, BY+2, yw, BHH-4, rx=0, ry=0,
               fillColor=colors.HexColor('#ca8a0444'), strokeColor=None, strokeWidth=0))
    # red zone 90-100%
    rw_s = yw_s+yw
    rw = BW - int(BW*0.90) - 4
    d.add(Rect(rw_s, BY+2, rw, BHH-4, rx=0, ry=0,
               fillColor=colors.HexColor('#dc262644'), strokeColor=None, strokeWidth=0))

    # soft limit marker at 80%
    sx = BL + int(BW*0.80)
    d.add(Line(sx, BY-8, sx, BY+BHH+8, strokeColor=YELLOWL, strokeWidth=2,
               strokeDashArray=[4,2]))
    lbl(d, sx, BY-16, 'Soft Limit\n80% = 800', size=7, color=YELLOWL, anchor='middle')

    # hard limit marker at 100%
    hx = BR - 2
    d.add(Line(hx, BY-8, hx, BY+BHH+8, strokeColor=REDL, strokeWidth=2))
    lbl(d, hx, BY-16, 'Hard Limit\n100% = 1000', size=7, color=REDL, anchor='middle')

    # labels
    lbl(d, BL, BY-5, '0', size=7, color=SUBTEXT, anchor='start')
    lbl(d, BL+int(BW*0.35), BY+BHH+12, 'OK — ✓ fresh', size=7.5, color=GREENL, anchor='middle')
    lbl(d, BL+int(BW*0.85), BY+BHH+12, '⚡ warn', size=7.5, color=YELLOWL, anchor='middle')
    lbl(d, BR-int(BW*0.04), BY+BHH+12, '✗', size=8, color=REDL, anchor='middle')

    # current usage arrow
    cur_x = BL + int(BW*0.57)
    d.add(Line(cur_x, BY+BHH+28, cur_x, BY+BHH+2, strokeColor=CYANL, strokeWidth=1.5))
    d.add(Polygon([cur_x-4, BY+BHH+4, cur_x, BY+BHH-2, cur_x+4, BY+BHH+4],
                  fillColor=CYANL, strokeColor=CYANL, strokeWidth=0))
    lbl(d, cur_x, BY+BHH+36, 'current: 570', size=7.5, color=CYANL, anchor='middle')

    # Soft limit response headers
    box(d, 14, 140, 220, 68, fill=SURFACE, stroke=YELLOWL, r=4, sw=1.5)
    lbl(d, 124, 200, 'Soft Limit Warning (800+)', size=8.5, color=YELLOWL, bold=True, anchor='middle')
    lbl_code(d, 22, 189, 'X-RateLimit-Remaining: 180', size=8, anchor='start')
    lbl_code(d, 22, 179, 'Warning: 299 - "Approaching limit"', size=7.5, anchor='start')
    lbl(d, 22, 169, '→ Still 200 OK — not rejected', size=7.5, color=GREENL, anchor='start')
    lbl(d, 22, 159, '→ Allow operators to react before', size=7.5, color=TEXT, anchor='start')
    lbl(d, 22, 149, '  customers are impacted', size=7.5, color=SUBTEXT, anchor='start')
    lbl(d, 22, 140, '→ Used by: Twilio (80% email alert)', size=7, color=SUBTEXT, anchor='start')

    # Hard limit response
    box(d, 246, 140, 226, 68, fill=colors.HexColor('#2e0a0a'), stroke=REDL, r=4, sw=1.5)
    lbl(d, 359, 200, 'Hard Limit (1000 reached)', size=8.5, color=REDL, bold=True, anchor='middle')
    lbl_code(d, 254, 189, 'HTTP/1.1 429 Too Many Requests', size=8, color=REDL, anchor='start')
    lbl_code(d, 254, 179, 'Retry-After: 54321', size=8, anchor='start')
    lbl_code(d, 254, 169, 'X-RateLimit-Remaining: 0', size=8, color=REDL, anchor='start')
    lbl(d, 254, 159, '→ Absolute ceiling — no exceptions', size=7.5, color=REDL, anchor='start')
    lbl(d, 254, 149, '→ Client must wait for reset', size=7.5, color=TEXT, anchor='start')
    lbl(d, 254, 140, '→ Retry-After tells client when', size=7.5, color=SUBTEXT, anchor='start')

    # ── Industry comparison table ─────────────────────────────────────────────
    tdata = [
        ['Provider',    'Algorithm',      'Window',    'Hard Limit',      'Soft Limit', 'Headers'],
        ['GitHub',      'Fixed Window',   '1 hour',    '5000 req/hr',     '—',          'X-RateLimit-*'],
        ['Stripe',      'Token Bucket',   'per second', '100 req/s',      '80% warning','X-RateLimit-*'],
        ['Twitter/X',   'Sliding Window', '15 min',    'per-endpoint',    '—',          'x-rate-limit-*'],
        ['One-Frame',   'Fixed Window',   '1 day',     '1000 calls/day',  '—',          '—'],
        ['forex-proxy', 'Fixed Window*',  '1 day',     'tracks upstream', '80% = 800',  'X-RateLimit-*'],
    ]
    cw = [(PAGE_W-2*MARGIN-30)*x for x in [0.15,0.16,0.11,0.18,0.15,0.14]]
    t  = Table(tdata, colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), PURPLE),
        ('TEXTCOLOR',     (0,0),(-1,0), WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0), 7.5),
        ('BACKGROUND',    (0,1),(-1,-1), SURFACE),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[SURFACE, SURFACE2]),
        ('TEXTCOLOR',     (0,1),(0,-1), CYANL),
        ('TEXTCOLOR',     (1,1),(-1,-1), TEXT),
        ('TEXTCOLOR',     (0,-1),(-1,-1), PURPLEL),  # last row (forex-proxy)
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))

    # draw table as flowable — embed it as a drawing approximation
    # Instead we'll include it in the story; return the drawing without it
    lbl(d, 14, 125, '* see implementation options below — industry comparison table on this page as separate flowable',
        size=7, color=SUBTEXT, anchor='start')

    return d, t

# ══════════════════════════════════════════════════════════════════════════════
# DIAGRAM 10 — Decision Tree: which algorithm to choose
# ══════════════════════════════════════════════════════════════════════════════
def diag_decision():
    W, H = 480, 340
    d = Drawing(W, H)
    d.add(Rect(0,0,W,H, fillColor=BG, strokeColor=BG))

    lbl(d, W//2, H-10, 'Decision Tree — Which Algorithm to Choose', size=10, bold=True, anchor='middle')

    def decision_node(x, y, w, h, q, cl=CYAN, fill=SURFACE):
        box(d, x, y, w, h, fill=fill, stroke=cl, r=5, sw=1.5)
        lines = q.split('\n')
        for i,ln in enumerate(lines):
            lbl(d, x+w//2, y+h//2+(len(lines)-1)*6 - i*12, ln, size=8, color=cl, bold=True, anchor='middle')

    def answer_node(x, y, w, h, txt, cl=GREEN):
        box(d, x, y, w, h, fill=colors.HexColor('#0a2e0a'), stroke=cl, r=5, sw=2)
        lines = txt.split('\n')
        for i,ln in enumerate(lines):
            lbl(d, x+w//2, y+h//2+(len(lines)-1)*6 - i*11, ln, size=7.5, color=cl, bold=True, anchor='middle')

    # Q1: multi-instance?
    decision_node(165, 278, 150, 32, 'Multiple service instances?', CYAN)

    # YES → Redis
    answer_node(360, 268, 108, 52, 'Redis\nSliding Window\n(Lua script)', GREEN)
    arr_r(d, 315, 294, 360, color=GREEN, sw=1.5)
    lbl(d, 337, 298, 'YES', size=7.5, color=GREENL, bold=True, anchor='middle')

    # NO → Q2: survive restart?
    arr_d(d, 240, 278, 242, color=CYAN, sw=1.5)
    lbl(d, 244, 261, 'NO', size=7.5, color=CYANL, bold=True, anchor='start')

    decision_node(165, 210, 150, 32, 'Must survive restart\n(exact accounting)?', PURPLE)

    # YES → DB
    answer_node(360, 200, 108, 52, 'PostgreSQL\nFixed Window\n(ON CONFLICT)', ORANGE)
    arr_r(d, 315, 226, 360, color=ORANGE, sw=1.5)
    lbl(d, 337, 230, 'YES', size=7.5, color=ORANGEL, bold=True, anchor='middle')

    # NO → Q3: boundary burst ok?
    arr_d(d, 240, 210, 178, color=PURPLE, sw=1.5)
    lbl(d, 244, 195, 'NO', size=7.5, color=PURPLEL, bold=True, anchor='start')

    decision_node(165, 146, 150, 32, 'Boundary burst\nacceptable?', YELLOW)

    # YES → Fixed Window + Ref
    answer_node(360, 136, 108, 52, 'Ref[F,_]\nFixed Window\n(simplest)', GREENL)
    arr_r(d, 315, 162, 360, color=GREENL, sw=1.5)
    lbl(d, 337, 166, 'YES', size=7.5, color=GREENL, bold=True, anchor='middle')

    # NO → Sliding Window + Ref
    arr_d(d, 240, 146, 114, color=YELLOW, sw=1.5)
    lbl(d, 244, 131, 'NO', size=7.5, color=YELLOWL, bold=True, anchor='start')

    answer_node(165, 78, 150, 36, 'Ref[F,_]\nSliding Window\n(interpolated)', CYANL)

    # Q4: need smooth output rate?
    decision_node(14, 146, 140, 32, 'Need smooth output\nrate (no bursts)?', ORANGE)
    arr_l(d, 14+140, 162, 165, color=ORANGE, sw=1.5)
    lbl(d, 154, 166, 'YES', size=7.5, color=ORANGEL, bold=True, anchor='middle')
    answer_node(14, 96, 140, 46, 'Leaky Bucket\n(traffic shaper)\n+ separate counter', ORANGEL)
    arr_d(d, 84, 146, 142, color=ORANGE, sw=1.5)

    # ── Recommendation box ────────────────────────────────────────────────────
    box(d, 14, 14, 454, 58, fill=colors.HexColor('#1a1a2e'), stroke=PURPLE, r=6, sw=1.5)
    lbl(d, 240, 64, 'For forex-mtl specifically:', size=9, color=PURPLEL, bold=True, anchor='middle')
    lbl(d, 22,  52, '→ Today (single instance): Ref[F, QuotaState] with Fixed Window. Zero infra, idiomatic cats-effect,', size=8, color=TEXT, anchor='start')
    lbl(d, 22,  42, '  sub-µs checks. Periodic SQLite flush for restart survival. Expose remaining in X-RateLimit-* headers.', size=8, color=SUBTEXT, anchor='start')
    lbl(d, 22,  31, '→ Future (multi-instance): Redis Sliding Window via Lua script. Upgrade path: swap Ref for RedisClient,', size=8, color=TEXT, anchor='start')
    lbl(d, 22,  21, '  keep the same algebra (QuotaAlgebra[F]) — callers see zero change.', size=8, color=SUBTEXT, anchor='start')

    return d

# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT ASSEMBLY
# ══════════════════════════════════════════════════════════════════════════════
def build(path):
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title='Rate Limiting & Quota Tracking — Industry Standards',
        author='forex-mtl'
    )
    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [sp(50),
              Paragraph('Rate Limiting &', S_COVER),
              Paragraph('Token Quota Tracking', S_COVER),
              sp(8),
              Paragraph('Industry-Standard Algorithms, Patterns & Scala/cats-effect Implementations', S_CSUB),
              sp(4),
              Paragraph('Token Bucket · Sliding Window · Fixed Window · Leaky Bucket · Redis · PostgreSQL · Ref[F,_]', S_CSUB),
              sp(20), hr(), sp(10)]

    toc = [
        ('1', 'Algorithm Comparison — Same Burst, Different Responses'),
        ('2', 'Token Bucket — Mechanics & State'),
        ('3', 'Sliding Window Counter — Interpolated Quota'),
        ('4', 'Fixed Window Counter — Boundary-Burst Risk'),
        ('5', 'Leaky Bucket — Traffic Shaper vs Quota Tracker'),
        ('6', 'Redis — Distributed Rate Limiting'),
        ('7', 'cats-effect Ref[F,_] — In-Memory Quota Tracker'),
        ('8', 'HTTP Rate Limit Headers — Standards & Examples'),
        ('9', 'Hard vs Soft Limits + Industry Comparison'),
        ('10','Decision Tree — Which Algorithm to Choose'),
    ]
    tdata = [['#', 'Section']] + [[n, t] for n,t in toc]
    tt = Table(tdata, colWidths=[1.2*cm, 13*cm])
    tt.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), PURPLE),
        ('TEXTCOLOR',     (0,0),(-1,0), WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0), 9),
        ('BACKGROUND',    (0,1),(-1,-1), SURFACE),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[SURFACE, SURFACE2]),
        ('TEXTCOLOR',     (0,1),(0,-1), PURPLEL),
        ('TEXTCOLOR',     (1,1),(1,-1), TEXT),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-1), 9),
        ('GRID',          (0,0),(-1,-1), 0.5, BORDER),
        ('ALIGN',         (0,0),(0,-1), 'CENTER'),
        ('TOPPADDING',    (0,0),(-1,-1), 5),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
        ('LEFTPADDING',   (0,0),(-1,-1), 8),
    ]))
    story.append(tt)

    # ── Page 1: Algorithm Comparison ─────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('1. Algorithm Comparison — Same Burst, Different Responses'))
    story.append(body(
        'Four algorithms receive the same 12-request burst against a limit of 8 per window. '
        'Each circle represents one request — green=allowed, red=rejected. '
        'The differences reveal each algorithm\'s core trade-off.'
    ))
    story.append(sp(4))
    story.append(DF(diag_algorithms()))
    story.append(cap('Figure 1 — Same burst, four algorithms. Fixed Window has a boundary exploit at the window edge.'))

    # ── Page 2: Token Bucket ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('2. Token Bucket'))
    story.append(body(
        'The canonical industry algorithm for burst-tolerant rate limiting. Used by Stripe, '
        'AWS API Gateway, Envoy Proxy, and nginx. State is two numbers: tokens remaining and '
        'last refill timestamp. The bucket refills continuously at a fixed rate — it does not '
        'reset at a clock boundary. Allows legitimate traffic spikes up to the bucket capacity.'
    ))
    story.append(sp(4))
    story.append(DF(diag_token_bucket()))
    story.append(cap('Figure 2 — Token Bucket: bucket drains on each request, refills at constant rate. Burst = bucket capacity.'))

    # ── Page 3: Sliding Window ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('3. Sliding Window Counter'))
    story.append(body(
        'Interpolates between the previous and current fixed windows to eliminate the boundary '
        'burst exploit. At any point in time, the effective count is: '
        'prev_count × (1 − elapsed%) + curr_count. '
        'Used by Cloudflare and Upstash. Requires two Redis keys and one Lua script. '
        'Most principled choice for "N per calendar day" semantics without a hard midnight cliff.'
    ))
    story.append(sp(4))
    story.append(DF(diag_sliding_window()))
    story.append(cap('Figure 3 — Sliding Window: 70% of yesterday\'s count + today\'s count. Gradual rollover, no cliff.'))

    # ── Page 4: Fixed Window ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('4. Fixed Window Counter'))
    story.append(body(
        'The simplest algorithm. One Redis key per (entity, day). INCR is atomic. Key expires '
        'automatically after 24h. Natural fit for "1000 calls/day" semantics that align with '
        'upstream quotas (GitHub, One-Frame). Primary weakness: boundary burst — a client can '
        'make 2000 calls in 2 seconds spanning midnight. Use a Lua script to make INCR+EXPIRE atomic.'
    ))
    story.append(sp(4))
    story.append(DF(diag_fixed_window()))
    story.append(cap('Figure 4 — Fixed Window: one counter per day, resets at UTC midnight. Simple, fast, auditable.'))

    # ── Page 5: Leaky Bucket ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('5. Leaky Bucket'))
    story.append(body(
        'A traffic shaper, not a quota counter. Incoming requests fill a FIFO queue; '
        'a background process drains the queue at a constant rate. Excess requests are dropped. '
        'Guarantees a perfectly smooth output rate to downstream services — ideal for protecting '
        'One-Frame from bursts. Does not track daily totals; combine with a Fixed Window counter '
        'for both rate shaping and quota enforcement.'
    ))
    story.append(sp(4))
    story.append(DF(diag_leaky_bucket()))
    story.append(cap('Figure 5 — Leaky Bucket: constant drain rate, overflow dropped. Traffic shaper, not quota tracker.'))

    # ── Page 6: Redis ─────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('6. Redis — Distributed Rate Limiting'))
    story.append(body(
        'The standard backend for rate limiting in multi-instance deployments. Redis is '
        'single-threaded — Lua scripts run as indivisible units, eliminating TOCTOU races without '
        'distributed locks. Sub-2ms LAN latency. Survives restarts with RDB/AOF persistence. '
        'In Redis Cluster, use hash tags ({user_id}) to force all quota keys onto the same slot.'
    ))
    story.append(sp(4))
    story.append(DF(diag_redis()))
    story.append(cap('Figure 6 — Redis: shared state across instances. Lua = atomic check+increment. Hash tags for cluster.'))

    # ── Page 7: cats-effect Ref ───────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('7. cats-effect Ref[F,_] — In-Memory Quota Tracker'))
    story.append(body(
        'The idiomatic cats-effect solution for single-instance deployments. '
        'Ref wraps an AtomicReference — modify() is a CAS (compare-and-swap) retry loop: '
        'wait-free, O(1), no locks, no blocking of fibers. The state is a case class holding '
        'count, date, and limit. Day rollover is handled inside the modify function. '
        'Persist with a 30-second periodic flush stream and a graceful-shutdown Resource.'
    ))
    story.append(sp(4))
    story.append(DF(diag_cats_ref()))
    story.append(cap('Figure 7 — Ref[F, QuotaState]: CAS-based, wait-free, zero deps. Periodic flush for restart survival.'))
    story.append(sp(6))
    story.append(h3('Recommended algebra for upgrade-safe design'))
    story.append(code(
        'trait QuotaAlgebra[F[_]] {\n'
        '  def check: F[QuotaResult]          // read without increment\n'
        '  def increment: F[QuotaResult]      // check + increment atomically\n'
        '  def remaining: F[Int]              // for X-RateLimit-Remaining header\n'
        '}\n'
        '// Today: InMemoryQuota[F](ref: Ref[F, QuotaState])\n'
        '// Future: RedisQuota[F](redis: RedisClient[F])   ← same trait, zero caller changes'
    ))

    # ── Page 8: HTTP Headers ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('8. HTTP Rate Limit Headers'))
    story.append(body(
        'Return quota state in every response header — not just on 429s. This lets clients '
        'self-throttle before hitting the hard limit. The de facto X-RateLimit-* standard '
        '(originated by GitHub) is widely supported by client libraries. The IETF '
        'draft-ietf-httpapi-ratelimit-headers is emerging as the formal standard supporting '
        'multiple simultaneous policies.'
    ))
    story.append(sp(4))
    story.append(DF(diag_headers()))
    story.append(cap('Figure 8 — Response headers: de facto X-RateLimit-* vs IETF draft. Full 429 example. http4s middleware.'))

    # ── Page 9: Hard vs Soft + Industry ──────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('9. Hard vs Soft Limits + Industry Comparison'))
    story.append(body(
        'A soft limit (typically 80%) warns clients before they hit the hard ceiling — '
        'allowing operators to react before customers are impacted. '
        'The Retry-After header tells clients exactly when their quota resets, '
        'enabling intelligent backoff rather than exponential polling.'
    ))
    story.append(sp(4))
    diag9, industry_table = diag_soft_hard()
    story.append(DF(diag9))
    story.append(sp(8))
    story.append(industry_table)
    story.append(cap('Figure 9 — Gauge: green (OK) → yellow (soft warn 80%) → red (hard limit 100%). Industry comparison table.'))

    # ── Page 10: Decision Tree ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('10. Decision Tree — Which Algorithm to Choose'))
    story.append(body(
        'Three questions determine the right algorithm: (1) multiple instances? (2) '
        'exact restart survival required? (3) is boundary-burst acceptable? '
        'For forex-mtl today: in-memory Ref with Fixed Window is the right answer. '
        'The QuotaAlgebra[F] trait makes the Redis upgrade path zero-cost to callers.'
    ))
    story.append(sp(4))
    story.append(DF(diag_decision()))
    story.append(cap('Figure 10 — Decision tree: multi-instance → Redis; single → Ref[F,_]; smooth rate → add Leaky Bucket.'))

    # ── Final summary page ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(h1('Summary — Algorithm Cheat Sheet'))
    story.append(sp(4))

    summary_data = [
        ['Algorithm',          'Latency',   'Distributed', 'Restart', 'Burst', 'N/day Fit',  'Best For'],
        ['Token Bucket',       '< 1µs*',    '✗ (needs Redis)', 'Flush','✓ Yes','△ Approx',  'API throughput shaping'],
        ['Sliding Window',     '1-2ms**',   '✓ Redis Lua', 'Redis',   '△ None','✓ Best',   'Rolling quota, no cliff'],
        ['Fixed Window',       '1-2ms**',   '✓ Redis Lua', 'Redis',   '△ None','✓ Great',  'Simple daily quotas'],
        ['Leaky Bucket',       '< 1µs*',    '✗ Hard',      'Lost',    '✗ No', 'N/A',        'Downstream rate shaping'],
        ['Redis (any algo)',   '1-2ms',      '✓ Native',    '✓ Yes',   'Depends','✓ Yes',   'Multi-instance production'],
        ['PostgreSQL (upsert)','5-20ms',     '✓ Native',    '✓ Yes',   '✗ No','✓ Yes',     'Audit trail, reporting'],
        ['Ref[F,_] (cats-eff)','< 0.1µs',   '✗ Single',    'Flush',   '△',   '✓ Yes',     'Single-instance + idiomatic'],
    ]
    cw2 = [(PAGE_W-2*MARGIN)*x for x in [0.18,0.10,0.15,0.10,0.09,0.11,0.21]]
    st = Table(summary_data, colWidths=cw2)
    st.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), PURPLE),
        ('TEXTCOLOR',     (0,0),(-1,0), WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0), 7.5),
        ('BACKGROUND',    (0,1),(-1,-1), SURFACE),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[SURFACE, SURFACE2]),
        ('TEXTCOLOR',     (0,1),(0,-1), CYANL),
        ('TEXTCOLOR',     (1,1),(-1,-1), TEXT),
        ('TEXTCOLOR',     (0,-1),(-1,-1), PURPLEL),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-1), 7.5),
        ('GRID',          (0,0),(-1,-1), 0.4, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 5),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ('WORDWRAP',      (0,0),(-1,-1), True),
    ]))
    story.append(st)
    story.append(sp(8))
    story.append(small('* In-memory with cats-effect Ref or local queue — no network RTT'))
    story.append(small('** Redis Lua script round-trip on LAN. Add 20-50ms for cross-region/cloud Redis.'))
    story.append(sp(8))

    story.append(h2('Applied to forex-mtl: Tracking the One-Frame 1000/day Quota'))
    story.append(body(
        'The current architecture already sidesteps the hardest part of quota management: '
        'the refresh scheduler fires exactly once per interval (240s default), consuming '
        '~360 of the 1000 daily calls predictably. No per-request quota check needed at the '
        'One-Frame boundary. What to add:'
    ))
    impl_data = [
        ['What',                    'How',                                           'When'],
        ['Count upstream calls',    'Ref[F, QuotaState] incremented by refresh loop','Now — zero infra'],
        ['Expose remaining quota',  'X-RateLimit-* headers on /rates responses',     'Now — middleware'],
        ['Warn at 80% (800 calls)', 'QuotaResult.Warning state → log + SSE event',  'Now — soft limit'],
        ['Reject at 100% (1000)',   'Return HTTP 503 / cached stale data instead',   'Now — hard limit'],
        ['Persist across restarts', 'SQLite upsert every 30s + Resource shutdown',   'Optional — low risk'],
        ['Multi-instance upgrade',  'Redis Sliding Window via QuotaAlgebra[F] trait','Future if needed'],
    ]
    cw3 = [(PAGE_W-2*MARGIN)*x for x in [0.25,0.48,0.25]]
    it = Table(impl_data, colWidths=cw3)
    it.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,0), GREEN),
        ('TEXTCOLOR',     (0,0),(-1,0), WHITE),
        ('FONTNAME',      (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0), 8),
        ('BACKGROUND',    (0,1),(-1,-1), SURFACE),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[SURFACE, SURFACE2]),
        ('TEXTCOLOR',     (0,1),(0,-1), CYANL),
        ('TEXTCOLOR',     (1,1),(1,-1), TEXT),
        ('TEXTCOLOR',     (2,1),(2,-1), GREENL),
        ('FONTNAME',      (0,1),(-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-1), 8),
        ('GRID',          (0,0),(-1,-1), 0.4, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 6),
        ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(sp(4))
    story.append(it)

    doc.build(story)
    print(f'PDF written → {path}')

if __name__ == '__main__':
    build('/home/juan/paidy/interview/rate-limit-guide.pdf')
