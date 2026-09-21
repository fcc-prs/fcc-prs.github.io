import json
import sys


def date_only(s):
    return s.split('T')[0]


def get_login(s):
    return s['login']


def get_merge(s):
    return 'yes' if s == 'MERGEABLE' else 'no'


def get_labels(s):
    return ' \n'.join(node['name'] for node in s['nodes'])


def get_assignees(s):
    return ' \n'.join(node['login'] for node in s['nodes'])


wanted_keys = ['number', 'title', 'author', 'createdAt', 'updatedAt', 'mergeable', 'url', 'labels', 'assignees']
rename = {'number': 'num', 'mergeable': 'mergeOk'}
transforms = {
    'createdAt': date_only,
    'updatedAt': date_only,
    'author': get_login,
    'mergeable': get_merge,
    'labels': get_labels,
    'assignees': get_assignees,
}


def process_prs(prs, org, repo):
    rows = []
    for pr in prs:
        cols = {'repo': f'{org}/<br>{repo}'}
        for key in wanted_keys:
            if key not in pr:
                continue
            if key == 'url':
                cols['title'] = f"<a href='{pr['url']}'>{cols['title']}</a>"
            else:
                tok = rename.get(key, key)
                cols[tok] = transforms.get(key, lambda x: x)(pr[key])
        rows.append(cols)
    return rows


input_file = sys.argv[1] if len(sys.argv) > 1 else 'all_prs.json'
with open(input_file) as f:
    data = json.load(f)

pr_list = []
repo_set = []

for org_data in data.get('orgs', []):
    org = org_data['login']
    for repo in org_data['repositories']:
        name = repo['name']
        prs = repo['pullRequests']['nodes']
        if prs:
            repo_set.append(f"<a href='https://github.com/{org}/{name}'>{org}/<br>{name}</a>")
        pr_list.extend(process_prs(prs, org, name))

for repo_data in data.get('repos', []):
    owner = repo_data['owner']
    name = repo_data['name']
    prs = repo_data['pullRequests']['nodes']
    if prs:
        repo_set.append(f"<a href='https://github.com/{owner}/{name}'>{owner}/<br>{name}</a>")
    pr_list.extend(process_prs(prs, owner, name))

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump({'data': pr_list}, f, indent=4)

repo_set.sort()
with open('repo_data.json', 'w', encoding='utf-8') as f:
    json.dump({'data': repo_set}, f, indent=4)
