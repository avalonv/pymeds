#!/usr/bin/env python3
# TODO:
# remove doses_pc
# remove doses_taken

from datetime import date, timedelta
from os import path, system
from re import search
import json
import time

# hardcoded for now:
my_file = path.expanduser('~/.meds.json')
logging = False
clear = True


def usage():
    print('''usage:
    [A]ction followed by one or more indexes.
    Index is the number to the left of each medication listed.
    Ex: `t 0 1 q` will mark meds with indexes zero and one as [t]aken and quit.
    ''')


# spits garbage
# :g/debug_log/d
def debug_log(*msg):
    if logging:
        print('log:', [item for item in msg])


# :pray: https://stackoverflow.com/a/19596793/8225672
def clear_screen():
    if not logging and clear:
        # clear output
        system('clear')
    else:
        debug_log('clear_screen()')


def time_now():
    return round(time.time())


def seconds_passed(timestamp):
    return round(time_now() - timestamp)


def minutes_passed(timestamp):
    return round(seconds_passed(timestamp) / 60)


def hours_passed(timestamp):
    return round(minutes_passed(timestamp) / 60)


def days_passed(timestamp):
    return round(hours_passed(timestamp) / 24)


# def date_to_timestamp(my_date):
#     return int(time.mktime(time.strptime(str(my_date), '%Y-%m-%d')))
def date_to_timestamp(my_date, date_format='%Y-%m-%d'):
    return int(time.mktime(time.strptime(str(my_date), date_format)))


def timestamp_to_date(my_timestamp):
    return date.fromtimestamp(my_timestamp)


def increase_date(my_date, num):
    return my_date + timedelta(days=num)


# :pray: https://stackoverflow.com/a/25244576/8225672
def strikethrough(text):
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result


# :pray: https://stackoverflow.com/a/6330109/8225672
# this function does way too much shit at once
def safe_cast(of_type, val, default=None, rtn_cast=True):
    # for the love of god don't make None a string
    if val is None:
        return default
    try:
        cast_val = of_type(val)
        if rtn_cast:
            return cast_val
        else:
            return True
    except (ValueError, TypeError):
        return default


class Medication:
    instances = []

    def __init__(
            self, name_generic: str, name_brand: str,
            dosage: str, cycle_len: int, notes=None,
            cycle_end=None, created_on=None,
            total_taken=0, last_taken=None, schedule=[], **kwargs):

        # append newly created instance
        # index=len(Medication.instances) # use a dict? idk tbh
        Medication.instances.append(self)

        # the name of the medication
        # string. ex: "estradiol"
        self.name_generic = safe_cast(str, name_generic)

        # brand name
        # string. ex: "estradot"
        self.name_brand = safe_cast(str, name_brand)

        # dosage
        # string. ex: "100mg"
        self.dosage = safe_cast(str, dosage)

        # the number of days in each cycle
        # (how long until the doses_taken counter is reset)
        # int:   ex: 3
        self.cycle_len = safe_cast(int, cycle_len)
        if self.cycle_len < 1:
            self.cycle_len = 1

        # any notes about the medication
        # str.   ex: "take 2 hours after eating"
        self.notes = safe_cast(str, notes)

        # timestamp of when the med was last taken
        # int. ex: 1556080265
        self.last_taken = safe_cast(int, last_taken)

        # timestamp of when the current cycle ends and the counter is reset
        # int. ex: 1556679600
        self.cycle_end = safe_cast(int, cycle_end)

        # timestamp of when the medication was created
        # int: ex: 1556766000
        self.created_on = safe_cast(int, created_on)

        # number of times the meds was taken
        # int: ex: 30
        self.total_taken = safe_cast(int, total_taken)

        # a list of timestamps for when a med should be taken
        exec(f'self.schedule = {schedule}')
        print("schedule type:", type(self.schedule))

    def __str__(self):
        string = f"{self.name_generic}"
        if self.name_brand is not None:
            string = f"{self.name_brand} ({self.name_generic})"
        if self.dosage is not None:
            string += f" {self.dosage}"
        return string

    def take(self, index=0):
        self.schedule[index][1] = True
        self.last_taken = time_now()
        self.total_taken += 1

    def untake(self, index=0):
        self.schedule[index][1] = False
        if self.total_taken > 0:
            self.total_taken -= 1

    def _update(self):
        def _advance_ts(ts):
            # increase ts by x days (86400s) until it is in the future
            return ts + (86400 * self.cycle_len)

        outdated = False
        while self.cycle_end < time_now():
            self.cycle_end = _advance_ts(self.cycle_end)
            outdated = True

        updated_schedule = []
        # pair of [timestamp, bool]
        for time_arr in self.schedule:
            # only do this if current_cycle has ended
            # keep old bool otherwise
            if outdated:
                time_arr[1] = False
            if time_arr[0] > time_now():
                updated_schedule.append(time_arr)
            else:
                # future time_arr retains its bool (if it's true it remains true)
                # but gets pushed into the future (this doesn't matter since
                # the user only sees the hour and minute)
                # future_time_arr = [0, False, '']
                future_ts = time_arr[0]
                future_bool = time_arr[1]
                future_hm = time_arr[2]
                while future_ts < time_now():
                    future_ts = _advance_ts(future_ts)
                future_time_arr = [future_ts, future_bool, future_hm]
                updated_schedule.append(future_time_arr)
        # put smallest ts (closest to the present) in the beggining so it's
        # the one we check as the "current" schedule
        updated_schedule.sort()
        self.schedule = updated_schedule

        debug_log("time_now:", time_now())
        debug_log("ts:", [time_arr[0] for time_arr in updated_schedule])

    def get_lastintake(self):
        if self.last_taken is not None:
            modifier = 's'
            base = seconds_passed(self.last_taken)
            if base > 60:
                base = minutes_passed(self.last_taken)
                modifier = 'm'
            if base > 60:
                base = hours_passed(self.last_taken)
                modifier = 'h'
            if base > 48:
                base = days_passed(self.last_taken)
                modifier = ' days'
            # return f'{base}{modifier}'
            return f'last taken {base}{modifier} ago'
        else:
            return ''

    def get_schedule(self):
        # this is a copy
        self._update()
        return self.schedule

    def check_nextintake(self):
        self._update()


def optional_ask(of_type, prompt):
    prompt += ':\n'
    while True:
        choice = input(prompt)
        if choice.lower() == 'q':
            if input('quit? ').lower() in 'y':
                exit(0)
        if choice == '':
            return None
        # if checking for an int and the user types '0' this condition will pass (which is not good)
        # elif safe_cast(of_type, choice, default=False) == False:
        # check against None instead because (0 == False) = True; but (0 == None) = False
        elif safe_cast(of_type, choice, rtn_cast=False) is None:
            print(f'(must be {str(of_type)})')
            # type(of_type).__name__  or .__class__.__name__ doesn't work for some reason?
            continue
        else:
            break
    return safe_cast(of_type, choice)


def required_ask(of_type, prompt):
    prompt += ' *'
    while True:
        choice = optional_ask(of_type, prompt)
        if choice is not None or '':
            break
        else:
            print("this field can't be empty")
    return safe_cast(of_type, choice)



def add_med():
    def make_schedule(start_ts, my_len):
        '''
        args must be a list of time strings in H:M format. Ex: 07:30 or 23:10
        '''
        time_strings = []
        total = 0
        for i in range(my_len):
            while True:
                choice = required_ask(str, f"intake {total}")
                # :pray: https://stackoverflow.com/a/51177696/8225672
                if search('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$', choice) is None:
                    print('invalid format. (24 HH:MM)')
                    continue
                else:
                    time_strings.append(choice)
                    break

        end_date = str(timestamp_to_date(start_ts))
        schedule = []
        for string in time_strings:
            arr = [0, False, string]
            date_str = f"{end_date} {string}"
            ts = date_to_timestamp(date_str, '%Y-%m-%d %H:%M')
            arr[0] = ts
            schedule.append(arr)

        return schedule

    while True:
        clear_screen()
        print("creating new medication")

        # pep8 hates this
        name_generic = required_ask(str, 'generic name')
        name_brand   = optional_ask(str, 'brand name')
        dosage       = optional_ask(str, 'dosage')
        doses_pc     = required_ask(int, 'take ... dose(s)')
        cycle_len    = required_ask(int, 'every ... day(s)')
        created_on   = time_now()
        schedule     = make_schedule(created_on, doses_pc)
        notes        = optional_ask(str, 'notes')
        cycle_end    = increase_date(timestamp_to_date(created_on), cycle_len)
        cycle_end    = date_to_timestamp(cycle_end)

        new_med = Medication(
                name_generic, name_brand, dosage,
                cycle_len, notes, cycle_end,
                created_on, schedule=schedule)

        print('created', str(new_med))

        if input('add another? ').lower() == 'y':
            continue
        break


def save_to_file():
    save_data = []
    for med in Medication.instances:
        attribute_dict = vars(med)
        save_data.append(attribute_dict)

    with open(my_file, 'w') as save_file:
        json.dump(save_data, save_file, indent=2)


def load_instances():
    # this should only be called ONCE each time the program runs
    try:
        with open(my_file, 'r') as load_file:
            try:
                json_str = json.load(load_file)
                has_records = True
            # no records exist
            except (ValueError):
                debug_log('load_instances ValueError: no records found')

    except (FileNotFoundError):
        choice = input(f"'{my_file}' doesn't exist. create? ").lower()
        if choice in 'y':
            debug_log('load_instances FileNotFoundError create', my_file)
            open(my_file, 'w')
        else:
            print("quitting")
            exit(1)

    if has_records:
        for object_dict in json_str:
            Medication(**object_dict)


def list_meds():
    index = 0
    for med in Medication.instances:
        print(f"{index} {med}")
        schedule = med.get_schedule()
        for time_arr in schedule:
            if time_arr[1] is True:
                print("✓ |- ", strikethrough(f"{time_arr[2]}"), "- TAKEN")
            else:
                print(f"  |-  {time_arr[2]} - NOT TAKEN")
        index += 1


def loop():
    def parse_choice(text):
        ''' each non numeral character becomes an action, with every numeral to the
        left of it assigned to a list, until the next non numeral character is read
        and so on
        '''
        actions = {}
        current_action = None
        for word in text.split(' '):
            if not word == '':
                # if word not a number or '*'
                if search('\d|\*', word) is None:
                    current_action = word
                    if current_action not in actions:
                        actions[current_action] = []
                # check if current_action exists before adding anything
                elif current_action is not None:
                    if word == '*':
                        allnums = [num for num in range(0, len(Medication.instances))]
                        actions[current_action] = allnums
                    else:
                        actions[current_action].append(int(word))
        return actions

    if len(Medication.instances) == 0:
        add_med()
    while True:
        clear_screen()
        list_meds()
        choice = input("[N]ew, [R]emove, [T]ake, [U]ntake, [I]nfo, [H]elp, [Q]uit: ").lower()
        for action, nums in parse_choice(choice).items():
            nums.sort(reverse=True)
            save_to_file()
            debug_log('action', action)
            debug_log('nums', nums)
            clear_screen()
            # quit
            if action == 'q':
                list_meds()
                exit(0)
            # new
            if action == 'n':
                add_med()
            # remove
            if action == 'r':
                for index in nums:
                    try:
                        selected = Medication.instances[index]
                    except (IndexError):
                        continue
                    print(f"delete '{selected}'?", end=': ')
                    if input().lower() in 'y':
                        Medication.instances.remove(selected)
                    else:
                        continue
            # take
            if action == 't':
                for index in nums:
                    # catch index error
                    try:
                        selected = Medication.instances[index]
                    except (IndexError):
                        continue
                    selected.take()
            # untake
            if action == 'u':
                for index in nums:
                    # catch index error
                    try:
                        selected = Medication.instances[index]
                    except (IndexError):
                        continue
                    selected.untake()
            # info
            if action == 'i':
                clear_screen()
                for index in nums:
                    # catch index error
                    try:
                        selected = Medication.instances[index]
                        print(f'{index} - {selected.get_info()}')
                    except (IndexError):
                        continue
                input('')

            if action == 'h':
                clear_screen()
                usage()
                input('')


if __name__ == "__main__":
    try:
        load_instances()
        loop()
    except (KeyboardInterrupt):
        print('')
        exit(1)
