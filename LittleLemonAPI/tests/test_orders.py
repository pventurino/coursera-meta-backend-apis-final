from rest_framework.test import APITestCase
from django.contrib.auth.models import User, Group
from ..models import Category, MenuItem, Cart, Order, OrderItem
from ..serializers import OrderSerializer
from datetime import date

URL = '/api/orders'

class OrdersTest(APITestCase):

    def setUp(self) -> None:
        # Set up users and groups
        self.customer = User.objects.create(username='customer')
        self.customer2 = User.objects.create(username='customer2')
        self.manager = User.objects.create(username='manager')
        self.delivery = User.objects.create(username='delivery')
        self.delivery2 = User.objects.create(username='delivery2')

        self.manager_group = Group.objects.create(name='Manager')
        self.delivery_group = Group.objects.create(name='Delivery Crew')

        self.manager.groups.add(self.manager_group)
        self.delivery.groups.add(self.delivery_group)

        # Set up some menuitems
        category = Category.objects.create(title='appetizer')

        MenuItem.objects.bulk_create([
            MenuItem(title='bread',price=2, category=category),
            MenuItem(title='cake',price=3, category=category),
        ])
        self.menuitems = MenuItem.objects.all()

        return super().setUp()
    
    def _createOrder(self, **kwargs):
        """
        Helper: creates an order for the given user
        """
        order = Order.objects.create(total=5, date=date.today(), **kwargs)
        OrderItem.objects.bulk_create(map(lambda item:OrderItem(
            order=order, 
            menuitem=item, 
            quantity=1, 
            unit_price=item.price,
            price=item.price,
            ), self.menuitems))
        return order

    def test_customer_list(self):
        """
        Lists all orders for this customer
        """
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer2)

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(URL)
        serializer = OrderSerializer(Order.objects.filter(user=self.customer), many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, 200)

    def test_customer_create(self):
        """
        Creates a new order with the contents of the cart
        """
        pass

    def test_customer_retrieve(self):
        """
        Retrieves a single order if it belongs to this customer
        """
        pass

    def test_manager_list(self):
        """
        Lists all orders
        """
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer2)

        self.client.force_authenticate(user=self.manager)
        response = self.client.get(URL)
        serializer = OrderSerializer(Order.objects.all(), many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, 200)

    def test_manager_retrieve(self):
        """
        Retrieves a single order
        """
        pass

    def test_manager_update(self):
        """
        Updates a single order (sets delivery crew)
        """
        pass

    def test_customer_update(self):
        """
        PATCH and PUT are not authorized
        """
        pass

    def test_delivery_list(self):
        """
        Lists all order assigned to this delivery member
        """
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer, delivery_crew=self.delivery)
        self._createOrder(user=self.customer, delivery_crew=self.delivery2)

        self.client.force_authenticate(user=self.delivery)
        response = self.client.get(URL)
        serializer = OrderSerializer(Order.objects.filter(delivery_crew=self.delivery), many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, 200)

    def test_delivery_retrieve(self):
        """
        Retrieves an order if it belongs to this delivery member
        """
        pass

    def test_delivery_update(self):
        """
        Updates a single order (sets status)
        """
        pass
