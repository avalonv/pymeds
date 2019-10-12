from time import time, strptime, mktime
from datetime import date, timedelta

def debug_log(*msg):
    print('log:', [item for item in msg])

def time_now() -> int:
    return round(time())


def seconds_passed(timestamp) -> int:
    return round(time_now() - timestamp)


def minutes_passed(timestamp) -> int:
    return round(seconds_passed(timestamp) / 60)


def hours_passed(timestamp) -> int:
    return round(minutes_passed(timestamp) / 60)


def days_passed(timestamp) -> int:
    return round(hours_passed(timestamp) / 24)


def date_to_timestamp(my_date) -> int:
    return int(mktime(strptime(str(my_date), '%Y-%m-%d')))


def timestamp_to_date(my_timestamp) -> str:
    return date.fromtimestamp(my_timestamp)


def increase_date(my_date, num) -> int:
    return my_date + timedelta(days=num)


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
    return safe_cast(of_type, choice)


class Medication:
    instances = []

    def __init__(
            self, name_generic: str, name_brand: str,
            dosage: str, doses_per_cycle: int, cycle_days: int, notes=None,
            cycle_end=None, created_on=None, doses_taken=0,
            total_taken=0, last_taken=None, missed_doses=0):

        # append newly created instance
        # index=len(Medication.instances) # use a dict? idk tbh
        Medication.instances.append(self)

        # the name of the medication
        # string. ex: "estradiol"
        self.name_generic = name_generic

        # brand name
        # string. ex: "estradot"
        self.name_brand = name_brand

        # dosage
        # string. ex: "100mg"
        self.dosage = dosage

        # the number of doses to be taken per cycle
        # int.    ex: 1
        self.doses_per_cycle = doses_per_cycle
        if self.doses_per_cycle < 1:
            self.doses_per_cycle = 1

        # the number of days in each cycle
        # (how long until the doses_taken counter is reset)
        # int:   ex: 3
        self.cycle_days = cycle_days
        if self.cycle_days < 1:
            self.cycle_days = 1

        # any notes about the medication
        # str.   ex: "take 2 hours after eating"
        self.notes = notes

        # the number of doses already taken
        # int.    ex: 1
        self.doses_taken = doses_taken

        # timestamp of when the med was last taken
        # int. ex: 1556080265
        self.last_taken = last_taken

        # timestamp of when the current cycle ends and the counter is reset
        # int. ex: 1556679600
        self.cycle_end = cycle_end

        # timestamp of when the medication was created
        # int: ex: 1556766000
        self.created_on = created_on

        # number of times the meds was taken
        # int: ex: 30
        self.total_taken = total_taken

        self.missed_doses = missed_doses

    def __str__(self) -> str:
        string = f"{self.name_generic}"
        if self.name_brand is not None:
            string = f"{self.name_brand} ({self.name_generic})"
        if self.dosage is not None:
            string += f" {self.dosage}"
        return string

    def take(self):
        self.last_taken = time_now()
        self.doses_taken += 1
        self.total_taken += 1

    def untake(self):
        if self.doses_taken > 0:
            self.doses_taken -= 1

        if self.total_taken > 0:
            self.total_taken -= 1

    def get_lastintake(self) -> str:
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
            if self.missed_doses:
                missed = self.missed_doses
                self.missed_doses = 0  # reset the warning after running once
                return f'last taken {base}{modifier} ago, missed {missed} dose(s)'
            else:
                return f'last taken {base}{modifier} ago'
        else:
            return ''

    def get_info(self) -> str:
        infostr = f'{str(self)}\n'
        if self.last_taken is not None:
            infostr += f'{self.get_lastintake()} '
        infostr += f'(counter resets on {timestamp_to_date(self.cycle_end)})'
        if self.notes is not None:
            infostr += f'\nnotes: {self.notes}'
        infostr += f'\ntotal taken: {self.total_taken}'
        infostr += f'\nadded on {timestamp_to_date(self.created_on)}'
        return infostr

    def get_dosesremaining(self) -> str:
        return f"{self.doses_taken}/{self.doses_per_cycle}"

    def _update(self):
        # checks if the cycle_end is in the past
        # ex: spiro last_taken = 2019-04-20 and spiro cycle_end = 1
        # if spiro last_taken (20) + spiro cycle (1) less than date today (21)
        # spiro advances to next cycle_end
        if self.cycle_end < time_now():
            debug_log(f"{self}._update - {self.cycle_end} < {time_now()}")
            # date_ce = date cycle ends
            date_ce = timestamp_to_date(self.cycle_end)
            debug_log("_update for", str(self), "starting date_ce", date_ce)

            if self.doses_taken < self.doses_per_cycle:
                self.missed_doses = self.doses_per_cycle - self.doses_taken

            # cycle_end = (cycle_end + cycle) until cycle_end + cycle > date_today
            # doses_taken = 0
            # while (date_ce + timedelta(days=self.cycle_days)) < date.today():
            while date_ce <= date.today():
                # date_ce = date_ce + timedelta(days=self.cycle_days)
                debug_log('_update increasing date_ce', date_ce)
                date_ce = increase_date(date_ce, self.cycle_days)
            self.doses_taken = 0
            debug_log('_update updated date_ce is', date_ce)

            # self.cycle_end = int(mktime(strptime(str(date_ce), '%Y-%m-%d')))
            self.cycle_end = date_to_timestamp(date_ce)

    def check_nextintake(self) -> bool:
        self._update()
        if self.doses_taken < self.doses_per_cycle:
            return True
        else:
            return False
