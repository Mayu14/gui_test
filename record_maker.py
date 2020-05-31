# -- coding: utf-8 --

import PySimpleGUI as sg
import datetime, locale, re

# 出席者情報の格納
class Attendance(object):
    __template = ''
    __fname_of_template = ''
    __user_edited_template = None
    def __init__(self, name, member_id):
        self.__name = name
        self.__member_id = member_id
        self.__overviews = ['']
        self.__details = [None]
        self.__item = 1

    def get_name(self):
        return self.__name

    def get_member_id(self):
        return self.__member_id

    def set_template(self, fname):
        if fname[-4:] != '.ini':
            fname += '.ini'
        self.__fname_of_template = fname

    def get_template(self):
        return self.__template

    def apply_template(self, template):
        self.__user_edited_template = template

    def get_situation(self, internal=False):
        self.__load_template(self.__user_edited_template)
        if internal:
            item, output = 0, ''
            for ov, dt in zip(self.__overviews, self.__details):
                item += 1
                output += f'{item}.{ov}\n'
                if dt is not None:
                    dt = dt.replace("\n\n\n", "").replace("\n", "\n  ->")
                    output += f'  ->{dt}\n'
        else:
            head, body1, body2, foot = self.__tmps[0], self.__tmps[1], self.__tmps[2], self.__tmps[3]
            output = f'{head}{self.__name}'
            for ov, dt in zip(self.__overviews, self.__details):
                output += f'{body1}{ov}'
                if dt is not None:
                    output += f'{body2}{dt}'
                output += f'{foot}'
        return output

    def print(self):
        print(self.get_situation())

    def __add_overviews(self):
        self.__overviews.append('')
        self.__details.append(None)
        self.__item += 1

    def __add_details(self, id):
        self.__details[id] = ''

    def __set_overviews(self, id, text):
        self.__overviews[id] = text

    def __set_details(self, id, text):
        self.__details[id] = text

    def __get_id(self, i):
        return int(i) + 1

    def __get_id_str(self, i):
        return str(self.__get_id(int(i))).zfill(3)

    def __get_inv_id(self, id):
        return int(id) - 1

    def __make_key(self, id, add=True, ov=True):
        body = f'{self.get_name()}_{id}'
        if add:
            if ov:
                return f'add_ov_{body}'
            else:
                return f'add_dt_{body}'
        else:
            if ov:
                return f'ov_{body}'
            else:
                return f'dt_{body}'

    def __parse_key(self, key):
        keys = key.split('_')
        if keys[0] == 'add':
            return True, keys[1], int(keys[-1])    # add, ov_or_dt, id
        else:
            return False, keys[0], int(keys[-1])   # add, ov_or_dt, id

    def __save_data(self, values):
        for key in values.keys():
            _, ov_or_dt, id = self.__parse_key(key)
            data = values[key]
            id = self.__get_inv_id(id)
            if data is not None:
                if ov_or_dt == 'ov':
                    self.__set_overviews(id=id, text=data)
                elif ov_or_dt == 'dt':
                    self.__set_details(id=id, text=data)
                else:
                    raise ValueError('check ov_or_dt')

    def __load_template(self, template=None):
        if template is not None:
            self.__template = template
        else:
            try:
                with open(self.__fname_of_template, 'r') as f:
                    self.__template = f.read()
            except:
                self.__template = '\t<NAME>\n\t\t・<OVERVIEW>\n\t\t  -><DETAIL>\n'
                with open('defalut_body_template.ini', "w") as f:
                    f.write(self.__template)

        head, body0 = self.__template.split('<NAME>')
        body, foot = body0.split('<DETAIL>')
        body1, body2 = body.split('<OVERVIEW>')
        self.__tmps = [head, body1, body2, foot]

    def __layout_overview(self, i, dt_add=False):
        num = self.__get_id(i)
        numstr = self.__get_id_str(i)
        key = self.__make_key(num, add=False)
        if dt_add:
            return [sg.Text(f'概要{numstr}'), sg.InputText(default_text=self.__overviews[i], key=key),
                    sg.Submit('詳細の追加', key=self.__make_key(num, add=True, ov=False))]
        else:
            return [sg.Text(f'概要{numstr}'),
                    sg.InputText(default_text=self.__overviews[i], key=key)]

    def __layout_detail(self, i):
        num = self.__get_id(i)
        numstr = self.__get_id_str(i)
        if self.__details[i] is None:
            raise ValueError('details is None')
        return [sg.Text(f'詳細{numstr}'),
                sg.Multiline(default_text=self.__details[i], key=self.__make_key(num, add=False, ov=False),
                             border_width=2)]

    def __set_layout(self):
        name = self.__name
        layout = [[sg.Text(f'{name}の状況')]]

        for i, dt in enumerate(self.__details):

            if dt is not None:
                layout.append(self.__layout_overview(i, dt_add=False))
                layout.append(self.__layout_detail(i))
            else:
                layout.append(self.__layout_overview(i, dt_add=True))

        layout.append([sg.Submit('概要の追加', key=f'add_ov_{name}_{self.__get_id(self.__item)}'),
                       sg.Submit('保存して閉じる', key='close')])
        return layout

    def create_window(self):
        layout = self.__set_layout()
        window = sg.Window(f'{self.__name}の状況', layout)

        while True:
            event, values = window.read()

            self.__save_data(values)

            if (event is None) or (event == 'close'):
                print('exit')
                break

            add, ov_or_dt, id = self.__parse_key(event)

            if add:
                if ov_or_dt == 'ov':
                    self.__add_overviews()
                elif ov_or_dt == 'dt':
                    self.__add_details(self.__get_inv_id(id))
                else:
                    raise ValueError('program has a conflict')
                window.close()
                layout = self.__set_layout()
                window = sg.Window(f'{self.__name}の状況', layout)

        window.close()
        return 0

# 議事録の情報の格納
class ValueField(object):
    def __init__(self, initial_value, name='<NAME>', var_type='str', fill=0):
        self.__value = initial_value
        self.__name = name
        self.__var_type = type(var_type)
        self.__fill = fill

    def get_value(self):
        return self.__value

    def update_value(self, value):
        if self.__var_type == type('str'):
            if self.__fill == 0:
                self.__value = str(value)
            else:
                self.__value = str(value).zfill(self.__fill)
        elif self.__var_type == type(1):
            self.__value = int(value)
        else:
            raise ValueError(f'{self.__var_type} is not supported.')

    def replace_text(self, in_text):
        return in_text.replace(self.__name, str(self.get_value()))

# 議事録そのもの
class Proceeding(object):
    __header = ValueField('', '<HEADER>')
    __name = ValueField('○○会議', '<CONFERENCE_NAME>')
    __year = ValueField(2020, '<YEAR>', fill=4)
    __month = ValueField(9, '<MONTH>', fill=2)
    __day = ValueField(2, '<DAY>', fill=2)
    __day_of_the_week = ValueField('水', '<DAY_OF_THE_WEEK>')
    __start_time = ValueField('00:00', '<START_TIME>')
    __end_time = ValueField('12:00', '<END_TIME>')
    __place = ValueField('第１会議室', '<PLACE>')
    __attendances = ValueField('X，Y，Z', '<ATTENDEES>')
    __body = ValueField('', '<BODY>')
    __footer = ValueField('', '<FOOTER>')
    __template = ''
    __attendance_names = []
    __attendees = {}
    __define_attendees = False
    __number_of_attendees = 0
    __separator = "，"

    fields = ['<HEADER>', '<CONFERENCE_NAME>', '<YEAR>', '<MONTH>', '<DAY>', '<DAY_OF_THE_WEEK>',
              '<START_TIME>', '<END_TIME>', '<PLACE>', '<ATTENDEES>','<BODY>', '<FOOTER>']

    def __init__(self, default_attendees_sep="[，、,, /]"):
        self.sep_pattern = default_attendees_sep
        self.set_template(fname='')

    def set_basic_information(self, name, year, month, day, start_time, end_time, place, attendees, separator=None):
        self.__set_name(name)
        self.__set_year(year)
        self.__set_month(month)
        self.__set_day(day)
        self.__set_start_time(start_time)
        self.__set_end_time(end_time)
        self.__set_place(place)
        self.__set_attendees(attendees, separator)

    def get_number_of_attendees(self):
        return self.__number_of_attendees

    def get_name_of_attendees(self):
        return self.__attendance_names

    def get_attendance(self, name):
        if not self.__define_attendees:
            self.__make_attendees()
            self.__define_attendees = True
        return self.__attendees[name]

    def get_secretary(self):
        if self.__number_of_attendees != 0:
            return self.get_attendance(self.get_name_of_attendees()[0])
        else:
            raise ValueError('Attendees are not defined.')

    def get_template(self):
        return self.__template

    def set_template(self, fname, fromFile=True):
        if not fromFile:
            self.__template = fname
            return 'user_edited'
        else:
            try:
                with open(fname, "r") as f:
                    self.__template = f.read()
                return fname
            except:
                self.__template = '<HEADER>\n<CONFERENCE_NAME> 議事録\n' \
                                '<YEAR>/<MONTH>/<DAY> (<DAY_OF_THE_WEEK>) <START_TIME>~<END_TIME> <PLACE>\n' \
                                '出席者：<ATTENDEES>\n\n\t●各自の状況\n\n<BODY>\n\n<FOOTER>'
                with open('default_header_template.ini', 'w') as f:
                    f.write(self.__template)
                return 'system_default'

    def save(self, fname):
        try:
            with open(fname, 'w') as f:
                f.write(self.__generate_proceeding())
            return f"The proceeding can save as {fname}"
        except:
            return 'The proceeding cannot saved!'

    def print(self):
        print(self.__generate_proceeding())

    def __set_header(self, text=''):
        self.__header.update_value(text)

    def __set_footer(self, text=''):
        self.__footer.update_value(text)

    def __set_name(self, text=''):
        self.__name.update_value(text)

    def __set_year(self, int_or_string):
        self.__year.update_value(int_or_string)

    def __set_month(self, int_or_string):
        self.__month.update_value(int_or_string)

    def __set_day(self, int_or_string):
        self.__day.update_value(int_or_string)

    def __set_day_of_the_week(self):
        year, month, day = int(self.__year.get_value()), int(self.__month.get_value()), int(self.__day.get_value())
        if (year != '') and (month != '') and (day != ''):
            locale.setlocale(locale.LC_ALL, '')
            dt = datetime.datetime(year, month, day)
            self.__day_of_the_week.update_value(dt.strftime('%a'))
        else:
            raise NameError('year, month and day must need before get day_of_the_week')

    def __set_start_time(self, text='hh:mm'):
        self.__start_time.update_value(text)

    def __set_end_time(self, text='hh:mm'):
        self.__end_time.update_value(text)

    def __set_place(self, text='conference_room_01'):
        self.__place.update_value(text)

    def __set_attendees(self, attendees, separater=None):
        if separater is None:
            sep = self.sep_pattern
        else:
            sep = separater
            self.__separator = sep

        self.__attendance_names = re.split(sep, attendees)
        self.__number_of_attendees = len(self.__attendance_names)
        output = ''
        for name in self.__attendance_names:
            output += f'{name}様，'
        else:
            output = output[:-2]    # 様，の削除
            output += '(記)'   # writer
        self.__attendances.update_value(output)

    def __make_attendees(self):
        for i, name in enumerate(self.__attendance_names):
            self.__attendees[name] = Attendance(name, member_id=i)

    def __update_body(self):
        body = ''
        print(self.__attendees)
        for name in self.__attendees.keys():
            body += self.__attendees[name].get_situation()

        self.__body.update_value(body)

    def __generate_proceeding(self):
        self.__update_body()
        if self.__template == '':
            self.set_template(fname='')
        out = self.__template
        out = self.__name.replace_text(out)
        out = self.__header.replace_text(out)
        out = self.__year.replace_text(out)
        out = self.__month.replace_text(out)
        out = self.__day.replace_text(out)
        self.__set_day_of_the_week()
        out = self.__day_of_the_week.replace_text(out)
        out = self.__start_time.replace_text(out)
        out = self.__end_time.replace_text(out)
        out = self.__place.replace_text(out)
        out = self.__attendances.replace_text(out)
        out = self.__body.replace_text(out)
        out = self.__footer.replace_text(out)
        return out

    def create_main_window(self, attendees=None):
        box_short = (5, 1)
        layout = [
            [sg.MenuBar([['File', ['Save', ['as Text'], '---', 'Exit']],
                         ['Tool', ['Load Header Template', 'Edit Header Template',
                                   'Load Body Template', 'Edit Body Template']],
                         ['Info', ['version']]], key='mb1')],
            [sg.Text('基本情報の設定')],
            [sg.Text('会議名称'), sg.InputText(default_text=self.__name.get_value(), key='<CONFERENCE_NAME>')],
            [sg.Text('日時'), sg.InputText(self.__year.get_value(), size=box_short, key='<YEAR>'),
             sg.Text('年'), sg.InputText(self.__month.get_value(), size=box_short, key='<MONTH>'),
             sg.Text('月'), sg.InputText(self.__day.get_value(), size=box_short, key='<DAY>'), sg.Text('日')],
            [sg.Text('開始時刻'), sg.InputText(self.__start_time.get_value(), size=box_short, key='<START_TIME>'),
             sg.Text('終了時刻'), sg.InputText(self.__end_time.get_value(), size=box_short, key='<END_TIME>')],
            [sg.Text('場所'), sg.InputText(self.__place.get_value(), key='<PLACE>')],
            [sg.Text('出席者(敬称略)'), sg.InputText(self.__attendances.get_value(), key='<ATTENDEES>')],
            [sg.Text('区切り文字'), sg.InputText(self.__separator, size=box_short, key='<SEPARATOR>'),
             sg.Submit('出席者の反映')],
        ]

        if attendees is not None:
            for person in attendees:
                layout.append([sg.Text(person + 'の状況')])
                layout.append(
                    [sg.Multiline(border_width=2, key=person, auto_size_text=True), sg.Submit('編集', key=f'bt{person}')])
        return layout
##########################################
###             以下GUI関連              ###
##########################################
def main():
    #  セクション1 - オプションの設定と標準レイアウト
    sg.theme('Dark Blue 3')

    pcd = Proceeding()
    layout = pcd.create_main_window()
    window = sg.Window('議事録作成支援ツール', layout)

    while True:
        event, values = window.read()

        # quit
        if event is None or event.lower() == "exit":
            print('exit')
            break

        # apply attendees
        if event == '出席者の反映':
            sep = None
            if values['<SEPARATOR>'] != '，':
                sep = values['<SEPARATOR>']

            pcd.set_basic_information(values['<CONFERENCE_NAME>'], values['<YEAR>'], values['<MONTH>'], values['<DAY>'],
                                      values['<START_TIME>'], values['<END_TIME>'], values['<PLACE>'],
                                      values['<ATTENDEES>'], sep)
            isYes = sg.popup_yes_no(f"出席者は全部で{pcd.get_number_of_attendees()}名です．\n詳細の入力に進みますか？",
                                    title='基本情報の確認')

            if (type(isYes) == type('a')) and (isYes.lower() == 'yes'):
                window.close()
                layout = pcd.create_main_window(attendees=pcd.get_name_of_attendees())
                window = sg.Window('議事録作成ツール', layout)

        # edit detail situation of attendees
        if 'bt' in event:
            name = event[2:]
            attendance = pcd.get_attendance(name)
            attendance.create_window()
            window[name].Update(attendance.get_situation(internal=True))

        # proceeding: save as text
        if event.lower() == "as text":
            lay = [[sg.InputText(enable_events=True, key='txt_path'),
                    sg.FileSaveAs('Browse', key='txt_save', file_types=(('Text Files', '.txt'),))],
                   [sg.Submit('Save', key='save')]]
            win = sg.Window('Save as...', lay)
            file_name = None
            while True:
                event, values = win.read()
                if (event == 'txt_path') and (values['txt_path'] != ''):
                    file_name = values['txt_path']

                if (file_name is not None) and (event == 'save'):
                    status = pcd.save(file_name)
                    sg.popup(status)

                if event is None:
                    break
            continue    # event.lower()対策

        # template loader
        if type(event) == type("str") and event.lower()[:4] == "load":
            file_name = sg.PopupGetFile(f'Please select a filename of {event.lower()[5:]}',
                                        file_types=(("Template Files", "*.ini"),))

            if 'header' in event.lower():
                pcd.set_template(file_name)
            else:
                if pcd.get_number_of_attendees() != 0:
                    pcd.get_secretary().set_template(file_name)
                else:
                    sg.popup('please define attendees before load body template')

        # template editor
        if type(event) == type("str") and event.lower()[:4] == "edit":
            flag_edit = 0
            tmp = ''
            if 'header' in event.lower():
                tmp = pcd.get_template()
            else:
                if pcd.get_number_of_attendees() != 0:
                    tmp = pcd.get_secretary().get_template()
                else:
                    sg.popup('please define attendees before load body template')
                    flag_edit = 1

            if flag_edit == 0:
                lay = [[sg.Text(f'{event.lower()[5:]}の編集')],
                       [sg.Multiline(default_text=tmp, size=(60, 10), key='editor')],
                       [sg.Text(f'File Name'), sg.InputText(enable_events=True, key='tmp_path'),
                        sg.FileSaveAs('Browse', key='tmp_save', file_types=(('Template Files', '.ini'),))],
                       [sg.Submit('Save and Close', key='save_and_close')]]
                win = sg.Window('Template Editor', lay)
                file_name = None
                while True:
                    event, values = win.read()
                    my_template = values['editor']

                    if (event == 'tmp_path') and (values['tmp_path'] != ''):
                        file_name = values['tmp_path']

                    if (file_name is not None) and (event == 'save_and_close'):
                        if 'header' in event.lower():
                            pcd.set_template(my_template, fromFile=False)
                        else:
                            pcd.get_secretary().apply_template(my_template)
                        with open(file_name, 'w') as f:
                            f.write(my_template)
                        sg.popup(f'{file_name}に保存しました')
                        event = None

                    if event is None:
                        break
                continue

        if (event == 'version'):
            sg.popup(
                f'record maker ver.0.1 by Mayu Shirakawa\n\tshirakawa.mayu.0810@gmail.com\n\n既知の不具合\n・body templateはたぶん編集できない\n・フォント変更不可\n\n(不具合に対応する気があるとは言ってない)',
                title='Information')


    window.close()
    # セクション 4 - ウィンドウの破棄と終了

if __name__ == '__main__':
    main()