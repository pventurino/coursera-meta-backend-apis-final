from django.urls import reverse
from rest_framework.test import APITestCase
from ..models import Category, MenuItem

LIST_URL = reverse('menuitems_list')

class MenuItemsTest(APITestCase):

    def setUp(self) -> None:

        Category.objects.bulk_create(
            map(lambda t: Category(title=t), ['appetizer','entree','dessert'])
        )
        self.categories = Category.objects.all()

        MenuItem.objects.bulk_create([
            MenuItem(title='chips', category=self.categories[0], price=1),
            MenuItem(title='pasta', category=self.categories[1], price=2),
            MenuItem(title='icecream', category=self.categories[2], price=1),
        ])
        self.menuitems = MenuItem.objects.all()

        return super().setUp()

    def test_sorting(self):

        cases = [
            ('',['chips','pasta','icecream']),
            ('?sort=title',['chips','icecream','pasta']),
            ('?sort=-title',['pasta','icecream','chips']),
            ('?sort=price,title',['chips','icecream','pasta']),
            ('?sort=price,-title',['icecream','chips','pasta']),
        ]

        for i, (params,expected) in enumerate(cases):
            response = self.client.get(LIST_URL + params)
            actual = [x.get('title') for x in response.data.get('results')]
            self.assertListEqual(actual, expected, f"with params: {params}")
