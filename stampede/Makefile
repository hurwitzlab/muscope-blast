APP = muscope-blast-0.0.3
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name launcher-\* \) -exec rm {} \;

upload: clean
	files-upload -F $(WORK)/$(APP) jklynch/applications

update:
	apps-addupdate -F app.json

test: clean
	sbatch test.sh

job:
	jobs-submit -F job.json

scriptsgz:
	(cd scripts && tar cvf ../bin.tgz *)

jobs-template:
	jobs-template $(APP) > job.json

jobs-submit:
	jobs-submit -F job.json
