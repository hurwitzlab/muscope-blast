APP = ohana-blast
VERSION = 0.0.8
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
	rm -f stampede2/$(APP).img
	sudo singularity create --size 1000 stampede2/$(APP).img
	sudo singularity bootstrap stampede2/$(APP).img singularity/$(APP).def
	sudo chown --reference=singularity/$(APP).def stampede2/$(APP).img

iput-container:
	iput -fK stampede2/$(APP).img

iget-container:
	iget -fK $(APP).img
	mv $(APP).img stampede2/
	irm $(APP).img

lytic-rsync-dry-run:
	rsync -n -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/imicrobe/apps/ohana-blast

lytic-rsync:
	rsync -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/imicrobe/apps/ohana-blast
