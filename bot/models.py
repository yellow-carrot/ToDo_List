import random
import string

from django.db import models

from core.models import User

CODE_VOCABULARY = string.ascii_letters + string.digits


class TgUser(models.Model):
    chat_id = models.BigIntegerField()
    user_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=512, verbose_name="tg username", null=True, blank=True, default=None)
    user = models.ForeignKey(User, models.PROTECT, null=True, blank=True, default=None)
    verification_code = models.CharField(max_length=32)

    def set_verification_code(self):
        code = "".join([random.choice(CODE_VOCABULARY) for _ in range(12)])
        self.verification_code = code

    def __str__(self):
        return '{}'.format(self.user)

    class Meta:
        verbose_name = "tg User"
        verbose_name_plural = "tg Users"
