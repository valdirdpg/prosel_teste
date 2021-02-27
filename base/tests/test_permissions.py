from django.test import TestCase
from django.contrib.auth.models import Group, User
from model_mommy import mommy
from ..custom import permissions


class UserInGroupTestCase(TestCase):

    def test_user_has_group_name(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        self.assertTrue(permissions.user_in_group(user, group.name))

    def test_user_has_no_group_name(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        self.assertFalse(permissions.user_in_group(user, "InexistentGroupName"))

    def test_superuser_has_any_group(self):
        user = mommy.make(User, is_superuser=True)
        self.assertTrue(permissions.user_in_group(user, "InexistentGroupName"))


class UserInGroupsTestCase(TestCase):

    def test_user_in_any_group(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        self.assertTrue(permissions.user_in_groups(user, [group.name]))

    def test_user_has_no_any_group(self):
        user = mommy.make(User)
        group = mommy.make(Group)
        user.groups.add(group)
        self.assertFalse(permissions.user_in_group(user, ["InexistentGroupName"]))

    def test_superuser_has_any_groups(self):
        user = mommy.make(User, is_superuser=True)
        self.assertTrue(permissions.user_in_group(user, ["InexistentGroupName"]))


class ProfileCheckerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.group = mommy.make(Group, name="Admin")
        cls.other_groups = [
            mommy.make(Group, name="Admin 2").name,
            mommy.make(Group, name="Admin 3").name,
        ]
        cls.profiles = [
            ("administrador", cls.group.name),
            ("other", [cls.other_groups]),
        ]

    def test_init_fill_user_and_perms_attributes(self):
        user = mommy.make(User)
        profile = permissions.ProfileChecker(user=user, perms=self.profiles)
        self.assertEqual(user, profile.user)
        self.assertEqual(dict(self.profiles), profile.perms)

    def test_run_create_methos_to_check(self):
        user = mommy.make(User)
        profile = permissions.ProfileChecker(user=user, perms=self.profiles)
        self.assertTrue(hasattr(profile, "is_administrador"))
        self.assertTrue(hasattr(profile, "is_other"))

    def test_check_is_administrador(self):
        user = mommy.make(User)
        user.groups.add(self.group)
        profile = permissions.ProfileChecker(user=user, perms=self.profiles)
        self.assertTrue(hasattr(profile, "is_administrador"))

    def test_check_is_other(self):
        user = mommy.make(User)
        user.groups.add(Group.objects.get(name=self.other_groups[0]))
        profile = permissions.ProfileChecker(user=user, perms=self.profiles)
        self.assertTrue(hasattr(profile, "is_other"))
