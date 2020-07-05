import logging
import re

from symbot.chat.message import Message
from symbot.dev.meta._base_meta_command import BaseMetaCommand
from symbot.dev.meta._builder import Builder
from symbot.util.strings import stringify


class Command(BaseMetaCommand):

    def __init__(self, control):
        super().__init__(control)
        self.name = '!command'
        self.author = 'fd_symbicort'

        self.builder = Builder(control)

        self.arg_extractor = re.compile('\\$(.*){(.*)}')
        self.setting_extractor = re.compile('-(.*)=(.*)')

    async def run(self, msg: Message):

        try:
            operation = msg.context[0]
        except IndexError:
            logging.info('!command missing operation argument')
            return

        if operation == 'add':
            await self.addcom(msg)
        elif operation == 'edit':
            await self.editcom(msg)
        elif operation == 'del':
            await self.delcom(msg)
        else:
            logging.info(f'!command encountered an undefined operation argument {operation}')

    async def addcom(self, msg):
        """add a new command

        Parameters
        ----------
        msg : Message
            user message trying to add a new command
        """

        # extract command name
        try:
            name = msg.context[1]
        except IndexError:
            logging.info('!command add missing command name argument')
            return
        if self.control.get_command(name):
            logging.info(f'!command add {name} already exists')
            return
        try:
            msg.context[2]
        except IndexError:
            logging.info(f'!command add {name} missing content')
            return

        # create command blueprint
        skeleton = self.skellify(msg, name)
        if skeleton:

            # create command as file and load it
            self.builder.create_command(skeleton)

            # feedback that command has been created
            await self.control.respond(f'{msg.user} has added {name} to commands')

    async def editcom(self, msg):
        pass

    async def delcom(self, msg):
        """delete a command

        Parameters
        ----------
        msg : Message
            message containing command to be deleted
        """

        # extract command name
        try:
            name = msg.context[1]
        except IndexError:
            logging.info('!command del missing command name argument')
            return
        if not self.control.get_command(name):
            logging.info(f'!command del {name} does not exists')
            return
        pass

    def skellify(self, msg, name):
        """parse message to blueprint of a command

        Parameters
        ----------
        msg : Message
            message to be parsed
        name : str
            command name
        """

        skeleton = {
            'r': [],
            'v': [],
            'c': [],
            'a': [],
            'u': [],
            'alias': [],
            'settings': {'name': stringify(name), 'author': stringify(msg.user)}
        }

        for s in msg.context[2:]:
            if s.startswith('$'):
                try:
                    arg, value = self.arg_extractor.search(s).groups()
                    skeleton[arg].append(value)
                    skeleton['r'].append('{' + value + '}')
                except AttributeError:
                    logging.info(f'!command add {name} has bad argument')
                    return
                except KeyError:
                    logging.info(f'!command add {name} encountered undefined argument')
                    return
            elif s.startswith('-'):
                try:
                    setting, value = self.setting_extractor.search(s).groups()
                    if setting == 'ul':
                        skeleton['settings']['permission_level'] = int(value)
                    elif setting == 'cd':
                        skeleton['settings']['cooldown'] = float(value)
                    elif setting == 'id':
                        skeleton['settings']['name'] = value
                    elif setting == 'on':
                        skeleton['settings']['enabled'] = value.lower() == 'true'
                    else:
                        logging.info(f'!command add {name} invalid setting {setting}')
                        return
                except AttributeError:
                    logging.info(f'!command add {name} has bad setting')
                    return
                except ValueError:
                    logging.info(f'!command add {name} can not convert setting value')
                    return
            else:
                skeleton['r'].append(s)

        return skeleton
