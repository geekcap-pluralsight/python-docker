import logging
from db import db

log = logging.getLogger(__name__)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @classmethod
    def find_by_id(cls, _id):
        log.debug(f'Find product by id: {_id}')
        return cls.query.get(_id)

    @classmethod
    def find_all(cls):
        log.debug('Query for all products')
        return cls.query.all()

    def save_to_db(self):
        log.debug(f'Save Product to database: id= {self.id}, name={self.name}')
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        log.debug(f'Delete Product from database: id= {self.id}, name={self.name}')
        db.session.delete(self)
        db.session.commit()

    @property
    def json(self):
        return {
            "id": self.id,
            "name": self.name
        }
