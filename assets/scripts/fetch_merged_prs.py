import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

import yaml

MAX_RETRIES = 5


def gh_graphql(query):
    for attempt in range(MAX_RETRIES):
        result = subprocess.run(
            ['gh', 'api', 'graphql', '-f', f'query={query}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        print(f'Attempt {attempt + 1} failed — stderr: {result.stderr.strip()}', flush=True)
        if attempt < MAX_RETRIES - 1:
            wait = 2 ** attempt
            print(f'Retrying in {wait}s...', flush=True)
            time.sleep(wait)
    result.check_returncode()


def fetch_org_repo_names(org):
    """Return a list of repo names for the org (no PR data)."""
    names = []
    cursor = None

    while True:
        after = f', after: "{cursor}"' if cursor else ''
        query = (
            'query {'
            f'  organization(login: "{org}") {{'
            f'    repositories(first: 100{after}, isArchived: false) {{'
            '      nodes { name }'
            '      pageInfo { hasNextPage endCursor }'
            '    }'
            '  }'
            '}'
        )
        data = gh_graphql(query)
        page = data['data']['organization']['repositories']
        names.extend(n['name'] for n in page['nodes'])

        if not page['pageInfo']['hasNextPage']:
            break
        cursor = page['pageInfo']['endCursor']

    return names


def fetch_org_repos(org):
    """Fetch merged PRs for each repo in the org, one repo at a time."""
    repo_names = fetch_org_repo_names(org)
    repos = []
    for name in repo_names:
        prs = fetch_repo_merged_prs(org, name)
        repos.append({'name': name, 'pullRequests': {'nodes': prs}})
    return repos


def fetch_repo_merged_prs(owner, name):
    query = (
        'query {'
        f'  repository(owner: "{owner}", name: "{name}") {{'
        '    pullRequests(first: 50, states: MERGED, orderBy: {field: UPDATED_AT, direction: DESC}) {'
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
