import requests
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/order_reminders_log.txt"
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

# Set up GraphQL client
transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, verify=False)
client = Client(transport=transport, fetch_schema_from_transport=True)

# Calculate date range for last 7 days
now = datetime.datetime.now()
week_ago = now - datetime.timedelta(days=7)

query = gql("""
query GetRecentOrders($from: DateTime!) {
  orders(orderDate_Gte: $from, status: "pending") {
    id
    customer {
      email
    }
    orderDate
  }
}
""")

params = {"from": week_ago.isoformat()}

try:
    result = client.execute(query, variable_values=params)
    orders = result.get("orders", [])
    with open(LOG_FILE, "a") as f:
        for order in orders:
            log_line = f"{now.strftime('%Y-%m-%d %H:%M:%S')} Order ID: {order['id']}, Email: {order['customer']['email']}\n"
            f.write(log_line)
    print("Order reminders processed!")
except Exception as e:
    print(f"Error: {e}")
