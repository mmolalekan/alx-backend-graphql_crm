import re
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.utils import timezone
from .models import Customer, Product, Order


# ---------- GRAPHQL TYPES ----------
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "total_amount", "order_date")


# ---------- QUERY ----------
class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    all_products = graphene.List(ProductType)
    all_orders = graphene.List(OrderType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()

    def resolve_all_products(root, info):
        return Product.objects.all()

    def resolve_all_orders(root, info):
        return Order.objects.all()


# ---------- MUTATIONS ----------
# Create Customer
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

    def mutate(self, info, name, email, phone=None):
        errors = []

        # Validate unique email
        if Customer.objects.filter(email=email).exists():
            errors.append("Email already exists")

        # Validate phone
        if phone and not re.match(r"^\+?\d[\d\-]{7,}$", phone):
            errors.append("Invalid phone format (use +1234567890 or 123-456-7890)")

        if errors:
            return CreateCustomer(customer=None, message="Validation failed", errors=errors)

        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully", errors=[])


# Bulk Create Customers
class BulkCreateCustomers(graphene.Mutation):
    class CustomerInput(graphene.InputObjectType):
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for i, data in enumerate(input):
            try:
                # Validate email
                if Customer.objects.filter(email=data.email).exists():
                    raise ValueError(f"Duplicate email: {data.email}")

                # Validate phone format
                if data.phone and not re.match(r"^\+?\d[\d\-]{7,}$", data.phone):
                    raise ValueError(f"Invalid phone format for {data.email}")

                c = Customer(name=data.name, email=data.email, phone=data.phone)
                c.save()
                created_customers.append(c)

            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")

        return BulkCreateCustomers(customers=created_customers, errors=errors)


# Create Product
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False, default_value=0)

    product = graphene.Field(ProductType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, name, price, stock=0):
        errors = []
        if price <= 0:
            errors.append("Price must be positive")
        if stock < 0:
            errors.append("Stock cannot be negative")

        if errors:
            return CreateProduct(product=None, errors=errors)

        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product, errors=[])


# Create Order
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.DateTime(required=False)

    order = graphene.Field(OrderType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        errors = []

        # Validate customer
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            errors.append("Invalid customer ID")
            return CreateOrder(order=None, errors=errors)

        # Validate products
        if not product_ids:
            errors.append("At least one product must be provided")
            return CreateOrder(order=None, errors=errors)

        products = Product.objects.filter(id__in=product_ids)
        if len(products) != len(product_ids):
            errors.append("Some product IDs are invalid")
            return CreateOrder(order=None, errors=errors)

        # Calculate total
        total_amount = sum(p.price for p in products)

        order = Order(
            customer=customer,
            total_amount=total_amount,
            order_date=order_date or timezone.now()
        )
        order.save()
        order.products.set(products)

        return CreateOrder(order=order, errors=[])


# ---------- ROOT MUTATION ----------
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()

