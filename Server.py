"""The module containing connection to given IP address and port, basic loop of application"""
import asyncio
import random
from service import User
from service import Admin
import os
import json
import socket
import signal
import string

signal.signal(signal.SIGINT, signal.SIG_DFL)
registered = {'client_name': [], 'client_password': [], 'client_privilege': []}
signedin = []
addr_port = []
created_folder = {}
path = str(os.getcwd())
with open(f'{path}/root/Server/signed-info.json', 'w') as file:
    json.dump(signedin, file)
async def send_back(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Gives the sent message from client in a loop, if the message is quit the loop will be stopped.
    The received message will be splited and message[0] will be compare with given known commands
    and in each part it will be made a user/admin instance and the related function will be called
    by this instance and get the answer from service module and sent it to Client.py
    """
    global path
    # 'peername' is remote address connected to
    addr = writer.get_extra_info('peername')
    message = f'{addr!r} is connected !!!!'
    print(message)
    pre_file_name = ""
    with open(f'{path}/root/Server/client-info.json', 'r') as file:
        registered = json.load(file)
    with open(f'{path}/root/Server/signed-info.json', 'r') as file:
        signedin = json.load(file)
    writer.write('\n\rYou are conected to Pytonista Server'.encode(encoding='UTF-8'))
    writer.write('\n\rPlease select login or register (login/register)'.encode(encoding='UTF-8'))
    writer.write('>>'.encode(encoding='UTF-8'))
    await writer.drain()

    while True:
        data = await reader.read(1000)
        msg = data.decode().strip()
        message = msg.split()

        if message[0] == 'register':
            reg_Flag = False
            while True:
                if len(message) == 4:
                    name = message[1]
                    password = message[2]
                    privilege = message[3]
                    restricted_char = string.punctuation
                    for char in restricted_char:
                        if char in name:
                            writer.write('\n\rError:The username characters are not acceptable. Try again!'.encode(encoding='UTF-8'))
                            await writer.drain()
                            reg_Flag = True
                            break
                    if reg_Flag == True:
                        break
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    writer.write('\n\rUse: register <username> <password> <privilege>'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break
                if username_check(name, registered['client_name']) == False and password != "" and (privilege == "user" or privilege == "admin"):
                    registered['client_name'].append(name)
                    registered['client_password'].append(password)
                    registered['client_privilege'].append(privilege)
                    if privilege == "user":
                        user_path = f"{path}/root/user/{name}"
                        os.mkdir(user_path)

                    elif privilege == "admin":
                        admin_path = f"{path}/root/admin/{name}"
                        os.mkdir(admin_path)

                    with open(f'{path}/root/Server/client-info.json', 'w') as file:
                        json.dump(registered, file)
                    break
                else:
                    if username_check(name, registered['client_name']) == True:
                        writer.write('\n\rError:The username has been already selected.'.encode(encoding='UTF-8'))
                        await writer.drain()
                        break
                    else:
                        writer.write('\n\rError: The selected username, password or privilege is not correct.'.encode(encoding='UTF-8'))
                        await writer.drain()
                        break

        elif message[0] == 'login':
            while True:
                if len(message) == 3:
                    name = message[1]
                    password = message[2]
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: login <username> <password>'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

                if (username_check(name, registered['client_name']) and name not in signedin):
                    index = registered['client_name'].index(name)

                    if password == registered['client_password'][index]:
                        with open(f'{path}/root/Server/signed-info.json', 'r') as file:
                            signedin = json.load(file)
                        signedin.append(name)
                        with open(f'{path}/root/Server/signed-info.json', 'w') as file:
                            json.dump(signedin, file)
                    else:
                        writer.write('\n\rError:The password is incorrect. Please try again.'.encode(encoding='UTF-8'))
                        await writer.drain()
                        break
                    index = registered['client_name'].index(name)
                    privilege = registered['client_privilege'][index]

                    if privilege == "user":
                        client = User(name, password, privilege)
                    else:
                        client = Admin(name, password, privilege)
                    break
                else:
                    writer.write('\n\rError: This username is not exist or already logged in.'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

        elif message[0] == 'commands':
            help_message = """
            mkdir <name>-----create a new folder
            cd <name>--------change folder
            ls--------list directory contents
            read <file_name>------read data from the file
            write <file_name> <input>-----write the data to the end of the file
            login <username> <password>-----log in the user
            register <username> <password> <privileges>--register a new user
            del <del_username> <admin_password>-------delete a user from the server
            quit------log out the user, close the connection, close the application
            commands--information about all available commands
            """
            writer.write(f'\n\r{help_message}'.encode())
            await writer.drain()

        elif message[0] == 'mkdir':
            while True:
                if len(message) == 2:
                    folder = message[1]
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: mkdir <folder_name>'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break
                if username_check(name, signedin):
                    writer.write(client.create_folder(name, privilege, folder).encode(encoding='UTF-8'))
                    break
                else:
                    writer.write('\n\rError: You should sign in first'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

        elif message[0] == 'cd':
            while True:
                if len(message) == 2:
                    folder = message[1]
                    restricted_char = string.punctuation

                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: cd <folder_name> or cd .. to go back'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

                if folder == '..':
                    if username_check(name, signedin):
                        writer.write(client.back_folder(name, privilege).encode(encoding='UTF-8'))
                        await writer.drain()
                        break

                for char in restricted_char:
                    cd_flag = False
                    if char in folder:
                        writer.write('\n\rError:The folder does not exist. Try again!!!!.'.encode(encoding='UTF-8'))
                        await writer.drain()
                        cd_flag = True
                        break

                if cd_flag == False:
                    writer.write(client.change_folder(name, privilege, folder).encode(encoding='UTF-8'))
                    await writer.drain()       
                    break
                break

        elif message[0] == 'ls':
            while True:
                if len(message) == 1:
                    if username_check(name, signedin):

                        writer.write(client.print_list(name).encode(encoding='UTF-8'))
                        await writer.drain()

                        break
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: ls'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

        elif message[0] == 'write':
            while True:
                if len(message) >= 2:
                    file_name = message[1]
                    user_input = ' '.join(message[2:])
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: write <filename> <input>'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break
                if username_check(name, signedin):
                    client.write_file(name, file_name, user_input)
                    break

        elif message[0] == 'read':
            read_flag = False
            while True:
                if len(message) == 1:
                    file_name = ""
                elif len(message) == 2:
                    file_name = message[1]
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: read <filename>'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

                if username_check(name, signedin):
                    if pre_file_name == file_name:
                        read_flag = True

                    writer.write(client.read_file(file_name, read_flag).encode(encoding='UTF-8'))
                    await writer.drain()
                    pre_file_name = str(file_name)
                    break

        elif message[0] == 'del':
            while True:
                if len(message) == 3:
                    user_name = message[1]
                    input_password = message[2]
                else:
                    writer.write('\n\rError: Wrong command format'.encode(encoding='UTF-8'))
                    await writer.drain()
                    writer.write('\n\rUse: del <username> <admin_password>'.encode(encoding='UTF-8'))
                    await writer.drain()
                    break

                if username_check(name, signedin):
                    writer.write(client.delete(name, user_name, input_password, signedin).encode(encoding='UTF-8'))
                    await writer.drain()
                    break

        elif message[0] == 'quit':
            with open(f'{path}/root/Server/signed-info.json', 'r') as file:
                signedin = json.load(file)

            signedin.remove(name)

            with open(f'{path}/root/Server/signed-info.json', 'w') as file:
                json.dump(signedin, file)

            close_msg = f'{addr!r} wants to close the connection.'
            print(close_msg)
            break
        else:
            writer.write('\n\rThe implemented command is wrong.Please type "commands"'.encode(encoding='UTF-8'))
            await writer.drain()

        writer.write('\n\r>>'.encode(encoding='UTF-8'))
        await writer.drain()
    writer.close()

async def main():
    """
    This function sets the connection to given IP address and port and calls call_back function.
    Make the server ready to listen.
    """
    server = await asyncio.start_server(send_back, '127.0.0.1', 8080)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    async with server:
        await server.serve_forever()

def username_check(name1, name2):
    for i in range(0, len(name2)):
        if name1 == name2[i]:
            return True
    return False

asyncio.run(main())
