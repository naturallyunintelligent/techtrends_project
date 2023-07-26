import sqlite3
import logging
import sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

post_count = 6
db_connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.logger.debug('Connected to database.db')
    db_connection_count += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    app.logger.debug(f'get_post:{post_id}')
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    app.logger.debug('Main index.html loaded')
    app.logger.debug(f'len(posts)={len(posts)}')
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.debug('Returned 404 - post id not found')
        return render_template('404.html'), 404
    else:
        app.logger.debug(f'`Retrieved post:{post_id}')
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug('Retrieved /about page')
    return render_template('about.html')

@app.route('/healthz/')
def status():
    try:
        connection = get_db_connection()
    except:
        response = app.response_class(
            response=json.dumps({"result": "db failure"}),
            status=500,
            mimetype='application/json'
        )
        app.logger.debug('db did not connect')
        app.logger.debug('Can return some useful debug info here')
    response = app.response_class(
              response=json.dumps({"result":"OK - healthy"}),
              status=200,
              mimetype='application/json'
    )
    app.logger.debug('Successfully returned status')
    app.logger.debug('Can return some useful debug info here')
    return response

@app.route('/teapot/')
def teapot():
    app.logger.debug('Successful teapot endpoint - for learning about endpoints')
    return "Would you like some tea?", 418

@app.route('/metrics/')
def metrics():
    #global post_count
    global db_connection_count
    connection = get_db_connection()
    connection.close()
    post_count = len(connection.execute('SELECT * FROM posts').fetchall())
    response = app.response_class(
          response=json.dumps({
                               "db_connection_count": db_connection_count,
                               "post_count": post_count}),
          status=200,
          mimetype='application/json'
    )
    app.logger.debug('Successfully returned metrics response')
    return response


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    #global post_count
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            #post_count += 1
            app.logger.debug(f'Successfully created post: {title}')
            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
    # Stream logs to a file, and set the default log level to DEBUG

    log_file_handler = logging.FileHandler(filename='app.log')
    log_stdout_handler = logging.StreamHandler(stream=sys.stdout)
    log_stderr_handler = logging.StreamHandler(stream=sys.stderr)
    log_handlers = [log_file_handler, log_stdout_handler, log_stderr_handler]

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)-8s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=log_handlers
    )

    app.run(host='0.0.0.0', port='3111')