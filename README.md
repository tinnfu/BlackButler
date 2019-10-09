# BlackButler
do everything by file defined

# ABSTR
as plan9, communicate with deamon BlackButler with different filepath.
such as:
1. run a period task
    + move a executable bin or script into /path/to/BlackButler/period/seconds/1/myTask1s.sh, it will be run per 1s
    + move a executable bin or script into /path/to/BlackButler/period/minutes/1/myTask1min.sh, it will be run per 1min
    + move a executable bin or script into /path/to/BlackButler/period/hours/1/myTask1hour.sh, it will be run per 1hour
    + period/days/, period/week/, and so on.
2. manage documents
    + collect all file and classify them by time created, type, size and name
    + but do not move them, just make a soft link for them into different dir(with different name, like 20191007/, mp4/, and so on)
3. shadow some sensitive documents( by a json config file)
    + way 1: rename them into other shadow filename, such as: xxx.avi -> .xxx.avi.x. In this way computer will not recognize them and display thumbnail (hehehehehehehehehehehehehehehehehehehehe...)
    + way 2: tar zcf file into package
    + way 3: encrypt file
4. an op path
    + /path/to/BlackButler/op/stop/shadow, will stop shadow file operation
    + /path/to/BlackButler/op/stop/period/seconds/1/myTask1s.sh, will stop run myTask1s.sh operation
    + /path/to/BlackButler/op/stop/BlackButler, will stop BlackButler deamon
    + /path/to/BlackButler/op/upgrade, will upgrade BlackButler from github
    + and so on
5. let me see see ...
