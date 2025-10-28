import json
import pickle
import random
from datetime import date, timedelta
from pathlib import Path
from sqlite3 import connect

import numpy as np
import pandas as pd
from scipy.stats import expon, norm, skewnorm
from sklearn.linear_model import LogisticRegression

cwd = Path(".").resolve()


def left_skew(a, loc, size=500):
    r = skewnorm.rvs(a=a, loc=loc, size=size)
    r = r - min(r)
    r = r / max(r)
    r = r * loc
    r = r.astype(int)
    return random.choice(r)


profiles = {
    "good": {
        "positive": lambda: norm.rvs(loc=norm.rvs(4), scale=1).astype(int),
        "negative": lambda: expon.rvs(loc=0, scale=np.random.choice([0.5, 1])).astype(
            int
        ),
        "chance": 0.5,
    },
    "normal": {
        "positive": lambda: norm.rvs(loc=norm.rvs(3), scale=1).astype(int),
        "negative": lambda: norm.rvs(
            loc=2, scale=np.random.choice([0.5, 1, 2, 3])
        ).astype(int),
        "chance": 0.15,
    },
    "poor": {
        "positive": lambda: expon.rvs(loc=0, scale=0.5).astype(int),
        "negative": lambda: norm.rvs(loc=0.5).astype(int),
        "chance": 0.1,
    },
    "chaotic_good": {
        "positive": lambda: left_skew(-1000, 5).astype(int),
        "negative": lambda: np.random.choice(
            [0, np.random.choice([50, 200])], p=[0.98, 0.02]
        ),
        "chance": 0.2,
    },
    "chotic_bad": {
        "positive": lambda: expon.rvs(loc=0, scale=5).astype(int),
        "negative": lambda: left_skew(-1000, 10).astype(int),
        "chance": 0.2,
    },
}

employees = {}
is_recruited = lambda x: np.random.choice([0, 1], p=[1 - x, x])

for employee_id in range(1, 26):

    employee_type = random.choice(list(profiles.keys()))
    event_distribution = profiles[employee_type]
    team_id = random.choice(range(1, 6))
    recruited = is_recruited(event_distribution["chance"])

    employees[employee_id] = dict(
        employee_type=employee_type,
        event_distribution=event_distribution,
        team_id=team_id,
        recruited=recruited,
    )


today = date.today()
last_year = today - timedelta(days=365)
daterange = pd.date_range(last_year, today)
data = []

for day in daterange:

    if day.weekday() < 5:

        for employee, config in employees.items():
            config["events"] = config.get("events", {})
            employee_type = config["employee_type"]
            positive = profiles[employee_type]["positive"]()
            negative = profiles[employee_type]["negative"]()
            data.append(
                [
                    employee,
                    config["team_id"],
                    day.strftime("%Y-%m-%d"),
                    positive,
                    negative,
                    config["recruited"],
                ]
            )


df = pd.DataFrame(
    data,
    columns=[
        "employee_id",
        "team_id",
        "event_date",
        "positive_events",
        "negative_events",
        "recruited",
    ],
)

data_path = cwd / "generated_data"
employees_path = data_path / "employees.json"
managers_path = data_path / "managers.json"
shifts_path = data_path / "shifts.json"
teams_path = data_path / "team_names.json"

with employees_path.open("r") as file:
    employee = json.load(file)

with managers_path.open("r") as file:
    managers = json.load(file)

with shifts_path.open("r") as file:
    shift = json.load(file)

with teams_path.open("r") as file:
    team_names = json.load(file)

_ = []
for idx, e in enumerate(employee, start=1):

    for note in e["notes"]:
        _.append([idx, e["name"], note])

notes = pd.DataFrame(_, columns=["employee_id", "employee_name", "note"]).assign(
    event_date=np.random.choice(df.event_date, size=len(_), replace=True)
)


df = df.merge(
    notes[["employee_id", "event_date", "note"]],
    on=["employee_id", "event_date"],
    how="left",
).merge(notes[["employee_id", "employee_name"]].drop_duplicates(), on=["employee_id"])

df = df.assign(shift=df.team_id.apply(lambda x: shift[x - 1]))

team_map = {}
for team in df.team_id.unique():
    team_map[team] = random.choice(managers)

df["manager_name"] = df.team_id.map(team_map)
df["team_name"] = df.team_id.apply(lambda x: team_names[x - 1])


employee = df.drop_duplicates("employee_id").assign(
    first_name=lambda x: x.employee_name.str.split().str[0],
    last_name=lambda x: x.employee_name.str.split().str[1],
)[["employee_id", "first_name", "last_name", "team_id"]]

events = df[
    ["event_date", "employee_id", "team_id", "positive_events", "negative_events"]
]

team = df.drop_duplicates("team_id")[["team_id", "team_name", "shift", "manager_name"]]

notes = df.dropna()[["employee_id", "team_id", "note", "event_date"]].rename(
    columns={"event_date": "note_date"}
)

model = LogisticRegression(penalty=None)

X = events.groupby("employee_id")[["positive_events", "negative_events"]].sum()
y = X.join(
    df.drop_duplicates("employee_id").set_index("employee_id")[["recruited"]]
).recruited

model.fit(X, y)

X.assign(true=y, pred=model.predict_proba(X)[:, 1])


model_path = cwd.parent / "assets" / "model.pkl"

with model_path.open("wb") as file:

    pickle.dump(model, file)


db_path = cwd.parent / "python-package" / "employee_events" / "employee_events.db"

connection = connect(db_path)

employee.to_sql("employee", connection, if_exists="replace")
team.to_sql("team", connection, if_exists="replace")
notes.to_sql("notes", connection, if_exists="replace")
events.to_sql("employee_events", connection, if_exists="replace")

connection.close()
