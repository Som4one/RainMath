#!/usr/bin/env python3
"""Rainmath - pip install customtkinter sympy numpy matplotlib pillow
Menu principal : Tools (calculs) / Daily (beta). Multilingue (Français / English / Русский) + infobulles (survol > 1 s)."""
import base64, copy, datetime, io, json, math, os, random, re, sys
try:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import filedialog
except ImportError:
    sys.exit("Rainmath needs Tk (tkinter), which is missing from this Python.\n"
             "  Debian/Ubuntu: sudo apt install python3-tk\n"
             "  Fedora/RHEL:   sudo dnf install python3-tkinter\n"
             "  Arch:          sudo pacman -S tk\n"
             "  openSUSE:      sudo zypper install python3-tk\n"
             "  Alpine:        sudo apk add py3-tkinter\n"
             "Or run ./install.sh to set everything up.")
try:
    import customtkinter as ctk
    import numpy as np
    import sympy as sp
    from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                            implicit_multiplication_application, convert_xor)
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
except ImportError as err:
    sys.exit(f"Missing Python module: {err.name}\n"
             "Install the dependencies with:  pip install -r requirements.txt\n"
             "On Linux you can also run ./install.sh")

# ======================= RÉGLAGES =======================
def _chemin_reglages():
    """reglages.json next to the script; if that folder is read-only (system-wide install), use ~/.config/rainmath."""
    dossier = os.path.dirname(os.path.abspath(__file__))
    if os.access(dossier, os.W_OK):
        return os.path.join(dossier, "reglages.json")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    dossier = os.path.join(base, "rainmath")
    try:
        os.makedirs(dossier, exist_ok=True)
    except OSError:
        pass
    return os.path.join(dossier, "reglages.json")


FICHIER = _chemin_reglages()
REGL = dict(theme="dark", decimales=6, imag="i", rayon=14, accent="Bleu", police=14, approx=True, langue="fr")
try:
    with open(FICHIER, encoding="utf-8") as _f:
        REGL.update(json.load(_f))
except Exception:
    pass

# HiDPI screens on Linux: RAINMATH_SCALE=1.5 python3 Rainmath.py
try:
    _ech = float(os.environ.get("RAINMATH_SCALE", "0"))
    if _ech > 0:
        ctk.set_widget_scaling(_ech)
        ctk.set_window_scaling(_ech)
except ValueError:
    pass


def sauver():
    try:
        with open(FICHIER, "w", encoding="utf-8") as f:
            json.dump(REGL, f)
    except OSError:
        pass


LANGS = {"fr": "Français", "en": "English", "ru": "Русский"}
if REGL["langue"] not in LANGS:
    REGL["langue"] = "fr"

ACCENTS = {"Bleu": "#3b82f6", "Violet": "#8b5cf6", "Vert": "#10b981",
           "Orange": "#f59e0b", "Rose": "#ec4899", "Rouge": "#ef4444"}
PAL = {"Dark": dict(bg="#15161c", card="#1f2029", fg="#e8e8f0", sub="#8b8ca0", line="#30313f"),
       "Light": dict(bg="#f2f3f8", card="#ffffff", fg="#1b1c24", sub="#6b6c80", line="#dcdde8"),
       "Noir": dict(bg="#000000", card="#0c0c0c", fg="#ffffff", sub="#9a9a9a", line="#2a2a2a")}   # noir & blanc pur
COURBES_NB = ["#ffffff", "#bdbdbd", "#8c8c8c", "#e0e0e0", "#6e6e6e"]
STYLES_NB = ["-", "--", ":", "-."]          # en noir & blanc, les courbes se distinguent par leur trait
COURBES = ["#3b82f6", "#f43f5e", "#22c55e", "#f59e0b", "#a855f7"]

# Thème de base de CustomTkinter (bleu) : copié pour pouvoir le passer en gris dans le thème « Noir & blanc »
THEME0 = copy.deepcopy(ctk.ThemeManager.theme)
GRIS = {"#3B8ED0": "#4a4a4a", "#1F6AA5": "#4a4a4a", "#36719F": "#5e5e5e", "#144870": "#5e5e5e"}


def _gris(v):
    if isinstance(v, str):
        return GRIS.get(v.upper(), v) if v.upper() in GRIS else v
    if isinstance(v, (list, tuple)):
        return [_gris(x) for x in v]
    if isinstance(v, dict):
        return {k: _gris(x) for k, x in v.items()}
    return v


def appliquer_theme():
    """Applique le thème choisi (dark / noir / light / system) et renvoie la palette correspondante."""
    noir = REGL["theme"] == "noir"
    ctk.ThemeManager.theme = _gris(THEME0) if noir else copy.deepcopy(THEME0)
    ctk.set_appearance_mode("dark" if noir else REGL["theme"])
    return PAL["Noir" if noir else ctk.get_appearance_mode()]


def accent():
    """(couleur d'accent, texte sur l'accent, couleur des onglets/segments sélectionnés)"""
    if REGL["theme"] == "noir":
        return "#ffffff", "#000000", "#3a3a3a"
    ac = ACCENTS[REGL["accent"]]
    return ac, "#ffffff", ac

# ======================= TRADUCTION =======================
# Les textes de base sont en français ; TXT donne (anglais, russe).
IDX = {"fr": 0, "en": 1, "ru": 2}


def tx(s):
    """Traduit un texte français dans la langue choisie (sinon le renvoie tel quel)."""
    v = TXT.get(s)
    return v[IDX[REGL["langue"]] - 1] if v and REGL["langue"] != "fr" else s


def pick(v):
    """Choisit le bon texte dans un triplet (fr, en, ru)."""
    return v[IDX[REGL["langue"]]] if v else None


# ======================= OUTILS DE CALCUL =======================
TR = standard_transformations + (implicit_multiplication_application, convert_xor)
LOC = {"e": sp.E, "i": sp.I, "j": sp.I}   # i et j acceptés en entrée
X, Y = sp.symbols("x y")


def E(s, d=None):
    return parse_expr(s.strip(), transformations=TR, local_dict={**LOC, **(d or {})})


def S(s, d="x"): return sp.Symbol(s.strip() or d)
def VS(s): return [sp.Symbol(k.strip()) for k in s.split(",")]
def Vec(s): return sp.Matrix([E(k) for k in s.split(",")])
def Mat(s): return sp.Matrix([[E(k) for k in l.split(",")] for l in s.split(";")])
def entier(s): return int(E(s))
def nums(s): return np.array([float(k) for k in s.split(",")])


def check(r):
    if r.has(sp.Integral, sp.Sum):
        raise ValueError(tx("SymPy n'a pas trouvé de résultat exact"))
    return r


def num(v):
    s = f"{v:.{REGL['decimales']}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def A(x):
    """valeur approchée arrondie selon les réglages"""
    try:
        v = complex(sp.N(x))
    except Exception:
        return "?"
    if abs(v.imag) < 1e-12:
        return num(v.real)
    return f"{num(v.real)} {'+' if v.imag >= 0 else '-'} {num(abs(v.imag))}{REGL['imag']}"


def L(x):
    s = re.sub(r"\bI\b", REGL["imag"], sp.sstr(x).replace("**", "^"))
    return re.sub(r"\bE\b", "e", s)


def P(x):
    return sp.pretty(x, use_unicode=True).replace("ⅈ", REGL["imag"])


def approchable(x):
    return REGL["approx"] and getattr(x, "is_number", False) and x.is_finite and not x.is_Integer


def V(x):
    x = sp.sympify(x)
    return L(x) + (f"  ≈ {A(x)}" if approchable(x) else "")


def R(x):
    return P(x) + (f"\n≈ {A(x)}" if approchable(x) else "")


class Res(str):
    """Résultat en texte + version LaTeX (parts) pour l'affichage mathématique."""
    def __new__(cls, texte, parts=None, tex=None):
        o = super().__new__(cls, texte)
        o.parts, o.tex = parts, tex
        return o


LATEX_LHS = {"∇f": r"\nabla f", "H(f)": r"H(f)", "div F": r"\mathrm{div}\,F", "rot F": r"\mathrm{rot}\,F",
             "det(M)": r"\det(M)", "M⁻¹": r"M^{-1}", "A·B": r"A\cdot B", "u · v": r"u\cdot v",
             "u × v": r"u\times v"}


def TEX(x, joli=False):
    """code LaTeX d'une expression sympy (avec i ou j selon les réglages).
    joli=True : version adaptée à l'affichage (espaces fins entre facteurs, sin x sans parenthèses)."""
    opts = dict(fold_func_brackets=True, mul_symbol=r"\,") if joli else {}
    try:
        return sp.latex(x, imaginary_unit=REGL["imag"], **opts)
    except Exception:
        return sp.latex(x, **opts)


def EQ(lhs, rhs, plus_c=False):
    """Résultat « ∫ f dx = valeur » : texte (unicode) + LaTeX (rendu par matplotlib)."""
    texte = P(sp.Eq(lhs, rhs + sp.Symbol("C") if plus_c else rhs, evaluate=False))
    try:
        ap = A(rhs) if approchable(sp.sympify(rhs)) else ""
    except Exception:
        ap = ""
    if ap:
        texte += f"\n≈ {ap}"
    try:
        nom = isinstance(lhs, sp.Symbol) and lhs.name in LATEX_LHS
        g, gj = (LATEX_LHS[lhs.name],) * 2 if nom else (TEX(lhs), TEX(lhs, True))
        if isinstance(rhs, sp.MatrixBase):
            cells = [[TEX(rhs[i, j], True) for j in range(rhs.cols)] for i in range(rhs.rows)]
            return Res(texte, [gj + " =", ("mat", cells)], g + " = " + TEX(rhs))
        c = " + C" if plus_c else ""
        return Res(texte, [gj + " = " + TEX(rhs, True) + c + (r" \approx " + ap if ap else "")],
                   g + " = " + TEX(rhs) + c)
    except Exception:
        return texte


def NOM(s):
    """symbole 'décoratif' pour le côté gauche (ex : det(M), ∇f...)"""
    return sp.Symbol(s)


def png_latex(parts, fg, bg, taille):
    """Dessine des formules LaTeX (mathtext de matplotlib, police Computer Modern) et renvoie un PNG.
    parts = liste de morceaux placés côte à côte : du LaTeX (str) ou ("mat", [[cellules]])."""
    import matplotlib
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.lines import Line2D
    with matplotlib.rc_context({"mathtext.fontset": "cm"}):
        fig = Figure(dpi=150, facecolor=bg)
        FigureCanvasAgg(fig)
        rend, em = fig.canvas.get_renderer(), taille * 150 / 72

        def mesure(tex):
            t = fig.text(0, 0, "$" + tex.replace("\\limits", "") + "$", fontsize=taille, color=fg)
            b = t.get_window_extent(rend)
            return t, b.width, b.height

        items = []
        for m in parts:
            if isinstance(m, str):
                t, w, h = mesure(m)
                items.append(("txt", t, w, h))
            else:
                cells = [[mesure(c) for c in row] for row in m[1]]
                cw = [max(r[j][1] for r in cells) for j in range(len(cells[0]))]
                rh = [max(c[2] for c in r) for r in cells]
                gx, gy = 0.9 * em, 0.35 * em
                w = sum(cw) + gx * (len(cw) - 1) + em
                h = sum(rh) + gy * (len(rh) - 1) + 0.5 * em
                items.append(("mat", cells, cw, rh, gx, gy, w, h))
        pad, esp = 0.6 * em, 0.5 * em
        W = sum(it[2] if it[0] == "txt" else it[-2] for it in items) + esp * (len(items) - 1) + 2 * pad
        H = max(it[3] if it[0] == "txt" else it[-1] for it in items) + 2 * pad
        fig.set_size_inches(W / 150, H / 150)
        x = pad
        for it in items:
            if it[0] == "txt":
                _, t, w, h = it
                t.set_ha("left"); t.set_va("center"); t.set_position((x / W, 0.5))
                x += w + esp
                continue
            _, cells, cw, rh, gx, gy, w, h = it
            top = H / 2 + h / 2 - 0.25 * em
            for i, row in enumerate(cells):
                yc = top - sum(rh[:i]) - gy * i - rh[i] / 2
                for j, (t, _, _) in enumerate(row):
                    xc = x + 0.5 * em + sum(cw[:j]) + gx * j + cw[j] / 2
                    t.set_ha("center"); t.set_va("center"); t.set_position((xc / W, yc / H))
            yt, yb, arm = (H + h) / 2, (H - h) / 2, 0.3 * em
            for x0, sg in ((x, 1), (x + w, -1)):
                fig.add_artist(Line2D([(x0 + sg * arm) / W, x0 / W, x0 / W, (x0 + sg * arm) / W],
                                      [yt / H, yt / H, yb / H, yb / H], transform=fig.transFigure,
                                      color=fg, lw=1.3))
            x += w + esp
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, facecolor=bg)
        return buf.getvalue()


def lignes(l, nom="x"):
    return "\n".join(f"{nom}{k + 1} = {V(s)}" for k, s in enumerate(l)) or tx("Aucune solution")


def base(n, b):
    c, s = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", ""
    while n:
        n, r = divmod(n, b)
        s = c[r] + s
    return s or "0"


TOOLS = []


def T(cat, nom, spec, f):
    """spec = 'Label=défaut|Label=défaut'"""
    TOOLS.append(dict(cat=cat, nom=nom, champs=[c.split("=", 1) for c in spec.split("|")], f=f))


# ---------- Algèbre ----------
T("Algèbre", "Simplifier", "Expression=(x^2-1)/(x-1)", lambda e: R(sp.simplify(E(e))))
T("Algèbre", "Développer", "Expression=(x+1)^5", lambda e: R(sp.expand(E(e))))
T("Algèbre", "Factoriser", "Expression=x^4-1", lambda e: R(sp.factor(E(e))))


def equation(t, v):
    v = S(v)
    g, _, d = t.partition("=")
    return lignes(sp.solve(E(g) - E(d) if d else E(g), v), v)


T("Algèbre", "Résoudre une équation", "Équation=x^2+2x+5=0|Inconnue=x", equation)


def systeme(t, vs):
    eqs = [E(a) - E(b) for a, b in (q.split("=") for q in t.split(";"))]
    sol = sp.solve(eqs, VS(vs), dict=True)
    return "\n".join(", ".join(f"{k} = {V(w)}" for k, w in s.items()) for s in sol) or tx("Aucune solution")


T("Algèbre", "Système d'équations", "Équations (séparées par ;)=x+y=3; x-y=1|Inconnues=x,y", systeme)


def inequation(t, v):
    x = sp.Symbol(v.strip() or "x", real=True)
    a, op, b = re.split(r"(<=|>=|<|>)", t)
    a, b = E(a, {str(x): x}), E(b, {str(x): x})
    rel = {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
    return P(sp.solve_univariate_inequality(rel, x, relational=False))


T("Algèbre", "Inéquation", "Inéquation=x^2-3x+2<=0|Inconnue=x", inequation)


def trinome(a, b, c):
    a, b, c = E(a), E(b), E(c)
    d, s, f = sp.simplify(b**2 - 4*a*c), -b / (2*a), a*X**2 + b*X + c
    rac, y = sp.solve(f, X), sp.simplify(f.subs(X, -b / (2*a)))
    w = max([6] + [1.5 * abs(float(sp.re(sp.N(q))) - float(s)) for q in rac])
    txt = (f"Δ = {V(d)}\n{lignes(rac)}\n{tx('Sommet')} : ({V(s)} ; {V(y)})\n"
           f"{tx('Forme canonique')} : {L(a)}(x - {L(s)})^2 + {L(y)}")
    return txt, [f], (float(s) - w, float(s) + w)


T("Algèbre", "Trinôme du 2nd degré", "a=1|b=-3|c=2", trinome)
T("Algèbre", "Fractions partielles", "Expression=1/(x^2-1)|Variable=x", lambda e, v: P(sp.apart(E(e), S(v))))
T("Algèbre", "Substituer une valeur", "Expression=x^2+y|Variable=x|Valeur=3",
  lambda e, v, w: R(E(e).subs(S(v), E(w))))


def division(a, b):
    q, r = sp.div(E(a), E(b), X)
    return f"{tx('Quotient')} : {L(q)}\n{tx('Reste')} : {L(r)}"


T("Algèbre", "Division de polynômes", "Dividende=x^3+2x+1|Diviseur=x+1", division)

# ---------- Analyse ----------
T("Analyse", "Dérivée", "f=x^3*sin(x)|Variable=x|Ordre=1",
  lambda f, v, n: EQ(sp.Derivative(E(f), (S(v), int(n))), sp.diff(E(f), S(v), int(n))))
T("Analyse", "Dérivée partielle", "f=x^2*y+sin(x*y)|Variables=x,y",
  lambda f, v: EQ(sp.Derivative(E(f), *VS(v)), sp.diff(E(f), *VS(v))))
T("Analyse", "Primitive", "f=x^2*exp(x)|Variable=x",
  lambda f, v: EQ(sp.Integral(E(f), S(v)), check(sp.integrate(E(f), S(v))), plus_c=True))
T("Analyse", "Intégrale définie", "f=x^2|Variable=x|De=0|À=pi",
  lambda f, v, a, b: EQ(sp.Integral(E(f), (S(v), E(a), E(b))),
                        check(sp.integrate(E(f), (S(v), E(a), E(b))))))
T("Analyse", "Intégrale double", "f(x,y)=x*y|x de=0|x à=1|y de=0|y à=2",
  lambda f, a, b, c, d: EQ(sp.Integral(E(f), (X, E(a), E(b)), (Y, E(c), E(d))),
                           check(sp.integrate(E(f), (X, E(a), E(b)), (Y, E(c), E(d))))))
T("Analyse", "Limite", "f=sin(x)/x|Variable=x|Tend vers=0|Côté (+, - ou +-)=+-",
  lambda f, v, p, c: EQ(sp.Limit(E(f), S(v), E(p), c.strip() or "+-"),
                        sp.limit(E(f), S(v), E(p), c.strip() or "+-")))
T("Analyse", "Série de Taylor", "f=exp(x)*cos(x)|Variable=x|En x0=0|Ordre=5",
  lambda f, v, a, n: EQ(E(f), sp.series(E(f), S(v), E(a), int(n) + 1)))
T("Analyse", "Somme", "Terme=1/k^2|Indice=k|De=1|À=oo",
  lambda f, k, a, b: EQ(sp.Sum(E(f), (S(k, "k"), E(a), E(b))),
                        check(sp.summation(E(f), (S(k, "k"), E(a), E(b))))))


def tangente(f, x0):
    f, a = E(f), E(x0)
    m = sp.diff(f, X).subs(X, a)
    y = m * (X - a) + f.subs(X, a)
    return (f"f({L(a)}) = {V(f.subs(X, a))}\nf'({L(a)}) = {V(m)}\n{tx('Tangente')} : y = {L(sp.expand(y))}",
            [f, y], (float(a) - 5, float(a) + 5))


T("Analyse", "Tangente en un point", "f(x)=x^2-2x+3|x0=2", tangente)


def critiques(f):
    f, out = E(f), []
    for s in sp.solve(sp.diff(f, X), X):
        if not s.is_real:
            continue
        d = sp.diff(f, X, 2).subs(X, s)
        nat = tx("minimum local") if d > 0 else tx("maximum local") if d < 0 else tx("à étudier")
        out.append(f"x = {V(s)}  →  f = {V(f.subs(X, s))}  ({nat})")
    return "\n".join(out) or tx("Aucun point critique réel"), [f]


T("Analyse", "Points critiques", "f(x)=x^3-3x", critiques)
T("Analyse", "Tracer des fonctions", "f (séparées par ;)=sin(x); cos(x)|x min=-10|x max=10",
  lambda f, a, b: (tx("Courbes tracées."), [E(k) for k in f.split(";")], (float(a), float(b))))


def edo(t):
    y = sp.Function("y")
    t = t.replace("y''", "Derivative(y(x),(x,2))").replace("y'", "Derivative(y(x),x)")
    t = re.sub(r"\by\b(?!\()", "y(x)", t)
    g, _, d = t.partition("=")
    return P(sp.dsolve(sp.Eq(E(g, {"y": y}), E(d or "0", {"y": y}))))


T("Analyse", "Équation différentielle", "Équation (y', y'')=y'' + y = 0", edo)

# ---------- Vectoriel ----------
T("Vectoriel", "Gradient", "f=x^2*y+z^3|Variables=x,y,z", lambda f, v: EQ(NOM("∇f"), sp.Matrix([sp.diff(E(f), k) for k in VS(v)])))
T("Vectoriel", "Hessienne", "f=x^2*y+sin(y)|Variables=x,y", lambda f, v: EQ(NOM("H(f)"), sp.hessian(E(f), VS(v))))
T("Vectoriel", "Divergence", "F (P,Q,R)=x*y,y*z,z*x|Variables=x,y,z",
  lambda F, v: EQ(NOM("div F"), sp.simplify(sum(sp.diff(E(c), k) for c, k in zip(F.split(","), VS(v))))))


def rot(F, v):
    (p, q, r), (x, y, z) = [E(c) for c in F.split(",")], VS(v)
    return EQ(NOM("rot F"), sp.Matrix([sp.diff(r, y) - sp.diff(q, z), sp.diff(p, z) - sp.diff(r, x),
                                       sp.diff(q, x) - sp.diff(p, y)]))


T("Vectoriel", "Rotationnel", "F (P,Q,R)=y*z,x*z,x*y|Variables=x,y,z", rot)

# ---------- Matrices ----------
T("Matrices", "Déterminant", "Matrice=1,2;3,4", lambda m: EQ(NOM("det(M)"), Mat(m).det()))
T("Matrices", "Inverse", "Matrice=1,2;3,4", lambda m: EQ(NOM("M⁻¹"), Mat(m).inv()))
T("Matrices", "Valeurs propres", "Matrice=2,1;1,2",
  lambda m: "\n".join(f"λ = {V(k)}   ({tx('multiplicité')} {n})" for k, n in Mat(m).eigenvals().items()))
T("Matrices", "Vecteurs propres", "Matrice=2,1;1,2",
  lambda m: "\n".join(f"λ = {V(k)}  →  ({', '.join(map(L, v))})" for k, _, vs in Mat(m).eigenvects() for v in vs))
T("Matrices", "Rang", "Matrice=1,2;2,4", lambda m: str(Mat(m).rank()))
T("Matrices", "Produit de matrices", "A=1,2;3,4|B=0,1;1,0", lambda a, b: EQ(NOM("A·B"), Mat(a) * Mat(b)))
T("Matrices", "Système Ax = b", "A=2,1;1,3|b=5,10",
  lambda a, b: P(sp.linsolve((Mat(a), Vec(b)), *sp.symbols(f"x1:{Mat(a).cols + 1}"))))
T("Matrices", "Produit scalaire", "u=1,2,3|v=4,5,6", lambda u, v: EQ(NOM("u · v"), Vec(u).dot(Vec(v))))
T("Matrices", "Produit vectoriel", "u=1,0,0|v=0,1,0", lambda u, v: EQ(NOM("u × v"), Vec(u).cross(Vec(v))))

# ---------- Nombres ----------
T("Nombres", "Facteurs premiers", "n=360360",
  lambda n: " × ".join(f"{p}" + (f"^{k}" if k > 1 else "") for p, k in sp.factorint(entier(n)).items()))
T("Nombres", "PGCD / PPCM", "Nombres (séparés par ,)=12,18,30",
  lambda s: (f"{tx('PGCD')} = {math.gcd(*map(int, s.split(',')))}\n"
             f"{tx('PPCM')} = {math.lcm(*map(int, s.split(',')))}"))


def premier(n):
    n = entier(n)
    return (tx("{} est premier") if sp.isprime(n) else tx("{} est composé")).format(n) \
        + "\n" + tx("Premier suivant : {}").format(sp.nextprime(n))


T("Nombres", "Nombre premier ?", "n=1000003", premier)
T("Nombres", "Inverse modulaire", "a=7|Modulo=26",
  lambda a, m: f"{a}^-1 ≡ {pow(entier(a), -1, entier(m))}  (mod {m})")
T("Nombres", "Combinatoire", "n=10|k=3",
  lambda n, k: f"n! = {math.factorial(int(n))}\nC(n,k) = {math.comb(int(n), int(k))}\nA(n,k) = {math.perm(int(n), int(k))}")
T("Nombres", "Changement de base", "Nombre=255|Base de départ=10|Base d'arrivée=2",
  lambda n, a, b: base(int(n, int(a)), int(b)))


def diviseurs(n):
    d = sp.divisors(entier(n))
    return tx("{} diviseurs, somme = {}").format(len(d), sum(d)) + "\n" + ", ".join(map(str, d))


T("Nombres", "Diviseurs", "n=360", diviseurs)


# ---------- Complexes ----------
def polaire(z):
    z = sp.expand_complex(E(z))
    m, a = sp.simplify(sp.Abs(z)), sp.simplify(sp.arg(z))
    return (f"z = {L(z)}\nRe = {V(sp.re(z))}    Im = {V(sp.im(z))}\n{tx('Conjugué')} = {L(sp.conjugate(z))}\n"
            f"|z| = {V(m)}\narg(z) = {V(a)} rad  ({A(a * 180 / sp.pi)}°)\n"
            f"{tx('Forme exponentielle')} : {L(m)}·e^({L(a)}·{REGL['imag']})")


T("Complexes", "Module, argument, forme polaire", "z=(1+2i)/(3-i)", polaire)


def racines(z, n):
    z, n = E(z), int(n)
    m, a = sp.Abs(z), sp.arg(z)
    return "\n".join(f"z{k} = {A(m**sp.Rational(1, n) * sp.exp(sp.I * (a + 2*sp.pi*k) / n))}" for k in range(n))


T("Complexes", "Racines n-ièmes", "z=1+i|n=4", racines)


# ---------- Statistiques ----------
def descr(d):
    a, nan = nums(d), float("nan")
    n, (q1, q3) = len(a), np.percentile(a, [25, 75])
    v = {"n": n, tx("Somme"): a.sum(), tx("Moyenne"): a.mean(), tx("Médiane"): np.median(a),
         tx("Variance (pop.)"): a.var(), tx("Variance (éch.)"): a.var(ddof=1) if n > 1 else nan,
         tx("Écart-type (pop.)"): a.std(), tx("Écart-type (éch.)"): a.std(ddof=1) if n > 1 else nan,
         tx("Min"): a.min(), tx("Max"): a.max(), "Q1": q1, "Q3": q3}
    larg = max(len(k) for k in v) + 2
    return "\n".join(f"{k:<{larg}}{num(w)}" for k, w in v.items())


T("Statistiques", "Statistiques descriptives", "Données=12,15,9,20,18,14,11", descr)


def regression(x, y):
    x, y = nums(x), nums(y)
    a, b = np.polyfit(x, y, 1)
    r = np.corrcoef(x, y)[0, 1]
    return f"y = {num(a)}·x + {num(b)}\nr = {num(r)}\nr² = {num(r * r)}"


T("Statistiques", "Régression linéaire", "x=1,2,3,4,5|y=2.1,3.9,6.2,7.8,10.1", regression)


def binom(n, p, k):
    n, k, p = int(n), int(k), float(p)
    f = lambda j: math.comb(n, j) * p**j * (1 - p)**(n - j)
    return (f"P(X = {k}) = {num(f(k))}\nP(X ≤ {k}) = {num(sum(f(j) for j in range(k + 1)))}\n"
            f"E(X) = {num(n*p)}\nV(X) = {num(n*p*(1-p))}")


T("Statistiques", "Loi binomiale", "n=10|p=0.3|k=4", binom)


def normale(m, s, a, b):
    m, s, a, b = map(float, (m, s, a, b))
    F = lambda t: 0.5 * (1 + math.erf((t - m) / (s * math.sqrt(2))))
    return f"P({a} < X < {b}) = {num(F(b) - F(a))}\nP(X < {b}) = {num(F(b))}\nP(X > {a}) = {num(1 - F(a))}"


T("Statistiques", "Loi normale", "Moyenne μ=0|Écart-type σ=1|a=-1.96|b=1.96", normale)


def poisson(l, k):
    l, k = float(l), int(k)
    f = lambda j: math.exp(-l) * l**j / math.factorial(j)
    return f"P(X = {k}) = {num(f(k))}\nP(X ≤ {k}) = {num(sum(f(j) for j in range(k + 1)))}"


T("Statistiques", "Loi de Poisson", "λ=3|k=2", poisson)

# ---------- Utilitaires ----------
T("Utilitaires", "Valeur numérique", "Expression=pi*sqrt(2)+exp(1)|Chiffres=30",
  lambda e, d: str(sp.N(E(e), int(d))).replace("I", REGL["imag"]))
T("Utilitaires", "Degrés ↔ radians", "Valeur=180|Unité (deg ou rad)=deg",
  lambda v, u: (tx("→ radians") if u.strip() == "deg" else tx("→ degrés")) + "\n"
               + R(E(v) * (sp.pi / 180 if u.strip() == "deg" else 180 / sp.pi)))

# ======================= TEXTES : TRADUCTIONS =======================
# clé française -> (anglais, russe)
TXT = {
    # catégories
    "Algèbre": ("Algebra", "Алгебра"), "Analyse": ("Calculus", "Анализ"),
    "Vectoriel": ("Vector calculus", "Векторный анализ"), "Matrices": ("Matrices", "Матрицы"),
    "Nombres": ("Number theory", "Теория чисел"), "Complexes": ("Complex numbers", "Комплексные числа"),
    "Statistiques": ("Statistics", "Статистика"), "Utilitaires": ("Utilities", "Утилиты"),
    # outils
    "Simplifier": ("Simplify", "Упростить"), "Développer": ("Expand", "Раскрыть скобки"),
    "Factoriser": ("Factor", "Разложить на множители"),
    "Résoudre une équation": ("Solve an equation", "Решить уравнение"),
    "Système d'équations": ("System of equations", "Система уравнений"),
    "Inéquation": ("Inequality", "Неравенство"),
    "Trinôme du 2nd degré": ("Quadratic trinomial", "Квадратный трёхчлен"),
    "Fractions partielles": ("Partial fractions", "Простые дроби"),
    "Substituer une valeur": ("Substitute a value", "Подставить значение"),
    "Division de polynômes": ("Polynomial division", "Деление многочленов"),
    "Dérivée": ("Derivative", "Производная"), "Dérivée partielle": ("Partial derivative", "Частная производная"),
    "Primitive": ("Antiderivative", "Первообразная"),
    "Intégrale définie": ("Definite integral", "Определённый интеграл"),
    "Intégrale double": ("Double integral", "Двойной интеграл"), "Limite": ("Limit", "Предел"),
    "Série de Taylor": ("Taylor series", "Ряд Тейлора"), "Somme": ("Sum", "Сумма"),
    "Tangente en un point": ("Tangent at a point", "Касательная в точке"),
    "Points critiques": ("Critical points", "Критические точки"),
    "Tracer des fonctions": ("Plot functions", "Построить графики"),
    "Équation différentielle": ("Differential equation", "Дифференциальное уравнение"),
    "Gradient": ("Gradient", "Градиент"), "Hessienne": ("Hessian", "Гессиан"),
    "Divergence": ("Divergence", "Дивергенция"), "Rotationnel": ("Curl", "Ротор"),
    "Déterminant": ("Determinant", "Определитель"), "Inverse": ("Inverse", "Обратная матрица"),
    "Valeurs propres": ("Eigenvalues", "Собственные значения"),
    "Vecteurs propres": ("Eigenvectors", "Собственные векторы"), "Rang": ("Rank", "Ранг"),
    "Produit de matrices": ("Matrix product", "Произведение матриц"),
    "Système Ax = b": ("System Ax = b", "Система Ax = b"),
    "Produit scalaire": ("Dot product", "Скалярное произведение"),
    "Produit vectoriel": ("Cross product", "Векторное произведение"),
    "Facteurs premiers": ("Prime factors", "Простые множители"),
    "PGCD / PPCM": ("GCD / LCM", "НОД / НОК"),
    "Nombre premier ?": ("Is it prime?", "Простое ли число?"),
    "Inverse modulaire": ("Modular inverse", "Обратный по модулю"),
    "Combinatoire": ("Combinatorics", "Комбинаторика"),
    "Changement de base": ("Base conversion", "Смена системы счисления"),
    "Diviseurs": ("Divisors", "Делители"),
    "Module, argument, forme polaire": ("Modulus, argument, polar form", "Модуль, аргумент, полярная форма"),
    "Racines n-ièmes": ("n-th roots", "Корни n-й степени"),
    "Statistiques descriptives": ("Descriptive statistics", "Описательная статистика"),
    "Régression linéaire": ("Linear regression", "Линейная регрессия"),
    "Loi binomiale": ("Binomial distribution", "Биномиальное распределение"),
    "Loi normale": ("Normal distribution", "Нормальное распределение"),
    "Loi de Poisson": ("Poisson distribution", "Распределение Пуассона"),
    "Valeur numérique": ("Numerical value", "Численное значение"),
    "Degrés ↔ radians": ("Degrees ↔ radians", "Градусы ↔ радианы"),
    # champs
    "Expression": ("Expression", "Выражение"), "Équation": ("Equation", "Уравнение"),
    "Inconnue": ("Unknown", "Неизвестная"), "Inconnues": ("Unknowns", "Неизвестные"),
    "Équations (séparées par ;)": ("Equations (separated by ;)", "Уравнения (через ;)"),
    "Variable": ("Variable", "Переменная"), "Variables": ("Variables", "Переменные"),
    "Valeur": ("Value", "Значение"), "Dividende": ("Dividend", "Делимое"), "Diviseur": ("Divisor", "Делитель"),
    "Ordre": ("Order", "Порядок"), "De": ("From", "От"), "À": ("To", "До"),
    "x de": ("x from", "x от"), "x à": ("x to", "x до"), "y de": ("y from", "y от"), "y à": ("y to", "y до"),
    "x min": ("x min", "x мин"), "x max": ("x max", "x макс"),
    "Tend vers": ("Tends to", "Стремится к"),
    "Côté (+, - ou +-)": ("Side (+, - or +-)", "Сторона (+, - или +-)"),
    "En x0": ("At x0", "В точке x0"), "Terme": ("Term", "Слагаемое"), "Indice": ("Index", "Индекс"),
    "f (séparées par ;)": ("f (separated by ;)", "f (через ;)"),
    "Équation (y', y'')": ("Equation (y', y'')", "Уравнение (y', y'')"),
    "Matrice": ("Matrix", "Матрица"),
    "Nombres (séparés par ,)": ("Numbers (separated by ,)", "Числа (через ,)"),
    "Modulo": ("Modulo", "Модуль"), "Nombre": ("Number", "Число"),
    "Base de départ": ("Source base", "Исходная система"), "Base d'arrivée": ("Target base", "Целевая система"),
    "Données": ("Data", "Данные"), "Moyenne μ": ("Mean μ", "Среднее μ"),
    "Écart-type σ": ("Std. deviation σ", "Стандартное отклонение σ"),
    "Chiffres": ("Digits", "Знаки"), "Unité (deg ou rad)": ("Unit (deg or rad)", "Единица (deg или rad)"),
    # résultats
    "Aucune solution": ("No solution", "Нет решений"),
    "SymPy n'a pas trouvé de résultat exact": ("SymPy found no exact result", "SymPy не нашёл точный результат"),
    "Sommet": ("Vertex", "Вершина"), "Forme canonique": ("Canonical form", "Каноническая форма"),
    "Quotient": ("Quotient", "Частное"), "Reste": ("Remainder", "Остаток"), "Tangente": ("Tangent", "Касательная"),
    "minimum local": ("local minimum", "локальный минимум"), "maximum local": ("local maximum", "локальный максимум"),
    "à étudier": ("to investigate", "требует исследования"),
    "Aucun point critique réel": ("No real critical point", "Нет вещественных критических точек"),
    "Courbes tracées.": ("Curves plotted.", "Графики построены."),
    "multiplicité": ("multiplicity", "кратность"), "PGCD": ("GCD", "НОД"), "PPCM": ("LCM", "НОК"),
    "{} est premier": ("{} is prime", "{} — простое число"),
    "{} est composé": ("{} is composite", "{} — составное число"),
    "Premier suivant : {}": ("Next prime: {}", "Следующее простое: {}"),
    "{} diviseurs, somme = {}": ("{} divisors, sum = {}", "{} делителей, сумма = {}"),
    "Conjugué": ("Conjugate", "Сопряжённое"), "Forme exponentielle": ("Exponential form", "Показательная форма"),
    "Moyenne": ("Mean", "Среднее"), "Médiane": ("Median", "Медиана"),
    "Variance (pop.)": ("Variance (pop.)", "Дисперсия (ген.)"),
    "Variance (éch.)": ("Variance (sample)", "Дисперсия (выб.)"),
    "Écart-type (pop.)": ("Std dev (pop.)", "Ст. откл. (ген.)"),
    "Écart-type (éch.)": ("Std dev (sample)", "Ст. откл. (выб.)"),
    "Min": ("Min", "Мин"), "Max": ("Max", "Макс"),
    "→ radians": ("→ radians", "→ радианы"), "→ degrés": ("→ degrees", "→ градусы"),
    # interface
    "🔍  Rechercher un outil...": ("🔍  Search a tool...", "🔍  Найти инструмент..."),
    "⚙  Réglages": ("⚙  Settings", "⚙  Настройки"),
    "☀ / 🌙  Changer de thème": ("☀ / 🌙  Switch theme", "☀ / 🌙  Сменить тему"),
    "Calculer": ("Calculate", "Вычислить"),
    "Copier le résultat": ("Copy result", "Копировать результат"),
    "Copier le LaTeX": ("Copy LaTeX", "Копировать LaTeX"),
    "Appuie sur Calculer (ou Entrée).": ("Press Calculate (or Enter).", "Нажмите «Вычислить» (или Enter)."),
    "Réglages": ("Settings", "Настройки"), "Thème": ("Theme", "Тема"),
    "Unité imaginaire": ("Imaginary unit", "Мнимая единица"),
    "Couleur d'accent": ("Accent color", "Цвет акцента"), "Décimales": ("Decimals", "Знаков после запятой"),
    "Coins arrondis": ("Rounded corners", "Скругление углов"), "Taille du texte": ("Text size", "Размер текста"),
    "Afficher les valeurs approchées": ("Show approximate values", "Показывать приближённые значения"),
    "Langue": ("Language", "Язык"), "Appliquer": ("Apply", "Применить"),
    "Sombre": ("Dark", "Тёмная"), "Clair": ("Light", "Светлая"), "Système": ("System", "Системная"),
    "Bleu": ("Blue", "Синий"), "Violet": ("Purple", "Фиолетовый"), "Vert": ("Green", "Зелёный"),
    "Orange": ("Orange", "Оранжевый"), "Rose": ("Pink", "Розовый"), "Rouge": ("Red", "Красный"),
}

# ======================= INFOBULLES : TEXTES (fr, en, ru) =======================
AIDE_CAT = {
    "Algèbre": ("Calcul avec des lettres : simplifier, résoudre, factoriser…",
                "Working with letters: simplify, solve, factor…",
                "Работа с буквами: упрощение, решение, разложение…"),
    "Analyse": ("Dérivées, intégrales, limites, séries… l'étude des fonctions.",
                "Derivatives, integrals, limits, series… the study of functions.",
                "Производные, интегралы, пределы, ряды… изучение функций."),
    "Vectoriel": ("Outils pour les fonctions et champs à plusieurs variables (gradient, divergence…).",
                  "Tools for multi-variable functions and fields (gradient, divergence…).",
                  "Инструменты для функций и полей многих переменных (градиент, дивергенция…)."),
    "Matrices": ("Tableaux de nombres et vecteurs : déterminant, inverse, valeurs propres…",
                 "Tables of numbers and vectors: determinant, inverse, eigenvalues…",
                 "Таблицы чисел и векторы: определитель, обратная матрица, собственные значения…"),
    "Nombres": ("Entiers : premiers, diviseurs, PGCD, bases, combinatoire…",
                "Integers: primes, divisors, GCD, bases, combinatorics…",
                "Целые числа: простые, делители, НОД, системы счисления, комбинаторика…"),
    "Complexes": ("Nombres de la forme a + bi.", "Numbers of the form a + bi.", "Числа вида a + bi."),
    "Statistiques": ("Résumer des données et calculer des probabilités.",
                     "Summarize data and compute probabilities.",
                     "Обобщение данных и вычисление вероятностей."),
    "Utilitaires": ("Petits outils pratiques : valeur décimale, conversion d'angles…",
                    "Handy little tools: decimal value, angle conversion…",
                    "Небольшие полезные инструменты: десятичное значение, перевод углов…"),
}

AIDE_OUTIL = {
    "Simplifier": ("Réduit une expression à sa forme la plus courte. Ex : (x²-1)/(x-1) devient x+1.",
                   "Reduces an expression to its shortest form. E.g. (x²-1)/(x-1) becomes x+1.",
                   "Приводит выражение к самому короткому виду. Напр.: (x²-1)/(x-1) → x+1."),
    "Développer": ("Enlève les parenthèses en multipliant tout. Ex : (x+1)² devient x²+2x+1.",
                   "Removes parentheses by multiplying everything out. E.g. (x+1)² becomes x²+2x+1.",
                   "Раскрывает скобки, перемножая всё. Напр.: (x+1)² → x²+2x+1."),
    "Factoriser": ("Écrit une expression comme un produit de facteurs. Ex : x²-1 = (x-1)(x+1).",
                   "Writes an expression as a product of factors. E.g. x²-1 = (x-1)(x+1).",
                   "Записывает выражение в виде произведения множителей. Напр.: x²-1 = (x-1)(x+1)."),
    "Résoudre une équation": ("Trouve les valeurs de l'inconnue qui rendent l'équation vraie (même les complexes).",
                              "Finds the values of the unknown that make the equation true (complex ones too).",
                              "Находит значения неизвестной, при которых уравнение верно (включая комплексные)."),
    "Système d'équations": ("Trouve les valeurs qui vérifient plusieurs équations en même temps.",
                            "Finds the values that satisfy several equations at once.",
                            "Находит значения, удовлетворяющие сразу нескольким уравнениям."),
    "Inéquation": ("Trouve l'ensemble des x pour lesquels une inégalité (<, >, ≤, ≥) est vraie.",
                   "Finds all x for which an inequality (<, >, ≤, ≥) holds.",
                   "Находит все x, при которых неравенство (<, >, ≤, ≥) выполняется."),
    "Trinôme du 2nd degré": ("Étudie ax²+bx+c : discriminant Δ, racines, sommet de la parabole et forme canonique. Trace la courbe.",
                             "Studies ax²+bx+c: discriminant Δ, roots, parabola vertex and canonical form. Plots the curve.",
                             "Исследует ax²+bx+c: дискриминант Δ, корни, вершину параболы и каноническую форму. Строит график."),
    "Fractions partielles": ("Découpe une grosse fraction en une somme de fractions simples. Ex : 1/(x²-1).",
                             "Splits a big fraction into a sum of simple fractions. E.g. 1/(x²-1).",
                             "Разбивает сложную дробь на сумму простых дробей. Напр.: 1/(x²-1)."),
    "Substituer une valeur": ("Remplace une lettre par une valeur (ou une expression) et calcule.",
                              "Replaces a letter with a value (or expression) and computes.",
                              "Заменяет букву значением (или выражением) и вычисляет."),
    "Division de polynômes": ("Divise un polynôme par un autre : donne le quotient et le reste.",
                              "Divides one polynomial by another: gives the quotient and remainder.",
                              "Делит один многочлен на другой: даёт частное и остаток."),
    "Dérivée": ("Calcule la dérivée : la vitesse à laquelle la fonction change (pente de la courbe).",
                "Computes the derivative: how fast the function changes (slope of the curve).",
                "Вычисляет производную: скорость изменения функции (наклон кривой)."),
    "Dérivée partielle": ("Dérive une fonction de plusieurs variables par rapport à chacune d'elles, les autres restant fixes.",
                          "Differentiates a multi-variable function with respect to each variable, holding the others fixed.",
                          "Дифференцирует функцию нескольких переменных по каждой, считая остальные постоянными."),
    "Primitive": ("Trouve une fonction dont la dérivée est f (l'inverse de la dérivée). « + C » est une constante.",
                  "Finds a function whose derivative is f (the inverse of differentiation). '+ C' is a constant.",
                  "Находит функцию, производная которой равна f (обратная операция к производной). «+ C» — константа."),
    "Intégrale définie": ("Calcule l'aire (signée) sous la courbe entre deux bornes.",
                          "Computes the (signed) area under the curve between two bounds.",
                          "Вычисляет площадь (со знаком) под кривой между двумя границами."),
    "Intégrale double": ("Calcule le volume sous une surface f(x,y) au-dessus d'un rectangle.",
                         "Computes the volume under a surface f(x,y) over a rectangle.",
                         "Вычисляет объём под поверхностью f(x,y) над прямоугольником."),
    "Limite": ("Calcule la valeur dont s'approche f(x) quand x s'approche d'un point (ou de l'infini).",
               "Computes the value f(x) approaches as x approaches a point (or infinity).",
               "Вычисляет значение, к которому приближается f(x), когда x приближается к точке (или к бесконечности)."),
    "Série de Taylor": ("Approche une fonction par un polynôme autour d'un point. Plus l'ordre est grand, plus c'est précis.",
                        "Approximates a function by a polynomial around a point. Higher order means more accuracy.",
                        "Приближает функцию многочленом вокруг точки. Чем выше порядок, тем точнее."),
    "Somme": ("Additionne des termes pour un indice qui va d'un début à une fin (∑). « oo » = infini.",
              "Adds terms for an index running from a start to an end (∑). 'oo' = infinity.",
              "Складывает слагаемые для индекса от начала до конца (∑). «oo» — бесконечность."),
    "Tangente en un point": ("Donne la droite qui touche la courbe en un point, avec son graphique.",
                             "Gives the line touching the curve at a point, with a plot.",
                             "Находит прямую, касающуюся кривой в точке, и рисует график."),
    "Points critiques": ("Trouve où la pente est nulle : minimums et maximums locaux. Trace la courbe.",
                         "Finds where the slope is zero: local minima and maxima. Plots the curve.",
                         "Находит точки с нулевым наклоном: локальные минимумы и максимумы. Строит график."),
    "Tracer des fonctions": ("Dessine une ou plusieurs courbes sur un graphique.",
                             "Draws one or more curves on a graph.",
                             "Рисует одну или несколько кривых на графике."),
    "Équation différentielle": ("Trouve les fonctions y(x) qui vérifient une équation contenant y' ou y''.",
                                "Finds the functions y(x) that satisfy an equation containing y' or y''.",
                                "Находит функции y(x), удовлетворяющие уравнению с y' или y''."),
    "Gradient": ("Vecteur des dérivées partielles : il pointe dans la direction où la fonction monte le plus vite.",
                 "Vector of partial derivatives: points where the function increases fastest.",
                 "Вектор частных производных: указывает направление наибыстрейшего роста функции."),
    "Hessienne": ("Matrice des dérivées secondes : décrit la courbure d'une fonction de plusieurs variables.",
                  "Matrix of second derivatives: describes the curvature of a multi-variable function.",
                  "Матрица вторых производных: описывает кривизну функции нескольких переменных."),
    "Divergence": ("Mesure si un champ de vecteurs « sort » ou « entre » en un point (source ou puits).",
                   "Measures whether a vector field flows out of or into a point (source or sink).",
                   "Показывает, вытекает ли векторное поле из точки или втекает в неё (источник или сток)."),
    "Rotationnel": ("Mesure la tendance d'un champ de vecteurs à tourner autour d'un point.",
                    "Measures how much a vector field tends to swirl around a point.",
                    "Показывает, насколько векторное поле закручивается вокруг точки."),
    "Déterminant": ("Nombre associé à une matrice carrée. S'il vaut 0, la matrice n'est pas inversible.",
                    "A number tied to a square matrix. If it is 0, the matrix is not invertible.",
                    "Число, связанное с квадратной матрицей. Если оно равно 0, матрица необратима."),
    "Inverse": ("Calcule la matrice M⁻¹ telle que M × M⁻¹ = matrice identité.",
                "Computes the matrix M⁻¹ such that M × M⁻¹ = identity matrix.",
                "Вычисляет матрицу M⁻¹, для которой M × M⁻¹ = единичная матрица."),
    "Valeurs propres": ("Nombres λ pour lesquels la matrice ne fait qu'étirer un vecteur sans changer sa direction.",
                        "Numbers λ for which the matrix only stretches a vector without changing its direction.",
                        "Числа λ, при которых матрица лишь растягивает вектор, не меняя его направления."),
    "Vecteurs propres": ("Les vecteurs dont la direction ne change pas quand on applique la matrice.",
                         "The vectors whose direction doesn't change when the matrix is applied.",
                         "Векторы, направление которых не меняется при умножении на матрицу."),
    "Rang": ("Nombre de lignes (ou colonnes) vraiment indépendantes dans la matrice.",
             "Number of truly independent rows (or columns) in the matrix.",
             "Число по-настоящему независимых строк (или столбцов) матрицы."),
    "Produit de matrices": ("Multiplie deux matrices A × B (le nombre de colonnes de A doit égaler le nombre de lignes de B).",
                            "Multiplies two matrices A × B (columns of A must equal rows of B).",
                            "Перемножает матрицы A × B (число столбцов A должно равняться числу строк B)."),
    "Système Ax = b": ("Résout un système linéaire écrit sous forme matricielle.",
                       "Solves a linear system written in matrix form.",
                       "Решает линейную систему, записанную в матричной форме."),
    "Produit scalaire": ("Multiplie deux vecteurs pour obtenir un nombre. Vaut 0 si les vecteurs sont perpendiculaires.",
                         "Multiplies two vectors to get a number. It is 0 if the vectors are perpendicular.",
                         "Перемножает два вектора и даёт число. Равно 0, если векторы перпендикулярны."),
    "Produit vectoriel": ("Donne un vecteur perpendiculaire aux deux vecteurs (en 3D).",
                          "Gives a vector perpendicular to both vectors (in 3D).",
                          "Даёт вектор, перпендикулярный обоим векторам (в 3D)."),
    "Facteurs premiers": ("Décompose un entier en produit de nombres premiers. Ex : 12 = 2² × 3.",
                          "Breaks an integer into a product of primes. E.g. 12 = 2² × 3.",
                          "Раскладывает целое число на простые множители. Напр.: 12 = 2² × 3."),
    "PGCD / PPCM": ("Plus grand diviseur commun et plus petit multiple commun de plusieurs entiers.",
                    "Greatest common divisor and least common multiple of several integers.",
                    "Наибольший общий делитель и наименьшее общее кратное нескольких целых чисел."),
    "Nombre premier ?": ("Teste si un entier est premier (divisible seulement par 1 et lui-même) et donne le suivant.",
                         "Tests whether an integer is prime (divisible only by 1 and itself) and gives the next one.",
                         "Проверяет, простое ли число (делится только на 1 и на себя), и даёт следующее простое."),
    "Inverse modulaire": ("Trouve x tel que a × x ≡ 1 (mod m). Utile en cryptographie.",
                          "Finds x such that a × x ≡ 1 (mod m). Useful in cryptography.",
                          "Находит x, для которого a × x ≡ 1 (mod m). Полезно в криптографии."),
    "Combinatoire": ("Compte les possibilités : factorielle n!, combinaisons C(n,k) (sans ordre) et arrangements A(n,k) (avec ordre).",
                     "Counts possibilities: factorial n!, combinations C(n,k) (unordered) and permutations A(n,k) (ordered).",
                     "Считает варианты: факториал n!, сочетания C(n,k) (без порядка) и размещения A(n,k) (с порядком)."),
    "Changement de base": ("Convertit un nombre d'une base (2, 10, 16…) à une autre.",
                           "Converts a number from one base (2, 10, 16…) to another.",
                           "Переводит число из одной системы счисления (2, 10, 16…) в другую."),
    "Diviseurs": ("Liste tous les entiers qui divisent exactement le nombre.",
                  "Lists all integers that divide the number exactly.",
                  "Перечисляет все целые числа, на которые данное число делится без остатка."),
    "Module, argument, forme polaire": ("Décrit un nombre complexe par sa distance à l'origine (module) et son angle (argument).",
                                        "Describes a complex number by its distance from the origin (modulus) and its angle (argument).",
                                        "Описывает комплексное число расстоянием до начала координат (модуль) и углом (аргумент)."),
    "Racines n-ièmes": ("Trouve les n nombres complexes dont la puissance n vaut z.",
                        "Finds the n complex numbers whose n-th power equals z.",
                        "Находит n комплексных чисел, n-я степень которых равна z."),
    "Statistiques descriptives": ("Résume une série de données : moyenne, médiane, écart-type, quartiles, min, max…",
                                  "Summarizes a data set: mean, median, standard deviation, quartiles, min, max…",
                                  "Сводка по набору данных: среднее, медиана, стандартное отклонение, квартили, мин, макс…"),
    "Régression linéaire": ("Trouve la droite y = ax + b qui colle le mieux à des points, et la corrélation r.",
                            "Finds the line y = ax + b that best fits some points, and the correlation r.",
                            "Находит прямую y = ax + b, лучше всего подходящую к точкам, и корреляцию r."),
    "Loi binomiale": ("Probabilité d'avoir k succès en n essais indépendants, chacun de probabilité p.",
                      "Probability of getting k successes in n independent trials, each with probability p.",
                      "Вероятность k успехов в n независимых испытаниях с вероятностью p каждое."),
    "Loi normale": ("Probabilités pour la courbe en cloche de moyenne μ et d'écart-type σ.",
                    "Probabilities for the bell curve with mean μ and standard deviation σ.",
                    "Вероятности для колоколообразной кривой со средним μ и стандартным отклонением σ."),
    "Loi de Poisson": ("Probabilité d'avoir k événements rares quand la moyenne est λ sur une période donnée.",
                       "Probability of k rare events when the average is λ over a given period.",
                       "Вероятность k редких событий при среднем λ за заданный период."),
    "Valeur numérique": ("Calcule une valeur décimale avec autant de chiffres que voulu. Ex : π√2+e.",
                         "Computes a decimal value with as many digits as you want. E.g. π√2+e.",
                         "Вычисляет десятичное значение с нужным числом знаков. Напр.: π√2+e."),
    "Degrés ↔ radians": ("Convertit un angle entre degrés et radians (180° = π rad).",
                         "Converts an angle between degrees and radians (180° = π rad).",
                         "Переводит угол между градусами и радианами (180° = π рад)."),
}

# clé = "Libellé" ou "Outil|Libellé" (prioritaire)
AIDE_CHAMP = {
    "Expression": ("Formule mathématique. Ex : (x^2-1)/(x-1). Utilise ^ pour les puissances.",
                   "Mathematical formula. E.g. (x^2-1)/(x-1). Use ^ for powers.",
                   "Математическая формула. Напр.: (x^2-1)/(x-1). Степень — знак ^."),
    "Équation": ("Équation avec un signe =. Ex : x^2+2x+5=0 (sans =, on suppose « = 0 »).",
                 "Equation with an = sign. E.g. x^2+2x+5=0 (without =, '= 0' is assumed).",
                 "Уравнение со знаком =. Напр.: x^2+2x+5=0 (без = считается «= 0»)."),
    "Inconnue": ("La lettre à trouver (souvent x).", "The letter to solve for (usually x).",
                 "Буква, которую нужно найти (обычно x)."),
    "Équations (séparées par ;)": ("Plusieurs équations séparées par un point-virgule. Ex : x+y=3; x-y=1",
                                   "Several equations separated by semicolons. E.g. x+y=3; x-y=1",
                                   "Несколько уравнений через точку с запятой. Напр.: x+y=3; x-y=1"),
    "Inconnues": ("Les lettres à trouver, séparées par des virgules. Ex : x,y",
                  "The letters to solve for, separated by commas. E.g. x,y",
                  "Буквы, которые нужно найти, через запятую. Напр.: x,y"),
    "Inéquation": ("Une inégalité avec <, <=, > ou >=. Ex : x^2-3x+2<=0",
                   "An inequality using <, <=, > or >=. E.g. x^2-3x+2<=0",
                   "Неравенство со знаком <, <=, > или >=. Напр.: x^2-3x+2<=0"),
    "Variable": ("La lettre par rapport à laquelle on calcule (souvent x).",
                 "The letter with respect to which we compute (usually x).",
                 "Буква, по которой ведётся вычисление (обычно x)."),
    "Variables": ("Liste de lettres séparées par des virgules. Ex : x,y,z",
                  "List of letters separated by commas. E.g. x,y,z",
                  "Список букв через запятую. Напр.: x,y,z"),
    "Valeur": ("La valeur à utiliser (un nombre ou une expression).",
               "The value to use (a number or an expression).",
               "Используемое значение (число или выражение)."),
    "Degrés ↔ radians|Valeur": ("Le nombre à convertir. Ex : 180 ou pi",
                                "The number to convert. E.g. 180 or pi",
                                "Число для перевода. Напр.: 180 или pi"),
    "Dividende": ("Le polynôme que l'on divise. Ex : x^3+2x+1",
                  "The polynomial being divided. E.g. x^3+2x+1",
                  "Делимый многочлен. Напр.: x^3+2x+1"),
    "Diviseur": ("Le polynôme par lequel on divise. Ex : x+1",
                 "The polynomial you divide by. E.g. x+1",
                 "Многочлен, на который делим. Напр.: x+1"),
    "f": ("La fonction à étudier. Ex : x^3*sin(x)", "The function to study. E.g. x^3*sin(x)",
          "Исследуемая функция. Напр.: x^3*sin(x)"),
    "f(x)": ("Une fonction de x. Ex : x^2-2x+3", "A function of x. E.g. x^2-2x+3",
             "Функция от x. Напр.: x^2-2x+3"),
    "f(x,y)": ("Une fonction de x et y. Ex : x*y", "A function of x and y. E.g. x*y",
               "Функция от x и y. Напр.: x*y"),
    "f (séparées par ;)": ("Une ou plusieurs fonctions séparées par ;. Ex : sin(x); cos(x)",
                           "One or more functions separated by ;. E.g. sin(x); cos(x)",
                           "Одна или несколько функций через ;. Напр.: sin(x); cos(x)"),
    "Ordre": ("Nombre de fois que l'on dérive (1 = dérivée première).",
              "How many times we differentiate (1 = first derivative).",
              "Сколько раз дифференцируем (1 = первая производная)."),
    "Série de Taylor|Ordre": ("Degré maximal du polynôme obtenu.", "Maximum degree of the resulting polynomial.",
                              "Максимальная степень получаемого многочлена."),
    "De": ("Borne de départ. Ex : 0", "Starting bound. E.g. 0", "Нижняя граница. Напр.: 0"),
    "À": ("Borne de fin. Ex : pi, ou oo pour l'infini.", "Ending bound. E.g. pi, or oo for infinity.",
          "Верхняя граница. Напр.: pi, или oo для бесконечности."),
    "x de": ("Début de l'intervalle en x.", "Start of the x interval.", "Начало интервала по x."),
    "x à": ("Fin de l'intervalle en x.", "End of the x interval.", "Конец интервала по x."),
    "y de": ("Début de l'intervalle en y.", "Start of the y interval.", "Начало интервала по y."),
    "y à": ("Fin de l'intervalle en y.", "End of the y interval.", "Конец интервала по y."),
    "Tend vers": ("La valeur dont x s'approche. Ex : 0, 1, oo (infini).",
                  "The value x gets close to. E.g. 0, 1, oo (infinity).",
                  "Значение, к которому стремится x. Напр.: 0, 1, oo (бесконечность)."),
    "Côté (+, - ou +-)": ("+ : par la droite, - : par la gauche, +- : des deux côtés.",
                          "+ : from the right, - : from the left, +- : from both sides.",
                          "+ : справа, - : слева, +- : с обеих сторон."),
    "En x0": ("Point autour duquel on développe. Ex : 0", "Point around which we expand. E.g. 0",
              "Точка, вокруг которой раскладываем. Напр.: 0"),
    "Terme": ("Le terme général de la somme. Ex : 1/k^2", "The general term of the sum. E.g. 1/k^2",
              "Общий член суммы. Напр.: 1/k^2"),
    "Indice": ("La lettre qui parcourt les valeurs (souvent k ou n).",
               "The letter that runs through the values (often k or n).",
               "Буква, пробегающая значения (обычно k или n)."),
    "x0": ("Abscisse du point où l'on veut la tangente. Ex : 2",
           "x-coordinate of the point where you want the tangent. E.g. 2",
           "Абсцисса точки, в которой нужна касательная. Напр.: 2"),
    "x min": ("Début de l'axe des x du graphique.", "Left end of the graph's x axis.", "Левый край оси x графика."),
    "x max": ("Fin de l'axe des x du graphique.", "Right end of the graph's x axis.", "Правый край оси x графика."),
    "Équation (y', y'')": ("Équation différentielle. Ex : y'' + y = 0 (y' = dérivée première, y'' = seconde).",
                           "Differential equation. E.g. y'' + y = 0 (y' = first derivative, y'' = second).",
                           "Дифференциальное уравнение. Напр.: y'' + y = 0 (y' — первая производная, y'' — вторая)."),
    "F (P,Q,R)": ("Les 3 composantes du champ de vecteurs, séparées par des virgules. Ex : x*y,y*z,z*x",
                  "The 3 components of the vector field, separated by commas. E.g. x*y,y*z,z*x",
                  "Три компоненты векторного поля через запятую. Напр.: x*y,y*z,z*x"),
    "Matrice": ("Lignes séparées par ;, valeurs séparées par des virgules. Ex : 1,2;3,4",
                "Rows separated by ;, values separated by commas. E.g. 1,2;3,4",
                "Строки через ;, значения через запятую. Напр.: 1,2;3,4"),
    "A": ("Première matrice (lignes séparées par ;). Ex : 1,2;3,4",
          "First matrix (rows separated by ;). E.g. 1,2;3,4",
          "Первая матрица (строки через ;). Напр.: 1,2;3,4"),
    "Système Ax = b|A": ("Matrice des coefficients du système. Ex : 2,1;1,3",
                         "Coefficient matrix of the system. E.g. 2,1;1,3",
                         "Матрица коэффициентов системы. Напр.: 2,1;1,3"),
    "B": ("Deuxième matrice (lignes séparées par ;). Ex : 0,1;1,0",
          "Second matrix (rows separated by ;). E.g. 0,1;1,0",
          "Вторая матрица (строки через ;). Напр.: 0,1;1,0"),
    "a": ("Un nombre.", "A number.", "Число."),
    "b": ("Un nombre.", "A number.", "Число."),
    "c": ("Terme constant du trinôme (sans x).", "Constant term of the trinomial (no x).",
          "Свободный член трёхчлена (без x)."),
    "Trinôme du 2nd degré|a": ("Coefficient de x² (ne doit pas être 0).", "Coefficient of x² (must not be 0).",
                               "Коэффициент при x² (не должен быть 0)."),
    "Trinôme du 2nd degré|b": ("Coefficient de x.", "Coefficient of x.", "Коэффициент при x."),
    "Système Ax = b|b": ("Vecteur des seconds membres, séparés par des virgules. Ex : 5,10",
                         "Right-hand side vector, separated by commas. E.g. 5,10",
                         "Вектор правых частей через запятую. Напр.: 5,10"),
    "Inverse modulaire|a": ("Le nombre dont on cherche l'inverse. Ex : 7",
                            "The number whose inverse we look for. E.g. 7",
                            "Число, для которого ищем обратное. Напр.: 7"),
    "Loi normale|a": ("Borne inférieure de l'intervalle.", "Lower bound of the interval.",
                      "Нижняя граница интервала."),
    "Loi normale|b": ("Borne supérieure de l'intervalle.", "Upper bound of the interval.",
                      "Верхняя граница интервала."),
    "u": ("Vecteur : composantes séparées par des virgules. Ex : 1,2,3",
          "Vector: components separated by commas. E.g. 1,2,3",
          "Вектор: компоненты через запятую. Напр.: 1,2,3"),
    "v": ("Vecteur : composantes séparées par des virgules. Ex : 4,5,6",
          "Vector: components separated by commas. E.g. 4,5,6",
          "Вектор: компоненты через запятую. Напр.: 4,5,6"),
    "n": ("Un nombre entier.", "An integer.", "Целое число."),
    "Facteurs premiers|n": ("L'entier à décomposer. Ex : 360360", "The integer to break down. E.g. 360360",
                            "Целое число для разложения. Напр.: 360360"),
    "Nombre premier ?|n": ("L'entier à tester.", "The integer to test.", "Целое число для проверки."),
    "Combinatoire|n": ("Nombre total d'éléments.", "Total number of elements.", "Общее число элементов."),
    "Loi binomiale|n": ("Nombre d'essais.", "Number of trials.", "Число испытаний."),
    "Racines n-ièmes|n": ("Combien de racines on veut (l'ordre n).", "How many roots you want (the order n).",
                          "Сколько корней нужно (степень n)."),
    "Diviseurs|n": ("L'entier dont on liste les diviseurs.", "The integer whose divisors are listed.",
                    "Целое число, делители которого перечисляются."),
    "k": ("Un nombre entier.", "An integer.", "Целое число."),
    "Combinatoire|k": ("Nombre d'éléments choisis parmi n.", "Number of elements chosen among n.",
                       "Сколько элементов выбираем из n."),
    "Loi binomiale|k": ("Nombre de succès voulu.", "Wanted number of successes.", "Нужное число успехов."),
    "Loi de Poisson|k": ("Nombre d'événements voulu.", "Wanted number of events.", "Нужное число событий."),
    "Nombres (séparés par ,)": ("Des entiers séparés par des virgules. Ex : 12,18,30",
                                "Integers separated by commas. E.g. 12,18,30",
                                "Целые числа через запятую. Напр.: 12,18,30"),
    "Modulo": ("Le modulo. Ex : 26", "The modulus. E.g. 26", "Модуль. Напр.: 26"),
    "Nombre": ("Le nombre à convertir, écrit dans la base de départ.",
               "The number to convert, written in the source base.",
               "Число для перевода, записанное в исходной системе."),
    "Base de départ": ("Base du nombre saisi (2 à 36). Ex : 10", "Base of the entered number (2 to 36). E.g. 10",
                       "Система счисления введённого числа (от 2 до 36). Напр.: 10"),
    "Base d'arrivée": ("Base dans laquelle on veut le résultat (2 à 36). Ex : 2",
                       "Base in which you want the result (2 to 36). E.g. 2",
                       "Система счисления результата (от 2 до 36). Напр.: 2"),
    "z": ("Un nombre complexe. Ex : (1+2i)/(3-i). Utilise i pour l'imaginaire.",
          "A complex number. E.g. (1+2i)/(3-i). Use i for the imaginary unit.",
          "Комплексное число. Напр.: (1+2i)/(3-i). Мнимая единица — i."),
    "Données": ("Liste de nombres séparés par des virgules. Ex : 12,15,9,20",
                "List of numbers separated by commas. E.g. 12,15,9,20",
                "Список чисел через запятую. Напр.: 12,15,9,20"),
    "x": ("Valeurs de x (abscisses), séparées par des virgules.",
          "x values (abscissas), separated by commas.", "Значения x через запятую."),
    "y": ("Valeurs de y (ordonnées), autant que de x.", "y values (ordinates), as many as x.",
          "Значения y через запятую, столько же, сколько x."),
    "p": ("Probabilité de succès d'un essai, entre 0 et 1.", "Success probability of one trial, between 0 and 1.",
          "Вероятность успеха в одном испытании, от 0 до 1."),
    "Moyenne μ": ("Le centre de la cloche (valeur moyenne).", "The centre of the bell curve (average value).",
                  "Центр колокола (среднее значение)."),
    "Écart-type σ": ("La largeur de la cloche (doit être > 0).", "The width of the bell curve (must be > 0).",
                     "Ширина колокола (должна быть > 0)."),
    "λ": ("Nombre moyen d'événements sur la période.", "Average number of events over the period.",
          "Среднее число событий за период."),
    "Chiffres": ("Nombre de chiffres significatifs à afficher.", "Number of significant digits to show.",
                 "Число выводимых значащих цифр."),
    "Unité (deg ou rad)": ("deg : convertit de degrés en radians ; rad : de radians en degrés.",
                           "deg: converts degrees to radians; rad: converts radians to degrees.",
                           "deg: градусы → радианы; rad: радианы → градусы."),
}

AIDE_UI = {
    "recherche": ("Tape un mot pour filtrer la liste des outils (nom ou catégorie).",
                  "Type a word to filter the tools (name or category).",
                  "Введите слово, чтобы отфильтровать инструменты (по названию или категории)."),
    "reglages": ("Ouvre la fenêtre des réglages (thème, couleurs, décimales, langue…).",
                 "Opens the settings window (theme, colors, decimals, language…).",
                 "Открывает окно настроек (тема, цвета, знаки после запятой, язык…)."),
    "theme_btn": ("Passe du thème sombre au thème clair, et inversement.",
                  "Switches between the dark and light theme.",
                  "Переключает между тёмной и светлой темой."),
    "langue_btn": ("Change la langue de l'application.", "Changes the application language.",
                   "Меняет язык приложения."),
    "calculer": ("Lance le calcul avec les valeurs saisies (raccourci : Entrée).",
                 "Runs the calculation with the entered values (shortcut: Enter).",
                 "Запускает вычисление с введёнными значениями (быстрая клавиша: Enter)."),
    "copier": ("Copie le résultat affiché dans le presse-papiers.",
               "Copies the displayed result to the clipboard.",
               "Копирует показанный результат в буфер обмена."),
    "copier_tex": ("Copie le code LaTeX de la formule affichée (à coller dans un document LaTeX).",
                   "Copies the LaTeX code of the displayed formula (to paste into a LaTeX document).",
                   "Копирует LaTeX-код показанной формулы (для вставки в документ LaTeX)."),
    "resultat": ("Ici s'affiche le résultat du calcul.", "The result of the calculation is shown here.",
                 "Здесь показывается результат вычисления."),
    "theme": ("Sombre, clair, ou selon ton système.", "Dark, light, or following your system.",
              "Тёмная, светлая или как в вашей системе."),
    "imag": ("Lettre utilisée pour afficher le nombre imaginaire (i ou j).",
             "Letter used to display the imaginary number (i or j).",
             "Буква для отображения мнимой единицы (i или j)."),
    "accent": ("Couleur des boutons et des éléments mis en avant.",
               "Color of the buttons and highlighted items.",
               "Цвет кнопок и выделенных элементов."),
    "decimales": ("Nombre de chiffres après la virgule pour les valeurs approchées.",
                  "Number of digits after the decimal point for approximate values.",
                  "Число знаков после запятой для приближённых значений."),
    "rayon": ("Arrondi des coins des boutons, cartes et champs.",
              "Roundness of the corners of buttons, cards and fields.",
              "Скругление углов кнопок, карточек и полей."),
    "police": ("Taille du texte dans les champs et les résultats.",
               "Text size in the fields and results.",
               "Размер текста в полях и результатах."),
    "approx": ("Affiche « ≈ valeur décimale » à côté des résultats exacts.",
               "Shows '≈ decimal value' next to exact results.",
               "Показывает «≈ десятичное значение» рядом с точными результатами."),
    "langue": ("Langue de l'interface : Français, English ou Русский.",
               "Interface language: Français, English or Русский.",
               "Язык интерфейса: Français, English или Русский."),
    "appliquer": ("Enregistre et applique tous les réglages.", "Saves and applies all settings.",
                  "Сохраняет и применяет все настройки."),
}


def aide_outil(nom): return pick(AIDE_OUTIL.get(nom))
def aide_cat(cat): return pick(AIDE_CAT.get(cat))
def ui(k): return pick(AIDE_UI.get(k))
def aide_champ(outil, label): return pick(AIDE_CHAMP.get(f"{outil}|{label}") or AIDE_CHAMP.get(label))


# ======================= MENU / DAILY : TEXTES =======================
VERSION = "v2.3-4"
TXT.update({
    "⚙  Paramètres": ("⚙  Settings", "⚙  Параметры"), "⌂  Menu principal": ("⌂  Main menu", "⌂  Главное меню"),
    "←  Menu principal": ("←  Main menu", "←  Главное меню"),
    "Problème du jour": ("Daily problem", "Задача дня"), "Problème aléatoire": ("Random problem", "Случайная задача"),
    "Intégrale": ("Integral", "Интеграл"), "Série": ("Series", "Ряд"),
    "🎲  Nouveau problème": ("🎲  New problem", "🎲  Новая задача"),
    "Ta réponse :": ("Your answer:", "Ваш ответ:"), "Vérifier": ("Check", "Проверить"),
    "Voir la solution": ("Show solution", "Показать решение"),
    "✓ Bravo !": ("✓ Well done!", "✓ Отлично!"),
    "✗ Pas tout à fait, réessaie.": ("✗ Not quite, try again.", "✗ Не совсем, попробуйте ещё."),
    "Calcule la valeur exacte": ("Compute the exact value", "Найдите точное значение"),
    "Donne f'(x)": ("Give f'(x)", "Найдите f'(x)"),
    "Donne toutes les solutions (séparées par des virgules)":
        ("Give all solutions (comma-separated)", "Найдите все решения (через запятую)"),
    "Calcule la somme": ("Compute the sum", "Найдите сумму"),
    "Dessin": ("Drawing", "Рисунок"), "Calculatrice": ("Calculator", "Калькулятор"),
    "Stylo": ("Pen", "Ручка"), "Gomme": ("Eraser", "Ластик"), "Texte": ("Text", "Текст"),
    "↶ Annuler": ("↶ Undo", "↶ Отменить"), "🗑 Effacer": ("🗑 Clear", "🗑 Очистить"),
    "💾 Enregistrer": ("💾 Save", "💾 Сохранить"), "Texte à écrire :": ("Text to write:", "Текст:"),
    "Épaisseur": ("Thickness", "Толщина"),
    "Noir & blanc": ("Black & white", "Чёрно-белая"),
    "Fer": ("Iron", "Железо"), "Argent": ("Silver", "Серебро"), "Or": ("Gold", "Золото"),
    "Platine": ("Platinum", "Платина"), "Diamant": ("Diamond", "Алмаз"), "Maître": ("Master", "Мастер"),
    "Légende": ("Legend", "Легенда"), "Bronze": ("Bronze", "Бронза"),
    "Victoires": ("Wins", "Победы"), "Défaites": ("Losses", "Поражения"),
    "Série en cours": ("Current streak", "Текущая серия"), "Meilleur ELO": ("Best ELO", "Лучший ELO"),
    "Historique": ("History", "История"), "Rangs": ("Ranks", "Ранги"),
    "Réinitialiser": ("Reset", "Сбросить"), "Confirmer ?": ("Confirm?", "Подтвердить?"),
    "Solution consultée": ("Solution viewed", "Решение просмотрено"), "déjà classé": ("already ranked", "уже засчитано"),
    "Prochain rang": ("Next rank", "Следующий ранг"), "Rang maximum atteint !": ("Max rank reached!", "Максимальный ранг!"),
    "pts": ("pts", "очк."),
})
AIDE_UI.update({
    "theme_btn": ("Change de thème : sombre, noir & blanc, puis clair.", "Cycles the theme: dark, black & white, then light.",
                  "Переключает тему: тёмная, чёрно-белая, светлая."),
    "theme": ("Sombre, noir & blanc (noir pur), clair, ou selon ton système.",
              "Dark, black & white (pure black), light, or following your system.",
              "Тёмная, чёрно-белая (чисто чёрная), светлая или как в вашей системе."),
    "menu_btn": ("Revient au menu principal.", "Goes back to the main menu.", "Возврат в главное меню."),
    "menu_tools": ("Tous les outils de calcul : algèbre, analyse, matrices, statistiques…",
                   "All the calculation tools: algebra, calculus, matrices, statistics…",
                   "Все инструменты: алгебра, анализ, матрицы, статистика…"),
    "menu_daily": ("Un problème par jour (intégrale, limite, dérivée…), un cahier de dessin et une calculatrice scientifique.",
                   "One problem a day (integral, limit, derivative…), a drawing pad and a scientific calculator.",
                   "Задача дня (интеграл, предел, производная…), доска для рисования и научный калькулятор."),
    "params": ("Ouvre les paramètres (thème, couleurs, décimales, langue…).",
               "Opens the settings (theme, colors, decimals, language…).",
               "Открывает настройки (тема, цвета, знаки после запятой, язык…)."),
})


# ======================= DAILY : PROBLÈMES =======================
def _t(x):
    return sp.latex(x, fold_func_brackets=True, mul_symbol=r"\,", inv_trig_style="full")


def _num_sol(sol):
    ap = A(sol) if approchable(sp.sympify(sol)) else ""
    return r"= " + _t(sol) + (r" \approx " + ap if ap else ""), "= " + V(sol)


def p_integrale(r):
    a, b = r.randint(1, 3), r.randint(1, 4)
    f, lo, hi = r.choice([
        (X**r.randint(1, 2) * sp.exp(X), 0, 1), (X * sp.sin(X), 0, sp.pi),
        (sp.sin(a * X) * sp.cos(a * X), 0, sp.pi / (2 * a)), (X / (X**2 + b), 0, a),
        (1 / (X**2 + a**2), 0, a), (X * sp.log(X), 1, sp.E), (1 / (X * (X + a)), 1, 2),
        (sp.sqrt(X) * (X + a), 0, b**2)])
    sol = sp.simplify(sp.integrate(f, (X, lo, hi)))
    st, sx = _num_sol(sol)
    return dict(tex=rf"\int_{{{_t(lo)}}}^{{{_t(hi)}}} {_t(f)}\,dx", txt=f"∫[{L(lo)} → {L(hi)}] {L(f)} dx",
                sol_tex=st, sol_txt=sx, sol=sol, mode="num", consigne="Calcule la valeur exacte",
                diff=1050 + 25 * sp.count_ops(f))


def p_limite(r):
    a, b = r.randint(2, 5), r.randint(2, 5)
    f, p = r.choice([
        (sp.sin(a * X) / (b * X), 0), ((1 + a / X)**X, sp.oo), ((X**2 - a**2) / (X - a), a),
        ((sp.exp(a * X) - 1) / (b * X), 0), ((1 - sp.cos(a * X)) / X**2, 0),
        (sp.sqrt(X**2 + a * X) - X, sp.oo), (sp.log(1 + a * X) / X, 0), ((X**3 - 1) / (X**2 - 1), 1)])
    sol = sp.simplify(sp.limit(f, X, p))
    g = rf"\left({_t(f)}\right)" if f.is_Add else _t(f)
    st, sx = _num_sol(sol)
    return dict(tex=rf"\lim_{{x \to {_t(p)}}} {g}", txt=f"lim(x→{L(p)}) {L(f)}", sol_tex=st, sol_txt=sx,
                sol=sol, mode="num", consigne="Calcule la valeur exacte", diff=1000 + 25 * sp.count_ops(f))


def p_derivee(r):
    a, b = r.randint(2, 4), r.randint(1, 5)
    f = r.choice([X**a * sp.sin(a * X), sp.log(X**2 + b), sp.exp(a * X) * sp.cos(X), sp.sqrt(X**2 + b),
                  X / (X**2 + b), sp.atan(a * X), X * sp.exp(X**2), sp.sin(X) / X, X * sp.log(X)])
    sol = sp.simplify(sp.diff(f, X))
    return dict(tex=rf"\frac{{d}}{{dx}}\left[{_t(f)}\right]", txt=f"d/dx [{L(f)}]",
                sol_tex=r"f'(x) = " + _t(sol), sol_txt="f'(x) = " + L(sol), sol=sol, mode="fonc",
                consigne="Donne f'(x)", diff=800 + 30 * sp.count_ops(f))


def p_equation(r):
    k = r.choice(["quad", "cubic", "exp", "cplx"])
    if k == "quad":
        s = r.sample(range(-4, 5), 2); e = sp.expand((X - s[0]) * (X - s[1]))
    elif k == "cubic":
        s = r.sample(range(-3, 4), 3); e = sp.expand(sp.prod([X - q for q in s]))
    elif k == "exp":
        u = r.sample(range(1, 7), 2); e = sp.exp(2 * X) - sum(u) * sp.exp(X) + u[0] * u[1]
        s = [sp.log(q) for q in u]
    else:
        a, b = r.randint(1, 4), r.randint(1, 3)
        e = X**2 + 2 * a * X + a**2 + b**2; s = [-a + b * sp.I, -a - b * sp.I]
    s = list(s)
    return dict(tex=_t(e) + " = 0", txt=L(e) + " = 0",
                sol_tex=r",\ ".join(rf"x_{{{i + 1}}} = {_t(q)}" for i, q in enumerate(s)),
                sol_txt="\n".join(f"x{i + 1} = {V(q)}" for i, q in enumerate(s)), sol=s, mode="liste",
                consigne="Donne toutes les solutions (séparées par des virgules)",
                diff={"quad": 800, "cubic": 1100, "exp": 1200, "cplx": 1000}[k])


def p_serie(r):
    a, b = r.randint(1, 3), r.randint(2, 4)
    k = sp.Symbol("k")
    t, lo, sol = r.choice([
        (1 / (k * (k + a)), 1, sp.harmonic(a) / a), (a / sp.Integer(b)**k, 0, sp.Rational(a * b, b - 1)),
        (k / sp.Integer(b)**k, 1, sp.Rational(b, (b - 1)**2)), (sp.Integer(a)**k / sp.factorial(k), 0, sp.exp(a)),
        (1 / k**2, 1, sp.pi**2 / 6)])
    st, sx = _num_sol(sol)
    return dict(tex=rf"\sum_{{k={lo}}}^{{\infty}} {_t(t)}", txt=f"Σ(k={lo}→∞) {L(t)}", sol_tex=st,
                sol_txt=sx, sol=sol, mode="num", consigne="Calcule la somme",
                diff=1250 + 25 * sp.count_ops(t))


PROBLEMES = [p_integrale, p_limite, p_derivee, p_equation, p_serie]


def juger(pr, rep):
    """True si la réponse de l'utilisateur est équivalente à la solution (test numérique)."""
    sol, mode = pr["sol"], pr["mode"]
    if mode == "liste":
        cle = lambda z: (round(z.real, 6), round(z.imag, 6))
        v = sorted((complex(sp.N(E(k))) for k in rep.split(",")), key=cle)
        s = sorted((complex(sp.N(k)) for k in sol), key=cle)
        return len(v) == len(s) and all(abs(a - b) < 1e-6 for a, b in zip(v, s))
    v = E(rep)
    if mode == "fonc":
        return all(abs(complex(sp.N((v - sol).subs(X, t)))) < 1e-6 for t in (0.37, 1.21, 2.05))
    return abs(complex(sp.N(v - sol))) < 1e-6


# ======================= DAILY : ELO / RANGS =======================
RANGS = [("Fer", 0, "#8b8ca0"), ("Bronze", 800, "#cd7f32"), ("Argent", 1000, "#c0c7d1"), ("Or", 1200, "#f5c542"),
         ("Platine", 1400, "#35d0c0"), ("Diamant", 1600, "#5aa9ff"), ("Maître", 1800, "#c06bff"),
         ("Légende", 2000, "#ff5470")]
ELO0 = 900


def elo_data():
    """Données de classement (sauvegardées dans reglages.json)."""
    d = REGL.setdefault("elo", {})
    for k, v in dict(elo=ELO0, best=ELO0, win=0, lose=0, streak=0, bstreak=0, hist=[], faits=[]).items():
        d.setdefault(k, v)
    return d


def rang(elo):
    """(rang actuel, rang suivant ou None) pour un ELO donné."""
    i = max(k for k, r in enumerate(RANGS) if elo >= r[1])
    return RANGS[i], (RANGS[i + 1] if i + 1 < len(RANGS) else None)


def elo_maj(diff, ok, nom):
    """Formule ELO classique (K = 32) : le problème a une difficulté 'diff' qui joue le rôle de l'adversaire."""
    d = elo_data()
    attendu = 1 / (1 + 10 ** ((diff - d["elo"]) / 400))
    delta = round(32 * ((1 if ok else 0) - attendu))
    delta = max(1, delta) if ok else min(-1, delta)
    d["elo"] = max(0, d["elo"] + delta)
    d["best"] = max(d["best"], d["elo"])
    d["win" if ok else "lose"] += 1
    d["streak"] = d["streak"] + 1 if ok else 0
    d["bstreak"] = max(d["bstreak"], d["streak"])
    d["hist"] = (d["hist"] + [[datetime.date.today().strftime("%d/%m"), nom, delta, d["elo"]]])[-30:]
    sauver()
    return delta


# ======================= DAILY : CALCULATRICE =======================
def calcul_sci(s, deg, ans):
    for a, b in (("÷", "/"), ("×", "*"), ("−", "-"), ("π", "pi"), ("√", "sqrt")):
        s = s.replace(a, b)
    k = sp.pi / 180
    d = dict(LOC, Ans=ans, ln=sp.log, abs=sp.Abs, log=lambda a: sp.log(a, 10))
    if deg:
        d.update(sin=lambda a: sp.sin(a * k), cos=lambda a: sp.cos(a * k), tan=lambda a: sp.tan(a * k),
                 asin=lambda a: sp.asin(a) / k, acos=lambda a: sp.acos(a) / k, atan=lambda a: sp.atan(a) / k)
    return parse_expr(s, transformations=TR, local_dict=d)


# ======================= INFOBULLE =======================
class Bulle:
    """Petite infobulle : apparaît quand la souris reste 1 s sur le widget."""

    def __init__(self, widget, texte, p, accent, delai=1000):
        self.w, self.texte, self.p, self.ac, self.delai = widget, texte, p, accent, delai
        self.job = self.fen = None
        # un CTkSegmentedButton contient plusieurs boutons : on les équipe tous
        for c in [widget] + list(getattr(widget, "_buttons_dict", {}).values()):
            for seq, fn in (("<Enter>", self.prevoir), ("<Leave>", self.cacher), ("<ButtonPress>", self.cacher)):
                try:
                    c.bind(seq, fn, add="+")
                except Exception:
                    pass

    def prevoir(self, _=None):
        self.cacher()
        try:
            self.job = self.w.after(self.delai, self.montrer)
        except Exception:
            self.job = None

    def montrer(self):
        self.job = None
        try:
            x, y = self.w.winfo_pointerxy()
            f = self.fen = tk.Toplevel(self.w)
            f.wm_overrideredirect(True)
            f.attributes("-topmost", True)
            tk.Label(f, text=self.texte, bg=self.p["card"], fg=self.p["fg"], justify="left", wraplength=320,
                     font=(police_ui(), 10), padx=10, pady=6, highlightthickness=1,
                     highlightbackground=self.ac, highlightcolor=self.ac).pack()
            f.update_idletasks()
            x = max(0, min(x + 14, f.winfo_screenwidth() - f.winfo_reqwidth() - 8))
            y = max(0, min(y + 18, f.winfo_screenheight() - f.winfo_reqheight() - 8))
            f.geometry(f"+{x}+{y}")
        except Exception:
            self.fen = None

    def cacher(self, _=None):
        try:
            if self.job is not None:
                self.w.after_cancel(self.job)
        except Exception:
            pass
        self.job = None
        if self.fen is not None:
            try:
                self.fen.destroy()
            except Exception:
                pass
            self.fen = None


# ======================= INTERFACE =======================
_POLICES = {}


def _famille(cle, choix, defaut):
    """First installed font of the list (cached). Windows fonts first, then macOS, then common Linux ones."""
    if cle not in _POLICES:
        fams = set(tkfont.families())
        _POLICES[cle] = next((f for f in choix if f in fams), defaut)
    return _POLICES[cle]


def police_ui():
    return _famille("ui", ("Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans", "Ubuntu", "Cantarell",
                           "DejaVu Sans", "Liberation Sans", "Arial"), "Helvetica")


def mono():
    return _famille("mono", ("Cascadia Code", "Consolas", "Menlo", "DejaVu Sans Mono", "Liberation Mono",
                             "Ubuntu Mono", "Noto Sans Mono", "Fira Code", "JetBrains Mono"), "Courier")


class Base(ctk.CTkFrame):
    """Écran de base : palette, infobulles, thème, langue et fenêtre de réglages (partagés par tous les écrans)."""

    def __init__(self, app):
        super().__init__(app, fg_color="transparent")
        self.app = app

    def style(self):
        self.p = appliquer_theme()
        self.ac, self.onac, self.sel = accent()
        self.r = REGL["rayon"]
        self.mono = ctk.CTkFont(family=mono(), size=REGL["police"])
        self.configure(fg_color=self.p["bg"])

    def tip(self, widget, texte):
        """Ajoute une infobulle (après 1 s de survol) à un widget."""
        if texte:
            Bulle(widget, texte, self.p, self.ac)

    def basculer(self):
        cycle = ["dark", "noir", "light"]
        cur = REGL["theme"] if REGL["theme"] in cycle else ("light" if ctk.get_appearance_mode() == "Light" else "dark")
        REGL["theme"] = cycle[(cycle.index(cur) + 1) % 3]
        sauver()
        self.app.after(20, self.app.rebuild)

    def changer_langue(self, code):
        if code == REGL["langue"]:
            return
        REGL["langue"] = code
        sauver()
        if self.app.fen is not None and self.app.fen.winfo_exists():
            self.app.fen.destroy()   # la fenêtre de réglages serait restée dans l'ancienne langue
        self.app.fen = None
        self.app.after(20, self.app.rebuild)

    def reglages(self):
        if self.app.fen is not None and self.app.fen.winfo_exists():
            self.app.fen.focus()
            return
        f = self.app.fen = ctk.CTkToplevel(self)
        f.title(tx("Réglages"))
        f.geometry("580x600")
        f.configure(fg_color=self.p["bg"])
        f.transient(self.winfo_toplevel())

        def ligne(i, nom, w, aide):
            lab = ctk.CTkLabel(f, text=nom)
            lab.grid(row=i, column=0, padx=20, pady=12, sticky="w")
            w.grid(row=i, column=1, padx=20, pady=12, sticky="e")
            self.tip(lab, aide)
            self.tip(w, aide)

        def curseur(i, nom, a, b, val, aide):
            lab = ctk.CTkLabel(f, text=f"{nom} : {val}")
            lab.grid(row=i, column=0, padx=20, pady=12, sticky="w")
            s = ctk.CTkSlider(f, from_=a, to=b, number_of_steps=b - a, width=170,
                              command=lambda x: lab.configure(text=f"{nom} : {int(x)}"))
            s.set(val)
            s.grid(row=i, column=1, padx=20, pady=12, sticky="e")
            self.tip(lab, aide)
            self.tip(s, aide)
            return s

        noms = {"dark": tx("Sombre"), "noir": tx("Noir & blanc"), "light": tx("Clair"), "system": tx("Système")}
        seg = dict(selected_color=self.sel, selected_hover_color=self.sel, unselected_color=self.p["card"],
                   unselected_hover_color=self.p["line"], text_color=self.p["fg"])
        th = ctk.CTkSegmentedButton(f, values=list(noms.values()), **seg)
        th.set(noms[REGL["theme"]])
        ligne(0, tx("Thème"), th, ui("theme"))
        im = ctk.CTkSegmentedButton(f, values=["i", "j"], **seg)
        im.set(REGL["imag"])
        ligne(1, tx("Unité imaginaire"), im, ui("imag"))
        ac = ctk.CTkOptionMenu(f, values=[tx(k) for k in ACCENTS])
        ac.set(tx(REGL["accent"]))
        ligne(2, tx("Couleur d'accent"), ac, ui("accent"))
        dec = curseur(3, tx("Décimales"), 0, 15, REGL["decimales"], ui("decimales"))
        ray = curseur(4, tx("Coins arrondis"), 0, 30, REGL["rayon"], ui("rayon"))
        pol = curseur(5, tx("Taille du texte"), 11, 22, REGL["police"], ui("police"))
        ap = ctk.CTkSwitch(f, text="")
        ap.select() if REGL["approx"] else ap.deselect()
        ligne(6, tx("Afficher les valeurs approchées"), ap, ui("approx"))
        lg = ctk.CTkOptionMenu(f, values=list(LANGS.values()))
        lg.set(LANGS[REGL["langue"]])
        ligne(7, tx("Langue"), lg, ui("langue"))

        def appliquer():
            inv = {v: k for k, v in noms.items()}
            inv_ac = {tx(k): k for k in ACCENTS}
            inv_lg = {v: k for k, v in LANGS.items()}
            ancienne = REGL["langue"]
            REGL.update(theme=inv[th.get()], imag=im.get(), accent=inv_ac[ac.get()], decimales=int(dec.get()),
                        rayon=int(ray.get()), police=int(pol.get()), approx=bool(ap.get()),
                        langue=inv_lg[lg.get()])
            sauver()
            if REGL["langue"] != ancienne:
                f.destroy()
                self.app.fen = None
            self.app.after(20, self.app.rebuild)

        b = ctk.CTkButton(f, text=tx("Appliquer"), command=appliquer)
        b.grid(row=8, column=0, columnspan=2, pady=24)
        self.tip(b, ui("appliquer"))
        f.after(200, lambda: f.winfo_exists() and (f.lift(), f.focus()))


class Outils(Base):
    """Écran Tools : tous les outils de calcul (ancien contenu de l'application)."""

    def __init__(self, app):
        super().__init__(app)
        self.actuel, self.entrees = app.outil or TOOLS[0], []
        self.build()

    def build(self):
        for w in self.winfo_children():
            if not isinstance(w, ctk.CTkToplevel):
                w.destroy()
        self.p = appliquer_theme()
        self.ac, self.onac, self.sel = accent()
        self.r = REGL["rayon"]
        self.mono = ctk.CTkFont(family=mono(), size=REGL["police"])
        self.configure(fg_color=self.p["bg"])
        self.cartes, self.carte_actuelle = {}, None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.sidebar()
        self.principal()
        self.choisir(self.actuel)

    def sidebar(self):
        p = self.p
        s = ctk.CTkFrame(self, width=290, corner_radius=0, fg_color=p["card"])
        s.grid(row=0, column=0, sticky="nsew")
        s.grid_propagate(False)
        s.grid_columnconfigure(0, weight=1)
        s.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(s, text="∑  Rainmath", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=p["fg"]).grid(row=0, column=0, padx=20, pady=(22, 10), sticky="w")
        self.recherche = ctk.StringVar()
        self.recherche.trace_add("write", lambda *_: self.lister())
        champ = ctk.CTkEntry(s, textvariable=self.recherche, placeholder_text=tx("🔍  Rechercher un outil..."),
                             height=36, corner_radius=self.r, fg_color=p["bg"], border_width=0,
                             text_color=p["fg"])
        champ.grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")
        self.tip(champ, ui("recherche"))
        self.liste = ctk.CTkScrollableFrame(s, fg_color="transparent")
        self.liste.grid(row=2, column=0, sticky="nsew", padx=4)
        self.items, self.entetes = {}, {}
        for t in TOOLS:
            if t["cat"] not in self.entetes:
                h = tk.Label(self.liste, text=tx(t["cat"]).upper(), bg=p["card"], fg=self.ac,
                             font=(police_ui(), 9, "bold"), anchor="w")
                self.tip(h, aide_cat(t["cat"]))
                self.entetes[t["cat"]] = h
            n = t["nom"]
            lab = tk.Label(self.liste, text=tx(n), bg=p["card"], fg=p["fg"], font=(police_ui(), 11),
                           anchor="w", padx=12, pady=6, cursor="hand2")
            lab.bind("<Button-1>", lambda e, t=t: self.choisir(t))
            lab.bind("<Enter>", lambda e, n=n, l=lab: l.configure(bg=self.ac if n == self.actuel["nom"] else p["line"]))
            lab.bind("<Leave>", lambda e, n=n, l=lab: l.configure(bg=self.ac if n == self.actuel["nom"] else p["card"]))
            self.tip(lab, aide_outil(n))
            self.items[n] = lab
        bas = ctk.CTkFrame(s, fg_color="transparent")
        bas.grid(row=3, column=0, sticky="ew", padx=14, pady=14)
        lg = ctk.CTkSegmentedButton(bas, values=["FR", "EN", "RU"], command=lambda v: self.changer_langue(v.lower()),
                                    selected_color=self.sel, selected_hover_color=self.sel, unselected_color=p["bg"],
                                    unselected_hover_color=p["line"], text_color=p["fg"])
        lg.set(REGL["langue"].upper())
        lg.pack(fill="x", pady=3)
        self.tip(lg, ui("langue_btn"))
        for txt, cmd, k in (("⌂  Menu principal", lambda: self.app.ecran("menu"), "menu_btn"),
                            ("⚙  Réglages", self.reglages, "reglages"),
                            ("☀ / 🌙  Changer de thème", self.basculer, "theme_btn")):
            b = ctk.CTkButton(bas, text=tx(txt), height=34, corner_radius=self.r, fg_color=p["bg"],
                              hover_color=p["line"], text_color=p["fg"], command=cmd)
            b.pack(fill="x", pady=3)
            self.tip(b, ui(k))
        self.lister()

    def lister(self):
        q, cat = self.recherche.get().lower(), None
        for w in self.liste.winfo_children():
            w.pack_forget()
        for t in TOOLS:
            if q and not any(q in s.lower() for s in (t["nom"], t["cat"], tx(t["nom"]), tx(t["cat"]))):
                continue
            if t["cat"] != cat:
                cat = t["cat"]
                self.entetes[cat].pack(fill="x", padx=10, pady=(12, 2))
            self.items[t["nom"]].pack(fill="x", padx=4, pady=1)

    def surligner(self):
        for nom, lab in self.items.items():
            actif = nom == self.actuel["nom"]
            lab.configure(bg=self.ac if actif else self.p["card"], fg=self.onac if actif else self.p["fg"])

    def principal(self):
        p, r = self.p, self.r + 4
        m = self.m = ctk.CTkFrame(self, fg_color="transparent")
        m.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        m.grid_columnconfigure(0, weight=1)
        m.grid_rowconfigure(3, weight=1)
        self.cat = ctk.CTkLabel(m, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.ac)
        self.cat.grid(row=0, column=0, sticky="w")
        self.titre = ctk.CTkLabel(m, text="", font=ctk.CTkFont(size=28, weight="bold"), text_color=p["fg"])
        self.titre.grid(row=1, column=0, sticky="w", pady=(0, 12))
        self.resultat = ctk.CTkTextbox(m, corner_radius=r, fg_color=p["card"], text_color=p["fg"],
                                       font=self.mono, wrap="none", height=170, border_width=0)
        self.resultat.grid(row=3, column=0, sticky="nsew", pady=14)
        self.tip(self.resultat, ui("resultat"))
        # zone d'affichage des formules (image LaTeX défilable), à la place du texte quand c'est possible
        self.tframe = ctk.CTkFrame(m, corner_radius=r, fg_color=p["card"])
        self.tframe.grid(row=3, column=0, sticky="nsew", pady=14)
        self.tframe.grid_rowconfigure(0, weight=1)
        self.tframe.grid_columnconfigure(0, weight=1)
        self.tcanvas = tk.Canvas(self.tframe, bg=p["card"], highlightthickness=0, height=170, width=100)
        self.tcanvas.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        sy = ctk.CTkScrollbar(self.tframe, orientation="vertical", command=self.tcanvas.yview)
        sx = ctk.CTkScrollbar(self.tframe, orientation="horizontal", command=self.tcanvas.xview)
        sy.grid(row=0, column=1, sticky="ns", pady=8)
        sx.grid(row=1, column=0, sticky="ew", padx=8)
        self.tcanvas.configure(xscrollcommand=sx.set, yscrollcommand=sy.set)
        for seq, d in (("<MouseWheel>", None), ("<Button-4>", -1), ("<Button-5>", 1)):
            self.tcanvas.bind(seq, lambda e, d=d: self.tcanvas.yview_scroll(
                d if d else (-1 if e.delta > 0 else 1), "units"))
        self.tip(self.tcanvas, ui("resultat"))
        self.tframe.grid_remove()
        self.tex_courant, self.img = None, None
        self.gframe = ctk.CTkFrame(m, corner_radius=r, fg_color=p["card"])
        self.gframe.grid(row=4, column=0, sticky="nsew")
        fig = Figure(figsize=(6, 3.2), facecolor=p["card"])
        self.ax = fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(fig, master=self.gframe)
        w = self.canvas.get_tk_widget()
        w.configure(bg=p["card"])
        w.pack(fill="both", expand=True, padx=8, pady=8)
        self.montrer_graphe(False)

    def montrer_graphe(self, oui):
        if oui:
            self.gframe.grid()
        else:
            self.gframe.grid_remove()
        self.m.grid_rowconfigure(4, weight=2 if oui else 0)

    def choisir(self, t):
        self.actuel = self.app.outil = t
        self.cat.configure(text=tx(t["cat"]).upper())
        self.titre.configure(text=tx(t["nom"]))
        if self.carte_actuelle is not None:
            self.carte_actuelle.grid_remove()
        if t["nom"] not in self.cartes:
            self.cartes[t["nom"]] = self.creer_carte(t)
        self.carte_actuelle, self.entrees = self.cartes[t["nom"]]
        self.carte_actuelle.grid()
        self.surligner()
        self.ecrire(tx("Appuie sur Calculer (ou Entrée)."))
        self.montrer_graphe(False)

    def creer_carte(self, t):
        p = self.p
        carte = ctk.CTkFrame(self.m, corner_radius=self.r + 4, fg_color=p["card"])
        carte.grid(row=2, column=0, sticky="ew")
        entrees = []
        for i, (nom, defaut) in enumerate(t["champs"]):
            cell = ctk.CTkFrame(carte, fg_color="transparent")
            cell.grid(row=i // 3, column=i % 3, padx=14, pady=10, sticky="w")
            lab = ctk.CTkLabel(cell, text=tx(nom), font=ctk.CTkFont(size=12), text_color=p["sub"])
            lab.pack(anchor="w")
            e = ctk.CTkEntry(cell, width=250, height=38, corner_radius=self.r, fg_color=p["bg"],
                             border_color=p["line"], text_color=p["fg"], font=self.mono)
            e.insert(0, defaut)
            e.pack()
            e.bind("<Return>", lambda _: self.calculer())
            aide = aide_champ(t["nom"], nom)
            self.tip(lab, aide)
            self.tip(e, aide)
            entrees.append(e)
        bt = ctk.CTkFrame(carte, fg_color="transparent")
        bt.grid(row=(len(t["champs"]) + 2) // 3, column=0, columnspan=3, sticky="w", padx=14, pady=(0, 14))
        b1 = ctk.CTkButton(bt, text=tx("Calculer"), width=150, height=38, corner_radius=self.r, fg_color=self.ac,
                           hover_color=self.ac, text_color=self.onac, command=self.calculer)
        b1.pack(side="left", padx=(0, 8))
        b2 = ctk.CTkButton(bt, text=tx("Copier le résultat"), width=200, height=38, corner_radius=self.r,
                           fg_color=p["bg"], hover_color=p["line"], text_color=p["fg"], command=self.copier)
        b2.pack(side="left")
        b3 = ctk.CTkButton(bt, text=tx("Copier le LaTeX"), width=170, height=38, corner_radius=self.r,
                           fg_color=p["bg"], hover_color=p["line"], text_color=p["fg"], command=self.copier_tex)
        b3.pack(side="left", padx=(8, 0))
        self.tip(b1, ui("calculer"))
        self.tip(b2, ui("copier"))
        self.tip(b3, ui("copier_tex"))
        return carte, entrees

    def calculer(self):
        try:
            r = self.actuel["f"](*[e.get() for e in self.entrees])
            plot = ()
            if isinstance(r, tuple):
                r, *plot = r
            self.ecrire(r if isinstance(r, str) else R(r))
            if plot:
                self.tracer(*plot)
            else:
                self.montrer_graphe(False)
        except Exception as err:
            self.ecrire(f"⚠  {type(err).__name__} : {err}")
            self.montrer_graphe(False)

    def tracer(self, exprs, xr=(-10, 10)):
        p, ax = self.p, self.ax
        ax.clear()
        ax.set_facecolor(p["card"])
        ax.tick_params(colors=p["sub"])
        for s in ax.spines.values():
            s.set_color(p["line"])
        ax.grid(True, color=p["line"], alpha=0.6)
        ax.axhline(0, color=p["sub"], lw=0.8)
        ax.axvline(0, color=p["sub"], lw=0.8)
        xs, tout = np.linspace(*xr, 1000), []
        for k, ex in enumerate(exprs):
            g = sp.lambdify(X, ex, "numpy")
            with np.errstate(all="ignore"):
                ys = np.array(g(xs) * np.ones_like(xs), dtype=float)
            ys[~np.isfinite(ys)] = np.nan
            tout.append(ys)
            noir = REGL["theme"] == "noir"
            ax.plot(xs, ys, color=(COURBES_NB if noir else COURBES)[k % 5], lw=2, label=L(ex),
                    linestyle=STYLES_NB[k % 4] if noir else "-")
        v = np.concatenate(tout)
        v = v[~np.isnan(v)]
        if len(v) > 1:
            lo, hi = np.percentile(v, [2, 98])
            m = (hi - lo) * 0.5 or 1
            ax.set_ylim(lo - m, hi + m)
        ax.set_xlim(*xr)
        ax.legend(facecolor=p["card"], edgecolor=p["line"], labelcolor=p["fg"])
        self.canvas.draw()
        self.montrer_graphe(True)

    def ecrire(self, t):
        self.resultat.configure(state="normal")
        self.resultat.delete("1.0", "end")
        self.resultat.insert("1.0", t)
        self.resultat.configure(state="disabled")
        # si le résultat a une version LaTeX, on l'affiche en "vraies" maths ; sinon on garde le texte
        self.tex_courant, vu = None, False
        if getattr(t, "parts", None):
            try:
                self.afficher_latex(t.parts)
                self.tex_courant, vu = t.tex, True
            except Exception:
                vu = False
        if vu:
            self.resultat.grid_remove()
            self.tframe.grid()
        else:
            self.tframe.grid_remove()
            self.resultat.grid()

    def afficher_latex(self, parts):
        data = png_latex(parts, self.p["fg"], self.p["card"], REGL["police"] * 1.5)
        self.img = tk.PhotoImage(data=base64.b64encode(data))   # garder une référence, sinon l'image disparaît
        c = self.tcanvas
        c.delete("all")
        c.create_image(6, 6, image=self.img, anchor="nw")
        c.configure(scrollregion=(0, 0, self.img.width() + 12, self.img.height() + 12))
        c.xview_moveto(0)
        c.yview_moveto(0)

    def copier(self):
        self.clipboard_clear()
        self.clipboard_append(self.resultat.get("1.0", "end").strip())

    def copier_tex(self):
        self.clipboard_clear()
        self.clipboard_append(self.tex_courant or self.resultat.get("1.0", "end").strip())


class Menu(Base):
    """Écran d'accueil : titre + ∑, boutons Tools / Daily, Paramètres en bas à droite, version en bas à gauche."""

    def __init__(self, app):
        super().__init__(app)
        self.style()
        p = self.p
        c = ctk.CTkFrame(self, fg_color="transparent")
        c.place(relx=0.5, rely=0.44, anchor="center")
        t = ctk.CTkFrame(c, fg_color="transparent")
        t.pack(pady=(0, 6))
        ctk.CTkLabel(t, text="Rainmath", font=ctk.CTkFont(size=58, weight="bold"),
                     text_color=p["fg"]).pack(side="left")
        ctk.CTkLabel(t, text="∑", font=ctk.CTkFont(size=88, weight="bold"),
                     text_color=self.ac).pack(side="left", padx=(16, 0))
        ctk.CTkFrame(c, height=3, width=330, fg_color=self.ac, corner_radius=2).pack(pady=(0, 40))
        for txt, cible, k in (("Tools", "outils", "menu_tools"), ("Daily  ·  beta", "daily", "menu_daily")):
            b = ctk.CTkButton(c, text=txt, width=380, height=72, corner_radius=self.r + 4,
                              font=ctk.CTkFont(size=26, weight="bold"),
                              fg_color=self.ac if cible == "outils" else p["card"],
                              hover_color=p["line"] if cible == "daily" else self.ac,
                              text_color=self.onac if cible == "outils" else p["fg"],
                              command=lambda c=cible: app.ecran(c))
            b.pack(pady=10)
            self.tip(b, ui(k))
        b = ctk.CTkButton(self, text=tx("⚙  Paramètres"), width=170, height=38, corner_radius=self.r,
                          fg_color=p["card"], hover_color=p["line"], text_color=p["fg"], command=self.reglages)
        b.place(relx=1, rely=1, x=-24, y=-24, anchor="se")
        self.tip(b, ui("params"))
        ctk.CTkLabel(self, text=VERSION, text_color=p["sub"], font=ctk.CTkFont(size=14)).place(
            relx=0, rely=1, x=24, y=-26, anchor="sw")


class Daily(Base):
    """Page Daily : problème du jour (généré localement avec SymPy, sans API), dessin, calculatrice."""
    TYPES = ["Intégrale", "Limite", "Dérivée", "Équation", "Série"]
    PEN = ("#111111", "#2563eb", "#dc2626", "#16a34a", "#f59e0b")

    def __init__(self, app):
        super().__init__(app)
        self.style()
        p = self.p
        self.cur, self.couleur, self.deg, self.ans = None, self.PEN[0], True, sp.Integer(0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 6))
        b = ctk.CTkButton(top, text=tx("←  Menu principal"), width=170, height=36, corner_radius=self.r,
                          fg_color=p["card"], hover_color=p["line"], text_color=p["fg"],
                          command=lambda: app.ecran("menu"))
        b.pack(side="left")
        self.tip(b, ui("menu_btn"))
        ctk.CTkLabel(top, text="Daily", font=ctk.CTkFont(size=28, weight="bold"),
                     text_color=p["fg"]).pack(side="left", padx=(18, 6))
        ctk.CTkLabel(top, text="BETA", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.ac).pack(side="left", pady=(10, 0))
        tabs = ctk.CTkTabview(self, corner_radius=self.r + 4, fg_color=p["card"], text_color=p["fg"],
                              segmented_button_selected_color=self.sel, segmented_button_selected_hover_color=self.sel,
                              segmented_button_unselected_color=p["bg"],
                              segmented_button_unselected_hover_color=p["line"])
        self.tabs = tabs
        tabs.grid(row=1, column=0, sticky="nsew", padx=24, pady=(4, 20))
        self.badge = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=16, weight="bold"))
        self.badge.pack(side="right", padx=6)
        noms = [tx("Problème du jour"), "✏  Paint", tx("Calculatrice"), "🏆  ELO"]
        for n in noms:
            tabs.add(n).grid_columnconfigure(0, weight=1)
        self.onglet_probleme(tabs.tab(noms[0]))
        self.onglet_paint(tabs.tab(noms[1]))
        self.onglet_calc(tabs.tab(noms[2]))
        self.onglet_elo(tabs.tab(noms[3]))
        self.maj_elo()

    def btn(self, parent, texte, cmd, w=140, accent=False):
        p = self.p
        return ctk.CTkButton(parent, text=texte, width=w, height=36, corner_radius=self.r, command=cmd,
                             fg_color=self.ac if accent else p["bg"], hover_color=self.ac if accent else p["line"],
                             text_color=self.onac if accent else p["fg"])

    def afficher(self, lab, tex, texte):
        """Affiche une formule LaTeX dans un tk.Label (sinon le texte brut)."""
        try:
            data = png_latex([tex], self.p["fg"], self.p["card"], REGL["police"] * 1.7)
            lab.img = tk.PhotoImage(data=base64.b64encode(data))
            lab.configure(image=lab.img, text="")
        except Exception:
            lab.img = None
            lab.configure(image="", text=texte)

    # ---------- onglet 1 : problème du jour ----------
    def onglet_probleme(self, t):
        p = self.p
        bar = ctk.CTkFrame(t, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        self.noms = [tx(k) for k in self.TYPES]
        self.seg = ctk.CTkSegmentedButton(bar, values=self.noms, command=lambda v: self.nouveau(False),
                                          selected_color=self.sel, selected_hover_color=self.sel,
                                          unselected_color=p["bg"], unselected_hover_color=p["line"],
                                          text_color=p["fg"])
        self.seg.set(self.noms[0])
        self.seg.pack(side="left")
        self.btn(bar, tx("🎲  Nouveau problème"), lambda: self.nouveau(True), 200).pack(side="right")
        self.info = ctk.CTkLabel(t, text="", text_color=p["sub"], anchor="w")
        self.info.grid(row=1, column=0, sticky="w", padx=14, pady=(6, 0))
        mf = tkfont.Font(family=mono(), size=14)
        self.enonce = tk.Label(t, bg=p["card"], fg=p["fg"], font=mf, justify="left")
        self.enonce.grid(row=2, column=0, pady=26)
        rep = ctk.CTkFrame(t, fg_color="transparent")
        rep.grid(row=3, column=0, sticky="ew", padx=10)
        ctk.CTkLabel(rep, text=tx("Ta réponse :"), text_color=p["sub"]).pack(side="left", padx=(4, 8))
        self.rep = ctk.CTkEntry(rep, width=320, height=38, corner_radius=self.r, fg_color=p["bg"],
                                border_color=p["line"], text_color=p["fg"], font=self.mono)
        self.rep.pack(side="left")
        self.rep.bind("<Return>", lambda _: self.verifier())
        self.btn(rep, tx("Vérifier"), self.verifier, 120, True).pack(side="left", padx=8)
        self.btn(rep, tx("Voir la solution"), self.voir, 170).pack(side="left")
        self.retour = ctk.CTkLabel(t, text="", font=ctk.CTkFont(size=15, weight="bold"), anchor="w")
        self.retour.grid(row=4, column=0, sticky="w", padx=14, pady=10)
        self.sol = tk.Label(t, bg=p["card"], fg=p["fg"], font=mf, justify="left")
        self.sol.grid(row=5, column=0, pady=6)
        self.nouveau(False)

    def nouveau(self, alea):
        idx = self.idx = self.noms.index(self.seg.get())
        graine = random.SystemRandom().randrange(10**9) if alea else datetime.date.today().toordinal() * 10 + idx
        self.prob = PROBLEMES[idx](random.Random(graine))
        self.cle = f"{idx}:{graine}"
        self.deja = self.cle in elo_data()["faits"]     # un problème ne compte qu'une fois pour l'ELO
        quand = tx("Problème aléatoire") if alea else f"{tx('Problème du jour')} — {datetime.date.today():%d/%m/%Y}"
        self.info.configure(text=f"{quand}   ·   {tx(self.prob['consigne'])}   ·   ELO {self.prob['diff']}"
                                 + (f"   ·   ✔ {tx('déjà classé')}" if self.deja else ""))
        self.afficher(self.enonce, self.prob["tex"], self.prob["txt"])
        self.sol.configure(image="", text="")
        self.retour.configure(text="")
        self.rep.delete(0, "end")

    def verifier(self):
        try:
            ok = juger(self.prob, self.rep.get())
            msg = self.noter(ok)
            self.retour.configure(text=(tx("✓ Bravo !") if ok else tx("✗ Pas tout à fait, réessaie.")) + msg,
                                  text_color="#22c55e" if ok else "#ef4444")
        except Exception as err:
            self.retour.configure(text=f"⚠  {err}", text_color="#f59e0b")

    def voir(self):
        self.afficher(self.sol, self.prob["sol_tex"], self.prob["sol_txt"])
        if not self.deja:       # regarder la solution avant de répondre = défaite
            self.retour.configure(text=tx("Solution consultée") + self.noter(False), text_color="#f59e0b")

    def noter(self, ok):
        """Met à jour l'ELO (une seule fois par problème) et renvoie le texte du gain/perte."""
        if self.deja:
            return ""
        self.deja = True
        d = elo_data()
        d["faits"] = (d["faits"] + [self.cle])[-500:]
        avant = rang(d["elo"])[0][0]
        delta = elo_maj(self.prob["diff"], ok, self.TYPES[self.idx])
        apres = rang(d["elo"])[0][0]
        self.maj_elo()
        return f"   {delta:+d} ELO" + (f"   {'⬆' if delta > 0 else '⬇'} {tx(apres)}" if apres != avant else "")

    # ---------- onglet 4 : ELO et rangs ----------
    def onglet_elo(self, t):
        p = self.p
        t.grid_columnconfigure((0, 1), weight=1)
        t.grid_rowconfigure(4, weight=1)
        self.e_rang = ctk.CTkLabel(t, text="", font=ctk.CTkFont(size=46, weight="bold"))
        self.e_rang.grid(row=0, column=0, columnspan=2, pady=(22, 0))
        self.e_pts = ctk.CTkLabel(t, text="", font=ctk.CTkFont(size=22), text_color=p["fg"])
        self.e_pts.grid(row=1, column=0, columnspan=2)
        self.e_bar = ctk.CTkProgressBar(t, width=520, height=14, fg_color=p["bg"])
        self.e_bar.grid(row=2, column=0, columnspan=2, pady=(12, 4))
        self.e_next = ctk.CTkLabel(t, text="", text_color=p["sub"])
        self.e_next.grid(row=3, column=0, columnspan=2, pady=(0, 10))
        g = ctk.CTkFrame(t, fg_color="transparent")
        g.grid(row=4, column=0, sticky="nsew", padx=(14, 7), pady=(0, 10))
        g.grid_rowconfigure(2, weight=1)
        g.grid_columnconfigure(0, weight=1)
        self.e_stats = ctk.CTkLabel(g, text="", justify="left", anchor="w", text_color=p["fg"], font=self.mono)
        self.e_stats.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(g, text=tx("Historique"), text_color=p["sub"], anchor="w").grid(row=1, column=0, sticky="w", pady=(10, 2))
        self.e_hist = ctk.CTkTextbox(g, corner_radius=self.r, fg_color=p["bg"], text_color=p["fg"], font=self.mono)
        self.e_hist.grid(row=2, column=0, sticky="nsew")
        h = ctk.CTkFrame(t, fg_color="transparent")
        h.grid(row=4, column=1, sticky="nsew", padx=(7, 14), pady=(0, 10))
        ctk.CTkLabel(h, text=tx("Rangs"), text_color=p["sub"], anchor="w").pack(anchor="w", pady=(0, 4))
        self.e_lignes = []
        for nom, seuil, col in reversed(RANGS):
            lab = ctk.CTkLabel(h, text="", anchor="w", font=ctk.CTkFont(size=15, weight="bold"), text_color=col)
            lab.pack(fill="x", pady=2)
            self.e_lignes.append((lab, nom, seuil))
        self.confirm = False
        self.b_reset = self.btn(h, tx("Réinitialiser"), self.reset_elo, 150)
        self.b_reset.pack(anchor="w", pady=(14, 0))

    def reset_elo(self):
        if not self.confirm:
            self.confirm = True
            self.b_reset.configure(text=tx("Confirmer ?"))
            self.b_reset.after(3000, self.annule_reset)
            return
        REGL.pop("elo", None)
        sauver()
        self.annule_reset()
        self.maj_elo()
        self.nouveau(False)

    def annule_reset(self):
        try:
            self.confirm = False
            self.b_reset.configure(text=tx("Réinitialiser"))
        except Exception:
            pass

    def maj_elo(self):
        d = elo_data()
        (nom, seuil, col), suivant = rang(d["elo"])
        self.badge.configure(text=f"🏆 {tx(nom)} · {d['elo']}", text_color=col)
        self.e_rang.configure(text=tx(nom).upper(), text_color=col)
        self.e_pts.configure(text=f"{d['elo']} ELO")
        self.e_bar.configure(progress_color=col)
        if suivant:
            self.e_bar.set((d["elo"] - seuil) / (suivant[1] - seuil))
            self.e_next.configure(text=f"{tx('Prochain rang')} : {tx(suivant[0])}  ({suivant[1] - d['elo']} {tx('pts')})")
        else:
            self.e_bar.set(1)
            self.e_next.configure(text=tx("Rang maximum atteint !"))
        total = d["win"] + d["lose"]
        self.e_stats.configure(text=(f"{tx('Victoires')} : {d['win']}    {tx('Défaites')} : {d['lose']}"
                                     f"    ({round(100 * d['win'] / total) if total else 0} %)\n"
                                     f"{tx('Série en cours')} : {d['streak']}    {tx('Meilleur ELO')} : {d['best']}"))
        for lab, n, s in self.e_lignes:
            lab.configure(text=("▶  " if n == nom else "    ") + f"{tx(n):<10} {s}+")
        self.e_hist.configure(state="normal")
        self.e_hist.delete("1.0", "end")
        for dt, typ, delta, nv in reversed(d["hist"]):
            self.e_hist.insert("end", f"{dt}  {tx(typ):<12} {delta:+4d}  →  {nv}\n")
        self.e_hist.configure(state="disabled")

    # ---------- onglet 2 : paint ----------
    def onglet_paint(self, t):
        p = self.p
        t.grid_rowconfigure(1, weight=1)
        bar = ctk.CTkFrame(t, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        self.modes = [tx("Stylo"), tx("Gomme"), tx("Texte")]
        self.msel = ctk.CTkSegmentedButton(bar, values=self.modes, selected_color=self.sel,
                                           selected_hover_color=self.sel, unselected_color=p["bg"],
                                           unselected_hover_color=p["line"], text_color=p["fg"])
        self.msel.set(self.modes[0])
        self.msel.pack(side="left", padx=(0, 10))
        for c in self.PEN:
            ctk.CTkButton(bar, text="", width=26, height=26, corner_radius=13, fg_color=c, hover_color=c,
                          command=lambda c=c: (setattr(self, "couleur", c), self.msel.set(self.modes[0]))
                          ).pack(side="left", padx=2)
        ctk.CTkLabel(bar, text=tx("Épaisseur"), text_color=p["sub"]).pack(side="left", padx=(12, 4))
        self.taille = ctk.CTkSlider(bar, from_=1, to=20, number_of_steps=19, width=110, progress_color=self.ac)
        self.taille.set(3)
        self.taille.pack(side="left")
        for txt, cmd in ((tx("💾 Enregistrer"), self.enregistrer), (tx("🗑 Effacer"), self.effacer),
                         (tx("↶ Annuler"), self.annuler)):
            self.btn(bar, txt, cmd, 120).pack(side="right", padx=3)
        z = self.zone = tk.Canvas(t, bg="#ffffff", highlightthickness=0, cursor="pencil")
        z.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4, 10))
        z.bind("<ButtonPress-1>", self.p_bas)
        z.bind("<B1-Motion>", self.p_move)
        z.bind("<ButtonRelease-1>", self.p_haut)
        for s in self.app.strokes:       # on redessine ce qui existait (changement de thème/langue)
            self.dessiner(s)

    def dessiner(self, s):
        z, (x, y) = self.zone, s["pts"][0]
        if s["k"] == "t":
            s["ids"] = [z.create_text(x, y, text=s["txt"], fill=s["c"], anchor="nw",
                                      font=(police_ui(), max(10, s["w"] * 4)))]
        elif len(s["pts"]) == 1:
            r = s["w"] / 2
            s["ids"] = [z.create_oval(x - r, y - r, x + r, y + r, fill=s["c"], outline=s["c"])]
        else:
            s["ids"] = [z.create_line(*[v for q in s["pts"] for v in q], fill=s["c"], width=s["w"],
                                      capstyle="round", joinstyle="round")]

    def p_bas(self, ev):
        m, w = self.modes.index(self.msel.get()), int(self.taille.get())
        if m == 2:
            txt = ctk.CTkInputDialog(text=tx("Texte à écrire :"), title=tx("Texte")).get_input()
            if txt:
                s = dict(k="t", c=self.couleur, w=w, pts=[(ev.x, ev.y)], txt=txt)
                self.app.strokes.append(s)
                self.dessiner(s)
            return
        self.cur = dict(k="l", c="#ffffff" if m == 1 else self.couleur, w=w * 4 if m == 1 else w,
                        pts=[(ev.x, ev.y)], ids=[])
        self.app.strokes.append(self.cur)

    def p_move(self, ev):
        s = self.cur
        if s:
            (x0, y0) = s["pts"][-1]
            s["ids"].append(self.zone.create_line(x0, y0, ev.x, ev.y, fill=s["c"], width=s["w"], capstyle="round"))
            s["pts"].append((ev.x, ev.y))

    def p_haut(self, _):
        s, self.cur = self.cur, None
        if s and len(s["pts"]) == 1:
            self.dessiner(s)

    def annuler(self):
        if self.app.strokes:
            for i in self.app.strokes.pop().get("ids", []):
                self.zone.delete(i)

    def effacer(self):
        self.zone.delete("all")
        self.app.strokes.clear()

    def enregistrer(self):
        from PIL import Image, ImageDraw, ImageFont
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not f:
            return
        W = max([self.zone.winfo_width()] + [int(x) + 40 for q in self.app.strokes for x, _ in q["pts"]])
        H = max([self.zone.winfo_height()] + [int(y) + 40 for q in self.app.strokes for _, y in q["pts"]])
        im = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(im)
        for s in self.app.strokes:
            if s["k"] == "t":
                ft = ImageFont.load_default()
                for nom in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf",
                            "NotoSans-Regular.ttf", "Ubuntu-R.ttf", "FreeSans.ttf"):
                    try:
                        ft = ImageFont.truetype(nom, int(max(10, s["w"] * 4) * 1.33))
                        break
                    except Exception:
                        pass
                d.text(s["pts"][0], s["txt"], fill=s["c"], font=ft)
            else:
                pts, r = (s["pts"] if len(s["pts"]) > 1 else s["pts"] * 2), s["w"] / 2
                d.line(pts, fill=s["c"], width=s["w"], joint="curve")
                for x, y in (pts[0], pts[-1]):
                    d.ellipse((x - r, y - r, x + r, y + r), fill=s["c"])
        im.save(f)

    # ---------- onglet 3 : calculatrice scientifique ----------
    PRETTY = {"^2": "x²", "sqrt(": "√", "pi": "π", "/": "÷", "*": "×", "-": "−", "10^(": "10ˣ",
              "1/(": "1/x", "exp(": "eˣ", "!": "n!"}
    ROWS = [["DEG", "sin(", "cos(", "tan(", "ln(", "log("], ["^2", "sqrt(", "^", "(", ")", "!"],
            ["asin(", "acos(", "atan(", "pi", "e", "Ans"], ["7", "8", "9", "/", "⌫", "C"],
            ["4", "5", "6", "*", "abs(", "1/("], ["1", "2", "3", "-", "exp(", "10^("],
            ["0", ".", ",", "+", "="]]

    def onglet_calc(self, t):
        p = self.p
        t.grid_columnconfigure(0, weight=3)
        t.grid_columnconfigure(1, weight=2)
        t.grid_rowconfigure(0, weight=1)
        g = ctk.CTkFrame(t, fg_color="transparent")
        g.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        for j in range(6):
            g.grid_columnconfigure(j, weight=1, uniform="c")
        self.ce = ctk.CTkEntry(g, height=54, corner_radius=self.r, fg_color=p["bg"], border_color=p["line"],
                               text_color=p["fg"], font=ctk.CTkFont(family=mono(), size=22))
        self.ce.grid(row=0, column=0, columnspan=6, sticky="ew", pady=(0, 6))
        self.ce.bind("<Return>", lambda _: self.calc_eval())
        self.cr = ctk.CTkLabel(g, text="0", anchor="e", text_color=self.ac,
                               font=ctk.CTkFont(family=mono(), size=20, weight="bold"))
        self.cr.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(0, 10), padx=6)
        for i, ligne in enumerate(self.ROWS):
            for j, s in enumerate(ligne):
                nombre = s in "0123456789.,+-*/" or s == "⌫"
                b = ctk.CTkButton(g, text=self.PRETTY.get(s) or s.rstrip("(") or s, height=48, corner_radius=self.r,
                                  font=ctk.CTkFont(size=16, weight="bold"),
                                  fg_color=self.ac if s == "=" else (p["bg"] if nombre else p["line"]),
                                  hover_color=self.ac if s == "=" else p["sub"],
                                  text_color=self.onac if s == "=" else p["fg"],
                                  command=lambda s=s: self.calc_touche(s))
                b.grid(row=i + 2, column=j, columnspan=2 if s == "=" else 1, sticky="ew", padx=3, pady=3)
                if s == "DEG":
                    self.bdeg = b
        self.hist = ctk.CTkTextbox(t, corner_radius=self.r, fg_color=p["bg"], text_color=p["fg"], font=self.mono)
        self.hist.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)

    def calc_touche(self, s):
        e = self.ce
        if s == "DEG":
            self.deg = not self.deg
            self.bdeg.configure(text="DEG" if self.deg else "RAD")
        elif s == "C":
            e.delete(0, "end")
        elif s == "⌫":
            txt = e.get()
            e.delete(0, "end")
            e.insert(0, txt[:-1])
        elif s == "=":
            self.calc_eval()
        else:
            e.insert("end", s)
        e.focus_set()

    def calc_eval(self):
        s = self.ce.get().strip()
        if not s:
            return
        try:
            r = calcul_sci(s, self.deg, self.ans)
            self.ans = r
            res = V(r)
            self.cr.configure(text=res, text_color=self.ac)
            self.hist.insert("end", f"{s}\n   = {res}\n\n")
            self.hist.see("end")
        except Exception as err:
            self.cr.configure(text=f"⚠  {err}", text_color="#ef4444")


class Rainmath(ctk.CTk):
    """Fenêtre principale : change d'écran (menu / outils / daily)."""

    def __init__(self):
        super().__init__()
        self.title("Rainmath")
        self.geometry("1240x800")
        self.minsize(1000, 640)
        self.nom, self.vue, self.fen, self.outil, self.strokes = "menu", None, None, None, []
        self.ecran("menu")

    def ecran(self, nom):
        if self.vue is not None:
            self.vue.destroy()
        self.configure(fg_color=appliquer_theme()["bg"])
        self.nom = nom
        self.vue = {"menu": Menu, "outils": Outils, "daily": Daily}[nom](self)
        self.vue.pack(fill="both", expand=True)

    def rebuild(self):
        self.ecran(self.nom)


if __name__ == "__main__":
    Rainmath().mainloop()