from datetime import date, timedelta
import json
import time

#TODO:
# add 'total_taken' counter, 'first_taken' timestamp
# implement info method

"""
start program

+load my_file.
#if there are no instances it

+enter loop
  #check len of Medication.instances. if it's zero add_medication() is called
  #otherwise, call get_nextintake() on each of them
  #get_nextintake()
  #each med is displayed next to a number, which will be the index in the Medicinies.instances list
  #choice_action is what function/method will be called, followed by the index(es) of the instances+
  #actions:

    +mark meds that were taken
      #call .take() on the instance. increase doses_taken and updated last_taken timestamp
      -go back to beggining of loop

    +unmark meds
      #call .untake() on the instance. just decreases doses_taken
      -go back to beggining of loop

    +delete
      #simply call remove (index) on the instances list
      -go back to beggining of loop

    +add
      #start add_medication()
      -go back to beggining of loop

    +quit
      -breaks from the loop

+serialize the instances as json objects and save them to my_file
#it might be a good idea to save every time something changes instead

end program

  cycle will be reset every 24 hours, or a multiple of this
  each instance has a timestamp of when it was last taken
"""

# hardcoded for now:
my_file = 'a.json'
logging = True

# :g/debug_log/d
def debug_log(*msg):
    if logging:
        print('log:', [item for item in msg])

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

def date_to_timestamp(my_date):
    return int(time.mktime(time.strptime(str(my_date), '%Y-%m-%d')))

def timestamp_to_date(my_timestamp):
    return date.fromtimestamp(my_timestamp)

def increase_date(my_date, num):
    return my_date + timedelta(days=num)

def strike(text):
    # :pray: https://stackoverflow.com/a/25244576/8225672
    result = ''
    for c in text:
        result = result + c + '\u0336'
    return result

def safe_cast(of_type, val, default=None, return_cast=True):
    # :pray: https://stackoverflow.com/a/6330109/8225672
    try:
        cast_val = of_type(val)
        if return_cast:
            return cast_val
        else:
            return True
    except (ValueError, TypeError):
        return default

def optional_ask(of_type, prompt):
    prompt += ': '
    while True:
        ui = input(prompt)
        if ui == '':
            return None
        #elif safe_cast(of_type, ui, default=False) == False:
        # if checking for an int and the user types '0' this condition will pass (which is not good)
        # check against None instead because (0 == False) = True; but (0 == None) = False
        elif safe_cast(of_type, ui, return_cast=False) == None:
            print('Wrong type')
            continue
        else:
            break
    return safe_cast(of_type, ui)

def required_ask(of_type, prompt):
    prompt += '*'
    while True:
        ui = optional_ask(of_type, prompt)
        if ui != None or '':
            break
        else: print("Can't be empty")
    return safe_cast(of_type, ui)

class Medication:
    instances = []
    def __init__(self, name_generic, name_brand, dosage, doses_pc, cycle_len, notes, doses_taken=0, cycle_end=None, last_taken=None):

        # append newly created instance
        #index=len(Medication.instances) # use a dict? idk tbh
        Medication.instances.append(self)

        # the name of the medication
        # string. ex: "estradiol"
        self.name_generic = safe_cast(str, name_generic)

        # brand name
        # string. ex: "estradot"
        self.name_brand = safe_cast(str, name_brand)

        # the dosage for the medication
        # string. ex: "100mg"
        self.dosage = safe_cast(str, dosage)

        # the number of doses to be taken per cycle
        # int.    ex: "2"
        self.doses_pc = safe_cast(int, doses_pc)

        # the number of hours between each cycle
        self.cycle_len = safe_cast(int, cycle_len)

        # any notes about the schedule or whatever
        # str:   ex: "take 2 hours after eating"
        self.notes = safe_cast(str, notes)

        # the number of doses already taken
        # int.    ex: "1"
        self.doses_taken = safe_cast(int, doses_taken)

        # timestamp of when the med was last taken
        # int. ex: 1556080265
        self.last_taken = safe_cast(int, last_taken)

        # timestamp of when the current cycle begins
        # int. ex:
        self.cycle_end = safe_cast(int, cycle_end)
        debug_log("type(self.cycle_end)", type(self.cycle_end))

    def __str__(self):
        if self.name_brand != None:
            return f"{self.name_brand} ({self.name_generic})"
        return f"{self.name_generic}"

    def take(self):
        self.last_taken = time_now()
        self.doses_taken += 1

    def untake(self):
        if self.doses_taken > 0:
            self.doses_taken -= 1

    def get_lastintake(self):
        if self.last_taken != None:
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
                modifier = 'days'
            #return f'{base}{modifier}'
            return f'last taken {base}{modifier} ago'
        else:
            return ''

    def get_dosesremaining(self):
        return f"{self.doses_taken}/{self.doses_pc}"

    def _advance_next_cycle(self):
        #date_ce = date.fromtimestamp(self.cycle_end)
        date_ce = timestamp_to_date(self.cycle_end)
        debug_log("_advance_next_cycle for", str(self), "starting date_ce", date_ce)

        '''
        # cycle_end = (cycle_end + cycle) until cycle_end + cycle > date_today
        # doses_taken = 0
        '''
        #while (date_ce + timedelta(days=self.cycle_len)) < date.today():
        while date_ce <= date.today():
            #date_ce = date_ce + timedelta(days=self.cycle_len)
            debug_log('_advance_next_cycle increasing date_ce', date_ce)
            date_ce = increase_date(date_ce, self.cycle_len)
        self.doses_taken = 0
        debug_log('_advance_next_cycle updated date_ce is', date_ce)

        #self.cycle_end = int(time.mktime(time.strptime(str(date_ce), '%Y-%m-%d')))
        self.cycle_end = date_to_timestamp(date_ce)

    def _update(self):
        '''
        # checks if the current cycle is in the past
        # spiro last_taken 2019-04-20 and spiro cycle = 1
          # if spiro last_taken (20) + spiro cycle (1) less than date today (21)
            # spiro advance cycle
        '''
        if date.fromtimestamp(self.last_taken) + timedelta(days=self.cycle_len) < date.today():
            debug_log(f"{self}._update - 1")
            self._advance_next_cycle()
        elif self.cycle_end < time_now():
            debug_log(f"{self}._update - 2 {self.cycle_end} < {time_now()}")
            self._advance_next_cycle()

    def check_nextintake(self):
        self._update()
        if self.doses_taken < self.doses_pc:
            return True
        else:
            return False


def add_medication():
    while True:
        name_generic = required_ask(str,'Med name')
        name_brand = optional_ask(str, 'Brand name')
        dosage = optional_ask(str, 'Dosage')
        doses_pc = required_ask(int, 'Doses')
        cycle_len = required_ask(int, 'Cycle (days)')
        notes = optional_ask(str, 'Notes')
        doses_taken = 0
        last_taken = time_now()
        cycle_end = increase_date(timestamp_to_date(time_now()), cycle_len) # cycle_ends = date today + cycle lenght
        cycle_end = date_to_timestamp(cycle_end)
        debug_log('add_medication new cycle_end', cycle_end)

        new_med = Medication(name_generic, name_brand, dosage, doses_pc, cycle_len, notes, doses_taken, cycle_end, last_taken)
        debug_log("add_medication created:", new_med)

        if input('break? ') == 'q':
            break

def save_to_file():
    # this should only be called ONCE each time the program runs

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
                load_data = json.load(load_file)
            # no records exist
            except (ValueError):
                debug_log('load_instances ValueError: no records found')
                return None

        for med in load_data:
            # this is probably not safe :(
            exec_str = 'load_med = Medication('
            for key,val in med.items():
                exec_str += f"{key}='{val}',"

            exec_str = exec_str[:-1] # cut last comma
            exec_str += ')'
            debug_log('load_instances exec_str', exec_str)
            exec(exec_str) # garbage collection :(

    except (FileNotFoundError):
        choice = input(f"'{my_file}' doesn't exist. create? ").lower()
        if choice == 'y':
            debug_log('load_instances FileNotFoundError create', my_file)
            open(my_file, 'w')
        else:
            print("quitting")
            exit(1)

    return True

def loop():
    if len(Medication.instances) == 0:
        add_medication()

    def print_all():
        i = 0
        for med in Medication.instances:
            if med.check_nextintake():
                print(f"  {i} - {med} [{med.get_dosesremaining()}] {med.get_lastintake()}")
            else:
                print(f"✓ {i} -", strike(f"{med} [{med.get_dosesremaining()}]"))
            i += 1

    while True:
        print_all()
        choice = input("[A]dd new, [R]emove, [T]ake, [U]ntake, [I]nfo, [Q]uit: ").lower()
        try:
            # first char in index that can't be an int or space
            action_choice = [char for char in choice.split(' ') if char != '' and not safe_cast(int, char)][0]
            debug_log('action_choice', action_choice)
        except (IndexError):
            # user typed nothing
            continue
        # all chars that can be an int (return cast = False so 0 passes the condition)
        num_choice = [safe_cast(int, char) for char in choice if safe_cast(int, char, return_cast=False)]
        debug_log('num_choice', num_choice)

        if action_choice == 'a': # add
            add_medication()

        if action_choice == 'q': # quit
            break

        if action_choice == 'r': # remove
            print(num_choice)
            for index in num_choice:
                print(index)
                # catch index error
                try:
                    selected = Medication.instances[index]
                except (IndexError):
                    continue
                print(f'Delete {selected}?', end=': ')
                if input().lower() in 'y':
                    Medication.instances.remove(index)
                else:
                    continue

        if action_choice == 't': # take
            for index in num_choice:
                # catch index error
                try:
                    selected = Medication.instances[index]
                except (IndexError):
                    continue
                selected.take()


        if action_choice == 'u': # untake
            for index in num_choice:
                # catch index error
                try:
                    selected = Medication.instances[index]
                except (IndexError):
                    continue
                selected.untake()

load_instances()
loop()
save_to_file()
