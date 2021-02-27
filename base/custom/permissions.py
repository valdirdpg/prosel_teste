def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists() or user.is_superuser


def user_in_groups(user, groups_names):
    return user.groups.filter(name__in=groups_names).exists() or user.is_superuser


class ProfileChecker:
    class ProfileNotFound(Exception):
        pass

    def __init__(self, user, perms):
        self.user = user
        self.perms = dict(perms)
        self.run()

    def run(self):
        for profile in self.perms:
            groups = self.perms[profile]
            if isinstance(groups, str):
                groups = [groups]
            setattr(self, "is_" + profile, user_in_groups(self.user, groups))
