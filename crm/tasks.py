from celery import shared_task
from datetime import datetime
import requests

@shared_task
def generate_crm_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = '/tmp/crm_report_log.txt'
    query = '''
    query {
      customers { id }
      orders { id totalAmount }
    }
    '''
    try:
        response = requests.post(
            'http://localhost:8000/graphql',
            json={'query': query}
        )
        if response.status_code == 200:
            data = response.json().get('data', {})
            customers = data.get('customers', [])
            orders = data.get('orders', [])
            total_customers = len(customers)
            total_orders = len(orders)
            total_revenue = sum([o.get('totalAmount', 0) for o in orders])
            with open(log_file, 'a') as f:
                f.write(f"{now} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n")
        else:
            with open(log_file, 'a') as f:
                f.write(f"{now} Error: Could not reach GraphQL endpoint\n")
    except Exception as e:
        with open(log_file, 'a') as f:
            f.write(f"{now} Exception: {e}\n")
