import logging
from datetime import datetime

from .conn_device import ConnDevice

# Logging
logger = logging.getLogger(__name__)


class BackupTrigger(ConnDevice):
    def __init__(self, backup_folder='backups', *args, **kwargs):
        """Junos Configuration Backup Trigger

        :param ConnDevice: Junos Interface which holds all the connections to the
                           Junos network devices
        :type ConnDevice: ConnDevice object
        :param backup_folder: Location of the Junos configuration back folder, defaults to 'backups'
        :param backup_folder: str, optional
        """
        self.backup_folder = backup_folder

        super(BackupTrigger, self).__init__(*args, **kwargs)
        logger.info('Started BackupTrigger')

    def backup_config(self, args, uuid):
        """Connects to the device specified in the arguments and
        backs up the configuration into the backup folder

        :param args: Device name to connect to
        :type args: str
        :param uuid: Unique ID corresponding to execution this command
                     was ran under
        :type uuid: str
        :return: Message containing the location of the backup
        :rtype: str
        """
        command = 'show configuration | no-more'
        dev = self.connected_devices[args].open()

        logger.info('Executing CLI command: %s', command)
        output = dev.cli(command)
        date = datetime.now().isoformat().replace(':', '_')
        filename = '{}/config_{}_{}.conf'.format(self.backup_folder, date, uuid)
        # Save configuration
        with open(filename, 'w') as f:
            f.write(output)
        return 'Config was backed up to {}'.format(filename)

    def execute(self, vars, uuid):
        """Executes BackupTrigger valid commands

        Supported commands
        ------------------
        - backup.config

        :param vars: Has all information on the action to take including
                     the command to be run and arguments associated with it
        :type vars: dict
        :param uuid: Unique ID for the set of executions
        :type uuid: str
        :return: Output of the command that was executed
        :rtype: str
        """
        command = vars['cmd']
        args = vars['args']

        if 'backup.config' == command:
            output = self.backup_config(args, uuid)
        else:
            logger.error('Undefined BackupTrigger command ... skipping - %s', command)
            return '', False
        return output, True
