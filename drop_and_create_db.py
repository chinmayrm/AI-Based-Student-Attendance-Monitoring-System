from app import db

def reset_db():
    from app import app
    with app.app_context():
        db.drop_all()
        db.create_all()
        print('Database dropped and recreated.')

if __name__ == '__main__':
    reset_db()
