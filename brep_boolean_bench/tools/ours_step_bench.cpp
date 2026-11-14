// session_cpp side of the STEP boolean bench (brep_boolean_bench/RESULTS.md).
//   ours_step_bench load <file.step>
//     LOAD <file> <status> read_s <s> breps <n> [error]
//     BREP <file> <i> faces edges vertices shells solids valid solid kinds=plane,sphere,cylinder,cone,torus,free vol_s volume
//   ours_step_bench bool <specA> <specB> <op> [dump.json]
//     BOOL <op> <status> bool_s faces edges vertices valid solid vol_s volume [message]
//   ours_step_bench dumpops <specA> <specB> <dump.json>   operands only
// A spec is `step=<path>` (the shell of largest volume), `box=sx,sy,sz` (centred), `cyl=r,h` (+Z from z=0) or
// `sph=r`, `cone=r,h` (+Z, apex up), followed by `|`-separated moves applied in order: `t=x,y,z` or `r=ax,ay,az,deg,cx,cy,cz`
// (rotation about the axis through c). op: intersection union a-b b-a xor.
#include "brep.h"
#include "file_step.h"
#include "nurbs_implicit.h"
#include "xform.h"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <map>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace session_cpp;

static double since(std::chrono::steady_clock::time_point t0) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
}

static std::vector<double> numbers(const std::string& s) {
    std::vector<double> v;
    std::stringstream in(s);
    std::string item;
    while (std::getline(in, item, ',')) v.push_back(std::stod(item));
    return v;
}

static std::vector<std::string> split(const std::string& s, char c) {
    std::vector<std::string> v;
    std::stringstream in(s);
    std::string item;
    while (std::getline(in, item, c)) v.push_back(item);
    return v;
}


// Driver-side topology repair (NOT kernel code), only with REPAIR=1: reverse the edge order of a wire that is open as
// read but closes when walked backwards, then flip shell face uses so every edge is used once each way, then flip the
// whole shell when the volume comes out negative. Separates the reader's orientation handling from the booleans.
static bool wire_closed(const BRep& b, const std::vector<BRepRef>& edges) {
    int start = -1, previous = -1;
    for (const BRepRef& r : edges) {
        if (r.orientation == BRepOrientation::Internal || r.orientation == BRepOrientation::External) continue;
        const BRepEdge& e = b.m_edges[r.index];
        const int first = r.orientation == BRepOrientation::Reversed ? e.end_vertex : e.start_vertex;
        const int last = r.orientation == BRepOrientation::Reversed ? e.start_vertex : e.end_vertex;
        if (previous >= 0 && previous != first) return false;
        if (start < 0) start = first;
        previous = last;
    }
    return start < 0 || previous == start;
}

static BRepOrientation flip(BRepOrientation o) {
    return o == BRepOrientation::Forward ? BRepOrientation::Reversed : o == BRepOrientation::Reversed ? BRepOrientation::Forward : o;
}

static std::string repair(BRep& b) {
    int wires = 0, faces = 0, shells = 0;
    for (BRepWire& w : b.m_wires)
        if (!wire_closed(b, w.edges)) {
            std::vector<BRepRef> c(w.edges.rbegin(), w.edges.rend());
            if (wire_closed(b, c)) { w.edges = c; ++wires; }
        }
    for (BRepShell& sh : b.m_shells) {
        const int n = (int)sh.faces.size();
        std::vector<std::vector<std::pair<int, int>>> uses(b.m_edges.size());  // (face slot, sign)
        for (int k = 0; k < n; ++k)
            for (const BRepRef& wr : b.m_faces[sh.faces[k].index].wires)
                for (const BRepRef& er : b.wire_edges(wr)) {
                    if (b.m_edges[er.index].degenerated) continue;
                    const BRepOrientation o = brep_compose(sh.faces[k].orientation, er.orientation);
                    if (o == BRepOrientation::Forward) uses[er.index].push_back({k, 1});
                    else if (o == BRepOrientation::Reversed) uses[er.index].push_back({k, -1});
                }
        std::vector<std::vector<std::pair<int, int>>> adj(n);  // (other slot, 1 when signs are equal)
        for (const auto& u : uses)
            if (u.size() == 2 && u[0].first != u[1].first) {
                const int same = u[0].second == u[1].second;
                adj[u[0].first].push_back({u[1].first, same});
                adj[u[1].first].push_back({u[0].first, same});
            }
        std::vector<int> state(n, -1);
        for (int s0 = 0; s0 < n; ++s0) {
            if (state[s0] >= 0) continue;
            state[s0] = 0;
            std::vector<int> stack{s0};
            while (!stack.empty()) {
                const int f = stack.back();
                stack.pop_back();
                for (const auto& [g, same] : adj[f])
                    if (state[g] < 0) { state[g] = state[f] ^ same; stack.push_back(g); }
            }
        }
        for (int k = 0; k < n; ++k)
            if (state[k] == 1) { sh.faces[k].orientation = flip(sh.faces[k].orientation); ++faces; }
    }
    double v = 0.0;
    try { v = b.volume_exact(); } catch (...) { try { v = b.volume(); } catch (...) {} }
    if (v < 0)
        for (BRepShell& sh : b.m_shells) { for (BRepRef& r : sh.faces) r.orientation = flip(r.orientation); ++shells; }
    std::ostringstream o;
    o << "wires_reordered=" << wires << " faces_flipped=" << faces << " shells_flipped=" << shells;
    return o.str();
}

static BRep largest(std::vector<BRep>& breps) {
    if (breps.empty()) throw std::runtime_error("STEP file holds no BRep");
    size_t best = 0;
    double best_volume = -1.0;
    for (size_t i = 0; i < breps.size(); ++i) {
        // |tessellated volume|, or the vertex box volume when that is not finite (same choice as OCCT's largest solid)
        double v = std::nan("");
        try { v = std::abs(breps[i].volume()); } catch (...) {}
        if (!std::isfinite(v)) {
            std::array<double, 3> lo{1e300, 1e300, 1e300}, hi{-1e300, -1e300, -1e300};
            for (const BRepVertex& p : breps[i].m_vertices)
                for (int k = 0; k < 3; ++k) { lo[k] = std::min(lo[k], p.point[k]); hi[k] = std::max(hi[k], p.point[k]); }
            v = breps[i].m_vertices.empty() ? 0.0 : (hi[0] - lo[0]) * (hi[1] - lo[1]) * (hi[2] - lo[2]);
        }
        if (v > best_volume) { best_volume = v; best = i; }
    }
    return breps[best];
}

static BRep build(const std::string& spec) {
    const std::vector<std::string> parts = split(spec, '|');
    const std::string head = parts[0];
    const size_t eq = head.find('=');
    const std::string kind = head.substr(0, eq), arg = head.substr(eq + 1);
    BRep b;
    if (kind == "step") {
        std::vector<BRep> breps = file_step::read_file_step_breps(arg);
        if (std::getenv("REPAIR")) for (BRep& x : breps) repair(x);
        b = largest(breps);
    } else if (kind == "box") {
        const auto s = numbers(arg);
        b = BRep::create_box(s[0], s[1], s[2]);
    } else if (kind == "cyl") {
        const auto s = numbers(arg);
        b = BRep::create_cylinder(s[0], s[1]);
    } else if (kind == "cone") {
        const auto s = numbers(arg);
        b = BRep::create_cone(s[0], s[1]);
    } else if (kind == "sph") {
        b = BRep::create_sphere(numbers(arg)[0]);
    } else {
        throw std::runtime_error("unknown spec " + kind);
    }
    for (size_t i = 1; i < parts.size(); ++i) {
        const std::string k = parts[i].substr(0, 1);
        const auto s = numbers(parts[i].substr(2));
        if (k == "t") {
            b.transform(Xform::translation(s[0], s[1], s[2]));
        } else if (k == "r") {
            const Xform x = Xform::translation(s[4], s[5], s[6]) * Xform::rotation(Vector(s[0], s[1], s[2]), s[3], true)
                * Xform::translation(-s[4], -s[5], -s[6]);
            b.transform(x);
        }
    }
    return b;
}

static std::string kinds(const BRep& b) {
    std::array<int, 6> n{};
    for (const BRepFace& f : b.m_faces) {
        if (f.surface_index < 0) continue;
        const NurbsSurface& s = b.m_surfaces[f.surface_index];
        int k = 0;
        try { k = nurbs_implicit::recognize(s, 1e-6).kind; } catch (...) { k = 0; }
        ++n[k == 0 ? 5 : k - 1];
    }
    std::ostringstream o;
    o << n[0] << "," << n[1] << "," << n[2] << "," << n[3] << "," << n[4] << "," << n[5];
    return o.str();
}


// Reasons behind is_valid()/is_solid() being false, counted (same checks as brep.cpp, read-only).
static std::string diagnose(const BRep& b) {
    int bad_srf = 0, bad_c3 = 0, bad_c2 = 0, open_wires = 0, bad_edge = 0, odd_use = 0, unbalanced = 0, faces_nowire = 0;
    for (const NurbsSurface& s : b.m_surfaces) if (!s.is_valid()) ++bad_srf;
    for (const NurbsCurve& c : b.m_curves_3d) if (!c.is_valid()) ++bad_c3;
    for (const NurbsCurve& c : b.m_curves_2d) if (!c.is_valid()) ++bad_c2;
    for (const BRepEdge& e : b.m_edges) if (!e.degenerated && e.curve_3d_index < 0) ++bad_edge;
    for (const BRepWire& w : b.m_wires) {
        int start = -1, previous = -1;
        bool gap = false;
        for (const BRepRef& r : w.edges) {
            if (r.orientation == BRepOrientation::Internal || r.orientation == BRepOrientation::External) continue;
            const BRepEdge& edge = b.m_edges[r.index];
            const int first = r.orientation == BRepOrientation::Reversed ? edge.end_vertex : edge.start_vertex;
            const int last = r.orientation == BRepOrientation::Reversed ? edge.start_vertex : edge.end_vertex;
            if (previous >= 0 && previous != first) gap = true;
            if (start < 0) start = first;
            previous = last;
        }
        if (gap || (start >= 0 && previous != start)) {
            ++open_wires;
            if (std::getenv("DIAG_DETAIL")) {
                int face = -1;
                for (size_t fi = 0; fi < b.m_faces.size(); ++fi)
                    for (const BRepRef& wr : b.m_faces[fi].wires) if (&b.m_wires[wr.index] == &w) face = (int)fi;
                int kind = face >= 0 ? nurbs_implicit::recognize(b.m_surfaces[b.m_faces[face].surface_index], 1e-6).kind : -1;
                std::cerr << "open wire face " << face << " kind " << kind << ":";
                for (const BRepRef& r : w.edges) {
                    const BRepEdge& e = b.m_edges[r.index];
                    std::cerr << " e" << r.index << (r.orientation == BRepOrientation::Reversed ? "R" : "F") << "(" << e.start_vertex << "->" << e.end_vertex << (e.degenerated ? " deg" : "") << ")";
                }
                std::cerr << "\n";
            }
        }
    }
    for (const BRepFace& f : b.m_faces) if (f.wires.empty()) ++faces_nowire;
    for (size_t si = 0; si < b.m_shells.size(); ++si) {
        std::vector<int> uses(b.m_edges.size(), 0), balance(b.m_edges.size(), 0);
        for (const BRepRef& fr : b.m_shells[si].faces)
            for (const BRepRef& wr : b.m_faces[fr.index].wires)
                for (const BRepRef& er : b.wire_edges(wr)) {
                    if (b.m_edges[er.index].degenerated) continue;
                    const BRepOrientation o = brep_compose(fr.orientation, er.orientation);
                    if (o == BRepOrientation::Internal || o == BRepOrientation::External) continue;
                    ++uses[er.index];
                    balance[er.index] += o == BRepOrientation::Forward ? 1 : -1;
                }
        for (size_t i = 0; i < uses.size(); ++i) {
            if (!b.m_edges[i].degenerated && uses[i] != 0 && uses[i] != 2) ++odd_use;
            if (balance[i] != 0) ++unbalanced;
        }
        if (std::getenv("DIAG_DETAIL")) {
            std::map<std::string, int> kinds_of;  // face kind pairs at unbalanced edges
            for (size_t fi = 0; fi < b.m_shells[si].faces.size(); ++fi) {
                const int face = b.m_shells[si].faces[fi].index;
                int bad = 0;
                for (const BRepRef& wr : b.m_faces[face].wires)
                    for (const BRepRef& er : b.wire_edges(wr)) if (balance[er.index] != 0) ++bad;
                if (bad) {
                    const int kind = nurbs_implicit::recognize(b.m_surfaces[b.m_faces[face].surface_index], 1e-6).kind;
                    std::cerr << "face " << face << " kind " << kind << " unbalanced edges " << bad << "\n";
                }
            }
        }
    }
    std::ostringstream o;
    o << "invalid_surfaces=" << bad_srf << " invalid_curves3d=" << bad_c3 << " invalid_curves2d=" << bad_c2 << " edges_without_curve=" << bad_edge
      << " open_wires=" << open_wires << " faces_without_wire=" << faces_nowire << " edges_not_used_twice=" << odd_use << " edges_same_direction_twice=" << unbalanced;
    return o.str();
}

static std::string dump(const BRep& r) {
    std::ostringstream o;
    o.precision(7);
    o << "{\"pos\":[";
    std::ostringstream idx;
    size_t base = 0;
    bool first = true;
    for (const Mesh& m : r.face_meshes()) {
        const auto [vs, fs] = m.to_vertices_and_faces();
        for (size_t i = 0; i < vs.size(); ++i) o << (base + i ? "," : "") << vs[i][0] << "," << vs[i][1] << "," << vs[i][2];
        for (const auto& f : fs)
            for (size_t k = 1; k + 1 < f.size(); ++k) { idx << (first ? "" : ",") << base + f[0] << "," << base + f[k] << "," << base + f[k + 1]; first = false; }
        base += vs.size();
    }
    o << "],\"idx\":[" << idx.str() << "],\"edges\":[";
    first = true;
    for (const BRepEdge& e : r.m_edges) {
        if (e.degenerated || e.curve_3d_index < 0) continue;
        const NurbsCurve& c = r.m_curves_3d[e.curve_3d_index];
        const auto [t0, t1] = c.domain();
        o << (first ? "" : ",") << "[";
        first = false;
        for (int i = 0; i <= 48; ++i) { const Point p = c.point_at(t0 + (t1 - t0) * i / 48.0); o << (i ? "," : "") << p[0] << "," << p[1] << "," << p[2]; }
        o << "]";
    }
    o << "],\"verts\":[";
    for (size_t i = 0; i < r.m_vertices.size(); ++i) { const Point& p = r.m_vertices[i].point; o << (i ? "," : "") << p[0] << "," << p[1] << "," << p[2]; }
    o << "],\"counts\":[" << r.face_count() << "," << r.edge_count() << "," << r.vertex_count() << "]}";
    return o.str();
}

static std::string volume_text(const BRep& r) {
    const auto t0 = std::chrono::steady_clock::now();
    std::ostringstream o;
    o.precision(12);
    if (r.face_count() == 0) { o << since(t0) << " 0"; return o.str(); }
    try {
        const double v = r.volume_exact();
        o << since(t0) << " " << v;
    } catch (const std::exception&) {
        double v = 0.0;
        try { v = r.volume(); } catch (...) { v = std::nan(""); }
        o << since(t0) << " " << v << "(mesh)";
    }
    return o.str();
}

int main(int argc, char** argv) {
    std::cout.precision(6);
    if (argc < 3) { std::cerr << "usage: see header\n"; return 2; }
    const std::string mode = argv[1];
    if (mode == "load") {
        const std::string path = argv[2];
        const auto t0 = std::chrono::steady_clock::now();
        std::vector<BRep> breps;
        try {
            breps = file_step::read_file_step_breps(path);
        } catch (const std::exception& e) {
            std::cout << "LOAD " << path << " FAIL read_s " << since(t0) << " breps 0 " << e.what() << "\n";
            return 0;
        }
        std::cout << "LOAD " << path << " ok read_s " << since(t0) << " breps " << breps.size() << "\n" << std::flush;
        for (size_t i = 0; i < breps.size(); ++i) {
            if (std::getenv("REPAIR")) std::cout << "REPAIR " << path << " " << i << " " << repair(breps[i]) << "\n";
            const BRep& b = breps[i];
            bool valid = false, solid = false;
            try { valid = b.is_valid(); } catch (...) {}
            try { solid = b.is_solid(); } catch (...) {}
            std::cout << "BREP " << path << " " << i << " " << b.face_count() << " " << b.edge_count() << " " << b.vertex_count() << " "
                      << b.shell_count() << " " << b.solid_count() << " " << valid << " " << solid << " kinds=" << kinds(b) << " " << std::flush;
            std::cout << volume_text(b) << "\n" << std::flush;
            {
                std::map<std::string, int> h;  // pcurve (2D trim) degree/cv-count histogram
                for (const NurbsCurve& c : b.m_curves_2d) ++h["deg" + std::to_string(c.degree()) + (c.cv_count() > 2 * (c.degree() + 1) ? "+many" : "")];
                std::cout << "PCURVES " << path << " " << i;
                for (const auto& [k, v] : h) std::cout << " " << k << "=" << v;
                std::cout << "\n";
            }
            if (!valid || !solid) std::cout << "DIAG " << path << " " << i << " " << diagnose(b) << "\n" << std::flush;
        }
        return 0;
    }
    if (mode == "probe") {
        const std::string path = argv[2];
        std::cout << "PROBE " << path << " points " << file_step::read_file_step_points(path).size() << " curves "
                  << file_step::read_file_step_nurbscurves(path).size() << " surfaces " << file_step::read_file_step_nurbssurfaces(path).size() << std::flush;
        std::cout << " trimmed " << file_step::read_file_step_nurbssurfaces_trimmed(path).size() << "\n";
        return 0;
    }
    if (mode == "chain") {
        // occt-booltest: body <- body ∩ rotated(body), repeated; argv: spec rotation(ax,ay,az,deg,cx,cy,cz) iterations
        BRep body = build(argv[2]);
        const auto q = numbers(argv[3]);
        const int iterations = std::stoi(argv[4]);
        const Xform turn = Xform::translation(q[4], q[5], q[6]) * Xform::rotation(Vector(q[0], q[1], q[2]), q[3], true)
            * Xform::translation(-q[4], -q[5], -q[6]);
        for (int it = 1; it <= iterations; ++it) {
            const BRep other = body.transformed(turn);
            const auto t0 = std::chrono::steady_clock::now();
            try {
                body = body.boolean_intersection(other);
            } catch (const std::exception& e) {
                std::string msg = e.what();
                for (char& c : msg) if (c == '\n') c = ' ';
                std::cout << "CHAIN " << it << " FAIL " << since(t0) << " 0 0 0 0 0 - - " << msg.substr(0, 300) << "\n";
                return 0;
            }
            const double seconds = since(t0);
            std::cout << "CHAIN " << it << " ok " << seconds << " " << body.face_count() << " " << body.edge_count() << " " << body.vertex_count() << " "
                      << body.is_valid() << " " << body.is_solid() << " " << std::flush << volume_text(body) << "\n" << std::flush;
            if (body.face_count() == 0) return 0;
        }
        return 0;
    }
    if (mode == "dumpops") {
        const BRep a = build(argv[2]), b = build(argv[3]);
        std::ofstream out(argv[4]);
        out << "[" << dump(a) << "," << dump(b) << "]";
        return 0;
    }
    if (mode == "bool") {
        const std::string op = argv[4];
        BRep a, b;
        try {
            a = build(argv[2]);
            b = build(argv[3]);
        } catch (const std::exception& e) {
            std::cout << "BOOL " << op << " LOADFAIL 0 0 0 0 0 0 - - " << e.what() << "\n";
            return 0;
        }
        BRep r;
        const auto t0 = std::chrono::steady_clock::now();
        try {
            const double tol = std::getenv("TOL") ? std::stod(std::getenv("TOL")) : 1e-7;  // kernel default 1e-7
            r = op == "intersection" ? a.boolean_intersection(b, tol) : op == "union" ? a.boolean_union(b, tol) : op == "a-b" ? a.boolean_difference(b, tol)
                : op == "b-a" ? b.boolean_difference(a, tol) : a.boolean_xor(b, tol);
        } catch (const std::exception& e) {
            std::string msg = e.what();
            for (char& c : msg) if (c == '\n') c = ' ';
            std::cout << "BOOL " << op << " FAIL " << since(t0) << " 0 0 0 0 0 - - " << msg.substr(0, 300) << "\n";
            return 0;
        }
        const double seconds = since(t0);
        bool valid = false, solid = false;
        try { valid = r.is_valid(); } catch (...) {}
        try { solid = r.is_solid(); } catch (...) {}
        std::cout << "BOOL " << op << " ok " << seconds << " " << r.face_count() << " " << r.edge_count() << " " << r.vertex_count() << " "
                  << valid << " " << solid << " " << std::flush;
        std::cout << volume_text(r) << "\n" << std::flush;
        if (argc > 5) {
            std::ofstream out(argv[5]);
            out << dump(r);
        }
        return 0;
    }
    return 2;
}
