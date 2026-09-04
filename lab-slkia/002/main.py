import os
import shutil
import json

# DEFINIMOS VARIABLES
cardinal_tasks: int = 4    # CANTODNDA DE TASK A CREAR
tasksDirectory: list = []   # CREO LA LISTA DEL DIRECTORIO DE TAREAS
task_dir = "tasks"          # NOMBDE DEL DIRECTORIO DONDE ALOJAMOS LAS TAREAS


# LIMPIO LAS TASKS DE FILESYSTEM EXISTENTES
if os.path.exists(task_dir):
    shutil.rmtree(task_dir)

# RECREO EL DIRECTORIO DE TASKS DESDE CERO
os.makedirs(task_dir)


# CREO EL DIRECORIO DE TAREAS EN EL TASK_DIRECTOY.JSON
for i in range(cardinal_tasks):
    task_id = str(i)
    task: dict = {
                    "id": task_id, 
                    "name": "Task name "+task_id,
                    "path": task_dir+"/"+task_id+".json",
                    "status": "",
                    "deps": [],
                }
    tasksDirectory.append(task)


# SEPARO CADA TASK Y LAS METO DENTRO DEL DIRECTORIO TASKS
for task in tasksDirectory:
    task_path: str = task["path"]

    with open(task_path, "w") as file:
        json.dump(task, file, indent = 4)
    

# GUARDO EL DIRECTORIO TASKS_DIRECORY
with open("tasksDirectory.json", "w") as file:
    json.dump(tasksDirectory, file, indent=4)



