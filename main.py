from flask import Flask, render_template
app = Flask(__name__)

@app.route("/")
def hello():
    return render_template("hexview.html", hello_world = "Hello World!")

if __name__ == "__main__":
    app.debug = True
    app.run()
