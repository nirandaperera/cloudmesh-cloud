from __future__ import print_function

from cloudmesh.key.api.manager import Manager
from cloudmesh.key.api.key import Key
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command
from cloudmesh.management.configuration.config import Config
from cloudmesh.common.Printer import Printer
from cloudmesh.management.configuration.SSHkey import SSHkey
from pprint import pprint

class KeyCommand(PluginCommand):

    # see https://github.com/cloudmesh/client/blob/master/cloudmesh_client/shell/plugins/KeyCommand.py
    # see https://github.com/cloudmesh/client/blob/master/cloudmesh_client/shell/plugins/AkeyCommand.py

    # noinspection PyUnusedLocal
    @command
    def do_key(self, args, arguments):
        """
        ::

           Usage:
             key  -h | --help
             key list --cloud=CLOUDS [--format=FORMAT]
             key list --source=ssh [--dir=DIR] [--format=FORMAT]
             key list --source=git [--format=FORMAT] [--username=USERNAME]
             key list [--format=FORMAT]
             key load [--format=FORMAT]
             key add [NAME] [--source=FILENAME]
             key add [NAME] [--git]
             key add [NAME] [--ssh]
             key get NAME [--format=FORMAT]
             key default --select
             key delete (NAMES | --select | --all) [--dryrun]
             key delete NAMES --cloud=CLOUDS [--dryrun]
             key upload [NAMES] [--cloud=CLOUDS] [--dryrun]
             key upload [NAMES] [VMS] [--dryrun]
             key group upload [--group=GROUPNAMES] [--cloud=CLOUDS] [--dryrun]
             key group add [--group=GROUPNAMES] [--cloud=CLOUDS] [--dryrun]
             key group delete [--group=GROUPNAMES] [NAMES] [--dryrun]
             key group list [--group=GROUPNAMES] [--format=FORMAT]


           Arguments:
             VMS            Para,eterized list of virtual machines
             CLOUDS         The clouds
             NAME           The name of the key.
             SOURCE         db, ssh, all
             KEYNAME        The name of a key. For key upload it defaults to the default key name.
             FORMAT         The format of the output (table, json, yaml)
             FILENAME       The filename with full path in which the key
                            is located

           Options:
              --dir=DIR                     the directory with keys [default: ~/.ssh]
              --format=FORMAT               the format of the output [default: table]
              --source=SOURCE               the source for the keys [default: db]
              --username=USERNAME           the source for the keys [default: none]
              --name=KEYNAME                The name of a key


           Description:

               Please note that some values are read from the cloudmesh4.yaml
               file. One such value is cloudmesh.profile.user

               Manages public keys is an essential component of accessing
               virtual machine sin the cloud. There are a number of sources
               where you can find public keys. This includes teh ~/.ssh
               directory and for example github. To list these keys the
               following list functions are provided.

                key list --source=git  [--username=USERNAME]
                    lists all keys in git for the specified user. If the
                    name is not specified it is read from cloudmesh4.yaml
                key list --source=ssh  [--dir=DIR] [--format=FORMAT]
                    lists all keys in the directory. If the directory is not
                    specified the default will be ~/.ssh

               The keys will be uploaded into cloudmesh with the add command
               under the given name. If the name is not specified the name
               cloudmesh.profile.user is assumed.

                key add --ssh
                    adds the default key in ~/.ssh/id_rsa.pub
                key add NAME  --source=FILENAME
                    adds the key specifid by the filename with the given name
                key add NAME --git --username=username
                    adds a named github key from a user with the given github
                    username.

                Once the keys are uploaded to github, they can be listed

                key list [NAME] [--format=FORMAT]
                    list the keys loaded to cloudmesh in the giiven format:
                    json, yaml, table. table is default. The NAME cabn be
                    specified and if ommitted the name cloudmesh.profile.user
                    is assumed.

                key get NAME
                    Retrieves the key indicated by the NAME parameter from
                    cloudmesh and prints its details.
                key default --select
                    Select the default key interactively
                key delete NAMES
                    deletes the keys. This may also have an impact on groups
                key rename NAME NEW
                    renames the key from NAME to NEW.

               Group management of keys is an important concept in cloudmesh,
               allowing multiple users to be added to virtual machines.
               The keys must be uploaded to cloudmesh with a name so they can
               be used in a group. The --dryrun option executes the command
               without uploading the information to the clouds. If no groupname
               is specified the groupname default is assumed. If no cloudnames
               are specified, all active clouds are assumed. active clouds can be
               set in the cloudmesh4.yaml file.

                key group delete [GROUPNAMES] [NAMES] [--dryrun]
                    deletes the named keys from the named groups.

                key group list [GROUPNAMES] [--format=FORMAT]
                    list the key names and details in the group.

                key group upload [GROUPNAMES] [CLOUDS] [--dryrun]
                    uploads the named groups to the specified clouds.

        """

        pprint(arguments)

        invalid_names = ['tbd', 'none', "", 'id_rsa']
        m = Manager()




        # if condition seems complex

        arguments.format = arguments['--format']
        arguments.source = arguments['--source']
        arguments.dir = arguments['--dir']


        if arguments.list and arguments.source == "git":
            # this is much simpler
            config = Config()
            username = config["cloudmesh.profile.github"]
            print("Username:", username)
            keys = SSHkey().get_from_git(username)
            print(Printer.flatwrite(keys,
                                    sort_keys=("name"),
                                    order=["id", "name", "fingerprint"],
                                    header=["Id", "Name", "Fingerprint"])
                  )

        elif arguments.list and arguments.source == "ssh":

            sshkey = SSHkey()
            print(Printer.flatwrite([sshkey],
                                    sort_keys=("name"),
                                    order=["name", "type", "fingerprint", "comment"],
                                    header=["Name", "Type", "Fingerprint", "Comment"]))


        elif arguments['list']:

            if "--source" not in arguments and "--cloud" not in arguments:
                arguments["--source"] = 'db'


            if arguments['--cloud']:
                print("cloud")


            elif arguments['--source'] == 'ssh':
                directory = arguments['--dir']
                publicKey =Key.get_from_dir(directory,True)
                print(publicKey)



            elif arguments['--source'] in ['cm', 'cloudmesh', 'yaml']:
                print(arguments['--source'])



            elif arguments['--source'] in ['git']:
                print(arguments['git'])



            elif arguments['--source'] == 'db':
                print(arguments['db'])



        # if arguments.FILE:
        #    print("option a")
        #    m.list(arguments.FILE)

        # elif arguments.list:
        #    print("option b")
        #    m.list("just calling list without parameter")
