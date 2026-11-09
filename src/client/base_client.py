
import logging
import requests

logger = logging.getLogger(__name__)

class TokenManager:
    def __init__(self, client, api):
        self.client = client
        self.api = api
        self.token = None

        self.TOKEN_URL = api.token_url
        self.TOKEN_DATA = api.token_data
        self.TOKEN_HEADERS = api.token_headers

    def get_token(self):
        return self.token

    def is_token_valid(self, response):
        status = response.status_code
        if status == 401:
            return False
        return True

    def generate_token(self):
        try:
            access_token_response = requests.post(
                self.TOKEN_URL, 
                data=self.TOKEN_DATA, 
                allow_redirects=False, 
                headers=self.TOKEN_HEADERS,
                timeout= 30
            )
            access_token_response.raise_for_status()
            self.token = access_token_response.json()['access_token']
            logger.info("Access token obtained successfully")
        except Exception as e:
            logger.error(f"Error obtaining token: {e}")
            logger.error(f"Response: {access_token_response.text if access_token_response else 'No response'}")
            raise

    def there_is_a_token(self):
        return self.client.session.headers.get('Authorization') is not None

    def token_headers(self):
        return {'Authorization': 'Bearer ' + self.token}

class BaseClient(object):

    def __init__(self, api):
        self.api = api
        self.session = requests.Session()
        self.session.headers.update(api.accept_header)
        # Ask the server to close the connection after each response.
        self.session.headers.update({"Connection": "close"})

        logger.info("Client initialized for API: %s with endpoint: %s", api.name, api.full_url)
        self.token_manager = TokenManager(self, api)
        logger.info("TokenManager initialized with API: %s", api.name) 

    def update_headers_with_token(self):
        self.session.headers.update({'Authorization': 'Bearer ' + self.token_manager.token})
        logger.info("Session headers updated with new token")

    def request(self, params):
        """Send an authenticated GET request using the endpoint parameters."""
        url = self.api.full_url
        logger.info("Sending request to %s with params %s", url, params)

        if not self.token_manager.there_is_a_token():
            logger.info("No token found, generating a new one")
            self.token_manager.generate_token()
            self.update_headers_with_token()
        self.response = self.session.request(
            'GET', url, params=params, timeout=self.api.timeout
        )
        if not self.token_manager.is_token_valid(self.response):
            logger.warning("Token expired, regenerating token and retrying request")
            self.token_manager.generate_token()
            self.update_headers_with_token()
            self.response = self.session.request(
                'GET', url, params=params, timeout=self.api.timeout
            )
        logger.info("Request completed with status code %s", self.response.status_code)
        return self.response