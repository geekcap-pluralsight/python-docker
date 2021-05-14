from flask import Flask, jsonify, request
import logging.config
from sqlalchemy import exc
import configparser
import debugpy
import os
from db import db
from Product import Product


# Configure the logging package from the logging ini file; defined as an environment variable
logging.config.fileConfig('/config/logging.ini',
                          disable_existing_loggers=False)

# Get a logger for our module
log = logging.getLogger(__name__)

# Setup debugger
debug = os.getenv('DEBUG', 'False')
if debug == 'True':
    debugpy.listen(("0.0.0.0", 5678))
    log.info('Started debugger on port 5678')


def get_database_url():
    """
    Loads the database configuration from the db.ini file and returns
    a database URL.
    :return: A database URL, built from values in the db.ini file
    """
    # Load our database configuration
    config = configparser.ConfigParser()
    config.read('/config/db.ini')
    database_configuration = config['mysql']
    host = database_configuration['host']
    username = database_configuration['username']
    db_password = open('/run/secrets/db_password')
    password = db_password.read()
    database = database_configuration['database']
    database_url = f'mysql://{username}:{password}@{host}/{database}'
    log.info(f'Connecting to database: {database_url}')
    return database_url


# Configure Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
db.init_app(app)


# curl -v http://localhost:5000/products
@app.route('/products')
def get_products():
    log.debug('GET /products')
    try:
        products = [product.json for product in Product.find_all()]
        return jsonify(products)
    except exc.SQLAlchemyError:
        log.exception('An exception occurred while retrieving all products')
        return 'An exception occurred while retrieving all products', 500


# curl -v http://localhost:5000/product/1
@app.route('/product/<int:id>')
def get_product(id):
    log.debug(f'GET /product/{id}')

    try:
        product = Product.find_by_id(id)
        if product:
            return jsonify(product.json)
        log.warning(f'GET /product/{id}: Product not found')
        return f'Product with id {id} not found', 404
    except exc.SQLAlchemyError:
        log.exception(f'An exception occurred while retrieving product {id}')
        return f'An exception occurred while retrieving product {id}', 500


# curl --header "Content-Type: application/json" --request POST --data '{"name": "Product 3"}' -v http://localhost:5000/product
@app.route('/product', methods=['POST'])
def post_product():

    # Retrieve the product from the request body
    request_product = request.json
    log.debug(f'POST /products with product: {request_product}')

    # Create a new Product
    product = Product(None, request_product['name'])

    try:
        # Save the Product to the database
        product.save_to_db()

        # Return the jsonified Product
        return jsonify(product.json), 201
    except exc.SQLAlchemyError:
        log.exception(
            f'An exception occurred while creating product with name: {product.name}')
        return f'An exception occurred while creating product with name: {product.name}', 500


# curl --header "Content-Type: application/json" --request PUT --data '{"name": "Updated Product 2"}' -v http://localhost:5000/product/2
@app.route('/product/<int:id>', methods=['PUT'])
def put_product(id):
    log.debug(f'PUT /product/{id}')
    try:
        existing_product = Product.find_by_id(id)

        if existing_product:
            # Get the request payload
            updated_product = request.json

            existing_product.name = updated_product['name']
            existing_product.save_to_db()

            return jsonify(existing_product.json), 200

        log.warning(f'PUT /product/{id}: Existing product not found')
        return f'Product with id {id} not found', 404

    except exc.SQLAlchemyError:
        log.exception(
            f'An exception occurred while updating product with name: {updated_product.name}')
        return f'An exception occurred while updating product with name: {updated_product.name}', 500


# curl --request DELETE -v http://localhost:5000/product/2
@app.route('/product/<int:id>', methods=['DELETE'])
def delete_product(id):
    log.debug(f'DELETE /product/{id}')
    try:
        existing_product = Product.find_by_id(id)
        if existing_product:
            existing_product.delete_from_db()
            return jsonify({
                'message': f'Deleted product with id {id}'
            }), 200

        log.warning(f'DELETE /product/{id}: Existing product not found')
        return f'Product with id {id} not found', 404

    except exc.SQLAlchemyError:
        log.exception(
            f'An exception occurred while deleting the product with id: {id}')
        return f'An exception occurred while deleting the product with id: {id}', 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
