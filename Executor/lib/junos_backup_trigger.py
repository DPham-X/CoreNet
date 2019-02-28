import logging
import yaml
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from datetime import datetime

logger = logging.getLogger(__name__)


class BackupTrigger(object):
    def __init__(self, backup_folder='backups/', *args, **kwargs):
        self.backup_folder = backup_folder

        logger.info('Started BackupTrigger')
        super(BackupTrigger, self).__init__(*args, **kwargs)

    def backup_config(self, args, uuid):
        command = 'show configuration | no-more'
        dev = self.connected_devices[args]
        logger.info('Executing CLI command: %s', command)
        output = dev.cli(command)
        date = datetime.now().isoformat().replace(':','_')
        filename = '{}config_{}_{}.conf'.format(self.backup_folder, date, uuid)
        with open(filename, 'w') as f:
            f.write(output)
        return 'Config was backed up to {}'.format(filename)

    def execute(self, vars, uuid):
        command  = vars['cmd']
        args = vars['args']

        if 'backup.config' == command:
            output = self.backup_config(args, uuid)
        else:
            logger.error('Undefined BackupTrigger command ... skipping - %s', command)
            return False
        return output