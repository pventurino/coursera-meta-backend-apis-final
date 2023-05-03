from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from ..models import Category, MenuItem, Cart
from ..serializers import CartItemSerializer

URL = '/api/cart/menu-items'

# Create your tests here.
class CartTest(APITestCase):

    def setUp(self) -> None:
        self.carl = User.objects.create(username='carl', password='password')
        self.cole = User.objects.create(username='cole', password='password')
        self.users = [self.carl, self.cole]

        Category.objects.bulk_create(
            map(lambda t: Category(title=t), ['appetizer','entree','dessert'])
        )
        self.categories = Category.objects.all()

        MenuItem.objects.bulk_create([
            MenuItem(title='chips', category=self.categories[0], price=1),
            MenuItem(title='meat', category=self.categories[1], price=2),
            MenuItem(title='icecream', category=self.categories[2], price=3),
        ])
        self.menuitems = MenuItem.objects.all()

    def _newCart(self, user, menuitem, quantity):
        return Cart(user=user, menuitem=menuitem, quantity=quantity, unit_price=menuitem.price, price=menuitem.price * quantity)
    
    def test_get_records(self):
        """
        WHEN user GETs their cart
        THEN only their own records are returned
        """
        carts = []
        for u in self.users:
            for m in self.menuitems:
                carts.append(self._newCart(u,m,1))
        Cart.objects.bulk_create(carts)
        self.assertEqual(Cart.objects.count(), 6, 'Precondition: should have 6 DB records')

        self.client.force_authenticate(user=self.carl)
        response = self.client.get(URL)
        serializer = CartItemSerializer(Cart.objects.filter(user=self.carl), many=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, serializer.data)

    def test_create_record(self):
        """
        WHEN user POSTs a new cart item
        THEN a new record is created
        AND that record's user is the current user
        AND that record's menuitem is the selected item
        AND that record's quantity is the selected quantity
        AND that record's unit_price is the menuitem's price
        AND that record's price is its quantity times its unit_price
        """
        self.client.force_authenticate(user=self.carl)
        response = self.client.post(URL, {'menuitem':1,'quantity':3})
        self.assertEqual(response.status_code, 201)
        
        record = Cart.objects.last()
        self.assertEqual(record.user, self.carl)
        self.assertEqual(record.menuitem, self.menuitems[0])
        self.assertEqual(record.quantity, 3)
        self.assertEqual(record.unit_price, self.menuitems[0].price)
        self.assertEqual(record.price, record.quantity * record.unit_price)

    def test_update_quantity(self):
        """
        WHEN user POSTs to an existing cart item with a different quantity
        THEN the cart item is updated with the new quantity
        """
        Cart.objects.bulk_create([self._newCart(self.carl, self.menuitems[0], 1)])
        oldRecord = Cart.objects.last()

        self.client.force_authenticate(user=self.carl)
        self.client.post(URL, {'menuitem':1, 'quantity':3})
        record = Cart.objects.last()
        self.assertEqual(record.quantity, 3)
        self.assertEqual(record.price, 3 * record.unit_price)

    def test_delete_cart_item(self):
        """
        WHEN user POSTs to an existing cart item with quantity 0
        THEN the cart item is removed 
        """

        Cart.objects.bulk_create([self._newCart(self.carl, self.menuitems[0], 1)])

        self.client.force_authenticate(user=self.carl)
        self.client.post(URL, {'menuitem':1, 'quantity':0})
        self.assertEqual(0, Cart.objects.count(), 'Count of Cart records in database')        

    def test_delete_cart(self):
        """
        WHEN user DELETEs their cart
        THEN all their cart item is deleted
        AND the cart items of other users are not deleted 
        """
        carts = []
        for u in self.users:
            for m in self.menuitems:
                carts.append(self._newCart(u,m,1))
        Cart.objects.bulk_create(carts)
        self.assertEqual(Cart.objects.count(), 6, 'Precondition: should have 6 DB records')

        self.client.force_authenticate(user=self.carl)
        response = self.client.delete(URL)
        self.assertEqual(response.status_code, 204)

        carts_in_db = Cart.objects.all()
        self.assertEqual(carts_in_db.__len__(), 3)
        for cart in carts_in_db:
            self.assertEqual(cart.user, self.cole)
