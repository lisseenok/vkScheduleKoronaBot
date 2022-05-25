import os
import json

weekdays = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ"]


def teacher_schedule_parser():
    filepath = os.path.abspath(os.curdir) + "/tables/groups_schedule.json"
    with open(filepath, 'r', encoding="utf-8") as file:
        file_data = json.load(file)

    used_teachers = []
    result = {"teachers": []}

    for group_data in file_data["groups"]:
        for col_name in "odd", "even":
            for wd in weekdays:
                for num in range(1, 7):
                    teacher_str = group_data["timetable"][col_name][wd][str(num)]["teacher"]

                    if teacher_str != '-':
                        tt = teacher_str.split("\n")

                        for k in range(len(tt)):
                            subjects = group_data["timetable"][col_name][wd][str(num)]["subject"].split("\n")
                            sub_types = group_data["timetable"][col_name][wd][str(num)]["type"].split("\n")
                            auds = group_data["timetable"][col_name][wd][str(num)]["aud"].split("\n")

                            if k >= len(subjects):
                                index = k - 1
                            else:
                                index = k
                            subject = subjects[index]
                            sub_type = sub_types[index]
                            aud = auds[index]
                            group = group_data["group"]

                            if tt[k] not in used_teachers:
                                teacher_data = {"teacher": "", "timetable": {}}
                                schedule_data = {"odd": {}, "even": {}}
                                for d in weekdays:
                                    schedule_data["odd"].update({d: {}})
                                    schedule_data["even"].update({d: {}})
                                    for n in "123456":
                                        schedule_data["odd"][d].update({n: {}})
                                        schedule_data["even"][d].update({n: {}})
                                        for f in "subject", "type", "aud", "group":
                                            schedule_data["odd"][d][n].update({f: '-'})
                                            schedule_data["even"][d][n].update({f: '-'})

                                schedule_data[col_name][wd][str(num)]["subject"] = subject
                                schedule_data[col_name][wd][str(num)]["type"] = sub_type
                                schedule_data[col_name][wd][str(num)]["aud"] = aud
                                schedule_data[col_name][wd][str(num)]["group"] = group

                                teacher_data["teacher"] = tt[k]
                                teacher_data["timetable"] = schedule_data

                                result["teachers"].append(teacher_data)
                                used_teachers.append(tt[k])
                            else:
                                for teacher_obj in result["teachers"]:
                                    if teacher_obj["teacher"] == tt[k]:
                                        if teacher_obj["timetable"][col_name][wd][str(num)]["subject"] == '-':
                                            teacher_obj["timetable"][col_name][wd][str(num)]["subject"] = subject
                                        else:
                                            teacher_obj["timetable"][col_name][wd][str(num)]["subject"] += "\n" + subject

                                        if teacher_obj["timetable"][col_name][wd][str(num)]["type"] == '-':
                                            teacher_obj["timetable"][col_name][wd][str(num)]["type"] = sub_type
                                        else:
                                            teacher_obj["timetable"][col_name][wd][str(num)]["type"] += "\n" + sub_type

                                        if teacher_obj["timetable"][col_name][wd][str(num)]["aud"] == '-':
                                            teacher_obj["timetable"][col_name][wd][str(num)]["aud"] = aud
                                        else:
                                            teacher_obj["timetable"][col_name][wd][str(num)]["aud"] += "\n" + aud

                                        if teacher_obj["timetable"][col_name][wd][str(num)]["group"] == '-':
                                            teacher_obj["timetable"][col_name][wd][str(num)]["group"] = group
                                        else:
                                            teacher_obj["timetable"][col_name][wd][str(num)]["group"] += "\n" + group

    filepath = os.path.abspath(os.curdir) + "/tables/teachers_schedule.json"
    with open(filepath, 'w', encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

