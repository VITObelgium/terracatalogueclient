import requests.auth, requests.models
from requests_auth import OAuth2AuthorizationCodePKCE, OAuth2ResourceOwnerPasswordCredentials


class NoAuth(requests.auth.AuthBase):
    def __call__(self, r: requests.models.PreparedRequest) -> requests.models.PreparedRequest:
        # passing the Authorization header with the Bearer keyword without an actual token will result
        # in a HTTP 401 response code instead of a redirect on a request for which authentication is required
        r.headers['Authorization'] = "Bearer"
        return r


def resource_owner_password_credentials_grant(
        username: str, password: str, client_id: str, client_secret: str, token_url: str
) -> OAuth2ResourceOwnerPasswordCredentials:
    auth = OAuth2ResourceOwnerPasswordCredentials(token_url=token_url, username=username, password=password, client_id=client_id, client_secret=client_secret)
    # explicitly remove authorization header from request, otherwise both the header and body contain authorization
    # information causing the request to WekEO WSO2 IdP (as used in HRVPP project) to fail with a 400 error (bad request)
    auth.session.auth = None
    return auth


def authorization_code_grant(
        authorization_url: str, token_url: str, client_id: str
) -> OAuth2AuthorizationCodePKCE:
    return OAuth2AuthorizationCodePKCE(authorization_url=authorization_url, token_url=token_url, client_id=client_id)