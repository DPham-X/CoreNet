import logging

from jnpr.junos.utils.config import Config

from .conn_device import ConnDevice

logger = logging.getLogger(__name__)


class JunosTrigger(ConnDevice):
    def __init__(self, *args, **kwargs):
        """Junos Trigger which perform configuration changes

        :param ConnDevice: Junos Interface which holds all the connections to the
                           Junos network devices
        :type ConnDevice: ConnDevice object
        """
        super(JunosTrigger, self).__init__(*args, **kwargs)
        logger.info('Started JunosTrigger')

    def _load_config(self, device_name, config_name):
        """Performs a load overwrite of the configuration snippet
        on the Junos network device

        :param device_name: Name of the network device
        :type device_name: str
        :param config_name: Configuration snippet to load
        :type config_name: str
        :return: Output as a result of loading the new config
        :rtype: str
        """
        dev = self.connected_devices[device_name]
        config_filepath = 'config_snippets/{}'.format(config_name)
        try:
            with Config(dev, mode='exclusive') as cu, open(config_filepath, 'r') as config_snippet:
                cu.load(config_snippet.read(), format='text', merge=True)
                output = cu.diff()
                cu.commit()
            if not output:
                output = 'No difference between old and new config'
        except Exception as e:
            logger.error(e)
            return str(e), False
        return output

    def execute(self, vars):
        """Executes JunosTrigger valid commands

        Supported commands
        ------------------
        - load.config

        :param vars: Has all information on the action to take including
                     the command to be run and arguments associated with it
        :type vars: dict
        :return: Output of the command that was executed
        :rtype: str
        """
        output = ''
        try:
            cmd = vars['cmd']
            args = vars['args']
            device_name = args['device']
            config_name = args['config_name']
        except KeyError as e:
            logger.error('Unable to unpack evaluation variables: %', e)

        if cmd == 'load.config':
            output, status = self._load_config(device_name, config_name)
        else:
            logger.error('Unsupported JunosTrigger command')
            return '', False
        return output, status


if __name__ == '__main__':
    JunosTrigger()
