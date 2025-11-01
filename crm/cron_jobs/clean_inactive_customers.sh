#!/bin/bash
# Delete customers with no orders in the past year and log the result

LOG_FILE="/tmp/customer_cleanup_log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

DELETED_COUNT=$(python3 manage.py shell << END
from crm.models import Customer, Order
from django.utils import timezone
from datetime import timedelta
one_year_ago = timezone.now() - timedelta(days=365)
qs = Customer.objects.exclude(order__order_date__gte=one_year_ago)
count = qs.count()
qs.delete()
print(count)
END
)

# Log the result with timestamp
echo "$TIMESTAMP Deleted customers: $DELETED_COUNT" >> "$LOG_FILE"
