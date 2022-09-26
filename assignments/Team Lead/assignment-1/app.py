from flask import Flask, request, render_template

app = Flask(__name__)

@app.route("/submit-form", methods=['GET', 'POST'])
def submitFormData():

    req = request.form

    return render_template("table.html", req = req)

@app.route("/")
def greetings():
    return render_template("index.html")

if __name__ == 'main':
    app.run()