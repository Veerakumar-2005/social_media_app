from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import sqlite3, os

app = Flask(__name__)
app.secret_key = 'secretkey'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# DB setup
def init_db():
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, content TEXT, image TEXT, likes INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, comment TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS follows (follower_id INTEGER, followee_id INTEGER)''')
    conn.close()

init_db()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT posts.id, users.username, posts.content, posts.image, posts.likes FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.id DESC")
    posts = c.fetchall()
    conn.close()
    return render_template('home.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                return redirect(url_for('login'))
            except:
                flash("Username already exists.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = username
                return redirect(url_for('index'))
            flash("Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form['content']
    image = request.files['image']
    filename = None
    if image:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO posts (user_id, content, image) VALUES (?, ?, ?)", (session['user_id'], content, filename))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/like/<int:post_id>')
def like(post_id):
    if 'user_id' in session:
        with sqlite3.connect("database.db") as conn:
            c = conn.cursor()
            c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
            conn.commit()
    return redirect(url_for('index'))

@app.route('/comment/<int:post_id>', methods=['POST'])
def comment(post_id):
    comment_text = request.form['comment']
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO comments (post_id, user_id, comment) VALUES (?, ?, ?)", (post_id, session['user_id'], comment_text))
        conn.commit()
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user:
        c.execute("SELECT content, image FROM posts WHERE user_id=?", (user[0],))
        posts = c.fetchall()
        return render_template("profile.html", username=username, posts=posts)
    else:
        return "User not found"

if __name__ == '__main__':
    app.run(debug=True)
