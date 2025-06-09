from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
from flask_wtf.csrf import CSRFProtect
import psycopg2
import psycopg2.extras
import os
import socket

app = Flask(__name__)
app.secret_key = 'supersecretkey'
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)

# Configure SocketIO
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   logger=True,
                   engineio_logger=True,
                   async_mode='eventlet',
                   manage_session=True,
                   cookie=None)

def get_container_info():
    try:
        # Get container ID (first 12 characters of hostname)
        hostname = socket.gethostname()
        container_id = hostname[:12] if len(hostname) >= 12 else hostname
        
        # Get container IP
        container_ip = socket.gethostbyname(hostname)
        
        return {
            'container_id': container_id,
            'container_ip': container_ip,
            'db_host': os.environ.get("DB_HOST", "db")
        }
    except Exception as e:
        app.logger.error(f"Error getting container info: {str(e)}")
        return {
            'container_id': 'Unknown',
            'container_ip': 'Unknown',
            'db_host': os.environ.get("DB_HOST", "db")
        }

# Database connection
def get_db():
    return psycopg2.connect(
        dbname="votingdb",
        user="votinguser",
        password="votingpass",
        host=os.environ.get("DB_HOST", "db"),
        port=5432
    )

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT id, username, password FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Username already exists.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        conn.close()
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(user['id'], user['username'], user['password'])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    try:
        # Initialize with 0 votes if no votes exist
        cur.execute("""
            SELECT 'A' as option, COALESCE(COUNT(*), 0) FROM votes WHERE option = 'A'
            UNION ALL
            SELECT 'B' as option, COALESCE(COUNT(*), 0) FROM votes WHERE option = 'B'
            ORDER BY option
        """)
        votes = cur.fetchall()
        # Store vote counts in session for Socket.IO access
        session['vote_counts'] = {
            'A': votes[0][1],
            'B': votes[1][1]
        }
        
        # Get container information
        container_info = get_container_info()
        
        return render_template('dashboard.html', 
                             votes=votes,
                             container_info=container_info)
    except Exception as e:
        app.logger.error(f'Error fetching votes: {str(e)}')
        flash('Error loading vote counts.', 'error')
        return render_template('dashboard.html', 
                             votes=[('A', 0), ('B', 0)],
                             container_info=get_container_info())
    finally:
        conn.close()

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    if not request.form:
        app.logger.error('No form data received')
        return jsonify({'error': 'No form data received'}), 400

    option = request.form.get('option')
    if not option:
        app.logger.error('No option provided in form data')
        error_msg = 'Please select an option to vote.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('dashboard'))

    if option not in ['A', 'B']:
        app.logger.error(f'Invalid option provided: {option}')
        error_msg = 'Invalid vote option.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('dashboard'))

    try:
        conn = get_db()
        cur = conn.cursor()

        # Check if user has already voted
        cur.execute("SELECT id FROM votes WHERE user_id = %s", (current_user.id,))
        existing_vote = cur.fetchone()

        if existing_vote:
            error_msg = 'You have already voted.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': error_msg}), 400
            flash(error_msg, 'error')
            return redirect(url_for('dashboard'))

        # Record the vote
        cur.execute("INSERT INTO votes (user_id, option) VALUES (%s, %s)", 
                   (current_user.id, option))
        conn.commit()

        # Get updated counts for both options
        cur.execute("""
            SELECT option, COUNT(*) 
            FROM votes 
            GROUP BY option 
            ORDER BY option
        """)
        vote_counts = dict(cur.fetchall())
        
        # Update session with new vote counts
        session['vote_counts'] = {
            'A': vote_counts.get('A', 0),
            'B': vote_counts.get('B', 0)
        }
        
        # Emit real-time update with new counts
        socketio.emit('vote_update', {
            'option': option,
            'counts': session['vote_counts']
        }, broadcast=True)

        success_msg = 'Vote recorded successfully!'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'message': success_msg,
                'counts': session['vote_counts']
            })
        flash(success_msg, 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        app.logger.error(f'Error processing vote: {str(e)}')
        error_msg = 'An error occurred while processing your vote.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('dashboard'))
    finally:
        conn.close()

@socketio.on('connect')
def handle_connect():
    app.logger.info('Client connected')
    # Send current vote counts to the newly connected client
    if 'vote_counts' in session:
        emit('vote_update', {
            'option': None,
            'counts': session['vote_counts']
        })

@socketio.on_error_default
def default_error_handler(e):
    app.logger.error(f'SocketIO error: {str(e)}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9032))
    socketio.run(app, 
                host='0.0.0.0', 
                port=port, 
                debug=True,
                use_reloader=False)
