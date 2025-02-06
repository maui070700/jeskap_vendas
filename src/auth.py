import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

def setup_authenticator():
    config_file = 'config.yaml'
    with open(config_file) as file:
        config = yaml.load(file, Loader=SafeLoader)

    updated, config = hash_passwords_if_needed(config)

    if updated:
        with open(config_file, 'w') as file:
            yaml.dump(config, file)

    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

def hash_passwords_if_needed(config):
    updated = False
    for username, user_data in config['credentials']['usernames'].items():
        if not user_data['password'].startswith('$2b$'):
            hashed_password = stauth.Hasher([user_data['password']]).generate()[0]
            config['credentials']['usernames'][username]['password'] = hashed_password
            updated = True
    return updated, config

def handle_login(authenticator):
    authenticator.login(fields={"Form name": "", "Username": "Usuário", "Password": "Senha", "Login": "Entrar"})

def handle_logout(authenticator):
    authenticator.logout("Sair")