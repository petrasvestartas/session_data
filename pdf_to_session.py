# PDF vector drawing -> Session (.pb + .json) stress-test fixture.
#   python pdf_to_session.py ["30700 Querschnitt G-G.pdf"] [out_stem] [page_number]
# Extracts page vector paths via PyMuPDF: line runs -> Line/Polyline, cubic beziers -> degree-3
# NurbsCurve, rects/quads -> closed Polyline. PDF y points down -> flipped; 1 pt = 1 mm; z = 0.
import sys
import fitz
from session_py import Session, Point, Line, Polyline, NurbsCurve, Color

SRC = sys.argv[1] if len(sys.argv) > 1 else "30700 Querschnitt G-G.pdf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "30700_querschnitt_gg"
PAGE = int(sys.argv[3]) if len(sys.argv) > 3 else 0
EPS = 1e-9
SCALE = 1.0

doc = fitz.open(SRC)
page = doc[PAGE]
H = page.rect.height

def pt(p):
    return Point(p.x * SCALE, (H - p.y) * SCALE, 0.0)

def same(a, b):
    return abs(a[0] - b[0]) < EPS and abs(a[1] - b[1]) < EPS

session = Session()
n_lines = 0
n_polylines = 0
n_curves = 0
n_segments = 0

def path_style(path):
    """Stroke color (fallback: fill, then black) + line width from the PDF path."""
    c = path.get("color") or path.get("fill")
    col = Color(float(c[0]), float(c[1]), float(c[2]), 1.0) if c else Color.black()
    w = path.get("width")
    return col, float(w) if w and w > 0 else 1.0

def flush(chain, col, w):
    global n_lines, n_polylines, n_segments
    if len(chain) < 2:
        return
    if len(chain) == 2:
        a, b = chain
        ln = Line(a[0], a[1], a[2], b[0], b[1], b[2])
        ln.linecolor = col
        ln.width = w
        session.add_line(ln)
        n_lines += 1
    else:
        points = []
        for c in chain:
            points.append(Point(c[0], c[1], c[2]))
        pl = Polyline(points)
        pl.linecolor = col
        pl.width = w
        session.add_polyline(pl)
        n_polylines += 1
    n_segments += len(chain) - 1

for path in page.get_drawings():
    col, w = path_style(path)
    chain = []
    for item in path["items"]:
        op = item[0]
        if op == "l":
            a = pt(item[1])
            b = pt(item[2])
            a = (a[0], a[1], a[2])
            b = (b[0], b[1], b[2])
            if same(a, b):
                continue
            if chain and same(chain[-1], a):
                chain.append(b)
            else:
                flush(chain, col, w)
                chain = [a, b]
        elif op == "c":
            flush(chain, col, w)
            chain = []
            points = []
            for q in item[1:5]:
                p = pt(q)
                points.append(Point(p[0], p[1], p[2]))
            nc = NurbsCurve.create(False, 3, points)
            nc.width = w
            session.add_nurbscurve(nc)
            n_curves += 1
            n_segments += 8
        elif op == "re":
            flush(chain, col, w)
            chain = []
            r = item[1]
            corners = [
                Point(r.x0 * SCALE, (H - r.y0) * SCALE, 0.0),
                Point(r.x1 * SCALE, (H - r.y0) * SCALE, 0.0),
                Point(r.x1 * SCALE, (H - r.y1) * SCALE, 0.0),
                Point(r.x0 * SCALE, (H - r.y1) * SCALE, 0.0),
                Point(r.x0 * SCALE, (H - r.y0) * SCALE, 0.0),
            ]
            pl = Polyline(corners)
            pl.linecolor = col
            pl.width = w
            session.add_polyline(pl)
            n_polylines += 1
            n_segments += 4
        elif op == "qu":
            flush(chain, col, w)
            chain = []
            quad = item[1]
            points = []
            for q in (quad.ul, quad.ur, quad.lr, quad.ll, quad.ul):
                p = pt(q)
                points.append(Point(p[0], p[1], p[2]))
            pl = Polyline(points)
            pl.linecolor = col
            pl.width = w
            session.add_polyline(pl)
            n_polylines += 1
            n_segments += 4
    flush(chain, col, w)

session.pb_dump(OUT + ".pb")
if "--nojson" not in sys.argv:
    session.file_json_dump(OUT + ".json")
print(f"page={PAGE + 1}/{len(doc)} lines={n_lines} polylines={n_polylines} curves={n_curves} segments~{n_segments}")
print(f"wrote {OUT}.pb + {OUT}.json")
