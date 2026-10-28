from contract.authentication import issue_session
from django.core.signals import request_finished
from django.db import close_old_connections


def close_download(response):
    """Match Django's streaming-test cleanup without closing an outer TestCase transaction."""
    if response.closed:
        return
    request_finished.disconnect(close_old_connections)
    try:
        response.close()
    finally:
        request_finished.connect(close_old_connections)


def authenticate_session(client, user):
    session, access, _ = issue_session(user)
    client.force_authenticate(user, token=session)
    return session


def grant_headers(client, kind, agreement_id, order_id=None, scope='agreement'):
    response = client.post('/api/files/grants/', {
        'kind': kind, 'agreementId': agreement_id, 'orderId': order_id, 'scope': scope,
    }, format='json')
    assert response.status_code == 200, response.data
    return {'HTTP_X_DOWNLOAD_GRANT': response.data['data']['grant']}
