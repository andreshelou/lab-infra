import json

with open("project.json") as f:
    project = json.load(f)

with open("microtasks.json") as f:
    microtasks = json.load(f)

task_not_ready = []
task_ready = []
 
for task in project["tasks"]:

    deps = []

    if len(task["depends_on"]) > 0:
        for dep in task["depends_on"]:
            for task_dep in project["tasks"]:
                if task_dep["id"] == dep:
                    if task_dep["status"] != "DONE":
                        deps.append(dep)


    if task["status"] == "PENDING":
        if len(deps) > 0:
            task_not_ready.append(task["id"])
        else:
            exists = False

            for microtask in microtasks:
                if microtask["id"] == task["id"]:
                    exists = True

            if exists == False:
                task_ready.append(task)
                task["status"] = "QUEUED"
            else:
                task["status"] = "QUEUED"

with open("project.json", "w") as g:
    json.dump(project, g, indent=4)

microtasks.extend(task_ready)

with open("microtasks.json", "w") as f:
    json.dump(microtasks, f, indent=4)