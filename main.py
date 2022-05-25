import math
import datetime
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
import re
import requests
import json

from group_schedule_parser import group_schedule_parser
from teacher_schedule_parser import teacher_schedule_parser
from weather_requests import make_weather_message
from group_schedule_requests import make_group_schedule_message
from teacher_schedule_requests import make_teacher_schedule_message
from methods import find_group, make_stat, find_teacher, find_region
from Client import Client


class Bot:
    def __init__(self, vk_session, vk, long_poll):
        self.vk_session = vk_session
        self.vk = vk
        self.long_poll = long_poll

        self.USERS_active = {}

        self.standard_keys = "keyboard/default.json"
        self.group_schedule_keys = "keyboard/group_schedule_keys.json"
        self.teacher_schedule_keys = "keyboard/teacher_schedule_keys.json"
        self.choose_keys = "keyboard/choose.json"
        self.weather_keys = "keyboard/weather_keys.json"
        self.cancel_keys = "keyboard/cancel.json"
        self.begin_keys = "keyboard/begin.json"
        self.covid_keys = "keyboard/covid_keys.json"

    def send_message(self, user_id, message, keyboard=None, attachment=None):
        try:
            if attachment and keyboard:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    keyboard=open(keyboard, "r", encoding="UTF-8").read(),
                    message=message,
                    attachment=attachment
                )
            elif keyboard:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    keyboard=open(keyboard, "r", encoding="UTF-8").read(),
                    message=message
                )
            elif attachment:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    message=message,
                    attachment=attachment
                )
            else:
                self.vk.messages.send(
                    user_id=user_id,
                    random_id=get_random_id(),
                    message=message
                )

        except vk_api.ApiError:
            print("Ошибка доступа")

    def start(self):
        lp_listen = self.long_poll.listen()

        with open("prev_users.json", 'r', encoding="utf-8") as file:
            file_data = json.load(file)
            message = "ой, меня перезапустили\nнапишите \"начать\", чтобы узнать, что я могу"
            for user in file_data["users"]:
                if user["id"] == 322847078:
                    self.send_message(user["id"], message, keyboard=self.begin_keys)

        print("server started...")

        for event in lp_listen:
            if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
                received_msg = event.text
                msg_from = event.user_id

                print(f'New message from {msg_from}, text = {received_msg}')

                if msg_from not in self.USERS_active:
                    self.USERS_active[msg_from] = Client()

                    with open("prev_users.json", 'r+', encoding="utf-8") as file:
                        file_data = json.load(file)
                        new_user = True
                        if len(file_data["users"]) > 0:
                            for user in file_data["users"]:
                                if user["id"] == msg_from:
                                    new_user = False
                                    break

                        if new_user:
                            file_data["users"].append({"id": msg_from})

                        file.seek(0)
                        json.dump(file_data, file, indent=4, ensure_ascii=False)
                else:
                    print(self.USERS_active[msg_from].mode)

                if re.search(r"начать", received_msg.lower()):
                    message = "привеет <3. я могу узнать расписание любой группы и любого преподавателя. " \
                              "\n\nчтобы узнать расписание, напишите в чат \"расписание\"" \
                              "\n\nчтобы узнать погоду, напишите в чат \"погода\"" \
                              "\n\nчтобы найти преподавателя, напишите в чат \"найти фамилия преподавателя\"" \
                              "\n\nчтобы получить статистку по коронавирусу, напишите в чат \"ковид\"" \
                              "\n\nчтобы вернуться в основное меню, напишите в чат \"отменить\""
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                if re.search(r"отменить", received_msg.lower()):
                    self.USERS_active[msg_from].mode = 0
                    message = "вы вернулись в основное меню"
                    self.send_message(msg_from, message, keyboard=self.standard_keys)
                    continue

                good_msg = True

                if self.USERS_active[msg_from].mode == 1:  # меню с расписанием
                    good_msg = self.group_schedule_handler(received_msg, msg_from)
                elif self.USERS_active[msg_from].mode == 2:  # меню с погодой
                    good_msg = self.weather_handler(received_msg, msg_from)
                elif self.USERS_active[msg_from].mode == 3:  # меню с расписанием преподавателя
                    good_msg = self.teacher_schedule_handler(received_msg, msg_from)
                elif self.USERS_active[msg_from].mode == 4:  # статус ввода группы
                    group = re.search(r"[а-яА-Я]{4}\-\d\d\-\d\d", received_msg)
                    self.send_message(msg_from, "поиск группы...")
                    if group and find_group(group.group(0)):
                        self.USERS_active[msg_from].group = group.group(0).upper()
                        message = "текущая группа: " + group.group(0).upper() + \
                                  "\nна какой период показать расписание?"
                        self.USERS_active[msg_from].mode = 1
                        self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
                    else:
                        message = "такой группы нет :с\nпопробуйте еще раз..."
                        self.send_message(msg_from, message, keyboard=self.cancel_keys)
                    continue

                elif self.USERS_active[msg_from].mode == 5:  # статус ввода преподавателя
                    if received_msg not in self.USERS_active[msg_from].teachers:
                        self.send_message(msg_from, "такого варианта нет :с\nпопробуйте другой...",
                                          keyboard=self.choose_keys)
                        continue

                    self.USERS_active[msg_from].teacher = received_msg
                    message = "выбранный преподаватель: " + received_msg + \
                              "\nна какой период показать расписание?"

                    self.send_message(msg_from, message, keyboard=self.teacher_schedule_keys)
                    self.USERS_active[msg_from].mode = 3
                    continue
                elif self.USERS_active[msg_from].mode == 6:  # меню короны
                    if "росси" in received_msg.lower():
                        self.covid_handler("/country/russia/", msg_from)
                        continue
                    elif "регион" in received_msg.lower():
                        self.USERS_active[msg_from].mode = 7
                        self.send_message(msg_from, "введите название региона",
                                          keyboard=self.cancel_keys)
                        continue
                    else:
                        good_msg = False

                elif self.USERS_active[msg_from].mode == 7:  # поиск региона
                    regions = find_region(received_msg)
                    self.USERS_active[msg_from].regions = regions
                    print(regions)
                    if not regions:
                        self.USERS_active[msg_from].mode = 6
                        self.send_message(msg_from, "такого региона нет :с",
                                          keyboard=self.covid_keys)
                        continue
                    elif 1 < len(regions) <= 7:
                        regions_for_keys = [r[1] for r in regions]
                        self.USERS_active[msg_from].mode = 8
                        self.make_choose_keys(regions_for_keys)
                        self.send_message(msg_from, "выберите регион",
                                          keyboard=self.choose_keys)
                        continue
                    elif len(regions) >= 8:
                        self.USERS_active[msg_from].mode = 6
                        self.send_message(msg_from, "по данному запросу слишком много совпадений :с"
                                                    "\nпопробуйте уточнить Ваш запрос...",
                                          keyboard=self.covid_keys)
                        continue
                    else:
                        self.USERS_active[msg_from].mode = 6
                        self.send_message(msg_from, f"выбранный регион: {regions[0][1]}"
                                                    f"\nпоиск статистики...")
                        self.covid_handler(regions[0][0], msg_from)
                        continue

                elif self.USERS_active[msg_from].mode == 8:  # выбор региона
                    found = False
                    link = ""
                    for i in self.USERS_active[msg_from].regions:
                        if received_msg == i[1]:
                            found = True
                            link = i[0]
                            break
                    if not found:
                        self.send_message(msg_from, "такого варианта нет :с\nпопробуйте другой...",
                                          keyboard=self.choose_keys)
                        continue

                    self.send_message(msg_from, "поиск статистики...")
                    self.covid_handler(link, msg_from)
                    self.USERS_active[msg_from].mode = 6
                    continue

                if self.USERS_active[msg_from].mode == 0 or not good_msg:
                    if re.search(r"расписание", received_msg.lower()):
                        self.USERS_active[msg_from].mode = 4
                        self.send_message(msg_from, "введите номер группы",
                                          keyboard=self.cancel_keys)

                    elif re.search(r"найти", received_msg.lower()):
                        self.send_message(msg_from, "поиск преподавателя...")
                        name = re.sub(r"найти\s+", '', received_msg.lower())
                        teachers = find_teacher(name)
                        self.USERS_active[msg_from].teachers = teachers
                        print(teachers)

                        if not teachers:
                            self.USERS_active[msg_from].mode = 0
                            self.send_message(msg_from, "такого преподавателя нет :с",
                                              keyboard=self.standard_keys)
                        elif 1 < len(teachers) <= 7:
                            self.USERS_active[msg_from].mode = 5
                            self.make_choose_keys(teachers)
                            self.send_message(msg_from, "выберите имя преподавателя",
                                              keyboard=self.choose_keys)
                        elif len(teachers) >= 8:
                            self.send_message(msg_from, "по данному запросу слишком много совпадений :с"
                                                        "\nпопробуйте уточнить Ваш запрос...",
                                              keyboard=self.standard_keys)
                        else:
                            self.USERS_active[msg_from].mode = 3
                            self.USERS_active[msg_from].teacher = teachers[0]
                            self.send_message(msg_from, f"открываю меню расписания преподавателя {teachers[0]}",
                                              keyboard=self.teacher_schedule_keys)

                    elif re.search(r"погода", received_msg.lower()):
                        self.USERS_active[msg_from].mode = 2
                        self.send_message(msg_from, "открываю меню погоды",
                                          keyboard=self.weather_keys)
                    elif "корона" in received_msg.lower() or "ковид" in received_msg.lower():
                        self.USERS_active[msg_from].mode = 6
                        self.send_message(msg_from, "открываю меню статистики коронавируса",
                                          keyboard=self.covid_keys)

                    elif re.search(r"помощь", received_msg.lower()):
                        self.USERS_active[msg_from].mode = 0
                        message = "чтобы пользоваться ботом напишите мне что-нибудь <3"
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

                    else:
                        self.USERS_active[msg_from].mode = 0
                        message = "простите я ничего не поняв(("
                        self.send_message(msg_from, message, keyboard=self.standard_keys)

    def group_schedule_handler(self, msg, msg_from):
        open_schedule = False
        message = "Error"
        command = "Error"
        if "сегодня" in msg.lower():
            command = "TOD"
            open_schedule = True
        elif "завтра" in msg.lower():
            command = "TOM"
            open_schedule = True
        elif "на эту неделю" in msg.lower():
            command = "THIS WEEK"
            open_schedule = True
        elif "на следующую неделю" in msg.lower():
            command = "NEXT WEEK"
            open_schedule = True
        elif "какая неделя" in msg.lower():
            current_week = datetime.datetime.now().date() - \
                           datetime.datetime.strptime("07.02.2022", '%d.%m.%Y').date()
            message = f"Идет {math.ceil(current_week.days / 7)} неделя"
        elif "какая группа" in msg.lower():
            message = "показываю расписание группы " + self.USERS_active[msg_from].group
        elif "понедельник" in msg.lower():
            command = "ПН"
            open_schedule = True
        elif "вторник" in msg.lower():
            command = "ВТ"
            open_schedule = True
        elif "среда" in msg.lower():
            command = "СР"
            open_schedule = True
        elif "четверг" in msg.lower():
            command = "ЧТ"
            open_schedule = True
        elif "пятница" in msg.lower():
            command = "ПТ"
            open_schedule = True
        elif "суббота" in msg.lower():
            command = "СБ"
            open_schedule = True
        elif "воскресенье" in msg.lower():
            message = "воскресенье - выходной"
        else:
            self.USERS_active[msg_from].mode = 0
            return False

        if open_schedule:
            self.send_message(msg_from, "поиск расписания группы...")
            self.group_schedule_sender(msg_from, self.USERS_active[msg_from].group, command)
        else:
            self.send_message(msg_from, message, keyboard=self.group_schedule_keys)
        return True

    def teacher_schedule_handler(self, msg, msg_from):
        if "сегодня" in msg.lower():
            command = "TOD"
        elif "завтра" in msg.lower():
            command = "TOM"
        elif "на эту неделю" in msg.lower():
            command = "THIS WEEK"
        elif "на следующую неделю" in msg.lower():
            command = "NEXT WEEK"
        else:
            self.USERS_active[msg_from].mode = 0
            return False

        self.send_message(msg_from, "поиск расписания преподавателя...")
        self.teacher_schedule_sender(msg_from, self.USERS_active[msg_from].teacher, command)
        return True

    def make_choose_keys(self, teachers):
        teachers.append("отменить")

        with open(self.choose_keys, 'w', encoding="utf-8") as file:
            file_data = {"one_time": True, "buttons": []}

            for i in teachers:
                color = "primary"

                if i == "отменить":
                    color = "negative"
                new_key = {
                    "action": {
                        "type": "text",
                        "label": i
                    },
                    "color": color
                }
                file_data["buttons"].append([new_key])

            json.dump(file_data, file, indent=4, ensure_ascii=False)

    def weather_handler(self, msg, msg_from):
        if "сейчас" in msg.lower():
            message = "NOW"
        elif "сегодня" in msg.lower():
            message = "TOD"
        elif "завтра" in msg.lower():
            message = "TOM"
        elif "недел" in msg.lower():
            message = "WEEK"
        else:
            self.USERS_active[msg_from].mode = 0
            return False

        self.send_message(msg_from, "поиск погоды...")
        self.weather_parser(msg_from, message)
        return True

    def covid_handler(self, link, msg_from):
        stat = make_stat(link)
        if stat == "BAD":
            print("сервер недоступен :с")
            self.send_message(msg_from, "сервер недоступен :с", keyboard=self.covid_keys)
            return

        if "russia" in link:
            upload = VkUpload(self.vk)
            photo = upload.photo_messages('stat.png')[0]
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            self.send_message(msg_from, stat, keyboard=self.covid_keys, attachment=attachment)
        else:
            self.send_message(msg_from, stat, keyboard=self.covid_keys)

    def group_schedule_sender(self, msg_from, group, command):
        schedule = make_group_schedule_message(group, command)
        for i in range(len(schedule)):
            if i == len(schedule) - 1:
                self.send_message(msg_from, schedule[i], keyboard=self.group_schedule_keys)
            else:
                self.send_message(msg_from, schedule[i])

    def teacher_schedule_sender(self, msg_from, teacher, command):
        schedule = make_teacher_schedule_message(teacher, command)

        for i in range(len(schedule)):
            if i == len(schedule) - 1:
                self.send_message(msg_from, schedule[i], keyboard=self.teacher_schedule_keys)
            else:
                self.send_message(msg_from, schedule[i])

    def weather_parser(self, msg_from, date):
        weather = make_weather_message(date)
        upload = VkUpload(self.vk)

        if date == "WEEK":
            self.send_message(msg_from, "погода на неделю")
            s = []
            for i in range(1, len(weather['message']), 2):
                s.append(weather['message'][i] + " | " + weather['message'][i - 1])
            print(s)
            for i in range(len(s)):
                photo = upload.photo_messages(f'icons/icon_double{i}.png')[0]
                attachment = f"photo{photo['owner_id']}_{photo['id']}"

                if i == len(s) - 1:
                    self.send_message(msg_from, s[i], keyboard=self.weather_keys, attachment=attachment)
                else:
                    self.send_message(msg_from, s[i], attachment=attachment)

        elif date == "NOW":
            print(weather['message'])
            response_icon = requests.get(weather['icons'][0], stream=True)
            photo = upload.photo_messages(photos=response_icon.raw)[0]
            attachment = f"photo{photo['owner_id']}_{photo['id']}"
            self.send_message(msg_from, weather['message'][0], attachment=attachment, keyboard=self.weather_keys)

        else:
            if date == "TOD":
                self.send_message(msg_from, "погода на сегодня")
            if date == "TOM":
                self.send_message(msg_from, "погода на завтра")

            print(weather['message'])
            for i in range(len(weather['icons'])):
                response_icon = requests.get(weather['icons'][i], stream=True)
                photo = upload.photo_messages(photos=response_icon.raw)[0]
                attachment = f"photo{photo['owner_id']}_{photo['id']}"

                if i == len(weather['icons']) - 1:
                    self.send_message(msg_from, weather['message'][i], attachment=attachment,
                                      keyboard=self.weather_keys)
                else:
                    self.send_message(msg_from, weather['message'][i], attachment=attachment)


def main():
    with open("token.txt", 'r') as f:  # WARNING no vk group api
        vk_session = vk_api.VkApi(token=f.readline())

    vk = vk_session.get_api()
    long_poll = VkLongPoll(vk_session)

    # функции парсящие таблицу
    #group_schedule_parser()
    #teacher_schedule_parser()

    vkbot = Bot(vk_session, vk, long_poll)
    vkbot.start()


if __name__ == "__main__":
    main()
