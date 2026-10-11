import os

from app import app, init_db_if_empty

application = app


if __name__ == '__main__':
    init_db_if_empty()
    from waitress import serve

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5000'))
    serve(application, host=host, port=port)
