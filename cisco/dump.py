import telnetlib


class Dump:
    def __init__(self, name, host, port = 23, password=None, debug_level=0):
        self.name = name
        self.host = host
        self.port = port
        self.password = password
        self.debug_level = debug_level

    def get_running_config(self):
        connection = telnetlib.Telnet(self.host, self.port, timeout=10)
        connection.set_debuglevel(self.debug_level)
        if self.password is not None:
            self.enable(connection)

        connection.write(b"\r\n")
        connection.write(b"terminal length 0\r\n")
        connection.read_until(b"#")
        connection.write(b"show running-config\r\n")

        connection.read_until(b'!')
        config = connection.read_until(b"\nend")
        self.logout(connection)

        return '!' + config.decode('ascii')

    def enable(self, connection):
        connection.read_until(b">")
        connection.write(b"enable\n")
        connection.write(bytes(self.password + '\n', "ascii"))
        connection.read_until(b"#")

    def logout(self, connection):
        connection.write(b'exit')

    def write_running_config(self):
        config = self.get_running_config()
        fp = open(self.name + ".config", "w")
        fp.write(config)
        fp.close()

    def get_config_filename(self):
        return self.name + ".config"