# ansible_cucm_cop_file_installer

[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com) 

Ansible is nowadays the de-facto DevOps technology for IT automation. Ansible modules and playbooks can automate a wide variety of tasks across many devices of multiple vendors. From services management and deployment, to more complex orchestration, Ansible can handle massive operations throughout a network. 

Cisco technologies are no exception. This repository includes an Ansible module developed in Python for automating the uploading and installation of general purpose COP files in Cisco CallManager (CUCM) servers for adding extra functionalities, such as add-ons, language packs and beyond. Although this process can be done manually via the Web UI or even through SSH CLI, it is very prone to human errors, plus not compatible with massive deployments. Hence the purpose of this Ansible module.

# Setting up the environment

- Ansible must be installed in the host OS
- Python v.3.6.9 must be installed. This must be the only python version in the virtual environment or host OS

Install the dependencies included in this repository with the following command:
```
pip install -r requirements.txt
```

Copy the files of this repository in your local environment. Make sure that the playbook file is located in the same directory as the * *library* * folder.

Prepare your hosts file with the CUCM servers of interest, as mentioned in the example **host** file of this repository: 
```
[mycallmanagers]
ansible_ssh_host=<your_ip_address> ansible_user=<your_ssh_username> ansible_ssh_pass=<your_ssh_password>
ansible_ssh_host=<your_ip_address> ansible_user=<your_ssh_username> ansible_ssh_pass=<your_ssh_password>
ansible_ssh_host=<your_ip_address> ansible_user=<your_ssh_username> ansible_ssh_pass=<your_ssh_password>
. . .
```

# Setting up the playbook

Update the **cucm_cop_upload.yml** playbook with the following information:
```
- name: CallManager COP Uploader
  hosts: mycallmanagers
  connection: local
  gather_facts: no
  tasks:
    - name: COP upload
      cucm_cop_upload:
        CUCM_IP: "{{ansible_ssh_host}}"
        CUCM_SSH_USERNAME: "{{ansible_user}}"
        CUCM_SSH_PASSWORD: "{{ansible_ssh_pass}}"
        REMOTE_SERVER: "<FTP/SFTP server address>"
        REMOTE_USERNAME: "<FTP/SFTP server username>"
        REMOTE_PASSWORD: "<FTP/SFTP server password>"
        REMOTE_DIRECTORY: "<FTP/SFTP server COP file route>"
        REMOTE_SMTP: ''
        REMOTE_FILE: "<COP file name>"
        REMOTE_SERVER_TYPE: "FTP" or "SFTP"
        DO_REBOOT: True/False
        DO_LOGGING: True/False
      register: result
    - debug: var=result
```

Leave the fields of CUCM_IP, CUCM_SSH_USERNAME and CUCM_SSH_PASSWORD as mentioned in the playbook given that the token notation will extract the values of the specified CUCM hosts group as stated in the **hosts** file.

The following is a more detailed explanation of the rest of the fields in the playbook:

- **REMOTE_SERVER:** Adress of the FTP/SFTP server where the COP file is located
- **REMOTE_USERNAME:** Username of the FTP/SFTP server where the COP file is located
- **REMOTE_PASSWORD:** Password of the FTP/SFTP server where the COP file is located
- **REMOTE_DIRECTORY:** Directory of the FTP/SFTP server where the COP file is located
- **REMOTE_SMTP:** SMTP of the FTP/SFTP server where the COP file is located (optional)
- **REMOTE_FILE:** Name of the COP file to be uploaded and installed. The name must include the extension of the file (ex: .cop.sgn)
- **REMOTE_SERVER_TYPE:** Server type to connecto to (FTP/STFP)
- **DO_REBOOT:** Option to reboot the CallManager server once the COP installation is complete (True/False)
- **DO_LOGGING:** Option to do extensive login of the SSH interaction in a file stored locally (True/False)

# Running the Ansible module

In order to run the playbook, issue the following command:
```
ansible-playbook cop_playbook.yml'
```

In case python3 is not the only version installed in the host system, issue the following command:
```
ansible-playbook my_playbook.yaml -e 'ansible_python_interpreter=/usr/bin/python3'
```

See the README.md file in the "library" folder for more information regarding the Ansible module.

Crafted with :heart: by [Alfonso Sandoval - Cisco](https://linkedin.com/in/asandovalros)