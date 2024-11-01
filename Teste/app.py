from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return redirect(url_for('dashboard'))  # Redireciona para o dashboard

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)