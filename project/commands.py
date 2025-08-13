import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from .db import db
from .models import WebUser

@click.command('add-user')
@click.argument('username')
@click.argument('password')
@with_appcontext
def add_user_command(username, password):
    """Creates a new web user or updates password."""
    user = WebUser.query.filter_by(username=username).first()
    if user:
        user.password_hash = generate_password_hash(password)
        click.echo(f"Updated user '{username}'.")
    else:
        new_user = WebUser(username=username, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        click.echo(f"Created user '{username}'.")
    db.session.commit()
