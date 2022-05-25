import re
import os
import math
import datetime
import json

weekdays = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]


def parser_for_weeks(s, flag_krome):
    if flag_krome:
        s = s.replace("кр.", "")
    s = s.replace("н.", "")
    s = s.strip()
    weeks = s.split(',')
    for w in range(len(weeks)):
        if "-" in weeks[w]:
            new = weeks[w].split('-')
            weeks[w] = new[0]
            for j in range(int(new[0]) + 1, int(new[1]) + 1):
                weeks.append(j)

    weeks = list(map(int, weeks))
    return weeks


def formatted_message(schedule_data, weekday, col_name, current_week):
    message = ""
    for i in range(1, 7):
        num = str(i)
        subject = schedule_data[col_name][weekday][num]["subject"]
        type_sub = schedule_data[col_name][weekday][num]["type"]
        aud = schedule_data[col_name][weekday][num]["aud"]
        teacher = schedule_data[col_name][weekday][num]["teacher"]

        if subject == "-":
            message += f"\n{num}. -"
        else:
            subject = subject.replace("  ", " ")

            found = False
            result = []
            for sub in subject.split("\n"):
                good = True
                match2 = re.findall(r"кр\. [0-9].*н\. ", sub)
                sub = re.sub(r"кр\. [0-9].*н\. ", "", sub).strip()

                match1 = re.findall(r"[0-9].*н\. ", sub)
                sub = re.sub(r"[0-9].*н\. ", "", sub).strip()
                if match2:
                    for match in match2:
                        weeks = parser_for_weeks(match, True)
                        if current_week in weeks:
                            good = False

                elif match1:
                    for match in match1:
                        weeks = parser_for_weeks(match, False)
                        if current_week not in weeks:
                            good = False

                if good:
                    found = True
                    result.append(sub)

            if found:
                type_subs = type_sub.split('\n')

                auds = aud.split('\n')
                teachers = teacher.split('\n')
                subjects_done = {}
                for j in range(len(result)):
                    if result[j] not in subjects_done:
                        msg = ""
                        msg += f'\n{num}. {result[j]}'
                        if type_sub != '-':
                            a = type_subs[j].replace("  ", " ")
                            msg += f' ({a.strip()})'

                        if aud != '-':
                            b = auds[j].replace("  ", " ")
                            msg += f', ауд. {b.strip()}'

                        if teacher != '-':
                            c = teachers[j].replace("  ", " ")
                            msg += f', преп. {c.strip()}'

                        subjects_done.update({result[j]: msg})
                    else:
                        c = teachers[j].replace("  ", " ")
                        subjects_done[result[j]] += f', {c.strip()}'

                message += "".join(subjects_done.values())

            else:
                message += f"\n{num}. -"

    return message


def make_group_schedule_message(group, command):
    group = group.upper()
    print("group", group, command)
    current_week = datetime.datetime.now().date() - \
                   datetime.datetime.strptime("06.02.2022", '%d.%m.%Y').date()
    current_week = math.ceil(current_week.days / 7)
    even_week = current_week % 2 == 0

    today = datetime.datetime.now().weekday()
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).weekday()

    filepath = os.path.abspath(os.curdir) + "/tables/groups_schedule.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        file_data = json.load(file)

    for group_data in file_data["groups"]:
        if group_data["group"] == group:
            schedule_data = group_data["timetable"]

            if not schedule_data:
                print("Ошибка группы")
                return ["ошибка группы"]
            else:
                result = []
                if command == "TOD":
                    if today == 6:
                        message = "сегодня воскресенье"
                    else:
                        message = f'засписание {group_data["group"]} на сегодня\n'
                        col_name = "even" if even_week else "odd"
                        message += formatted_message(schedule_data, weekdays[today], col_name, current_week)
                    result.append(message)

                elif command == "TOM":
                    if tomorrow == 6:
                        message = "завтра воскресенье"
                    else:
                        message = f'расписание {group_data["group"]} на завтра\n'
                        col_name = "even" if even_week else "odd"
                        if tomorrow == 0:
                            current_week += 1
                            col_name = "odd" if even_week else "even"
                        message += formatted_message(schedule_data, weekdays[tomorrow], col_name, current_week)
                    result.append(message)

                elif command == "THIS WEEK":
                    col_name = "even" if even_week else "odd"
                    for i in range(6):
                        message = ""
                        if i == 0:
                            message += f'расписание {group_data["group"]} на эту неделю'
                        message += "\n\n" + weekdays[i]
                        message += formatted_message(schedule_data, weekdays[i], col_name, current_week)
                        result.append(message)

                elif command == "NEXT WEEK":
                    col_name = "odd" if even_week else "even"
                    for i in range(6):
                        message = ""
                        if i == 0:
                            message += f'расписание {group_data["group"]} на следующую неделю'
                        message += "\n\n" + weekdays[i]
                        message += formatted_message(schedule_data, weekdays[i], col_name, current_week+1)
                        result.append(message)

                elif command in weekdays:  # command - день недели
                    message = f'расписание {group_data["group"]} на {command}\n'
                    col_name = "even" if even_week else "odd"

                    message += formatted_message(schedule_data, command, col_name, current_week+1)
                    result.append(message)

                else:
                    message = "команда не распознана"
                    result.append(message)

                # print(*result)
                return result

