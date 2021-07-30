#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: cucm_cop_upload
short_description: Ansible module for Cisco CallManager COP file upload and install 
description:
    - This module logs in the provided CUCM servers via SSH and executes the COP file upload process
    - The entire process is done via an interactive SSH console, however no input is required: the module handles all steps by itself
    - Please verify options and example for supported usage
version_added: "2.5.1"
author: "Alfonso Sandoval Rosas"
options:
# One or more of the following
    CUCM_IP:
        description:
            - Target IP address of the CUCM server
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    CUCM_SSH_USERNAME:
        description:
            - SSH-enabled username of the CUCM server
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    CUCM_SSH_PASSWORD:
        description:
            - SSH-enabled password of the CUCM server
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_SERVER:
        description:
            - Adress of the FTP/SFTP server where the COP file is located
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_USERNAME:
        description:
            - Username of the FTP/SFTP server where the COP file is located
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_PASSWORD:
        description:
            - Password of the FTP/SFTP server where the COP file is located
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_DIRECTORY:
        description:
            - Directory of the FTP/SFTP server where the COP file is located
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_SMTP:
        description:
            - SMTP of the FTP/SFTP server where the COP file is located
        required: false
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_FILE:
        description:
            - Name of the COP file to be uploaded and installed. The name must include the extension of the file (ex: .cop.sgn)
        required: true
        default: null
        choices:
          - null
        aliases:
          - null
        version_added: "1.5"
    REMOTE_SERVER_TYPE:
        description:
            - Server type to connecto to (FTP/STFP)
        required: true
        default: null
        choices:
          - FTP
          - SFTP
        aliases:
          - null
        version_added: "1.5"
    DO_REBOOT:
        description:
            - Option to reboot the CallManager server once the COP installation is complete
        required: true
        default: null
        choices:
          - True
          - False
        aliases:
          - null
        version_added: "1.5"
    DO_LOGGING:
        description:
            - Option to do extensive login of the SSH interaction in a file stored locally
        required: true
        default: null
        choices:
          - True
          - False
        aliases:
          - null
        version_added: "1.5"
notes:
    - CallManager Publishers and Subscribers are supported
    - CallManager versions supported are v11.x and v12.x
    - DO NOT HALT THE EXECUTION OF THE PROCESS, as the interruption of a COP file upload/installation can result in the process getting stuck and the necessity of restarting the server
requirements:
    - ansible==2.9.12
    - paramiko==2.0.0
    - paramiko-expect==0.2.8
'''

EXAMPLES = '''
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
        REMOTE_SERVER: "192.168.0.15"
        REMOTE_USERNAME: "mysftpuser"
        REMOTE_PASSWORD: "mysftppassword123"
        REMOTE_DIRECTORY: "/cop_files/current/"
        REMOTE_SMTP: ''
        REMOTE_FILE: "ciscocucm-latest-copfile-495.k3.cop.sgn"
        REMOTE_SERVER_TYPE: "SFTP"
        DO_REBOOT: False
        DO_LOGGING: True
      register: result
    - debug: var=result
'''

import re, paramiko, logging, datetime
from paramiko_expect import SSHClientInteraction
from ansible.module_utils.basic import AnsibleModule

COP_RESULT = {}

def ssh_connector(IP, USERNAME, PASSWORD, DO_LOGGING):
    CUCM_IP = IP
    CUCM_SSH_USERNAME = USERNAME
    CUCM_SSH_PASSWORD = PASSWORD
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(CUCM_IP, username=CUCM_SSH_USERNAME, password=CUCM_SSH_PASSWORD, timeout=25)
    if DO_LOGGING:
        interact = SSHClientInteraction(ssh, display=True, output_callback = lambda m: logging.warning(m))
    else:
         interact = SSHClientInteraction(ssh, display=False) 
    return [ssh,interact]

def get_cucm_version(interact):
    interact.send('show version active')
    interact.expect('admin:')
    output = interact.current_output_clean
    cli_lines_active=output.split('\n')
    for line in cli_lines_active:
        if 'Active Master Version: ' in line:
                if '11.' in line:
                    return '11.x'
                elif '12.' in line:
                    return '12.x'

def get_node_type(interact,name):
    interact.send(f'run sql SELECT processnode.tknodeusage from callmanager LEFT JOIN processnode on callmanager.fkprocessnode=processnode.pkid WHERE processnode.name="{name}"')
    interact.expect('admin:')
    output = interact.current_output_clean
    if '0' in output:
        return 'Publisher'
    else:
        return 'Subscriber'

def get_node_name(interact,target_ip):
    possible_names = []
    node_name = ''
    interact.send('show tech network hosts')
    interact.expect('admin:')
    output = interact.current_output_clean
    cli_lines=output.split('\n')
    #Creation of a list with the structure IP:fqdn:hostname
    for line in cli_lines:
        if target_ip in line:
            possible_names = line.split(' ')
            break
    #Retrieval of processnode names
    interact.send('run sql select name from processnode')
    interact.expect('admin:')
    output = interact.current_output_clean.split('\n')
    for current_name in possible_names:
        for target_name in output:
            if current_name!='' and (current_name.lower() == target_name.lower().strip()):
                return target_name
    return node_name

def do_system_reboot(interact):
    interact.send('utils system restart')
    interact.expect(['.*(yes/no)?.*','.*restart.*'], timeout = 10)
    interact.send('yes')
    interact.expect(['.*The system is going down for reboot NOW!.*','.*(yes/no).*','.*restart.*'],timeout = 300)
    if interact.last_match == '.*(yes/no)?.*' or interact.last_match == '.*restart.*':
        interact.send('yes')
        interact.expect('.*The system is going down for reboot NOW!.*',timeout = 300)

def find_file_index(output_text,filename):
    for LINE in output_text:
        if filename in LINE:
            return re.search(r'(\d+).+', LINE, re.IGNORECASE).group(1)
    return False

def sftp_ftp_loading(interact,REMOTE_SERVER_TYPE,REMOTE_DIRECTORY,REMOTE_SERVER,REMOTE_USERNAME,REMOTE_PASSWORD,REMOTE_SMTP,REMOTE_FILE,DO_REBOOT,CUCM_VERSION):
    if REMOTE_SERVER_TYPE == 'SFTP':
        interact.send('1')
    else:
        interact.send('2')
    interact.expect('.*Directory.*',timeout = 5)
    interact.send(REMOTE_DIRECTORY)
    interact.expect('.*Server.*',timeout = 5)
    interact.send(REMOTE_SERVER)
    interact.expect('.*User Name.*',timeout = 5)
    interact.send(REMOTE_USERNAME)
    interact.expect('.*Password.*',timeout = 5)
    interact.send(REMOTE_PASSWORD)
    interact.expect('.*Please enter SMTP Host Server.*',timeout = 5)
    interact.send(REMOTE_SMTP)
    
    #The following 2 prompts will appear only on CUCM v12.x
    if CUCM_VERSION == '12.x':    
        interact.expect('.*Continue with upgrade after download.*',timeout = 5)
        interact.send('no')
        interact.expect('.*Switch-version server after upgrade.*',timeout = 5)
        interact.send('no')
    
    #Normal SSH flow
    try:    
        interact.expect(['.*Please select an option.*','admin:'],timeout = 1800)
        #Get index and start file upload
        if interact.last_match == '.*Please select an option.*':
            file_index = find_file_index(interact.current_output_clean.split('\n'),REMOTE_FILE)
            if not file_index:
                logging.error(f'The specified COP file {REMOTE_FILE} was not found in the specified location')
                COP_RESULT['changed'] = False
                COP_RESULT['meta'] = f'The specified COP file {REMOTE_FILE} was not found in the specified location'
                return False
            else:
                interact.send(file_index)
                interact.expect(['.*Start installation.*','admin:'],timeout = 1800)
                #Check if the upload was successful
                if interact.last_match == '.*Start installation.*':
                    interact.send('yes')
                    interact.expect('.*Successfully installed.*',timeout = 600)                    
                    #If the installation was successful and reboot is required, issue it now
                    if DO_REBOOT:                        
                        COP_RESULT['changed'] = True
                        COP_RESULT['meta'] = f'CUCM rebooted. COP {REMOTE_FILE} successfully installed'
                        do_system_reboot(interact)
                    else:
                        COP_RESULT['changed'] = True
                        COP_RESULT['meta'] = f'COP {REMOTE_FILE} successfully installed'
                    return True
                else:
                    #Handle errors in SFTP/FTP collection
                    logging.error(interact.current_output_clean)
                    COP_RESULT['changed'] = True
                    COP_RESULT['meta'] = interact.current_output_clean
                    return False
        else:
            #Handle errors in SFTP/FTP collection
            logging.error(interact.current_output_clean)
            COP_RESULT['changed'] = False
            COP_RESULT['meta'] = interact.current_output_clean
            return False
    except:
        logging.error('TIMEOUT! Please check remote server IP address')
        COP_RESULT['changed'] = False
        COP_RESULT['meta'] = 'TIMEOUT! Please check remote server IP address'
        return False

def check_cop_existance(interact, REMOTE_FILE):
    VALID = False
    interact.send('show version active')
    interact.expect('admin:')
    output = interact.current_output_clean
    cli_lines_active=output.split('\n')
    REMOTE_FILE_FINAL = REMOTE_FILE.replace('.sgn','')
    for line in cli_lines_active:
        if(REMOTE_FILE_FINAL in line):
            VALID = True
            break
    return VALID

def run_module():
    fields = {
        'CUCM_IP' : { 'required': True, 'type': 'str' },
        'CUCM_SSH_USERNAME' : { 'required': True, 'type': 'str' },
        'CUCM_SSH_PASSWORD' : { 'required': True, 'type': 'str', 'no_log': True },
        'REMOTE_SERVER' : { 'required': True, 'type': 'str' },
        'REMOTE_USERNAME' : { 'required': True, 'type': 'str' },
        'REMOTE_PASSWORD' : { 'required': True, 'type': 'str', 'no_log': True  },
        'REMOTE_DIRECTORY' : { 'required': True, 'type': 'str' },
        'REMOTE_SMTP' : { 'required': False, 'type': 'str' },
        'REMOTE_FILE' : { 'required': True, 'type': 'str' },
        'REMOTE_SERVER_TYPE' : { 'required': True, 'type': 'str' },
        'DO_REBOOT' : { 'required': True, 'type': 'bool' },
        'DO_LOGGING' : { 'required': True, 'type': 'bool' }
    }
    module = AnsibleModule( argument_spec=fields )
    try:
        result = True
        #Logging set, if required
        if module.params['DO_LOGGING']:
            logging.basicConfig(filename=f'{str(datetime.datetime.now().strftime("%m-%d-%Y"))}_{module.params["CUCM_IP"].replace("ansible_ssh_host=","")}.log', filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)
        #Connection establishment
        [ssh,interact] = ssh_connector(
            module.params['CUCM_IP'].replace("ansible_ssh_host=",""), 
            module.params['CUCM_SSH_USERNAME'].replace("ansible_user=",""), 
            module.params['CUCM_SSH_PASSWORD'].replace("ansible_ssh_pass=",""),
            module.params['DO_LOGGING']
            )
        #Check if the COP is already in place
        interact.expect('admin:')
        if(check_cop_existance(interact,module.params['REMOTE_FILE'])):            
            COP_RESULT['changed'] = False
            COP_RESULT['meta'] = f"COP {module.params['REMOTE_FILE']} already installed"            
        else:
            #If not in place, execution proceeds   
            #Get CUCM version
            CUCM_TYPE = ''
            CUCM_VERSION = get_cucm_version(interact)  
            #If CUCM version is 12.5, determine if it is a Publisher of a Subscriber
            if CUCM_VERSION == '12.x':
                CUCM_NAME = get_node_name(interact,module.params['CUCM_IP'].replace("ansible_ssh_host=",""))
                CUCM_TYPE = get_node_type(interact,CUCM_NAME)
            #Command initialization
            interact.send('utils system upgrade cancel')
            interact.expect('admin:')
            interact.send('utils system upgrade initiate')
            #v12.5 subscriber prompt
            if CUCM_VERSION == '12.x' and CUCM_TYPE == 'Subscriber':
                interact.expect('.*download credentials.*',timeout = 10)
                interact.send('no')
            #Normal SSH Flow
            interact.expect(['.*Please select an option.*','.*Assume control.*'],timeout = 50)
            #Assume control in case it is neccesary and then begin upload
            if interact.last_match == '.*Assume control.*':
                interact.send('yes')
                interact.expect('.*Please select an option.*',timeout = 5)
                result = sftp_ftp_loading(
                    interact,
                    module.params['REMOTE_SERVER_TYPE'],
                    module.params['REMOTE_DIRECTORY'],
                    module.params['REMOTE_SERVER'],
                    module.params['REMOTE_USERNAME'],
                    module.params['REMOTE_PASSWORD'],
                    module.params['REMOTE_SMTP'],
                    module.params['REMOTE_FILE'],
                    module.params['DO_REBOOT'],
                    CUCM_VERSION
                )
            else:
                #Upload initialization
                result = sftp_ftp_loading(
                    interact,
                    module.params['REMOTE_SERVER_TYPE'],
                    module.params['REMOTE_DIRECTORY'],
                    module.params['REMOTE_SERVER'],
                    module.params['REMOTE_USERNAME'],
                    module.params['REMOTE_PASSWORD'],
                    module.params['REMOTE_SMTP'],
                    module.params['REMOTE_FILE'],
                    module.params['DO_REBOOT'],
                    CUCM_VERSION
                )        
        #Return results
        if result:
            module.exit_json(
                    changed = COP_RESULT['changed'],
                    meta = COP_RESULT['meta']
                )
        else:
            module.fail_json(
                changed = COP_RESULT['changed'],
                msg = COP_RESULT['meta']
            )        
        #Close SSH connection
        ssh.close()
    except Exception as ex:
        module.fail_json(
            changed = False,
            msg = f'{ex}'
        )

if __name__ == '__main__':
	run_module()