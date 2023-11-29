from flask import Flask, render_template, redirect, url_for, flash
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired
import subprocess
import threading
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Simulated user database for demonstration purposes
class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role

users = {1: User(1, 'admin'), 2: User(2, 'user')}

# Global variables
server_process = None
server_status = "Stopped"
server_properties = {
    "max_players": 20,
    "motd": "Welcome to My Server!"
}

# Function to run the server
def run_server():
    global server_process, server_status
    server_process = subprocess.Popen(['java', '-Xmx1024M', '-Xms1024M', '-jar', 'server.jar', 'nogui'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, text=True)
    server_status = "Running"
    for line in server_process.stdout:
        emit('server_output', {'output': line.strip()})
    server_status = "Stopped"
    emit('server_status', {'status': server_status})

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

class ConfigureForm(FlaskForm):
    max_players = IntegerField('Max Players', validators=[DataRequired()])
    motd = StringField('MOTD', validators=[DataRequired()])
    submit = SubmitField('Save Changes')

class LoginForm(FlaskForm):
    user_id = IntegerField('User ID', validators=[DataRequired()])
    submit = SubmitField('Log In')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        user = load_user(user_id)
        if user:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('User not found. Please try again.', 'danger')
    return render_template(r'D:\Apps\Programeren\Minecraft server controller\templates\login_advanced.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template(r'D:\Apps\Programeren\Minecraft server controller\templates\index_advanced.html', server_status=server_status, server_properties=server_properties)

@app.route('/start_server', methods=['POST'])
@login_required
def start_server():
    global server_process, server_status
    if server_process and server_process.poll() is None:
        return 'Server is already running!'
    threading.Thread(target=run_server).start()
    return 'Starting Minecraft server...'

@app.route('/stop_server', methods=['POST'])
@login_required
def stop_server():
    global server_process, server_status
    if server_process and server_process.poll() is None:
        server_process.stdin.write('stop\n')
        server_process.stdin.flush()
        return 'Stopping Minecraft server...'
    return 'Server is not running!'

@app.route('/configure', methods=['GET', 'POST'])
@login_required
def configure():
    form = ConfigureForm()
    if form.validate_on_submit():
        server_properties['max_players'] = form.max_players.data
        server_properties['motd'] = form.motd.data
        flash('Changes saved successfully!', 'success')
    return render_template(r'D:\Apps\Programeren\Minecraft server controller\templates\configure_advanced.html', form=form, server_properties=server_properties)

@socketio.on('connect')
def handle_connect():
    emit('server_status', {'status': server_status})
    emit('server_properties', {'properties': server_properties})

if __name__ == '__main__':
    socketio.run(app, debug=True)
