import asyncore
import socket
from asyncore import dispatcher
from asynchat import async_chat

PORT = 5005
NAME = 'TestChat'


class EndSession:
    pass


class CommandHandler:
    def unknown(self, session, cmd):
        session.push(bytes('Unknown command: %s\r\n' % cmd, encoding='utf-8'))

    def handle(self, session, line):
        if not line.strip():
            return
        parts = line.split(' ', 1)
        cmd = parts[0]
        try:
            line = parts[1].strip()
        except IndexError:
            line = ''
        meth = getattr(self, 'do_' + cmd, None)
        try:
            meth(session, line)
        except TypeError:
            self.unknown(session, cmd)


class Room(CommandHandler):

    def __init__(self, server):
        self.server = server
        self.sessions = []

    def add(self, session):
        self.sessions.append(session)

    def remove(self, session):
        self.sessions.remove(session)

    def broadcast(self, line):
        for session in self.sessions:
            session.push(line)

    def do_logout(self, session, line):
        raise EndSession


class LoginRoom(Room):
    def add(self, session):
        Room.add(self, session)
        self.broadcast(bytes('Welcome to %s\r\n' % self.server.name, encoding='utf-8'))

    def unknown(self, session, cmd):
        session.push(b'Please log in \nUse "login <nick>"\r\n')

    def do_login(self, session, line):
        name = line.strip()
        if not name:
            session.push(b'Please enter a name\r\n')
        elif name in self.server.users:
            session.push(bytes('The name "%s" is taken.\r\n' % name, encoding='utf-8'))
            session.push(b'Please try again.\r\n')
        else:
            session.name = name
            session.enter(self.server.main_room)


class ChatRoom(Room):
    def add(self, session):
        self.broadcast(bytes(session.name + ' has entered the room.\r\n', encoding='utf-8'))
        self.server.users[session.name] = session
        Room.add(self, session)

    def remove(self, session):
        Room.remove(self, session)
        self.broadcast(bytes(session.name + ' has left the room.\r\n', encoding='utf-8'))

    def do_say(self, session, line):
        self.broadcast(session.name + ': ' + line + '\r\n')

    def do_look(self, session, line):
        session.push(b'The following are in this room:\r\n')
        for other in self.sessions:
            session.push(other.name + '\r\n')

    def do_who(self, session, line):
        session.push(b'The following are logged in: \r\n')
        for name in self.server.users:
            session.push(name + '\r\n')


class LogoutRoom(Room):

    def add(self, session):
        try:
            del self.server.users[session.name]
        except KeyError:
            pass


class ChatSession(async_chat):

    def __init__(self, server, sock):
        async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator(b'\r\n')
        self.data = []
        self.name = None
        self.enter(LoginRoom(server))

    def enter(self, room):
        try:
            cur = self.room
        except AttributeError:
            pass
        else:
            cur.remove(self)
        self.room = room
        room.add(self)

    def collect_incoming_data(self, data):
        self.data.append(str(data, encoding='utf-8'))

    def found_terminator(self):
        line = ''.join(self.data)
        self.data = []
        try:
            self.room.handle(self, line)
        except EndSession:
            self.handle_close()

    def handle_close(self):
        async_chat.handle_close(self)
        self.enter(LogoutRoom(self.server))


class ChatServer(dispatcher):

    def __init__(self, port, name):
        dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('', port))
        self.listen(5)
        self.name = name
        self.users = {}
        self.main_room = ChatRoom(self)

    def handle_accept(self):
        conn, addr = self.accept()
        ChatSession(self, conn)


if __name__ == '__main__':

    s = ChatServer(PORT, NAME)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        print()


