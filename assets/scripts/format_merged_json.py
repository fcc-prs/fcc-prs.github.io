import json
import sys
from datetime import datetime, timezone


def date_only(s):
    return s.split('T')[0] if s else ''


def get_login(node):
    return node['login'] if node else ''


def truncate(s, n):
    if not s:
        return ''
    s = s.strip()
    return s if len(s) <= n else s[:n] + '…'


def process_prs(prs, org, repo):
    rows = []
    for pr in prs:
        comments_data = pr.get('comments', {})
        comments = [
            {'author': get_login(c.get('author')), 'body': truncate(c.get('body', ''), 300)}
            for c in comments_data.get('nodes', [])
            if c.get('body', '').strip()
        ]
        reviews_data = pr.get('reviews', {})
        reviews = [
            {
                'author': get_login(r.get('author')),
                'state': r.get('state', ''),
                'body': truncate(r.get('body', ''), 300),
            }
            for r in reviews_data.get('nodes', [])
            if r.get('body', '').strip()
        ]
        rows.append({
            'org': org,
            'repo': repo,
            'num': pr['number'],
            'title': pr['title'],
            'url': pr['url'],
            'author': get_login(pr.get('author')),
            'mergedAt': date_only(pr.get('mergedAt', '')),
            'mergedBy': get_login(pr.get('mergedBy')),
            'labels': [n['name'] for n in pr.get('labels', {}).get('nodes', [])],
            'body': truncate(pr.get('body', ''), 800),
            'diff': {
                'additions': pr.get('additions', 0),
                'deletions': pr.get('deletions', 0),
                'files': pr.get('changedFiles', 0),
            },
            'files': [n['path'] for n in pr.get('files', {}).get('nodes', [])],
            'comments': comments,
            'comments_total': comments_data.get('totalCount', len(comments)),
            'reviews': reviews,
            'reviews_total': reviews_data.get('totalCount', len(reviews)),
        })
    return rows


input_file = sys.argv[1] if len(sys.argv) > 1 else 'all_merged_prs.json'
with open(input_file) as f:
    data = json.load(f)

pr_list = []

for org_data in data.get('orgs', []):
    org = org_data['login']
    for repo in org_data['repositories']:
        pr_list.extend(process_prs(repo['pullRequests']['nodes'], org, repo['name']))

for repo_data in data.get('repos', []):
    pr_list.extend(process_prs(
        repo_data['pullRequests']['nodes'],
        repo_data['owner'],
        repo_data['name'],
    ))

pr_list.sort(key=lambda r: r['mergedAt'], reverse=True)

output = {
    'updated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'data': pr_list,
}

with open('merged_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=4)
