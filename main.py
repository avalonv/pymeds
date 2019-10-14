#!/usr/bin/env python3
# vim:foldenable:foldmethod=indent
# TODO:
# add a calendar, proper day by day tracking? also a prompt to check if the user took the meds they were supposed
# to when the counter resets and doses_taken is less than doses
# add an option to not clear the screen or list anything, pass arguments to the file, interpret them and then exit
# add another option to list all meds and quit
# add another option to display usage and quit

from os import path, system
from re import search
from medication import Medication
import json

# GLOBALS (hardcoded for now):
my_file = path.expanduser('~/.meds.json')  # where json data is saved
logging = False  # spits hot garbage
clear = True  # clears the screen. ignored if logging is True
save_on_interrupt = True  # saves when the user presses Ctrl+C
no_strikethrough = False  # set to True if your font doesn't have strikethrough
checkmark = '\u2713'  # checkmark symbol. '\u2611' and '\u2714' are cool too


def usage():
    print('''usage:
    [C]ommand followed by one or more meds, which are represented by numbers.
    Ex: 't 0 1 q' will mark meds with numbers zero and one as [t]aken and quit.
    '*' can be used to select all meds at once.
    A check mark is displayed when all doses have been taken for the day,
    otherwise the time since the most recent dose was taken is shown.
    ''')


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


# :pray: https://stackoverflow.com/a/25244576/8225672
def strikethrough(text) -> str:
    if no_strikethrough:
        return text
    result = ''
    for char in text:
        result = result + char + '\u0336'
    return result


def list_meds():
    i = 0
    for med in Medication.instances:
        if med.check_nextintake():
            print(f"  {i} - [{med.get_dosesremaining()}] {med} {med.get_lastintake()}")
        else:
            print(f"{checkmark} {i} -", strikethrough(f"[{med.get_dosesremaining()}] {med}"))
        i += 1


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
        # this is a bit messy and overly complex
        # might want to remove it
        return default


def optional_ask(of_type, prompt):
    prompt += ': '
    while True:
        choice = input(prompt)
        if choice.lower() == 'q':
            if input('quit? ').lower() in 'y':
                exit(0)
        if choice == '':
            return None
        # if checking for an int and the user types '0' this condition will
        # pass (which is not good)
        # elif safe_cast(of_type, choice, default=False) == False:
        # check against None instead because (0 == False) = True;
        # but (0 == None) = False
        elif safe_cast(of_type, choice, rtn_cast=False) is None:
            print(f'(must be {str(of_type)})')
            # type(of_type).__name__  or .__class__.__name__
            # doesn't work for some reason?
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
    return choice


def add_med():
    while True:
        clear_screen()
        print("creating new medication")

        # pep8 hates this
        name_generic    = required_ask(str, 'generic name')
        name_brand      = optional_ask(str, 'brand name')
        dosage          = optional_ask(str, 'dosage')
        doses_per_cycle = required_ask(int, 'take ... dose(s)')
        cycle_days      = required_ask(int, 'every ... day(s)')
        notes           = optional_ask(str, 'notes')

        new_med = Medication(name_generic, name_brand, dosage, doses_per_cycle,
                             cycle_days, notes)

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


def load_file():
    # this should only be called ONCE each time the program runs
    has_records = False

    try:
        with open(my_file, 'r') as load_file:
            try:
                json_str = json.load(load_file)
                has_records = True
            # no records exist
            except (ValueError):
                debug_log('load_file ValueError: no records found')

    except (FileNotFoundError):
        choice = input(f"'{my_file}' doesn't exist. create? ").lower()
        if choice in 'y':
            debug_log('load_file FileNotFoundError create', my_file)
            open(my_file, 'w')
        else:
            print("quitting")
            exit(1)

    if has_records:
        for object_dict in json_str:
            Medication(**object_dict)


def loop():
    def parse_choice(text):
        ''' each non numeral character becomes a command, with every numeral to the
        left of it assigned to a list, until the next non numeral character is read
        and so on
        returns a dict of letters + numbers
        '''
        commands = {}
        current_command = None
        for word in text.split(' '):
            if search('^([a-z]|[A-Z])$', word):  # word is a lowercase letter
                current_command = word
                if current_command not in commands:
                    # only assign an empty list to the key if it doesn't exist
                    commands[current_command] = []

            # check if current_command key exists before adding anything
            if current_command is not None:
                if search('^\*$', word):  # word is an asterisk
                    allnums = [num for num in range(0, len(Medication.instances))]
                    commands[current_command] += allnums
                elif search('^\d$', word):  # word is a digit
                    commands[current_command].append(int(word))
        return commands

    if len(Medication.instances) == 0:
        add_med()
    while True:
        clear_screen()
        list_meds()
        choice = input("[N]ew, [R]emove, [T]ake, [U]ntake, [I]nfo, [H]elp, Save & [Q]uit: ").lower()
        for command, nums in parse_choice(choice).items():
            nums.sort(reverse=True)
            debug_log('command', command)
            debug_log('nums', nums)
            clear_screen()
            # quit
            if command == 'q':
                list_meds()
                return
            # new
            if command == 'n':
                add_med()
            # remove
            if command == 'r':
                for i in nums:
                    try:
                        selected = Medication.instances[i]
                    except (IndexError):
                        continue
                    print(f"delete '{selected}'?", end=': ')
                    if input().lower() in 'y':
                        Medication.instances.remove(selected)
                    else:
                        continue
            # take
            if command == 't':
                for i in nums:
                    # catch index error
                    try:
                        selected = Medication.instances[i]
                    except (IndexError):
                        continue
                    selected.take()
            # untake
            if command == 'u':
                for i in nums:
                    # catch index error
                    try:
                        selected = Medication.instances[i]
                    except (IndexError):
                        continue
                    selected.untake()
            # info
            if command == 'i':
                clear_screen()
                for i in nums:
                    # catch index error
                    try:
                        selected = Medication.instances[i]
                        print(f'{i} - {selected.get_info()}')
                        input('')
                    except (IndexError):
                        continue

            if command == 'h':
                clear_screen()
                usage()
                input('')


if __name__ == "__main__":
    try:
        load_file()
        loop()
        save_to_file()
        exit(0)
    except (KeyboardInterrupt):
        if save_on_interrupt:
            save_to_file()
        print('')
        exit(1)
