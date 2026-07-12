from flask import Flask, render_template
import sqlite3

# create the flask app
app = Flask(__name__)

# routes home url /
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()