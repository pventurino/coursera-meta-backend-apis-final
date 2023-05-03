from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User, Group
from ..models import Category, MenuItem, Cart, Order, OrderItem
from ..serializers import OrderSerializer
from datetime import date

from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND
    )

LIST_URL = reverse('orders_list')
def DETAIL_URL(pk): return reverse('orders_detail', kwargs={'pk':pk})

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
        response = self.client.get(LIST_URL)
        serializer = OrderSerializer(Order.objects.filter(user=self.customer), many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_customer_create(self):
        """
        Creates a new order with the contents of the cart
        """
        self.client.force_authenticate(user=self.customer)
        try:
            cart_url = reverse('cart')
            self.client.post(cart_url, {'menuitem':1, 'quantity':2})
            self.client.post(cart_url, {'menuitem':2, 'quantity':2})
            self.assertEqual(Cart.objects.count(), 2)
            self.assertEqual(Order.objects.count(), 0)
        except:
            raise NotImplementedError('Precondition failed: /cart/menu-items not working as expected')

        response = self.client.post(LIST_URL)
        order = Order.objects.last()
        serializer = OrderSerializer(order)
        self.assertEqual(response.data, serializer.data, 'response.data')
        self.assertEqual(response.status_code, HTTP_201_CREATED, 'response.status_code')

        self.assertEqual(OrderItem.objects.count(), 2, 'Did not create order item records')
        self.assertEqual(Cart.objects.count(), 0, 'Did not delete cart records')

        self.assertEqual(order.total, 10.0, 'order.total')
        self.assertEqual(order.delivery_crew, None, 'order.delivery_crew')
        self.assertEqual(order.status, 0, 'order.status')
        self.assertEqual(order.date, date.today(), 'order.date')

    def test_customer_create_empty(self):
        """
        If the customer attempts to create a new order with an empty cart, return 404
        """
        self.client.force_authenticate(user=self.customer)
        response = self.client.post(LIST_URL)
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {'detail':'cart is empty'})

    def test_customer_retrieve(self):
        """
        Retrieves a single order if it belongs to this customer
        """
        order1 = self._createOrder(user=self.customer)
        order2 = self._createOrder(user=self.customer2)

        self.client.force_authenticate(user=self.customer)
        response = self.client.get(DETAIL_URL(order1.id))
        serializer = OrderSerializer(Order.objects.get(id=order1.id))
        self.assertEqual(response.data, serializer.data)

        response = self.client.get(DETAIL_URL(order2.id))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_manager_list(self):
        """
        Lists all orders
        """
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer)
        self._createOrder(user=self.customer2)

        self.client.force_authenticate(user=self.manager)
        response = self.client.get(LIST_URL)
        serializer = OrderSerializer(Order.objects.all(), many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_manager_retrieve(self):
        """
        Retrieves a single order
        """
        order1 = self._createOrder(user=self.customer)
        order2 = self._createOrder(user=self.customer2)

        self.client.force_authenticate(user=self.manager)
        response = self.client.get(DETAIL_URL(order1.id))
        serializer = OrderSerializer(Order.objects.get(id=order1.id))
        self.assertEqual(response.data, serializer.data)

        response = self.client.get(DETAIL_URL(order2.id))
        serializer = OrderSerializer(Order.objects.get(id=order2.id))
        self.assertEqual(response.data, serializer.data)

        response = self.client.get(DETAIL_URL(99))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

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
        response = self.client.get(LIST_URL)
        serializer = OrderSerializer(Order.objects.filter(delivery_crew=self.delivery), many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, HTTP_200_OK)

    def test_delivery_retrieve(self):
        """
        Retrieves an order if it belongs to this delivery member
        """
        order1 = self._createOrder(user=self.customer, delivery_crew=self.delivery)
        order2 = self._createOrder(user=self.customer2, delivery_crew=self.delivery2)

        self.client.force_authenticate(user=self.delivery)
        response = self.client.get(DETAIL_URL(order1.id))
        serializer = OrderSerializer(Order.objects.get(id=order1.id))
        self.assertEqual(response.data, serializer.data)

        response = self.client.get(DETAIL_URL(order2.id))
        self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)

    def test_delivery_update(self):
        """
        Updates a single order (sets status)
        """
        pass
