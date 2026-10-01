import json
import sys


def date_only(s):
    return s.split('T')[0]


def get_login(s):
    return s['login']


def get_labels(s):
    return ' \n'.join(node['name'] for node in s['nodes'])


def get_assignees(s):
    return ' \n'.join(node['login'] for node in s['nodes'])


wanted_keys = ['number', 'title', 'author', 'createdAt', 'updatedAt', 'url', 'labels', 'assignees']
rename = {'number': 'num'}
transforms = {
    'createdAt': date_only,
    'updatedAt': date_only,
    'author': get_login,
    'labels': get_labels,
    'assignees': get_assignees,
}


def process_issues(issues, org, repo):
    rows = []
    for issue in issues:
        cols = {'repo': f'{org}/<br>{repo}'}
        for key in wanted_keys:
            if key not in issue:
                continue
            if key == 'url':
                cols['title'] = f"<a href='{issue['url']}'>{cols['title']}</a>"
            else:
                tok = rename.get(key, key)
                cols[tok] = transforms.get(key, lambda x: x)(issue[key])
        rows.append(cols)
    return rows


input_file = sys.argv[1] if len(sys.argv) > 1 else 'all_issues.json'
with open(input_file) as f:
    data = json.load(f)

issue_list = []
repo_set = []

for org_data in data.get('orgs', []):
    org = org_data['login']
    for repo in org_data['repositories']:
        name = repo['name']
        issues = repo['issues']['nodes']
        if issues:
            repo_set.append(f"<a href='https://github.com/{org}/{name}'>{org}/<br>{name}</a>")
        issue_list.extend(process_issues(issues, org, name))

for repo_data in data.get('repos', []):
    owner = repo_data['owner']
    name = repo_data['name']
    issues = repo_data['issues']['nodes']
    if issues:
        repo_set.append(f"<a href='https://github.com/{owner}/{name}'>{owner}/<br>{name}</a>")
    issue_list.extend(process_issues(issues, owner, name))

with open('issues_data.json', 'w', encoding='utf-8') as f:
    json.dump({'data': issue_list}, f, indent=4)

repo_set.sort()
with open('issues_repo_data.json', 'w', encoding='utf-8') as f:
    json.dump({'data': repo_set}, f, indent=4)
