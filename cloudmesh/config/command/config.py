import os
import re
import sys
import shutil
import oyaml as yaml
import tempfile
from pprint import pprint
from base64 import b64encode, b64decode
from cloudmesh.common.FlatDict import flatten
from cloudmesh.common.Printer import Printer
from cloudmesh.common.Shell import Shell
from cloudmesh.common.console import Console
from cloudmesh.common.util import banner
from cloudmesh.common.util import path_expand, writefd, readfile
from cloudmesh.configuration.Config import Config
from cloudmesh.shell.command import PluginCommand
from cloudmesh.shell.command import command, map_parameters
from cloudmesh.common.util import path_expand
from cloudmesh.configuration.security.encrypt import CmsEncryptor, KeyHandler, CmsHasher
from progress.bar import Bar

from shutil import copy2


class ConfigCommand(PluginCommand):

    # see https://github.com/cloudmesh/client/blob/master/cloudmesh_client/shell/plugins/KeyCommand.py
    # see https://github.com/cloudmesh/client/blob/master/cloudmesh_client/shell/plugins/AkeyCommand.py

    # noinspection PyUnusedLocal
    @command
    def do_config(self, args, arguments):
        """
        ::

           Usage:
             config  -h | --help
             config cat [less]
             config check
             config secinit
             config security add (--secret=REGEXP | --exception=REGEXP )
             config security rmv (--secret=REGEXP | --exception=REGEXP )
             config encrypt 
             config decrypt [--nopass]
             config edit [ATTRIBUTE]
             config set ATTRIBUTE=VALUE
             config get ATTRIBUTE [--output=OUTPUT]
             config value ATTRIBUTE
             config ssh keygen
             config ssh verify
             config ssh check
             config ssh pem
             config cloud verify NAME [KIND]
             config cloud edit [NAME] [KIND]
             config cloud list NAME [KIND] [--secrets]


           Arguments:
             SOURCE           the file to encrypted or decrypted.
                              an .enc is added to the filename or removed form it
                              dependent of if you encrypt or decrypt
             ATTRIBUTE=VALUE  sets the attribute with . notation in the
                              configuration file.
             ATTRIBUTE        reads the attribute from the container and sets it
                              in the configuration file
                              If the attribute is a password, * is written instead
                              of the character included
             REGEXP           python regular expression

           Options:
              --secret=REGEXP       ensures all attributes within cloudmesh.yaml 
                                    whose dot path matches REGEXP are not encrypted
                                    (even if listed in secrets)
              --exception=REGEXP    ensures attributes within cloudmesh.yaml whose 
                                    dot path matches REGEXP are encrypted
              --name=KEYNAME        The name of a key
              --nopass              Indicates if private key is password protected
              --output=OUTPUT       The output format [default: yaml]
              --secrets             Print the secrets. Use carefully.

           Description:

             config check
                checks if the ssh key ~/.ssh/id_rsa has a password. Verifies it
                through entering the passphrase

             Key generation

                Keys must be generated with

                    ssh-keygen -t rsa -m pem
                    openssl rsa -in ~/.ssh/id_rsa -out ~/.ssh/id_rsa.pem

                or
                    cms config ssh keygen

                Key validity can be checked with

                    cms config check

                The key password can be verified with

                    cms config verify


                ssh-add

                cms config encrypt ~/.cloudmesh/cloudmesh.yaml
                cms config decrypt ~/.cloudmesh/cloudmesh.yaml


                config set ATTRIBUTE=VALUE

                    config set profile.name=Gregor

                In case the ATTRIBUTE is the name of a cloud defined under
                cloudmesh.cloud, the value will be written into the credentials
                attributes for that cloud this way you can safe a lot of
                typing. An example is

                    cms config set aws.AWS_TEST=Gregor

                which would write the AWS_TEST attribute in the credentials
                of the cloud aws. This can naturally be used to set for
                example username and password.

        """
        # d = Config()                #~/.cloudmesh/cloudmesh.yaml
        # d = Config(encryted=True)   # ~/.cloudmesh/cloudmesh.yaml.enc

        map_parameters(arguments,
                       "exception",
                       "keep", 
                       "nopass",
                       "output", 
                       "secret",
                       "secrets")

        source = arguments.SOURCE or path_expand("~/.cloudmesh/cloudmesh.yaml")
        destination = source + ".enc"

        if arguments.cloud and arguments.edit and arguments.NAME is None:
            path = path_expand("~/.cloudmesh/cloudmesh.yaml")
            print(path)
            Shell.edit(path)
            return ""

        cloud = arguments.NAME
        kind = arguments.KIND
        if kind is None:
            kind = "cloud"

        configuration = Config()

        if arguments.cloud and arguments.verify:
            service = configuration[f"cloudmesh.{kind}.{cloud}"]

            result = {"cloudmesh": {"cloud": {cloud: service}}}

            action = "verify"
            banner(
                f"{action} cloudmesh.{kind}.{cloud} in ~/.cloudmesh/cloudmesh.yaml")

            print(yaml.dump(result))

            flat = flatten(service, sep=".")

            for attribute in flat:
                if "TBD" in str(flat[attribute]):
                    Console.error(
                        f"~/.cloudmesh.yaml: Attribute cloudmesh.{cloud}.{attribute} contains TBD")

        elif arguments.cloud and arguments.list:
            service = configuration[f"cloudmesh.{kind}.{cloud}"]
            result = {"cloudmesh": {"cloud": {cloud: service}}}

            action = "list"
            banner(
                f"{action} cloudmesh.{kind}.{cloud} in ~/.cloudmesh/cloudmesh.yaml")

            lines = yaml.dump(result).split("\n")
            secrets = not arguments.secrets
            result = Config.cat_lines(lines, mask_secrets=secrets)
            print(result)

        elif arguments.cloud and arguments.edit:

            #
            # there is a duplicated code in config.py for this
            #
            action = "edit"
            banner(
                f"{action} cloudmesh.{kind}.{cloud}.credentials in ~/.cloudmesh/cloudmesh.yaml")

            credentials = configuration[f"cloudmesh.{kind}.{cloud}.credentials"]

            print(yaml.dump(credentials))

            for attribute in credentials:
                if "TBD" in credentials[str(attribute)]:
                    value = credentials[attribute]
                    result = input(f"Please enter {attribute}[{value}]: ")
                    credentials[attribute] = result

            # configuration[f"cloudmesh.{kind}.{cloud}.credentials"] = credentials

            print(yaml.dump(
                configuration[f"cloudmesh.{kind}.{cloud}.credentials"]))

        elif arguments["edit"] and arguments["ATTRIBUTE"]:

            attribute = arguments.ATTRIBUTE

            config = Config()

            config.edit(attribute)

            config.save()

            return ""


        elif arguments.cat:

            content = Config.cat()

            import shutil
            columns, rows = shutil.get_terminal_size(fallback=(80, 24))

            lines = content.split("\n")

            counter = 1
            for line in lines:
                if arguments.less:
                    if counter % (rows - 2) == 0:
                        x = input().split("\n")[0].strip()
                        if x != '' and x in 'qQxX':
                            return ""
                print(line)
                counter += 1

            return ""

        elif arguments.check and not arguments.ssh:

            Config.check()

        elif arguments.encrypt:
            config = Config()
            config.encrypt()

        elif arguments.decrypt:
            config = Config()
            config.decrypt(ask_pass=not arguments.nopass)

        elif arguments.ssh and arguments.verify:

            e = EncryptFile(source, destination)

            e.pem_verify()

        elif arguments.ssh and arguments.check:

            e = EncryptFile(source, destination)

            key = path_expand("~/.ssh/id_rsa")
            r = e.check_key(key)
            if r:
                Console.ok(f"Key {key} is valid")
            # does not work as it does not change it to pem format
            # e.check_passphrase()

        elif arguments.ssh and arguments.pem:

            e = EncryptFile(source, destination)

            r = e.pem_create()

        elif arguments.set:

            config = Config()
            clouds = config["cloudmesh.cloud"].keys()

            line = arguments["ATTRIBUTE=VALUE"]
            attribute, value = line.split("=", 1)

            cloud, field = attribute.split(".", 1)

            if cloud in clouds:
                attribute = f"cloudmesh.cloud.{cloud}.credentials.{field}"

            elif not attribute.startswith("cloudmesh."):
                attribute = f"cloudmesh.{attribute}"

            config[attribute] = value
            config.save()

        elif arguments.value:

            config = Config()

            attribute = arguments.ATTRIBUTE
            if not attribute.startswith("cloudmesh."):
                attribute = f"cloudmesh.{attribute}"

            try:
                value = config[attribute]
                if type(value) == dict:
                    raise Console.error("the variable is a dict")
                else:
                    print(f"{value}")

            except Exception as e:
                print(e)
                return ""

        elif arguments.secinit:
            config = Config()
            secpath = path_expand(config['cloudmesh.security.secpath'])
            if not os.path.isdir(secpath):
                Shell.mkdir(secpath) # Use Shell that makes all dirs as needed
        
        elif arguments.security:
            # Get the regular expression from command line
            regexp = None
            if arguments.secret:
                regexp = arguments.secret
            elif arguments.exception:
                regexp = arguments.exception

            # Verify argument is valid python regular expression
            valid = False
            try:
                r = re.compile(regexp)
                valid = True
            except re.error:
                Console.error( f"Invalid Python RegExp:{regexp}")

            if valid:
                config = Config()
                path = None
                section = None
                # Assign information based on arguments
                if arguments.secret:
                    path = 'cloudmesh.security.secrets'
                    section = "secrets"
                elif arguments.exception:
                    path = 'cloudmesh.security.exceptions'
                    section = "exceptions"

                # Get current list of regular expressions from related section
                exps = config[path]

                # Add argument to expressions in related section
                if arguments.add:
                    if regexp not in exps:
                        config[path].append(regexp)
                        config.save()
                        Console.ok( f"Added {regexp} to {section}" )
                    else:
                        Console.warning( f"{regexp} already in {section}" )
                # Remove argument from expressions in related section
                elif arguments.rmv:
                    if regexp in exps:
                        config[path].remove(regexp)
                        config.save()
                        Console.ok( f"Removed {regexp} from {section}" )
                    else:
                        Console.warning( f"{regexp} not in {section}" )

        elif arguments.get:

            print()

            config = Config()
            clouds = config["cloudmesh.cloud"].keys()

            attribute = arguments.ATTRIBUTE

            try:
                cloud, field = attribute.split(".", 1)
                field = f".{field}"
            except:
                cloud = attribute
                field = ""

            if cloud in clouds:
                attribute = f"cloudmesh.cloud.{cloud}{field}"
            elif not attribute.startswith("cloudmesh."):
                attribute = f"cloudmesh.{attribute}"

            try:
                value = config[attribute]
                if type(value) == dict:
                    print(Printer.write(value, output=arguments.output))
                else:
                    print(f"{attribute}={value}")

            except Exception as e:
                print(e)
                return ""

        elif arguments.ssh and arguments.keygen:

            e = EncryptFile(source, destination)

            e.ssh_keygen()

        return ""
