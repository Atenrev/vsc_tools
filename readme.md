# VSC tools
A repository for useful tools for the Vlaams Supercomputer Centrum (VSC) clusters.

## Index
- [VSC tools](#vsc-tools)
  - [Index](#index)
  - [Prerequisites](#prerequisites)
  - [VSCode](#vscode)
  - [Contributing](#contributing)

## Prerequisites
You will need the following tools installed on your local machine:
- [Visual Studio Code](https://code.visualstudio.com/)
- [Remote - SSH](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh)

And the following python packages:
- paramiko
- getpass
- cryptography

(You can install these packages by running ```pip install -r requirements.txt```)

You will also need to modify your hosts configuration file. You'll find a template with what you have to add under ```configs/hosts_template``` which you can copy and modify to your needs. 

*Note: this script will modify your hosts configuration file to add a new entry for compute nodes dinamically, so you don't have to do it manually.*

## VSCode
To launch a remote session on a compute node, you can use the following command:
```bash
python vsc_tools --hostname <hostname> --username <vsc_username> --identity_file <path_to_private_key> --group <vsc_group> --project_folder <path_to_project_folder_in_cluster>
```

For example:
```bash
python vsc_tools --hostname VSC --username vscXXXXX --identity_file ~/.ssh/id_rsa --allocation_time 01:00:00 --group lcomputervision --project_folder /user/leuven/XXX/vscXXXXX/projectX
```

For more information, run:
```bash
python vsc_tools --help
```

## Contributing
Pull requests are welcome.
