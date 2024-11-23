from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from dotenv import load_dotenv
import bcrypt
import json
from db_monitor import DatabaseMonitor
from datetime import datetime, timezone
import csv
from io import StringIO

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///dbmonitor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def init_db():
    with app.app_context():
        db.create_all()
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin',
                is_active=True
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def get_id(self):
        return str(self.id)

    def check_password(self, password):
        """Check the password against the hash"""
        if not self.password_hash:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def set_password(self, password):
        """Set the password hash for the user"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    access_ip = db.Column(db.String(45), nullable=False)
    menu_accessed = db.Column(db.String(255), nullable=False)  # Using menu_accessed instead of action
    access_time = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now())  # Using access_time instead of timestamp
    user_agent = db.Column(db.String(255), nullable=False, default='Unknown')  # New field for user agent
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

class QueryHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('database_server.id'), nullable=False)
    query_text = db.Column(db.Text, nullable=False)
    execution_time = db.Column(db.Float)  # in seconds
    status = db.Column(db.String(50))  # active, completed, error
    start_time = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime)
    database_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('query_history', lazy=True))
    server = db.relationship('DatabaseServer', backref=db.backref('query_history', lazy=True))

class DatabaseServer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.String(20), nullable=False)  # postgresql, mysql, sqlserver, mariadb
    host = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    last_error = db.Column(db.String(500))
    last_check = db.Column(db.DateTime)
    
    @property
    def is_connected(self):
        if not self.last_check or (datetime.now(timezone.utc) - self.last_check).total_seconds() > 300:
            self.test_connection()
        return not bool(self.last_error)
    
    def test_connection(self):
        try:
            config = {
                'db_type': self.db_type,
                'host': self.host,
                'port': self.port,
                'database': 'postgres' if self.db_type == 'postgresql' else 'master',
                'username': self.username,
                'password': self.password
            }
            monitor = DatabaseMonitor(config)
            monitor.connect()
            monitor.close()
            
            self.last_error = None
            self.last_check = datetime.now(timezone.utc)
            db.session.commit()
            return True
        except Exception as e:
            self.last_error = str(e)
            self.last_check = datetime.now(timezone.utc)
            db.session.commit()
            return False

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user is None or not user.is_active:
        return None
    return user

def log_activity(user_id, menu_accessed, details=None):
    """Log user activity with detailed information
    Args:
        user_id: ID of the user performing the action
        menu_accessed: Description of the action performed
        details: Additional details about the action (optional)
    """
    try:
        # Get more detailed information about the request
        user_agent = request.headers.get('User-Agent', 'Unknown')
        method = request.method
        endpoint = request.endpoint
        
        # Create a more detailed activity description
        if endpoint in ['create_user', 'update_user', 'delete_user', 'toggle_user_status']:
            if details:
                action_details = f"User Management: {details}"
            else:
                action_details = f"User Management: {method} operation on {menu_accessed}"
                
        elif endpoint in ['add_server', 'edit_server', 'delete_server']:
            if details:
                action_details = f"Database Server: {details}"
            else:
                action_details = f"Database Server: {method} operation on {menu_accessed}"
                
        elif endpoint == 'query_history':
            if details:
                action_details = f"Query History: {details}"
            else:
                action_details = f"Query History: Viewed {menu_accessed}"
                
        elif endpoint == 'activity_logs':
            if details:
                action_details = f"Activity Logs: {details}"
            else:
                action_details = f"Activity Logs: Viewed logs"
                
        elif endpoint == 'index':
            action_details = "Dashboard: Viewed main dashboard"
            
        else:
            action_details = f"{method} {menu_accessed}"
            if details:
                action_details += f" - {details}"
        
        activity = ActivityLog(
            user_id=user_id,
            access_ip=request.remote_addr,
            menu_accessed=action_details,
            access_time=datetime.now(),
            user_agent=user_agent
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error logging activity: {str(e)}")

@app.route('/')
@login_required
def index():
    log_activity(current_user.id, 'dashboard')
    servers = DatabaseServer.query.all()
    return render_template('index.html', servers=servers)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # Check if user is active before allowing login
            if not user.is_active:
                flash('User telah dinonaktifkan, segera hubungi admin', 'danger')
                return render_template('login.html')
            
            login_user(user)
            log_activity(user.id, 'login')
            return redirect(url_for('index'))
        
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_activity(current_user.id, 'logout')
    logout_user()
    return redirect(url_for('login'))

@app.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('Unauthorized access')
        return redirect(url_for('index'))
    
    log_activity(current_user.id, 'user management')
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/activity_logs')
@login_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    export = request.args.get('export', False, type=bool)
    per_page = 20  # Increased from 10 to show more logs per page

    # Create base query
    query = ActivityLog.query

    # If user is not admin, only show their own logs
    if current_user.role != 'admin':
        query = query.filter_by(user_id=current_user.id)

    # Order by access_time descending
    query = query.order_by(ActivityLog.access_time.desc())

    if export:
        # Get all logs for export
        logs = query.all()
        
        # Create CSV in memory
        si = StringIO()
        cw = csv.writer(si)
        
        # Write headers with more details
        headers = ['Time', 'User', 'IP Address', 'Action', 'Browser/Client']
        cw.writerow(headers)
        
        # Write data
        for log in logs:
            row = [
                log.access_time.strftime('%Y-%m-%d %H:%M:%S'),  # Local time
                log.user.username,
                log.access_ip,
                log.menu_accessed,
                log.user_agent
            ]
            cw.writerow(row)
        
        output = si.getvalue()
        si.close()
        
        # Generate filename with timestamp
        filename = f'activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Create the response
        response = make_response(output)
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        response.headers['Content-type'] = 'text/csv'
        return response
    
    # Paginate for normal view
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    logs = pagination.items
    total_pages = pagination.pages

    return render_template('activity_logs.html', 
                         logs=logs, 
                         page=page, 
                         total_pages=total_pages,
                         max=max,
                         min=min)

@app.route('/query_history')
@login_required
def query_history():
    # Get search parameters
    server_id = request.args.get('server', type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    export = request.args.get('export', type=int)

    # Base query
    query = QueryHistory.query

    # Apply filters
    if server_id:
        query = query.filter_by(server_id=server_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(QueryHistory.query_text.ilike(f'%{search}%'))

    # Order by start time descending
    query = query.order_by(QueryHistory.start_time.desc())

    # Get all database servers for the filter dropdown
    servers = DatabaseServer.query.all()

    if export:
        # Get all matching queries for export
        queries = query.all()
        
        # Create CSV
        si = StringIO()
        cw = csv.writer(si)
        
        # Write headers
        headers = ['Server', 'Database', 'Username', 'Query', 'Status', 'Start Time', 'End Time', 'Execution Time (s)']
        cw.writerow(headers)
        
        # Write data
        for query in queries:
            row = [
                query.server.name,
                query.database_name,
                query.username,
                query.query_text,
                query.status,
                query.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                query.end_time.strftime('%Y-%m-%d %H:%M:%S') if query.end_time else '',
                f'{query.execution_time:.2f}' if query.execution_time else ''
            ]
            cw.writerow(row)
        
        output = si.getvalue()
        si.close()
        
        # Create the response
        response = make_response(output)
        response.headers['Content-Disposition'] = 'attachment; filename=query_history.csv'
        response.headers['Content-type'] = 'text/csv'
        return response
    
    # Get paginated queries for display
    page = request.args.get('page', 1, type=int)
    queries = query.paginate(page=page, per_page=50)
    
    return render_template('query_history.html', queries=queries, servers=servers)

@app.route('/database_servers')
@login_required
def database_servers():
    log_activity(current_user.id, 'database servers')
    servers = DatabaseServer.query.all()
    return render_template('database_servers.html', servers=servers)

@app.route('/add_server', methods=['GET', 'POST'])
@login_required
def add_server_page():
    if request.method == 'POST':
        try:
            # Create new server
            server = DatabaseServer(
                name=request.form['name'],
                db_type=request.form['db_type'],
                host=request.form['host'],
                port=int(request.form['port']),
                username=request.form['username'],
                password=request.form['password']
            )
            
            # Test connection
            if not server.test_connection():
                flash('Could not connect to database server. Please check your credentials.', 'error')
                return render_template('add_server.html')
            
            # Save to database
            db.session.add(server)
            db.session.commit()
            
            # Log the activity
            log_activity(current_user.id, "servers", f"Added new database server: {server.name} ({server.host}:{server.port})")
            
            flash('Database server added successfully!', 'success')
            return redirect(url_for('database_servers'))
            
        except Exception as e:
            flash(f'Error adding server: {str(e)}', 'error')
            return render_template('add_server.html')
    
    return render_template('add_server.html')

@app.route('/api/servers', methods=['POST'])
@login_required
def add_server_api():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['name', 'db_type', 'host', 'port', 'username', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.title()} is required'}), 400
                
        # Check if server name already exists
        if DatabaseServer.query.filter_by(name=data['name'].strip()).first():
            return jsonify({'error': 'Server name already exists'}), 400
            
        # Validate db_type
        valid_db_types = ['postgresql', 'mysql', 'sqlserver', 'mariadb']
        if data['db_type'].strip().lower() not in valid_db_types:
            return jsonify({'error': 'Invalid db_type specified'}), 400
            
        server = DatabaseServer(
            name=data['name'].strip(),
            db_type=data['db_type'].strip(),
            host=data['host'].strip(),
            port=data['port'],
            username=data['username'].strip(),
            password=data['password']  # In production, this should be encrypted
        )
        
        # Test connection
        if not server.test_connection():
            return jsonify({'error': 'Could not connect to database server. Please check your credentials.'}), 400
        
        db.session.add(server)
        db.session.commit()
        
        # Log the activity
        log_activity(current_user.id, "servers", f"Added new database server: {server.name} ({server.host}:{server.port})")
        
        return jsonify({
            'id': server.id,
            'name': server.name,
            'host': server.host,
            'port': server.port,
            'username': server.username,
            'db_type': server.db_type
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/edit_server/<int:server_id>', methods=['GET', 'POST'])
@login_required
def edit_server_page(server_id):
    server = DatabaseServer.query.get_or_404(server_id)
    
    if request.method == 'POST':
        try:
            # Get old values for logging
            old_name = server.name
            old_host = server.host
            old_port = server.port
            
            # Update server
            server.name = request.form['name']
            server.db_type = request.form['db_type']
            server.host = request.form['host']
            server.port = int(request.form['port'])
            server.username = request.form['username']
            if request.form['password']:  # Only update password if provided
                server.password = request.form['password']
            
            # Test connection with new credentials
            if not server.test_connection():
                flash('Could not connect to database server. Please check your credentials.', 'error')
                return render_template('edit_server.html', server=server)
            
            # Save changes
            db.session.commit()
            
            # Log the activity with changes
            changes = []
            if old_name != server.name:
                changes.append(f"name from {old_name} to {server.name}")
            if old_host != server.host:
                changes.append(f"host from {old_host} to {server.host}")
            if old_port != server.port:
                changes.append(f"port from {old_port} to {server.port}")
            
            log_activity(current_user.id, "servers", f"Updated database server {server.name}: changed {', '.join(changes)}")
            
            flash('Database server updated successfully!', 'success')
            return redirect(url_for('database_servers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating server: {str(e)}', 'error')
            return render_template('edit_server.html', server=server)
    
    return render_template('edit_server.html', server=server)

@app.route('/api/servers/<int:server_id>', methods=['PUT'])
@login_required
def edit_server_api(server_id):
    try:
        server = DatabaseServer.query.get_or_404(server_id)
        data = request.json
        
        # Get old values for logging
        old_name = server.name
        old_host = server.host
        old_port = server.port
        
        # Update fields if provided
        if 'name' in data:
            # Check if new name already exists (excluding current server)
            existing = DatabaseServer.query.filter(
                DatabaseServer.name == data['name'].strip(),
                DatabaseServer.id != server_id
            ).first()
            if existing:
                return jsonify({'error': 'Server name already exists'}), 400
            server.name = data['name'].strip()
            
        if 'host' in data:
            server.host = data['host'].strip()
        if 'port' in data:
            server.port = data['port']
        if 'username' in data:
            server.username = data['username'].strip()
        if 'password' in data:
            server.password = data['password']
            
        # Test connection with new credentials
        if not server.test_connection():
            return jsonify({'error': 'Could not connect to database server with new credentials'}), 400
            
        # Save changes
        db.session.commit()
        
        # Log the activity with changes
        changes = []
        if old_name != server.name:
            changes.append(f"name from {old_name} to {server.name}")
        if old_host != server.host:
            changes.append(f"host from {old_host} to {server.host}")
        if old_port != server.port:
            changes.append(f"port from {old_port} to {server.port}")
        
        log_activity(current_user.id, "servers", f"Updated database server {server.name}: changed {', '.join(changes)}")
        
        return jsonify({
            'id': server.id,
            'name': server.name,
            'host': server.host,
            'port': server.port,
            'username': server.username
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/servers/<int:server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    try:
        server = DatabaseServer.query.get_or_404(server_id)
        server_name = server.name
        
        db.session.delete(server)
        db.session.commit()
        
        # Log the deletion
        log_activity(current_user.id, "servers", f"Deleted database server: {server_name}")
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active
    })

@app.route('/api/users', methods=['POST'])
@login_required
def create_user():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.title()} is required'}), 400
        
        # Validate field lengths
        if len(data['username']) < 3 or len(data['username']) > 80:
            return jsonify({'error': 'Username must be between 3 and 80 characters'}), 400
        
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            
        # Check if username already exists
        if User.query.filter_by(username=data['username'].strip()).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        # Check if email already exists
        if User.query.filter_by(email=data['email'].strip()).first():
            return jsonify({'error': 'Email already exists'}), 400
            
        # Validate role
        if data['role'] not in ['user', 'admin']:
            return jsonify({'error': 'Invalid role specified'}), 400
            
        user = User(
            username=data['username'].strip(),
            email=data['email'].strip(),
            role=data['role']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(current_user.id, "users", f"Created new user: {user.username} with role {user.role}")
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        # Store old values for logging
        old_username = user.username
        old_role = user.role
        
        # Validate required fields
        required_fields = ['username', 'email', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.title()} is required'}), 400
        
        # Validate field lengths
        if len(data['username']) < 3 or len(data['username']) > 80:
            return jsonify({'error': 'Username must be between 3 and 80 characters'}), 400
            
        # Validate role
        if data['role'] not in ['user', 'admin']:
            return jsonify({'error': 'Invalid role specified'}), 400
            
        # Check if username is being changed and if it's already taken
        if data['username'].strip() != user.username and User.query.filter_by(username=data['username'].strip()).first():
            return jsonify({'error': 'Username already exists'}), 400
            
        # Check if email is being changed and if it's already taken
        if data['email'].strip() != user.email and User.query.filter_by(email=data['email'].strip()).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Validate password if provided
        if data.get('password'):
            if len(data['password']) < 6:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            user.set_password(data['password'])
        
        user.username = data['username'].strip()
        user.email = data['email'].strip()
        user.role = data['role']
        
        db.session.commit()
        
        changes = []
        if old_username != user.username:
            changes.append(f"username from {old_username} to {user.username}")
        if old_role != user.role:
            changes.append(f"role from {old_role} to {user.role}")
        if data.get('password'):
            changes.append("password updated")
            
        log_activity(current_user.id, "users", f"Updated user {user.username}: {', '.join(changes)}")
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
            
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        log_activity(current_user.id, "users", f"Deleted user: {username}")
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    try:
        if current_user.id == user_id:
            return jsonify({'error': 'Cannot toggle your own account status'}), 400
            
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "activated" if user.is_active else "deactivated"
        log_activity(current_user.id, "users", f"{status.capitalize()} user: {user.username}")
        
        return jsonify({
            'success': True,
            'is_active': user.is_active
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
@login_required
def get_users():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active
    } for user in users])

@app.route('/api/metrics')
@login_required
def get_metrics():
    db_id = request.args.get('db_id', 'all')
    print(f"Fetching metrics for db_id: {db_id}")
    
    try:
        if db_id == 'all':
            servers = DatabaseServer.query.all()
        else:
            servers = [DatabaseServer.query.get_or_404(int(db_id))]
        
        all_metrics = []
        
        for server in servers:
            server_metrics = {
                'id': server.id,
                'name': server.name,
                'type': server.db_type,
                'host': server.host,
                'port': server.port,
                'status': 'error',
                'error': None,
                'metrics': None,
                'queries': []
            }
            
            try:
                config = {
                    'db_type': server.db_type,
                    'host': server.host,
                    'port': server.port,
                    'database': 'postgres' if server.db_type == 'postgresql' else 'mysql',
                    'username': server.username,
                    'password': server.password
                }
                
                print(f"Connecting to server {server.name} ({server.db_type})")
                monitor = DatabaseMonitor(config)
                monitor.connect()
                
                # Get metrics
                metrics = monitor.get_performance_metrics()
                active_queries = monitor.get_active_queries()
                
                server_metrics['status'] = 'connected'
                server_metrics['metrics'] = metrics
                server_metrics['queries'] = active_queries
                
                # Update server status in database
                server.last_check = datetime.now(timezone.utc)
                server.last_error = None
                db.session.commit()
                
            except Exception as e:
                error_msg = str(e)
                print(f"Error collecting metrics from {server.name}: {error_msg}")
                server_metrics['error'] = error_msg
                
                # Update server status in database
                server.last_check = datetime.now(timezone.utc)
                server.last_error = error_msg
                db.session.commit()
            
            all_metrics.append(server_metrics)
        
        return jsonify({
            'status': 'success',
            'servers': all_metrics
        })
        
    except Exception as e:
        print(f"Error in get_metrics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/server/<int:server_id>/metrics')
@login_required
def server_metrics(server_id):
    try:
        server = DatabaseServer.query.get_or_404(server_id)
        
        # Get server metrics
        config = {
            'db_type': server.db_type,
            'host': server.host,
            'port': server.port,
            'database': 'postgres' if server.db_type == 'postgresql' else 'master',
            'username': server.username,
            'password': server.password
        }
        
        monitor = DatabaseMonitor(config)
        monitor.connect()  # Need to connect first
        metrics = monitor.get_performance_metrics()
        active_queries = monitor.get_active_queries()
        monitor.close()
        
        return jsonify({
            'cpu_percent': metrics.get('cpu_percent', 0),
            'memory_percent': metrics.get('memory_percent', 0),
            'disk_usage': metrics.get('disk_usage', 0),
            'active_connections': metrics.get('active_connections', 0),
            'active_queries': active_queries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query_history', methods=['POST'])
@login_required
def add_query():
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['server_id', 'query_text']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.title()} is required'}), 400
                
        # Get server details for logging
        server = DatabaseServer.query.get_or_404(data['server_id'])
        
        query = QueryHistory(
            user_id=current_user.id,
            server_id=data['server_id'],
            query_text=data['query_text'],
            execution_time=data.get('execution_time', 0),
            status=data.get('status', 'completed'),
            error_message=data.get('error_message', '')
        )
        
        db.session.add(query)
        db.session.commit()
        
        # Log the activity with query details
        status_text = "successfully" if query.status == 'completed' else "with errors"
        log_activity(current_user.id, "query_history", 
                    f"Executed query on {server.name}: {query.query_text[:50]}... ({status_text})")
        
        return jsonify({
            'id': query.id,
            'query_text': query.query_text,
            'execution_time': query.execution_time,
            'status': query.status,
            'error_message': query.error_message
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/query_history/<int:query_id>', methods=['DELETE'])
@login_required
def delete_query(query_id):
    try:
        query = QueryHistory.query.get_or_404(query_id)
        
        # Get server name for logging
        server = DatabaseServer.query.get(query.server_id)
        server_name = server.name if server else "Unknown Server"
        
        # Store query details for logging
        query_preview = query.query_text[:50]
        
        db.session.delete(query)
        db.session.commit()
        
        # Log the deletion
        log_activity(current_user.id, "query_history", 
                    f"Deleted query from {server_name}: {query_preview}...")
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/query_history/clear', methods=['POST'])
@login_required
def clear_query_history():
    try:
        # Get count of queries to be deleted
        query_count = QueryHistory.query.filter_by(user_id=current_user.id).count()
        
        # Delete all queries for current user
        QueryHistory.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        # Log the clear action
        log_activity(current_user.id, "query_history", 
                    f"Cleared query history ({query_count} queries deleted)")
        
        return jsonify({'success': True, 'count': query_count})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.cli.command("create-admin")
def create_admin():
    """Create an admin user."""
    username = os.getenv('ADMIN_USERNAME', 'admin')
    password = os.getenv('ADMIN_PASSWORD', 'change-this-password')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')

    # Check if admin already exists
    if User.query.filter_by(username=username).first():
        print("Admin user already exists")
        return

    # Create admin user
    user = User(
        username=username,
        email=email,
        role='admin'
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Admin user created: {username}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
