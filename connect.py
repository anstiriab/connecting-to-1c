# -*- coding: utf8 -*-
from smtplib import SMTP
from email.mime.text import MIMEText
from pythoncom import CoInitialize
from win32com.client import Dispatch
from pywintypes import com_error
from sqlite3 import connect, Row as sqliteRow, Error as sqliteError
from logging import basicConfig, error as logging_error, info as logging_info, DEBUG
from datetime import datetime
from sys import exit
import json

# SMTP-server
SERVER = 'server'
PORT = 25
USER_NAME = 'username'
USER_PASSWD = 'password'

# logging settings
basicConfig(format='[%(asctime)s] %(message)s', level=DEBUG, filename='log.txt')


class Database(object):
    """
    This class is for working with a database, which includes
    information about 1c databases, schedules and records about inspecting
    these 1c databases
    """
    def __init__(self, name=None):
        if name:
            try:
                self.conn = connect(name)
                self.conn.row_factory = sqliteRow
                self.cursor = self.conn.cursor()

            except sqliteError:
                logging_error('Error connecting to database!')

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            self.conn.close()

    def get_strings(self, time):
        """
        Getting data about 1c databases that need to be checked at the given time
        :param time:
        :return: query result
        """
        self.cursor.execute(('select\n'
                             '  databases.id as id_db, name, string, '
                             '  version, schedule.id  as id_schedule,\n'
                             '  time,  checks.check_date\n'
                             'from databases\n'
                             '  inner join schedule\n'
                             '    on databases.id = schedule.id_base\n'
                             '       and databases.relevance = 1\n'
                             '       and schedule.relevance = 1\n'
                             '  left join (select\n'
                             '               id_schedule,\n'
                             '               max(check_date) as check_date\n'
                             '             from checks\n'
                             '             group by id_schedule) as checks\n'
                             '    on schedule.id = checks.id_schedule\n'
                             'where time <= time("{0}")\n'
                             '      and (date(check_date) < date("{0}")\n'
                             '           or check_date is NULL)\n'
                             'order by databases.id').format(time))
        return self.cursor.fetchall()

    def write_check(self, id_schedule, time, result):
        """
        Record the result of the check in the db
        :param id_schedule:
        :param time: check time
        :param result: check result
        """
        self.cursor.execute(('INSERT INTO checks (id_schedule, check_date,\n'
                             'data) VALUES({}, datetime("{}"), "{}")')
                            .format(id_schedule, time, result))

    def get_addresses(self):
        self.cursor.execute('select address from addresses')
        return self.cursor.fetchall()


class Message(object):
    def __init__(self, msg_from, msg_to, subj, text):
        self.msg = MIMEText(text)
        self.msg['Subject'] = subj
        self.msg['From'] = msg_from
        self.msg['To'] = msg_to
        self.to_list = msg_to.split(',')

    def send(self):
        try:
            s = SMTP(SERVER, PORT)
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(USER_NAME, USER_PASSWD)
            s.sendmail(self.msg['From'], self.to_list, self.msg.as_string())
            s.quit()
            logging_info(u'Повідомлення відправлені!')
        except:
            logging_error(u'Помилка при відправленні повідомлень!')


def check_data(json_string):
    """
    Function for parsing and checking the json string
    and generating the message text
    :param json_string: input json string (type <dict>)
    :return: message text (type <str>)
    """
    result = []
    list_obj = json.loads(json_string)
    for obj in list_obj:
        if isinstance(obj, dict):
            for database in obj:
                for task in obj[database]:
                    template = u'Регламентне завдання "{}"'.format(task['name'])
                    if task['status'] == 'Error':
                        result.append(template + u' не виконалось. Помилка: {}'
                                      .format(task['infoError']))
                    elif task['status'] == 'Canceled':
                        result.append(template + u' відмінено.')
    return '\n'.join(result)


if __name__ == '__main__':

    logging_info(u'Скрипт запущено')
    check_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    db = Database('database.db')
    strings = db.get_strings(check_time)

    if not strings:
        logging_info(u'Бази для перевірки не знайдено')
    else:
        errors = []
        checked_bases = set()
        for row in strings:
            if not row['id_db'] in checked_bases:

                # connecting to 1c database
                err = None
                for attempt in range(3):
                    try:
                        CoInitialize()
                        if row['version'] == "V83":
                            com_obj = Dispatch('V83.COMConnector').Connect(row['string'])
                        else:
                            com_obj = Dispatch('V82.COMConnector').Connect(row['string'])
                        break
                    except com_error as e:
                        strerror = e.strerror.decode('cp1251')
                        excepinfo = e.excepinfo[2].encode('cp1251').decode('cp1251')
                        err = u'{} З\'єднання не встановлено! {} {}' \
                            .format(row['name'], strerror, excepinfo)
                    except:
                        err = u'{} З\'єднання не встановлено!'.format(row['name'])

                if err:
                    logging_error(err)
                    errors.append(err.encode('utf-8'))
                else:
                    try:
                        # get data about results of scheduled jobs
                        data = com_obj.ExchangeWithExternalSourcesAPI.CheckUsingRegularTasks()
                        del(com_obj)
                        # formation of message text
                        text_msg = check_data(data)
                        if text_msg:
                            errors.append(text_msg.encode('cp1251'))
                    except com_error as e:
                        strerror = e.strerror.decode('cp1251')
                        excepinfo = e.excepinfo[2].encode('cp1251').decode('cp1251')
                        err = u'{} Помилка при читанні з бази. {} {}' \
                            .format(row['name'], strerror, excepinfo)
                        logging_error(err)
                        errors.append(err.encode('utf-8'))
                    except:
                        err = u'{} Помилка при читанні з бази.'.format(row['name'])
                        logging_error(err)
                        errors.append(err.encode('utf-8'))

                checked_bases.add(row['id_db'])

            db.write_check(row['id_schedule'], check_time, "Перевірено")

        if errors:
            addresses = db.get_addresses()
            for row in addresses:
                Message(USER_NAME, row['address'], 'Checking tasks', '\n\n'.join(errors)).send()

    db.close()
    logging_info(u'Виконання скрипту завершено')
    exit()
