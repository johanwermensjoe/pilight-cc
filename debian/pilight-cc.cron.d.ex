#
# Regular cron jobs for the pilight-cc package
#
0 4	* * *	root	[ -x /usr/bin/pilight-cc_maintenance ] && /usr/bin/pilight-cc_maintenance
