# STATUS LAVEL
#
# PENDING   = todavía no fue enviada
# QUEUED    = está en cola del modelo
# REVIEW    = modelo respondió
# DONE      = validada
# FAILED    = abandonada después de N intentos

import json

with open("project.json") as f:
    project = json.load(f)

task_not_ready = []
task_ready = []
 
for task in project["tasks"]:
    # LISTA DE TAREAS DEPENDIENTES
    deps = []

    # BUSCO LAS DEPENDENCIAS POR TAREA
    if len(task["depends_on"]) > 0:                     # SI HAY DEPS
        for dep in task["depends_on"]:                  # POR CADA DEP EN DEPS
            #print(task["id"])                          # IMPRIMO CHECK
            for task_dep in project["tasks"]:           # BUSCO SI LA DEP ES LA TASK
                if task_dep["id"] == dep:               # SI ES IGUAL A LA DEP
                    if task_dep["status"] != "DONE":    # REVISO SI NO ESTA DONE
                        deps.append(dep)                # NO ESTA DONE LA AGREGO A DEPS 

    # IMPRIMIMOS LAS TASK EN PENDING
    if task["status"] == "PENDING":
        if len(deps) > 0: MENSAJE = 'NOT READY    '; task_not_ready.append(task["id"])
        else: MENSAJE = 'READY        '; task_ready.append(task)
        print(MENSAJE, task["id"]+'  - '+task["status"]+' LIST ->', deps)

print('\nTASKS NOT READY    '+str(task_not_ready))
print('TASK READY TO SEND '+str(task_ready)+'\n')

with open("microtasks.json", "w") as f:
    json.dump(task_ready, f, indent=4)