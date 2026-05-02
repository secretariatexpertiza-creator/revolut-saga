from flask import Flask, request, send_file, render_template_string
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Revolut → SAGA</title>
</head>
<body style="font-family: Arial; text-align:center; margin-top:50px;">

<h2>Upload PDF Revolut</h2>

<form method="post" enctype="multipart/form-data">
    <input type="file" name="file" required><br><br>
    <button type="submit">Genereaza SAGA</button>
</form>

</body>
</html>
"""

@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        f = request.files.get("file")

        if not f:
            return "No file uploaded", 400

        # TEST simplu (fără pdfplumber momentan)
        out = "saga.txt"

        with open(out, "w") as g:
            g.write("2025-01-01;OP;1;Test;5124.3;704;100;EUR\n")

        return send_file(out, as_attachment=True)

    return render_template_string(HTML)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)