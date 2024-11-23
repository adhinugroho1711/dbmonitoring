from app import app, db

with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create admin user
    from app import User
    admin = User(
        username='admin',
        email='admin@example.com',
        role='admin',
        is_active=True
    )
    admin.set_password('admin')
    db.session.add(admin)
    db.session.commit()
    print("Database recreated and admin user created successfully!")
