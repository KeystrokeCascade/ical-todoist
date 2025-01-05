#!/usr/bin/python
import yaml
from pathlib import Path
from requests import get
from icalendar import Calendar
from datetime import datetime
from markdownify import markdownify
from todoist_api_python.api import TodoistAPI

# Open config
with open(Path(__file__).with_name('config.yaml'), 'r', encoding='utf8') as f:
	CONFIG = yaml.safe_load(f)

# Read calendar file
if CONFIG['ical_url']:
	req = get(CONFIG['ical_url'])
	if req.status_code != 200:
		print(f'HTTP Error: {req.status_code}')
		exit(1)
	cal = Calendar.from_ical(req.text)

elif CONFIG['ical_file']:
	with open(Path(CONFIG['ical_file'])) as f:
		cal = Calendar.from_ical(f.read())

else:
	print('No calendar file specified.')
	exit(1)

# Get events
class Event:
	name = None
	description = None
	due_date = None
	def __str__(self):
		return f'Name: {self.name}\nDesc: {self.description}\nDate:{self.due_date}'

events = []
for event in cal.walk('VEVENT'):
	new_event = Event()
	new_event.name = event.get('SUMMARY').strip()
	new_event.description = markdownify(event.get('X-ALT-DESC')).strip()
	new_event.due_date = event.get('DTSTART').dt
	events.append(new_event)

# Order and remove older than today
events.sort(key=lambda x: x.due_date)
events[:] = [x for x in events if x.due_date > datetime.now().astimezone()]

api = TodoistAPI(CONFIG['todoist_api_key'])

# Remove duplicates
if not CONFIG['allow_duplicates']: 
	try:
		tasks = api.get_tasks(label=CONFIG['todoist_labels'])
	except Exception as error:
		print(error)
	
	def deduplicate(e):
		for task in tasks:
			if (e.name == task.content
			and e.description == task.description
			and e.due_date.astimezone() == datetime.fromisoformat(task.due.datetime).astimezone()):
				return False
		return True
	events = list(filter(deduplicate, events))

# Dry run
if CONFIG['dry_run']:
	for event in events:
		print(event)
	exit(0)

# Push to Todoist
for event in events:
	try:
		task = api.add_task(
			content=event.name,
			description=event.description,
			project_id=CONFIG['todoist_project'],
			section_id=CONFIG['todoist_section'],
			parent_id=CONFIG['todoist_parent'],
			labels=CONFIG['todoist_labels'],
			due_datetime=str(event.due_date))
	except Exception as error:
		print(error)