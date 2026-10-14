"""Private helpers of the "forms" author (criteria 3.3.1, 3.3.2, 3.3.3, 3.3.4).

Small HTML builders for form fields and one compact, deterministic client-side
validation engine (vanilla JS, runs on ``submit`` with ``preventDefault()``).
Error containers always exist in the static DOM so target selectors resolve and
a headless browser can observe the state after submitting.
"""
from __future__ import annotations

import json

from common import esc, pick, wrap

FORM_CSS = (
    ".fld{margin:0 0 14px}.fld label{margin-top:0}"
    ".hint{margin:2px 0 4px;font-size:.92rem;color:#4b5563}"
    ".err{margin:4px 0 0;color:#a3001b;font-weight:600;min-height:0}"
    ".is-invalid{border:2px solid #c8102e;background:#fff1f2}"
    ".msgbox{border:2px solid #a3001b;background:#fff6f6;padding:10px 14px;border-radius:6px;margin:0 0 16px}"
    ".okbox{border:2px solid #2f6b3a;background:#eef7ef;padding:10px 14px;border-radius:6px;margin:16px 0}"
    ".row{display:flex;flex-wrap:wrap;gap:0 18px}.row .fld{flex:1 1 180px}"
    "fieldset{border:1px solid #c5ccd3;border-radius:8px;padding:8px 16px 4px;margin:0 0 16px}"
    "legend{font-weight:700;padding:0 4px}"
    ".req{color:#a3001b}"
    ".visually-hidden{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}"
    ".icon-slot svg{vertical-align:middle;margin-left:6px}"
    ".actions{margin-top:18px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}"
    ".btn-sec{background:#ffffff;color:#1d2327;border:1px solid #6b7280}"
    "aside.box{margin-top:24px}"
    ".dialog{position:fixed;left:50%;top:20%;transform:translateX(-50%);max-width:440px;background:#ffffff;"
    "border:2px solid #1d2327;border-radius:10px;padding:16px 20px;box-shadow:0 8px 30px rgba(0,0,0,.25)}"
    ".crumbs{font-size:.9rem;margin:0 0 8px}"
)

BTN = {"de": "Absenden", "fr": "Envoyer", "it": "Invia", "en": "Submit"}
THANKS = {
    "de": "Vielen Dank! Ihre Angaben wurden übermittelt.",
    "fr": "Merci ! Vos données ont bien été transmises.",
    "it": "Grazie! I suoi dati sono stati trasmessi.",
    "en": "Thank you! Your data has been sent.",
}
REQ_NOTE = {"de": "* Pflichtfeld", "fr": "* champ obligatoire", "it": "* campo obbligatorio"}
CONTACT = {"de": "Kontakt", "fr": "Contact", "it": "Contatto"}


def field(fid, label, *, type="text", hint=None, hint_before=False, star=False, err=True,
          err_live=None, err_cls="err", describe_err=True, value=None, ph=None, ac=None, im=None,
          pattern=None, title=None, required=False, extra="", size=None, label_html=None,
          no_label=False, textarea=False, rows=4, icon_slot=None, err_hidden_cls=None,
          wrap_cls="fld", err_text=""):
    """One labelled control with optional hint and an (empty) error container ``#err-<fid>``.

    icon_slot : inner HTML of a hidden icon container ``#err-<fid>`` (instead of a text container)
    err_hidden_cls : class for the error container (e.g. "visually-hidden")
    """
    desc = []
    hint_html = ""
    if hint:
        desc.append(f"hint-{fid}")
        hint_html = f'<p class="hint" id="hint-{fid}">{hint}</p>'
    err_html = ""
    if icon_slot is not None:
        err_html = f'<span class="icon-slot" id="err-{fid}" hidden>{icon_slot}</span>'
        if describe_err:
            desc.append(f"err-{fid}")
    elif err:
        live = ""
        if err_live == "polite":
            live = ' aria-live="polite"'
        elif err_live == "alert":
            live = ' role="alert"'
        cls = err_hidden_cls or err_cls
        err_html = f'<p class="{cls}" id="err-{fid}"{live}>{esc(err_text)}</p>'
        if describe_err:
            desc.append(f"err-{fid}")
    a = [f'id="{fid}"', f'name="{fid}"']
    if not textarea:
        a.append(f'type="{type}"')
    if desc:
        a.append(f'aria-describedby="{" ".join(desc)}"')
    if value is not None:
        a.append(f'value="{esc(value)}"')
    if ph:
        a.append(f'placeholder="{esc(ph)}"')
    if ac:
        a.append(f'autocomplete="{ac}"')
    if im:
        a.append(f'inputmode="{im}"')
    if pattern:
        a.append(f'pattern="{esc(pattern)}"')
    if title:
        a.append(f'title="{esc(title)}"')
    if size:
        a.append(f'size="{size}"')
    if required:
        a.append("required")
    if extra:
        a.append(extra)
    if textarea:
        ctl = f'<textarea {" ".join(a)} rows="{rows}" cols="40"></textarea>'
    else:
        ctl = f'<input {" ".join(a)}>'
    lab = ""
    if not no_label:
        st = ' <span class="req" aria-hidden="true">*</span>' if star else ""
        lab = f'<label for="{fid}">{label_html if label_html else esc(label)}{st}</label>'
    parts = [lab]
    if hint_before:
        parts += [hint_html, ctl]
    else:
        parts += [ctl, hint_html]
    parts.append(err_html)
    return f'<div class="{wrap_cls}">' + "".join(p for p in parts if p) + "</div>"


def select(fid, label, options, *, err=True, star=False, required=False, first=None):
    opts = ""
    if first is not None:
        opts += f'<option value="">{esc(first)}</option>'
    opts += "".join(f'<option>{esc(o)}</option>' for o in options)
    st = ' <span class="req" aria-hidden="true">*</span>' if star else ""
    e = f'<p class="err" id="err-{fid}"></p>' if err else ""
    ad = f' aria-describedby="err-{fid}"' if err else ""
    rq = " required" if required else ""
    return (f'<div class="fld"><label for="{fid}">{esc(label)}{st}</label>'
            f'<select id="{fid}" name="{fid}"{ad}{rq}>{opts}</select>{e}</div>')


def radios(name, legend, options, *, gid=None, checked=None):
    gid_attr = f' id="{gid}"' if gid else ""
    items = []
    for i, o in enumerate(options):
        c = " checked" if checked == i else ""
        items.append(f'<div><input type="radio" id="{name}-{i + 1}" name="{name}" value="{esc(o)}"{c}> '
                     f'<label for="{name}-{i + 1}" style="display:inline;font-weight:400">{esc(o)}</label></div>')
    return f'<fieldset{gid_attr}><legend>{esc(legend)}</legend>{"".join(items)}</fieldset>'


def fieldset(legend, inner):
    return f"<fieldset><legend>{esc(legend)}</legend>{inner}</fieldset>"


def row(*parts):
    return '<div class="row">' + "".join(parts) + "</div>"


def okbox(lang, text=None, oid="danke"):
    return f'<div class="okbox" id="{oid}" tabindex="-1" hidden><p>{esc(text or THANKS[lang])}</p></div>'


def actions(label, extra=""):
    return f'<div class="actions"><button type="submit">{esc(label)}</button>{extra}</div>'


def _js_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False).replace("</", "<\\/")


def js_validate(form_id, rules, *, done_id="danke", summary=None, dialog=None):
    """Return an inline <script> validating ``rules`` on submit.

    rule keys: f (field id), t (JS boolean expression using the trimmed value ``v``),
               m (message text, may be ""), mf (optional JS expression computing the message from v), o ('text' | 'show' | 'list' | 'dlg' | 'none'),
               x (element id receiving the text / to unhide; default 'err-<f>'),
               mk (bool: set aria-invalid + .is-invalid), ln (bool: link in summary list)
    summary : dict(box=, list=)   dialog : dict(box=, list=, close=)
    """
    objs = []
    for r in rules:
        o = r.get("o", "text")
        x = r.get("x", f"err-{r['f']}") if o in ("text", "show") else ""
        mf = (",mf:function(v){return %s;}" % r["mf"]) if r.get("mf") else ""
        objs.append("{f:%s,t:function(v){return %s;},m:%s,o:%s,x:%s,mk:%d,ln:%d%s}" % (
            _js_str(r["f"]), r["t"], _js_str(r.get("m", "")), _js_str(o), _js_str(x),
            1 if r.get("mk", True) else 0, 1 if r.get("ln", False) else 0, mf))
    lines = [
        'document.addEventListener("DOMContentLoaded", function () {',
        f'  var form = document.getElementById({_js_str(form_id)});',
        f'  var done = document.getElementById({_js_str(done_id)});',
        "  var rules = [\n    " + ",\n    ".join(objs) + "\n  ];",
    ]
    if summary:
        lines.append(f'  var sbox = document.getElementById({_js_str(summary["box"])}), slist = document.getElementById({_js_str(summary["list"])});')
    if dialog:
        lines.append(f'  var dbox = document.getElementById({_js_str(dialog["box"])}), dlist = document.getElementById({_js_str(dialog["list"])});')
        lines.append(f'  document.getElementById({_js_str(dialog["close"])}).addEventListener("click", function () {{ dbox.hidden = true; }});')
    lines += [
        '  form.addEventListener("submit", function (ev) {',
        "    ev.preventDefault();",
        "    var first = null, items = [];",
        "    done.hidden = true;",
        "    rules.forEach(function (r) {",
        "      var f = document.getElementById(r.f);",
        "      var v = f.value.trim(), ok = r.t(v);",
        "      r.cur = (!ok && r.mf) ? r.mf(v) : r.m;",
        "      var x = r.x ? document.getElementById(r.x) : null;",
        '      if (r.mk) { if (ok) { f.removeAttribute("aria-invalid"); f.classList.remove("is-invalid"); }',
        '                  else { f.setAttribute("aria-invalid", "true"); f.classList.add("is-invalid"); } }',
        '      if (r.o === "text") { x.textContent = ok ? "" : r.cur; if (x.hasAttribute("hidden") || ok) { x.hidden = ok; } }',
        '      if (r.o === "show") { x.hidden = ok; }',
        "      if (!ok) { items.push(r); if (!first) { first = f; } }",
        "    });",
    ]
    if summary or dialog:
        lines += [
            "    function fill(list, kind) {",
            "      while (list.firstChild) { list.removeChild(list.firstChild); }",
            "      items.forEach(function (r) {",
            "        if (r.o !== kind) { return; }",
            '        var li = document.createElement("li");',
            '        if (r.ln) { var a = document.createElement("a"); a.href = "#" + r.f; a.textContent = r.cur; li.appendChild(a); }',
            "        else { li.textContent = r.cur; }",
            "        list.appendChild(li);",
            "      });",
            "      return list.children.length;",
            "    }",
        ]
    if summary:
        lines.append('    var ns = fill(slist, "list"); sbox.hidden = ns === 0; if (ns) { sbox.focus(); return; }')
    if dialog:
        lines.append('    var nd = fill(dlist, "dlg"); dbox.hidden = nd === 0; if (nd) { document.getElementById(%s).focus(); return; }' % _js_str(dialog["close"]))
    lines += [
        "    if (first) { first.focus(); return; }",
        "    done.hidden = false; done.focus();",
        "  });",
        "});",
    ]
    return "<script>\n" + "\n".join(lines) + "\n</script>"


def js_done_only(form_id, done_id="danke"):
    """Script for forms relying on native constraint validation (submit fires only when valid)."""
    return ("<script>\n"
            'document.addEventListener("DOMContentLoaded", function () {\n'
            f'  var form = document.getElementById({_js_str(form_id)});\n'
            '  form.addEventListener("submit", function (ev) {\n'
            "    ev.preventDefault();\n"
            f'    var d = document.getElementById({_js_str(done_id)}); d.hidden = false; d.focus();\n'
            "  });\n"
            "});\n</script>")


def compose(rng, lang, org, h1, form_html, *, intro="", aside=None, crumbs=None, chrome=None,
            after="", before_h1=""):
    """Assemble the <body> content: optional breadcrumb, h1, intro, form, aside (position varies)."""
    if chrome is None:
        chrome = rng.random() < 0.7
    parts = []
    if crumbs:
        parts.append(f'<p class="crumbs">{crumbs}</p>')
    parts.append(before_h1)
    parts.append(f"<h1>{esc(h1)}</h1>")
    if intro:
        parts.append(intro)
    side_first = aside is not None and rng.random() < 0.3
    if side_first:
        parts.append(aside)
    parts.append(form_html)
    if aside is not None and not side_first:
        parts.append(aside)
    if after:
        parts.append(after)
    return wrap(lang, org, "\n".join(p for p in parts if p), chrome=chrome)


def contact_aside(lang, office, phone, mail, hours=None):
    h = {"de": "Fragen?", "fr": "Des questions ?", "it": "Domande?"}[lang]
    lines = [f"<h2>{esc(h)}</h2>", f"<p>{esc(office)}<br>Tel. {esc(phone)}<br>"
             f'<a href="mailto:{esc(mail)}">{esc(mail)}</a></p>']
    if hours:
        lines.append(f"<p>{esc(hours)}</p>")
    return '<aside class="box">' + "".join(lines) + "</aside>"


def choose(rng, seq):
    return pick(rng, seq)


# ---------------------------------------------------------------------------
# JS boolean expressions on the trimmed value ``v``
# ---------------------------------------------------------------------------
T_PLZ = r"/^\d{4}$/.test(v)"
T_EMAIL = r"/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(v)"
T_AHV = r"/^756\.\d{4}\.\d{4}\.\d{2}$/.test(v)"
T_DATE = (r"(function(){var m=/^(\d{2})\.(\d{2})\.(\d{4})$/.exec(v);if(!m){return false;}"
          r"var d=new Date(+m[3],+m[2]-1,+m[1]);return d.getDate()===+m[1]&&d.getMonth()===+m[2]-1;})()")
T_FILLED = 'v !== ""'
T_PLATE = r"/^[A-Z]{2} ?\d{1,6}$/.test(v.toUpperCase())"
T_PHONE = r"/^(0|\+41 ?)\d{2} ?\d{3} ?\d{2} ?\d{2}$/.test(v)"
T_IBAN = r'/^CH\d{19}$/.test(v.replace(/\s+/g, "").toUpperCase())'


def t_digits(n):
    return r"/^\d{%d}$/.test(v)" % n


def t_range(a, b):
    return r"/^\d+$/.test(v) && +v >= %d && +v <= %d" % (a, b)


def t_oneof(values, *, strip_suffix=None):
    arr = "[" + ",".join(_js_str(x.lower()) for x in values) + "]"
    expr = "v.toLowerCase()"
    if strip_suffix:
        expr = f"v.toLowerCase().replace({strip_suffix}, \"\")"
    return f"{arr}.indexOf({expr}) >= 0"


DONE_ID = {"de": "danke", "fr": "merci", "it": "grazie", "en": "thanks"}


def form_case(rng, criterion, lang, org, h1, intro, inner, rules=(), *, fid, target, expected, rule,
              notes, trap=False, difficulty="medium", alt=None, aside=None, novalidate=True,
              action=None, top="", bottom="", btn=None, summary=None, dialog=None, mode="validate",
              extra_after="", custom_script="", buttons=None, chrome=None, crumbs=None):
    """Build a Case whose page contains one form.

    mode: "validate" (js_validate with ``rules``), "native" (constraint validation + thank-you),
          "none" (no script; form posts to ``action``), "custom" (``custom_script`` verbatim)
    """
    from common import Case, page, SITE_LANG_TAG
    done = DONE_ID[lang]
    nv = " novalidate" if novalidate else ""
    act = f' action="{action}" method="post"' if action else ""
    acts = buttons if buttons is not None else actions(btn or BTN[lang])
    form = f'<form id="{fid}"{act}{nv}>{top}{inner}{bottom}{acts}</form>'
    if mode in ("validate", "native"):
        form += okbox(lang, oid=done)
    form += extra_after
    body = compose(rng, lang, org, h1, form, intro=intro, aside=aside, chrome=chrome, crumbs=crumbs)
    if mode == "validate":
        body += "\n" + js_validate(fid, list(rules), done_id=done, summary=summary, dialog=dialog)
    elif mode == "native":
        body += "\n" + js_done_only(fid, done)
    elif mode == "custom":
        body += "\n" + custom_script
    tag = pick(rng, [SITE_LANG_TAG[lang], lang])
    html = page(tag, f"{h1} – {org}", body, rng=rng, css=FORM_CSS)
    return Case(criterion, lang, expected, html=html, target=target, rule=rule, notes=notes,
                trap=trap, alt_expected=alt, difficulty=difficulty)
