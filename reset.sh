lord nuke --sure --really
lord setup --name logger --wait 1 --attempts 3
lord run pyjob "python jobs/badpyjob.py" --wait 1
lord run pyjob "python jobs/badpyjob.py" --wait 1
lord run pyjob "python jobs/pyjob.py" --wait 1
