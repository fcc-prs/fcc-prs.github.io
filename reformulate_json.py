import json
import sys
# Open the file and parse the JSON content into a dictionary/list
datas=[]
orgs=[]
for f in sys.argv[1:]:
    orgs.append(f.split('.')[0].split('/')[-1])
    with open(f, "r") as file:
        data = json.load(file)
        datas.append(data)
        
pr_list=[]
repo_list=[]

def dummy(s):
    return s

def date_only(s):
    return s.split('T')[0]

def get_login(s):
    return s['login']

def get_merge(s):
    if s=="MERGEABLE": return "yes"
    return "no"

def get_labels(s):
    o=''
    node_info = s['nodes']
    
    for i,node in enumerate(node_info):
        if i!=0:
            o=o+' \n'
        o=o+node['name']
    return o

def get_assignees(s):
    o=''
    node_info = s['nodes']
    
    for i,node in enumerate(node_info):
        if i!=0:
            o=o+' \n'
        o=o+node['login']
    return o
    
wanted_keys=['number', 'title', 'author', 'createdAt', 'updatedAt', 'mergeable', 'url', 'labels', 'assignees']
funcs={}
for key in wanted_keys:
    funcs[key]=dummy

funcs['createdAt']=date_only
funcs['updatedAt']=date_only
funcs['author']=get_login
funcs['mergeable']=get_merge
funcs['labels']=get_labels
funcs['assignees']=get_assignees

for i,data in enumerate(datas):
    org=orgs[i]
    pr_infos=data['data']['organization']['repositories']['nodes']
    for v in pr_infos:
        repo=v['name']
        if repo not in repo_list: repo_list.append("<a href='https://github.com/"+repo+"'>"+repo+"</a>")
        prs=v['pullRequests']['nodes']
        for pr in prs:
            cols={}
            cols['repo']=org+"/"+repo
            for key in wanted_keys:
                if key not in pr: continue 
                if key != 'url':
                    cols[key]=funcs[key](pr[key])
                else:
                    cols['title']="<a href='"+pr['url']+"'>"+cols['title']+"</a>"
            pr_list.append(cols)

json_list={}
json_list['data']=pr_list

with open("data.json", "w", encoding="utf-8") as file:
    json.dump(json_list, file, indent=4)

json_pr_list={}
json_pr_list['data']=repo_list

with open("repo_data.json", "w", encoding="utf-8") as file:
    json.dump(json_pr_list, file, indent=4)

