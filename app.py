from flask import Flask, request, send_file, render_template_string
import pdfplumber
import re
import requests
from datetime import datetime
import os

app = Flask(__name__)

HTML_UPLOAD = """
<h2>Revolut → SAGA</h2>
<form method="post" enctype="multipart/form-data">
<input type="file" name="file" required><br><br>
<button type="submit">Preview</button>
</form>
"""

HTML_TABLE = """
<h2>Preview tranzactii</h2>
<form method="post" action="/export">
<table border="1" cellpadding="5">
<tr>
<th>Data</th><th>Tip</th><th>EUR</th><th>RON</th><th>Explicatie</th>
</tr>
{% for t in tx %}
<tr>
<td>{{t[0]}}</td>
<td>{{t[1]}}</td>
<td>{{t[2]}}</td>
<td>{{t[3]}}</td>
<td>{{t[4]}}</td>
</tr>
{% endfor %}
</table>
<br>
<button type="submit">Genereaza SAGA</button>
</form>
"""

cache = []

def get_bnr(date):
    try:
        url = f"https://api.exchangerate.host/{date}?base=EUR&symbols=RON"
        return float(requests.get(url).json()["rates"]["RON"])
    except:
        return 5.08

def map_account(text):
    t = text.lower()
    if "coolunity" in t: return "704"
    if "omv" in t: return "6022"
    if "leasing" in t: return "167"
    if "taxa" in t: return "635"
    if "delegare" in t: return "625"
    return "401"

def parse_pdf(file):
    data = []

    with pdfplumber.open(file) as pdf:
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])

    blocks = re.split(r'\n(?=\d{1,2}\s\w{3}\.\s\d{4})', text)

    for b in blocks:
        if "€" not in b:
            continue

        date_match = re.search(r'(\d{1,2}\s\w{3}\.\s\d{4})', b)
        if not date_match:
            continue

        try:
            date = datetime.strptime(date_match.group(1), "%d %b. %Y").strftime("%Y-%m-%d")
        except:
            continue

        eur = re.findall(r'€\s?([\d\.,]+)', b)
        ron = re.findall(r'([\d\.,]+)\sRON', b)

        eur = float(eur[0].replace(",", "")) if eur else 0
        ron = float(ron[0].replace(",", "")) if ron else 0

        if "De la" in b:
            tip = "inc"
        elif "Către" in b:
            tip = "pl"
        elif "RON" in b:
            tip = "fx"
        else:
            continue

        data.append((date, tip, eur, ron, b[:80]))

    return data

@app.route("/", methods=["GET","POST"])
def home():
    global cache

    if request.method == "POST":
        f = request.files.get("file")
        cache = parse_pdf(f)
        return render_template_string(HTML_TABLE, tx=cache)

    return render_template_string(HTML_UPLOAD)

@app.route("/export", methods=["POST"])
def export():
    global cache

    out = "saga.txt"

    with open(out, "w", encoding="utf-8") as g:
        nr = 1

        for d,t,eur,ron,exp in cache:

            exp = exp.replace(";", " ")[:50]

            if t == "inc":
                g.write(f"{d};OP;{nr};{exp};5124.3;704;{eur:.2f};EUR\n")
                nr += 1

            elif t == "pl":
                cont = map_account(exp)
                g.write(f"{d};OP;{nr};{exp};{cont};5124.3;{eur:.2f};EUR\n")
                nr += 1

            elif t == "fx":
                kurs = get_bnr(d)
                diff = round(eur * kurs - ron, 2)

                g.write(f"{d};NC;{nr};Schimb;581.2;5124.3;{eur:.2f};EUR\n")
                nr += 1

                g.write(f"{d};NC;{nr};Schimb;5121.3;581.2;{ron:.2f};RON\n")
                nr += 1

                if diff > 0:
                    g.write(f"{d};NC;{nr};Dif curs;665;581.2;{diff:.2f};RON\n")
                elif diff < 0:
                    g.write(f"{d};NC;{nr};Dif curs;581.2;765;{abs(diff):.2f};RON\n")

                nr += 1

    return send_file(out, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)