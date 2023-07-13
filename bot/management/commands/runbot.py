import logging
from django.conf import settings
from django.core.management import BaseCommand
from bot.models import TgUser
from bot.tg.client import TgClient
from bot.tg.dc import Message
from goals.models import Goal, GoalCategory, BoardParticipant, Board

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("start bot")

user_states = {'state': {}}
cat_id = []
logger.info(user_states)
logger.info(cat_id)


class Command(BaseCommand):
    help = "run bot"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tg_client = TgClient(settings.BOT_TOKEN)

    def handle(self, *args, **kwargs):
        offset = 0
        while True:
            res = self.tg_client.get_updates(offset=offset)
            for item in res.result:
                offset = item.update_id + 1
                self.handle_message(item.message)

    def handle_message(self, msg: Message):
        tg_user, created = TgUser.objects.get_or_create(user_ud=msg.from_.id, defaults={"chat_id": msg.chat.id,
                                                                                        "username": msg.from_.username})
        if "/start" in msg.text:
            self.tg_client.send_message(
                msg.chat.id, "Привет! {msg.chat.first_name}\n"
                             'Бот может обрабатывает следующие команды:\n'
                             '/board -> список досок\n'
                             '/category -> список категорий\n'
                             '/goals -> список целей\n'
                             '/create -> создать цель\n'
                             '/cancel -> отменить создание цели\n')

        if tg_user.user:
            self.handle_verified_user(msg, tg_user)
        else:
            self.handle_user_without_verification(msg, tg_user)

    #
    def handle_user_without_verification(self, msg: Message, tg_user: TgUser):
        self.tg_client.send_message(
            msg.chat.id,
            'Добро пожаловать!\n'
            'Для продолжения работы необходимо привязать\n'
            'Ваш аккаунт\n',
        )
        tg_user.set_verification_code()
        tg_user.save(update_fields=["verification_code"])
        self.tg_client.send_message(msg.chat.id, f"Верификационный  код: {tg_user.verification_code}")

    def handle_verified_user(self, msg: Message, tg_user: TgUser):
        allowed_commands = ['/goals', '/create', '/cancel']

        if not msg.text:
            return
        if "/start" in msg.text:
            return
        if "/board" in msg.text:
            self.fetch_board(msg, tg_user)
        elif '/goal_category' in msg.text:
            self.fetch_category(msg, tg_user)
        elif '/goals' in msg.text:
            self.fetch_tasks(msg, tg_user)
        elif '/create' in msg.text:
            self.handle_categories(msg, tg_user)
        elif '/cancel' in msg.text:
            self.get_cancel(msg, tg_user)

        elif ('user' not in user_states['state']) and (msg.text not in allowed_commands):
            self.tg_client.send_message(tg_user.chat_id, 'Неизвестная команда')

        elif (msg.text not in allowed_commands) and (user_states['state']['user']) and (
                'category' not in user_states['state']):
            category = self.handle_save_category(msg, tg_user)
            if category:
                user_states['state']['category'] = category
                self.tg_client.send_message(tg_user.chat_id,
                                            f'Выбрана категория:\n {category}.\nВведите заголовок цели')

        elif (msg.text not in allowed_commands) and (user_states['state']['user']) and (
                user_states['state']['category']) and ('goal_title' not in user_states['state']):
            user_states['state']['goal_title'] = msg.text
            logger.info(user_states)
            goal = Goal.objects.create(title=user_states['state']['goal_title'], user=user_states['state']['user'],
                                       category=user_states['state']['category'], )
            self.tg_client.send_message(tg_user.chat_id, f'Цель: {goal} создана в БД')
            del user_states['state']['user']
            del user_states['state']['msg_chat_id']
            del user_states['state']['category']
            del user_states['state']['goal_title']
            cat_id.clear()

    def fetch_board(self, msg: Message, tg_user: TgUser):
        boards = BoardParticipant.objects.filter(user=tg_user.user)
        # logger.info(boards)
        if boards:
            [self.tg_client.send_message(msg.chat.id, f"Название: {item.board}\n") for item in boards]
        else:
            self.tg_client.send_message(msg.chat.id, "У вас нет досок")

    def fetch_category(self, msg: Message, tg_user: TgUser):
        resp_categories: list[str] = [
            f'{category.id} {category.title}'
            for category in GoalCategory.objects.filter(
                board__participants__user=tg_user.user_id, is_deleted=False)]
        if resp_categories:
            self.tg_client.send_message(msg.chat.id,
                                        "Ваши категории" + '\n'.join(resp_categories))
        else:
            self.tg_client.send_message(msg.chat.id, 'У Вас нет ни одной категории!')

    def handle_categories(self, msg: Message, tg_user: TgUser):

        categories = GoalCategory.objects.filter(user=tg_user.user)
        if categories.count() > 0:
            cat_text = ''
            for cat in categories:
                cat_text += f'{cat.id}: {cat.title} \n'
                cat_id.append(cat.id)
            self.tg_client.send_message(
                chat_id=tg_user.chat_id,
                text=f'Выберите номер категории для новой цели:\n========================\n{cat_text}'
            )
            if 'user' not in user_states['state']:
                user_states['state']['user'] = tg_user.user
                user_states['state']['msg_chat_id'] = tg_user.chat_id
                logger.info(user_states)
        else:
            self.tg_client.send_message(msg.chat.id, 'список категорий пуст')

    def fetch_tasks(self, msg: Message, tg_user: TgUser):

        goals = Goal.objects.filter(user=tg_user.user)
        if goals.count() > 0:
            [self.tg_client.send_message(tg_user.chat_id,
                                         f'Название: {goal.title},\n'
                                         f'Категория: {goal.category},\n'
                                         f'Статус: {goal.get_status_display()},\n'
                                         f'Пользователь: {goal.user},\n'
                                         f'Дедлайн {goal.due_date if goal.due_date else "Нет"} \n') for goal in goals]
        else:
            self.tg_client.send_message(msg.chat.id, "Список целей пуст")

    @staticmethod
    def handle_save_category(msg: Message, tg_user: TgUser):
        category_id = int(msg.text)
        category_data = GoalCategory.objects.filter(user=tg_user.user).get(pk=category_id)
        return category_data

    def get_cancel(self, msg: Message, tg_user: TgUser):
        if 'user' in user_states['state']:
            del user_states['state']['user']
            del user_states['state']['msg_chat_id']

            if 'category' in user_states['state']:
                del user_states['state']['category']

            if 'goal_title' in user_states['state']:
                del user_states['state']['goal_title']
        self.tg_client.send_message(tg_user.chat_id, 'Операция отменена')
