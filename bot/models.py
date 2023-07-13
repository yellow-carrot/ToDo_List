import string


from django.db import models

from core.models import User

CODE_VOCABULARY = string.ascii_letters + string.digits


class TgUser(models.Model):
    tg_chat_id = models.BigIntegerField()
    tg_user_id = models.BigIntegerField()
    user_id = models.ForeignKey(User, models.PROTECT, null=True, blank=True, default=None, verbose_name='Пользователь')
