APP = aloha-blast
VERSION = 1.0.0
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name *_launcher_jobfile\* \) -exec rm {} \;

files-delete:
	files-delete $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

files-upload:
	files-upload -F stampede2/ $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

apps-addupdate:
	apps-addupdate -F stampede2/app.json

deploy-app: clean files-delete files-upload apps-addupdate

test: clean
	cd stampede2; sbatch test.sh; cd ..

submit-test-job:
	jobs-submit -F stampede2/job.json

submit-public-test-job:
	jobs-submit -F stampede2/job-public.json

container:
	rm -f singularity/$(APP)-$(VERSION).img
	sudo singularity create --size 1000 singularity/$(APP)-$(VERSION).img
	sudo singularity bootstrap singularity/$(APP)-$(VERSION).img singularity/$(APP).def
	sudo chown --reference=singularity/$(APP).def singularity/$(APP)-$(VERSION).img

iput-container:
	iput -fK singularity/$(APP)-$(VERSION).img

iget-container:
	cd /work/05066/imicrobe/singularity/; iget -fK $(APP)-$(VERSION).img; chmod ag+r $(APP)-$(VERSION).img
	irm $(APP)-$(VERSION).img

lytic-rsync-dry-run:
	rsync -n -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/imicrobe/apps/aloha-blast

lytic-rsync:
	rsync -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/imicrobe/apps/aloha-blast
