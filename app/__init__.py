from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirect to login page if not authenticated
    login_manager.login_message_category = 'info' # Flash message category

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User # Has to be here to avoid circular import.
        return User.query.get(int(user_id))
    
    # Add template globals. This is a way to make variables available in all templates without passing them explicitly.
    # Also allows for use in jinja.
    @app.context_processor
    def inject_globals():
        return {
            'ADMIN_EMAIL': app.config['ADMIN_EMAIL']
        }

    # Register blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    
    return app