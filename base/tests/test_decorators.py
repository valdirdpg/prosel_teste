from django.test import TestCase
from django.utils.safestring import SafeString

from base.custom.views import decorators


class ColumnTestCase(TestCase):

    def test_should_add_short_description_attribute(self):
        @decorators.column("Name")
        def a():
            pass
        self.assertEqual("Name", a.short_description)

    def test_should_mark_return_as_safe(self):
        @decorators.column("Name", mark_safe=True)
        def a():
            return ""
        self.assertIsInstance(a(), SafeString)


class TabTestCase(TestCase):

    def test_should_add_short_description_attribute(self):
        @decorators.tab("Name")
        def a():
            pass
        self.assertEqual("Name", a.short_description)
