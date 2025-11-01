
import datetime
from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client

def log_crm_heartbeat():
    now = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
    log_line = f"{now} CRM is alive\n"
    with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
        f.write(log_line)
    # Query GraphQL hello field to verify endpoint
    try:
        transport = RequestsHTTPTransport(url='http://localhost:8000/graphql', verify=False)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql('{ hello }')
        result = client.execute(query)
        with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
            f.write(f"{now} GraphQL hello: {result.get('hello', 'No response')}\n")
    except Exception as e:
        with open('/tmp/crm_heartbeat_log.txt', 'a') as f:
            f.write(f"{now} GraphQL hello error: {e}\n")

def update_low_stock():
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = '/tmp/low_stock_updates_log.txt'
        mutation = '''
        mutation {
            updateLowStockProducts {
                updatedProducts {
                    name
                    stock
                }
                message
            }
        }
        '''
        try:
                response = requests.post(
                        'http://localhost:8000/graphql',
                        json={'query': mutation}
                )
                if response.status_code == 200:
                        data = response.json()
                        updates = data.get('data', {}).get('updateLowStockProducts', {})
                        products = updates.get('updatedProducts', [])
                        with open(log_file, 'a') as f:
                                for product in products:
                                        f.write(f"{now} Updated: {product['name']} New stock: {product['stock']}\n")
                else:
                        with open(log_file, 'a') as f:
                                f.write(f"{now} Error: Could not reach GraphQL endpoint\n")
        except Exception as e:
                with open(log_file, 'a') as f:
                        f.write(f"{now} Exception: {e}\n")
