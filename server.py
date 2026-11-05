"""Development entry point: `python server.py`."""
from os import environ as env

from payment_api.app import create_connexion_app

connexion_app = create_connexion_app()

if __name__ == '__main__':
    connexion_app.run(host='0.0.0.0', port=int(env.get('PORT', 8080)))
