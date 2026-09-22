import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import yaml


def gh_graphql(query):
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={query}'],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'gh stderr: {result.stderr}', flush=True)
        print(f'gh stdout: {result.stdout}', flush=True)
        result.check_returncode()
    return json.loads(result.stdout)


def fetch_org_repos(org):
    all_repos = []
    cursor = None

    while True:
        after = f', after: "{cursor}"' if cursor else ''
        query = (
            'query {'
            f'  organization(login: "{org}") {{'
            f'    repositories(first: 100{after}, isArchived: false) {{'
            '      nodes {'
            '        name'
            '        pullRequests(first: 50, states: MERGED) {'
            '          nodes {'
            '            number title'
            '            author { login }'
            '            mergedAt'
            '            mergedBy { login }'
            '            labels(first: 10) { nodes { name } }'
            '            url'
            '          }'
            '        }'
            '      }'
            '      pageInfo { hasNextPage endCursor }'
            '    }'
            '  }'
            '}'
        )

        data = gh_graphql(query)
        page = data['data']['organization']['repositories']
        all_repos.extend(page['nodes'])

        if not page['pageInfo']['hasNextPage']:
            break
        cursor = page['pageInfo']['endCursor']

    return all_repos


def fetch_repo_merged_prs(owner, name):
    query = (
        'query {'
        f'  repository(owner: "{owner}", name: "{name}") {{'
        '    pullRequests(first: 50, states: MERGED) {'
        '      nodes {'
        '        number title'
        '        author { login }'
        '        mergedAt'
        '        mergedBy { login }'
        '        labels(first: 10) { nodes { name } }'
        '        url'
        '      }'
        '    }'
        '  }'
        '}'
    )
    data = gh_graphql(query)
    return data['data']['repository']['pullRequests']['nodes']


def within_week(merged_at_str):
    if not merged_at_str:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    merged_at = datetime.fromisoformat(merged_at_str.replace('Z', '+00:00'))
    return merged_at >= cutoff


def filter_prs(nodes):
    return [n for n in nodes if within_week(n.get('mergedAt'))]


config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yml'
with open(config_path) as f:
    config = yaml.safe_load(f)

output = {'orgs': [], 'repos': []}

for org in config.get('organizations', []):
    print(f'Fetching org: {org}', flush=True)
    repos = fetch_org_repos(org)
    filtered = [
        {**r, 'pullRequests': {'nodes': filter_prs(r['pullRequests']['nodes'])}}
        for r in repos
    ]
    output['orgs'].append({'login': org, 'repositories': filtered})

for repo in config.get('repositories') or []:
    owner = repo['owner']
    name = repo['name']
    print(f'Fetching repo: {owner}/{name}', flush=True)
    prs = filter_prs(fetch_repo_merged_prs(owner, name))
    output['repos'].append({'owner': owner, 'name': name, 'pullRequests': {'nodes': prs}})

with open('all_merged_prs.json', 'w') as f:
    json.dump(output, f, indent=2)

print('Wrote all_merged_prs.json', flush=True)
