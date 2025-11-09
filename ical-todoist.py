import yaml
from pathlib import Path
from requests import get
from icalendar import Calendar
from datetime import datetime
from dateutil import parser
from markdownify import markdownify
from todoist_api_python.api import TodoistAPI

def main():
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
	to_remove = []
	for event in cal.walk('VEVENT'):
		new_event = Event()
		new_event.name = event.get('SUMMARY').strip()
		new_event.description = markdownify(event.get('X-ALT-DESC')).strip().replace('\n\n', ' ') # Idk why I have to do this but I do since markdownify updated
		new_event.due_date = event.get('DTSTART').dt
		events.append(new_event)

	# Order and remove older than today
	events.sort(key=lambda x: x.due_date)
	events[:] = [x for x in events if x.due_date > datetime.now().astimezone()]

	api = TodoistAPI(CONFIG['todoist_api_key'])

	if (not CONFIG['allow_duplicates']) or CONFIG['allow_sync']:
		try:
			tasks_iter = api.get_tasks(label=CONFIG['todoist_labels'])
		except Exception as error:
			print(error)

		# Extract tasks from iterator
		tasks = []
		for tasks_arr in tasks_iter:
			for task in tasks_arr:
				tasks.append(task)

		# Find tasks not present
		if CONFIG['allow_sync']:
			def removed_tasks(t):
				for event in events:
					if (event.name == t.content
					and event.description == t.description
					and event.due_date.astimezone() == t.due.date.astimezone()):
						return False
				return True
			to_remove = list(filter(removed_tasks, tasks))

		# Remove duplicates
		if not CONFIG['allow_duplicates']:
			def deduplicate(e):
				for task in tasks:
					if (e.name == task.content
					and e.description == task.description
					and e.due_date.astimezone() == task.due.date.astimezone()):
						return False
				return True
			events = list(filter(deduplicate, events))

	# Dry run
	if CONFIG['dry_run']:
		print(f'Adding: {len(events)}')
		for event in events:
			print(event)
		print()
		print(f'Removing: {len(to_remove)}')
		for task in to_remove:
			print(task)
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

	for task in to_remove:
		try:
			api.delete_task(task_id=task.id)
		except Exception as error:
			print(error)

if __name__ == "__main__":
	main()
