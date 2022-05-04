from django_auth_ldap import backend as ldap_backend


class MyLDAPBackend(ldap_backend.LDAPBackend):
    def get_or_build_user(self, username, ldap_user):
        user, built = super(
            MyLDAPBackend, self
        ).get_or_build_user(username, ldap_user)

        if not user.is_staff:
            user.is_staff = True
            user.save()

        return user, built
