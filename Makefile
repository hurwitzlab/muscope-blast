APP = ohana-blast
VERSION = 0.0.6
EMAIL = jklynch@email.arizona.edu

clean:
	find . \( -name \*.conf -o -name \*.out -o -name \*.log -o -name \*.param -o -name *_launcher_jobfile\* \) -exec rm {} \;

files-delete:
	files-delete $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

files-upload:
	files-upload -F stampede/ $(CYVERSEUSERNAME)/applications/$(APP)-$(VERSION)

apps-addupdate:
	apps-addupdate -F stampede/app.json

deploy-app: clean scriptsgz files-delete files-upload apps-addupdate

test: clean
	cd stampede; sbatch test.sh; cd ..

job:
	jobs-submit -F stampede/job.json

scriptsgz:
	(cd stampede/scripts && tar cvf ../bin.tgz *)

container:
	rm -f singularity/$(APP).img
	sudo singularity create --size 2048 singularity/$(APP).img
	sudo singularity bootstrap singularity/$(APP).img singularity/$(APP).def
	sudo chown --reference=singularity/${APP}.def singularity/${APP}.img

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
	rsync -n -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/imicrobe/apps/ohana-blast

lytic-rsync:
	rsync -arvzP --delete --exclude-from=rsync.exclude -e "ssh -A -t hpc ssh -A -t lytic" ./ :project/imicrobe/apps/ohana-blast
