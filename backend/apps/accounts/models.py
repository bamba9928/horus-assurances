from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.GENERAL_ADMIN)
        extra_fields.setdefault("partner_group", None)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        GENERAL_ADMIN = "GENERAL_ADMIN", "Admin general"
        GROUP_ADMIN = "GROUP_ADMIN", "Admin de groupe"
        CONTRIBUTOR = "CONTRIBUTOR", "Apporteur"

    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.CONTRIBUTOR,
    )
    partner_group = models.ForeignKey(
        "groups.PartnerGroup",
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )
    phone = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(role="GENERAL_ADMIN", partner_group__isnull=True)
                    | (~Q(role="GENERAL_ADMIN") & Q(partner_group__isnull=False))
                ),
                name="accounts_user_role_group_consistency",
            )
        ]

    @property
    def is_general_admin(self) -> bool:
        return self.role == self.Role.GENERAL_ADMIN

    @property
    def is_group_admin(self) -> bool:
        return self.role == self.Role.GROUP_ADMIN

    @property
    def is_contributor(self) -> bool:
        return self.role == self.Role.CONTRIBUTOR

    def clean(self):
        super().clean()
        if self.role == self.Role.GENERAL_ADMIN and self.partner_group_id is not None:
            raise ValidationError(
                {"partner_group": "Un admin general ne doit pas etre rattache a un groupe."}
            )
        if self.role != self.Role.GENERAL_ADMIN and self.partner_group_id is None:
            raise ValidationError(
                {"partner_group": "Un utilisateur non admin general doit appartenir a un groupe."}
            )
