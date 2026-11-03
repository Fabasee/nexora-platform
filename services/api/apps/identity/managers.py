from django.contrib.auth.base_user import BaseUserManager


class NexoraUserManager(BaseUserManager):
    """Create canonical platform identities without local passwords."""

    use_in_migrations = True

    def create_user(self, **extra_fields):
        user = self.model(**extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if not extra_fields["is_staff"] or not extra_fields["is_superuser"]:
            raise ValueError("A superuser must have staff and superuser privileges.")
        return self.create_user(**extra_fields)
