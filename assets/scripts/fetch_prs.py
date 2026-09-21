import json
import subprocess
import sys
import yaml


def gh_graphql(query):
    result = subprocess.run(
        ['gh', 'api', 'graphql', '-f', f'query={query}'],
        capture_output=True, text=True, check=True
    )
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
            '        pullRequests(first: 30, states: OPEN) {'
            '          nodes {'
            '            number title'
            '            author { login }'
            '            createdAt updatedAt'
            '            labels(first: 10) { nodes { name } }'
            '            assignees(first: 10) { nodes { login } }'
            '            mergeable url'
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


def fetch_repo_prs(owner, name):
    query = (
        'query {'
        f'  repository(owner: "{owner}", name: "{name}") {{'
        '    pullRequests(first: 30, states: OPEN) {'
        '      nodes {'
        '        number title'
        '        author { login }'
        '        createdAt updatedAt'
        '        labels(first: 10) { nodes { name } }'
        '        assignees(first: 10) { nodes { login } }'
        '        mergeable url'
        '      }'
        '    }'
        '  }'
        '}'
    )
    data = gh_graphql(query)
    return data['data']['repository']['pullRequests']['nodes']


config_path = sys.argv[1] if len(sys.argv) > 1 else 'config.yml'
with open(config_path) as f:
    config = yaml.safe_load(f)

output = {'orgs': [], 'repos': []}

for org in config.get('organizations', []):
    print(f'Fetching org: {org}', flush=True)
    repos = fetch_org_repos(org)
    output['orgs'].append({'login': org, 'repositories': repos})

for repo in config.get('repositories') or []:
    owner = repo['owner']
    name = repo['name']
    print(f'Fetching repo: {owner}/{name}', flush=True)
    prs = fetch_repo_prs(owner, name)
    output['repos'].append({'owner': owner, 'name': name, 'pullRequests': {'nodes': prs}})

with open('all_prs.json', 'w') as f:
    json.dump(output, f, indent=2)

print('Wrote all_prs.json', flush=True)
