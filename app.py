from flask import Flask, request, send_file, render_template_string
import pdfplumber
import re
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revolut → SAGA</title>
</head>
<body style="font-family: Arial; text-align:center; margin-top:50px;">

<h2>Revolut → SAGA</h2>

<form method="post" enctype="multipart/form-data">
    <input type="file" name="file" required><br><br>
    <button type="submit">Genereaza SAGA</button>
</form>

</body>
</html>
"""

def parse_pdf(file):
    transactions = []

    with pdfplumber.open(file) as pdf:
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])

    lines = text.split("\n")

    for line in lines:
        if "€" not in line:
            continue

        try:
            amount_match = re.search(r'€\s?([\d\.,]+)', line)
            if not amount_match:
                continue

            amount = float(amount_match.group(1).replace(",", ""))

            if "De la" in line:
                tip = "inc"
            elif "Către" in line:
                tip = "pl"
            else:
                continue

            transactions.append((tip, amount, line[:80]))

        except:
            continue

    return transactions

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        f = request.files.get("file")

        if not f:
            return "No file", 400

        tx = parse_pdf(f)

        out = "saga.txt"

        with open(out, "w") as g:
            nr = 1

            for tip, suma, exp in tx:
                if tip == "inc":
                    g.write(f"2025-01-01;OP;{nr};{exp};5124.3;704;{suma};EUR\n")
                else:
                    g.write(f"2025-01-01;OP;{nr};{exp};401;5124.3;{suma};EUR\n")

                nr += 1

        return send_file(out, as_attachment=True)

    return render_template_string(HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)