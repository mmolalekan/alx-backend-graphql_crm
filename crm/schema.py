from crm.models import Product

# Mutation for updating low-stock products
class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        # Use Product from crm.models
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)
        msg = f"Updated {len(updated)} products."
        return UpdateLowStockProducts(updated_products=updated, message=msg)
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
import re

# import Product for UpdateLowStockProducts
from crm.models import Product

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)

# Mutation for updating low-stock products
class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        # Use Product from crm.models
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)
        msg = f"Updated {len(updated)} products."
        return UpdateLowStockProducts(updated_products=updated, message=msg)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customerId = graphene.Int(required=True)
    productIds = graphene.List(graphene.Int, required=True)
    orderDate = graphene.DateTime()

# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def validate_phone(phone):
        if not phone:
            return True
        pattern = r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$'
        return re.match(pattern, phone)

    @classmethod
    def mutate(cls, root, info, input):
        if Customer.objects.filter(email=input.email).exists():
            return CreateCustomer(customer=None, message="Email already exists")
        if input.phone and not cls.validate_phone(input.phone):
            return CreateCustomer(customer=None, message="Invalid phone format")
        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone
        )
        return CreateCustomer(customer=customer, message="Customer created")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, input):
        created = []
        errors = []
        for idx, data in enumerate(input):
            if Customer.objects.filter(email=data.email).exists():
                errors.append(f"Email already exists for {data.email}")
                continue
            if data.phone and not CreateCustomer.validate_phone(data.phone):
                errors.append(f"Invalid phone format for {data.phone}")
                continue
            customer = Customer.objects.create(
                name=data.name,
                email=data.email,
                phone=data.phone
            )
            created.append(customer)
        return BulkCreateCustomers(customers=created, errors=errors)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        if input.price <= 0:
            return CreateProduct(product=None, message="Price must be positive")
        if input.stock is not None and input.stock < 0:
            return CreateProduct(product=None, message="Stock cannot be negative")
        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock if input.stock is not None else 0
        )
        return CreateProduct(product=product, message="Product created")

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info, input):
        try:
            customer = Customer.objects.get(pk=input.customerId)
        except Customer.DoesNotExist:
            return CreateOrder(order=None, message="Invalid customer ID")
        if not input.productIds:
            return CreateOrder(order=None, message="At least one product must be selected")
        products = Product.objects.filter(pk__in=input.productIds)
        if products.count() != len(input.productIds):
            return CreateOrder(order=None, message="One or more product IDs are invalid")
        total = sum([p.price for p in products])
        order = Order.objects.create(
            customer=customer,
            total_amount=total,
            order_date=input.orderDate if input.orderDate else timezone.now()
        )
        order.products.set(products)
        return CreateOrder(order=order, message="Order created")

# Query
class Query(graphene.ObjectType):
    hello = graphene.String()
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter, order_by=graphene.List(graphene.String))
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter, order_by=graphene.List(graphene.String))
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter, order_by=graphene.List(graphene.String))

    def resolve_hello(root, info):
        return "Hello, GraphQL!"

# Mutation
class Mutation(graphene.ObjectType):
    createCustomer = CreateCustomer.Field()
    bulkCreateCustomers = BulkCreateCustomers.Field()
    createProduct = CreateProduct.Field()
    createOrder = CreateOrder.Field()
    updateLowStockProducts = UpdateLowStockProducts.Field()

# Mutation for updating low-stock products
# Mutation for updating low-stock products
class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        # Use Product from crm.models
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)
        msg = f"Updated {len(updated)} products."
        return UpdateLowStockProducts(updated_products=updated, message=msg)
class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @classmethod
    def mutate(cls, root, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated.append(product)
        msg = f"Updated {len(updated)} products."
        return UpdateLowStockProducts(updated_products=updated, message=msg)
schema = graphene.Schema(query=Query, mutation=Mutation)
