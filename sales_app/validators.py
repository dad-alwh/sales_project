import re
from .models import User, Role, Customer, Product, Invoice

class BaseValidator:
    """
    (data types - min&max length - unique - required - data format)
    """
    def __init__(self, data):
        self.data = data
        self.errors = {}

    def add_error(self, field, message):
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)

    def check_required(self, fields):
        for field in fields:
            value = self.data.get(field)
            if value is None or value == "":
                self.add_error(field, "This field is required.")

    def check_length(self, field, min_len=None, max_len=None):
        value = self.data.get(field)
        if value and isinstance(value, str):
            if min_len and len(value) < min_len:
                self.add_error(field, f"Length must be at least {min_len}.")
            if max_len and len(value) > max_len:
                self.add_error(field, f"Length must not exceed {max_len}.")

    def check_email_format(self, field):
        email = self.data.get(field)
        if email:
            regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
            if not re.match(regex, email):
                self.add_error(field, "Invalid email format.")

    def check_positive_number(self, field):
        value = self.data.get(field)
        if value is not None:
            try:
                val = float(value)
                if val < 0:
                    self.add_error(field, "Must be a positive number.")
            except (ValueError, TypeError):
                self.add_error(field, "Must be a valid number.")

    def check_unique(self, model, field, exclude_id=None):
        value = self.data.get(field)
        if value:
            query = {field: value}
            qs = model.objects.filter(**query)
            if exclude_id:
                qs = qs.exclude(id=exclude_id)
            
            if qs.exists():
                self.add_error(field, f"This {field} already exists.")

    def is_valid(self):
        self.validate() 
        return len(self.errors) == 0


class UserValidator(BaseValidator):
    def validate(self):
        self.check_required(['name', 'email', 'password', 'role_id'])
        self.check_email_format('email')
        self.check_unique(User, 'email')
        self.check_length('name', min_len=3, max_len=50)
        self.check_length('password', min_len=6)
        role_id = self.data.get('role_id')
        if role_id and not Role.objects.filter(id=role_id).exists():
            self.add_error('role_id', "Role does not exist.")


class ProductValidator(BaseValidator):
    def validate(self):
        self.check_required(['name', 'price', 'quantity'])
        self.check_unique(Product, 'name')
        self.check_positive_number('price')
        self.check_positive_number('quantity')


class CustomerValidator(BaseValidator):
    def validate(self):
        self.check_required(['name', 'email', 'mobile'])
        self.check_email_format('email')
        self.check_unique(Customer, 'email')
        self.check_unique(Customer, 'mobile')


class InvoiceValidator(BaseValidator):
    def validate(self):
        self.check_required(['customer_id', 'items'])
        
        items = self.data.get('items')
        if items and isinstance(items, list):
            if len(items) == 0:
                self.add_error('items', "Invoice must have at least one product.")
            
            for index, item in enumerate(items):
                if 'product_id' not in item or 'quantity' not in item:
                    self.add_error(f'item_{index}', "Product ID and Quantity are required.")
                else:
                    prod = Product.objects.filter(id=item['product_id']).first()
                    if not prod:
                        self.add_error(f'item_{index}', "Product not found.")
                    elif prod.quantity < int(item['quantity']):
                        self.add_error(f'item_{index}', f"Not enough quantity for {prod.name}. Available: {prod.quantity}")