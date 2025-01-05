# Ical-Todoist
A small script that can read an ical file from a link or filesystem and push its contents to Todoist.

---

Requres PyYAML, icalendar, todoist-api-python and markdownify libraries.

To get started, copy `config.yaml.sample` into `config.yaml` if you want to use a template.

```
cp config.yaml.sample config.yaml
```

## Config File Parameters

| Parameter | Type | Explanation |
| --- | --- | --- |
| `ical_url` 			| String 		| URL to the raw ical file |
| `ical_file`			| String	 	| Local path to the ical file |
| `todoist_api_key` 	| String 		| API key token for Todoist account |
| `todoist_project` 	| String 		| Parent project ID.  If not set task will be put into Inbox |
| `todoist_section` 	| String 		| Parent section ID.  If not set task will not be put in a section |
| `todoist_parent` 		| String	 	| Parent task ID.  If not set task will be put at the top level |
| `todoist_labels`		| String Array 	| Labels to assign to generated tasks |
| `allow_duplicates`	| Boolean 		| Allow duplicate tasks to be uploaded.  Recommended to set to `true` if `todoist_label` is not set |
| `dry_run`				| Boolean 		| Prints out tasks to create to console instead of creating them |

If both `ical_url` and `ical_file` are provided, the url will be prioritised.

Duplicates are checked by name, description and due date against tasks with a label within `todoist_label`.

---

To use with Microsoft Shifts for Teams I used the Power Automate example "Forward my Shifts Schedule to my calendar" with trigger replaced with "When a Shift is created, updated or deleted" and final node replaced with "Update file" from OneDrive for Business, pointing at a .ical file shared publicly with a link and file content set to Response.

This file can be accessed raw by copying the share link and adding "&download=1" to the end.