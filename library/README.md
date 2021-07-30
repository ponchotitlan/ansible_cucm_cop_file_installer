# CUCM COP File Installer Ansible module

The **cucm_cop_upload** module connects to the target CUCM node and cancels all current upgrade processes. Afterwards, a utils upgrade initiate process is issued, and prompts are followed accordingly. If the COP file is already installed in the target CUCM node, this module does nothing.

The following exceptions are covered as per standard CLI prompts of CUCM **v.10.x, v.11.x and v.12.x**:

- Remote server unreachable
- Bad remote server credentials
- Bad remote server file path
- Bad file name in playbook (COP file not available in remote server)

If the * *DO_REBOOT* * variable in the playbook is set to True, a system reboot is issued after the COP file is uploaded. A maximum of 2 attempts is done in case reboot takes too long.

If the * *DO_LOGGING* * variable in the playbook is set to True, a dump file will be generated in the same location as the playbook with all the CLI dumps. The log file name is *<current_date>_<cucm_ip_address>.log*. Ever since Ansible does not show feedback or console prints in read time (invoking console is blocked until the current task is done), a useful workaround for real-time monitoring is the following:
```
tail -f <log_file.log>
```

The output will be similar to the following:
```
2021-06-16 09:31:19,302 - Connected (version 2.0, client OpenSSH_5.3)
2021-06-16 09:31:20,161 - Authentication (password) successful!
2021-06-16 09:31:20,832 - Command Line Interface is starting up, please wait ...

2021-06-16 09:31:26,225 -
   Welcome to the Platform Command Line Interface

2021-06-16 09:31:27,840 - VMware Installation:
        4 vCPU: Intel(R) Xeon(R) CPU E5-2643 0 @ 3.30GHz
        Disk 1: 110GB, Partitions aligned
        8192 Mbytes RAM

2021-06-16 09:31:28,768 - admin:
2021-06-16 09:31:28,890 - show version active

2021-06-16 09:31:33,662 - Active Master Version: 11.5.1.12900-21
Active Version Installed Software Options:
cmterm-devicepack9.1.2.13070-1.cop
cmterm-devicepack9.1.2.15130-1.cop

...

Start installation (yes/no):
2021-06-16 09:32:08,590 - yes
2021-06-16 09:32:08,762 - The upgrade log is install_log_2021-06-16.10.31.45.log
Upgrading the system.  Please wait...

...

2021-06-16 09:33:05,792 - Successfully installed ciscocm-ucmgmt-agent-corpccuc-cop.v20201218-495.k3.cop.sgn
```

At the same time, the console will display the result of the COP file upload and installation in a JSON object. If the installation was successful, a message with the following format will be displayed per CallManager node:

```
{
    host: 192.56.89.15 
    changed: True,
    meta: {
        COP ciscocm-ucmgmt-agent-corpccuc-cop.v20201218-495.k3.cop.sgn successfully installed
    }
},
{
    host: 192.56.78.16 
    changed: True,
    meta: {
        COP ciscocm-ucmgmt-agent-corpccuc-cop.v20201218-495.k3.cop.sgn successfully installed
    }
},
... 

```

Crafted with :heart: by [Alfonso Sandoval - Cisco](https://linkedin.com/in/asandovalros)