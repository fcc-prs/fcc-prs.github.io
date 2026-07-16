import json

# Open the file and parse the JSON content into a dictionary/list
with open("gh.json", "r") as file:
    data = json.load(file)

pr_list=[]

def dummy(s):
    return s

def date_only(s):
    return s.split('T')[0]

def get_login(s):
    return s['login']

def get_merge(s):
    if s=="MERGEABLE": return "yes"
    return "no"

wanted_keys=['number', 'title', 'author', 'createdAt', 'updatedAt', 'mergeable', 'url']
funcs={}
for key in wanted_keys:
    funcs[key]=dummy

funcs['createdAt']=date_only
funcs['updatedAt']=date_only
funcs['author']=get_login
funcs['mergeable']=get_merge

org="key4hep"

pr_infos=data['data']['organization']['repositories']['nodes']

for v in pr_infos:
    repo=v['name']
    prs=v['pullRequests']['nodes']
    for pr in prs:
        cols={}
        cols['repo']=org+"/"+repo
        for key in wanted_keys:
            if key != 'url':
                cols[key]=funcs[key](pr[key])
            else:
                cols['title']="<a href='"+pr['url']+"'>"+cols['title']+"</a>"
        pr_list.append(cols)

json_list={}
json_list['data']=pr_list

with open("data.json", "w", encoding="utf-8") as file:
    json.dump(json_list, file, indent=4)
