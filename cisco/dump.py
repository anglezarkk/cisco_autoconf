import telnetlib


# Dump class
# handle telnet connection with routers, retrieval of running config
class Dump:
    def __init__(self, name, host, port = 23, password=None, debug_level=0):
        self.name = name
        self.host = host
        self.port = port
        self.password = password
        self.debug_level = debug_level

    # Download running config from router via telnet
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

    # login (enable password)
    def enable(self, connection):
        connection.read_until(b">")
        connection.write(b"enable\n")
        connection.write(bytes(self.password + '\n', "ascii"))
        connection.read_until(b"#")

    # exit telnet connection
    def logout(self, connection):
        connection.write(b'exit')

    # write config to file
    def write_running_config(self):
        config = self.get_running_config()
        fp = open(self.get_config_filename(), "w")
        fp.write(config)
        fp.close()

    # get config filename for current instance
    def get_config_filename(self):
        path = './config/'
        return path + self.name + ".config"

