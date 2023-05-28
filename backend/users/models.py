from django.contrib.auth.models import AbstractUser
from django.db import models

NAME_LEN = 150
CHAR_LEN = 15
CHAR_LEN_TWO = 20


class User(AbstractUser):
    email = models.EmailField(verbose_name="email address", unique=True)
    password = models.CharField(verbose_name="password", max_length=NAME_LEN)
    first_name = models.CharField(verbose_name="Имя", max_length=NAME_LEN)
    last_name = models.CharField(verbose_name="Фамилия", max_length=NAME_LEN)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        ordering = ("id",)
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username[:CHAR_LEN]


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, related_name="subscriber_subscriptions", on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User, related_name="author_subscriptions", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        constraints = (
            models.UniqueConstraint(
                fields=("subscriber", "author"), name="resubscription"
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F("subscriber")),
                name="selfsubscription",
            ),
        )

    def __str__(self):
        return f"""{self.subscriber.username[:CHAR_LEN_TWO]}
        follows {self.author.username[:CHAR_LEN_TWO]}"""
