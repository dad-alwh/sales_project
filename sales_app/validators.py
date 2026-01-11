import re
from .models import User, Role, Customer, Product, Invoice

class BaseValidator:
    """
    Validation Layer: (data types - min&max length - unique - required - data format)
    """
    def __init__(self, data):
        self.data = data
        self.errors = {}
        self.exclude_id = None  

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
            
            actual_exclude_id = exclude_id or self.exclude_id
            if actual_exclude_id:
                qs = qs.exclude(id=actual_exclude_id)
            
            if qs.exists():
                self.add_error(field, f"This {field} already exists.")

    def is_valid(self, exclude_id=None):
        self.exclude_id = exclude_id
        self.validate() 
        return len(self.errors) == 0
    def validate(self):
        raise NotImplementedError("Subclasses must implement validate method.")

class UserValidator(BaseValidator):
    def validate(self):

        role_key = 'role' if 'role' in self.data else 'role_id'
        self.check_required(['name', 'email', 'password', role_key])
        self.check_email_format('email')
        self.check_unique(User, 'email')
        self.check_length('name', min_len=3, max_len=50)
        
        if not self.exclude_id or self.data.get('password'):
             self.check_length('password', min_len=6)
        
        role_val = self.data.get(role_key)
        if role_val and not Role.objects.filter(id=role_val).exists():
            self.add_error(role_key, "Role does not exist.")


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
        if items is not None and isinstance(items, list):
            if len(items) == 0:
                self.add_error('items', "Invoice must have at least one product.")

            for index, item in enumerate(items):
                if not isinstance(item, dict):
                     self.add_error(f'item_{index}', "Invalid item format.")
                     continue
                if 'product_id' not in item or 'quantity' not in item:
                    self.add_error(f'item_{index}', "Product ID and Quantity are required.")
                else:
                    prod = Product.objects.filter(id=item['product_id']).first()
                    if not prod:
                        self.add_error(f'item_{index}', "Product not found.")
                    else:
                        try:
                            qty = int(item['quantity'])
                            if qty <= 0:
                                self.add_error(f'item_{index}', "Quantity must be positive.")
                            elif prod.quantity < qty:
                                self.add_error(f'item_{index}', f"Not enough quantity for {prod.name}. Available: {prod.quantity}")
                        except ValueError:
                             self.add_error(f'item_{index}', "Quantity must be a number.")