APP = muscope-blast
VERSION = 1.0.0
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name *_launcher_jobfile\* \) -exec rm {} \;

files-delete:
	files-delete $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

files-upload:
	files-upload -F stampede/ $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

apps-addupdate:
	apps-addupdate -F stampede/app.json

deploy-app: clean files-delete files-upload apps-addupdate

test:
	sbatch stampede/test.sh

jobs-submit:
	jobs-submit -F stampede/job.json

container:
	rm -f singularity/$(APP).img
	sudo singularity create --size 2000 singularity/$(APP).img
	sudo singularity bootstrap singularity/$(APP).img singularity/$(APP).def
	sudo chown --reference=singularity/$(APP).def singularity/$(APP).img

iput-container:
	rm -f singularity/$(APP).img.xz
	xz --compress --force --keep singularity/$(APP).img
	iput -fKP singularity/$(APP).img.xz

iget-container:
	iget -fKP $(APP).img.xz
	xz --decompress --force --keep $(APP).img.xz
	mv $(APP).img singularity/
	mv $(APP).img.xz stampede/

lytic-rsync-dry-run:
	rsync -n -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc.arizona.edu ssh -A -t lytic" ./ :project/muscope/apps/$(APP)

lytic-rsync:
	rsync -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc.arizona.edu ssh -A -t lytic" ./ :project/muscope/apps/$(APP)
