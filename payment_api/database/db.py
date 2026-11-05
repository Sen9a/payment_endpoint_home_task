"""Engine + scoped-session wiring — pure SQLAlchemy 2.0, no Flask extension."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

# Scoped to the thread/greenlet; managers import and use it directly.
# Bound to an engine in init_db(). expire_on_commit=False keeps committed
# objects readable after the session is removed at request teardown.
db_session = scoped_session(sessionmaker(expire_on_commit=False))


class Base(DeclarativeBase):

    def update_field(self, name, value):
        """Update an attribute if it exists."""
        if hasattr(self, name):
            setattr(self, name, value)

    def to_dict(self):
        """Return model's dictionary representation."""
        columns = self.__table__.columns
        return {column.name: getattr(self, column.name) for column in columns}


def init_db(flask_app) -> None:
    engine = create_engine(flask_app.config['DATABASE_URI'])
    db_session.configure(bind=engine)
    flask_app.extensions['engine'] = engine

    @flask_app.teardown_appcontext
    def remove_session(_exc=None):
        db_session.remove()
