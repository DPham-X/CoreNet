import logging

from jnpr.junos.utils.config import Config

from .conn_device import ConnDevice

logger = logging.getLogger(__name__)

class JunosTrigger(ConnDevice):
    def __init__(self, *args, **kwargs):
        logger.info('Started JunosTrigger')
        super(JunosTrigger, self).__init__(*args, **kwargs)

    def _load_config(self, device_name, config_name):
        dev = self.connected_devices[device_name]
        config_filepath = 'config_snippets/{}'.format(config_name)
        try:
            with Config(dev, mode='exclusive') as cu:
                with open(config_filepath, 'r') as config:
                    cu.load(config.read(), format='text', merge=True)
                    output = cu.diff()
                    cu.commit()
            if not output:
                output = 'No difference between old and new config'
        except Exception as e:
            logger.error(e)
            output = e
        return output

    def execute(self, vars):
        output = ''
        try:
            cmd = vars['cmd']
            args = vars['args']
            device_name = args['device']
            config_name = args['config_name']
        except KeyError as e:
            logger.error('Unable to unpack evaluation variables: %', e)

        if cmd == 'load.config':
            output = self._load_config(device_name, config_name)
        else:
            logger.error('Unsupported JunosTrigger command')

        return output

if __name__ == '__main__':
    JunosTrigger()
