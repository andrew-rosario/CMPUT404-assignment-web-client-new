#!/usr/bin/env python3
# coding: utf-8

# Appended code is copyright 2023 Andrew Rosario

# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, solely version 3 of the License.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <https://www.gnu.org/licenses/>.

# Original code is copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json
# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse


def help():
    print("httpclient.py [GET/POST] [URL]\n")


class HTTPResponse(object):
    """
    A HTTP response object, for debugging purposes.
    """

    def __init__(self, code=200, headers=None, body=""):
        if headers is None:
            headers = []
        self.code = code
        self.headers = headers
        self.body = body


class HTTPClient(object):
    """
    An HTTP client that can send GET/ POST requests to HTTP servers.
    """

    # def get_host_port(self,url):

    def parse_json_to_url_encoded(self, json_string):
        """
        Transform a JSON string into application/x-www-urlencoded form.
        :param json_string: A valid JSON string.
        :return: A URL encoded form.
        """
        json_dictionary = json.loads(json_string)
        final_string = ""
        for key in json_dictionary:
            final_string += f"{key}={json_dictionary[key]}&"
        return final_string[:-1]

    def connect(self, host, port):
        """
        Connect to the specified host and port.
        :param host: The host to connect, either an IP address or the URL.
        :param port: The port to connect out of.
        :return: None.
        """
        if not port:
            port = 80
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {host} port {port}")

        self.socket.connect((host, port))

    def get_code(self, data):
        """
        Get the HTTP response code from the HTTP response.
        :param data: The HTTP response.
        :return: A string containing the HTTP response code
        """
        first_line = data.split("\r\n")[0]

        try:
            int(first_line.split(" ")[1])
        except ValueError:
            print("This is not a number.")
            return "500"

        return int(first_line.split(" ")[1])

    def get_headers(self, data):
        """
        Get the headers from an HTTP response.
        :param data: An HTTP-compliant response.
        :return: a list of strings containing the headers
        """
        headers = []
        traverse = data.split("/r/n")[1:]  # omit the first line that denotes the code and response description.
        for line in traverse:
            header_split = line.split(": ")
            header_split[1] = header_split[1].rstrip()
            headers.append((header_split[0], header_split[1]))
            if line == "\r\n":
                break
        return headers

    def get_body(self, data):
        """
        Get the body from a= HTTP response.
        :param data: An HTTP-compliant response.
        :return: the body of the HTTP response.
        """
        lines = data.split("\r\n")
        index_start = 0

        found = False
        # find the blank line which denotes the content body.
        for line in lines:
            if line != "":
                index_start += 1
            else:
                found = True
                break
        if not found:
            return ""
        else:
            return ''.join(lines[index_start:])

    def sendall(self, data):
        """
        Send the data to the server.
        :param data: A string containing the data to send
        :return: None
        """
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        """
        Close the socket, if open.
        :return: None.
        """
        if self.socket:
            self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        """
        Receive all bytes from a socket, if any.
        :param sock: An open socket.
        :return: The received data.
        """
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if part:
                buffer.extend(part)
            else:
                done = True
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        """
        Send a GET request to the server.
        :param url: A URL to send the GET request to.
        :param args: Not used.
        :return: An HTTPResponse object containing the code, header, and body of the response.
        """
        url_split = urllib.parse.urlparse(url)
        self.connect(url_split.hostname, url_split.port)
        code = 500
        headers = []
        body = ""

        get_what = url_split.path

        if not get_what:
            get_what = "/"

        request = f"GET {get_what} HTTP/1.1\r\nHost: {url_split.hostname}\r\nAccept: */*\r\n\r\n"
        print(f'Sent following message: {request}')

        self.sendall(request)

        response = self.recvall(self.socket)
        print("Exited.")
        self.close()
        if response:
            print(f"Response received: {response}")
            code = self.get_code(response)
            headers = self.get_headers(response)
            body = self.get_body(response)
        else:
            print("Message has not been received. Perhaps the connection was lost?")
        return HTTPResponse(code, headers, body)

    def POST(self, url, args=None):
        """
        Send a POST request to the specified URL.
        :param url: The URL to post to.
        :param args: The data to be posted.
        :return: A HTTPResponse object containing the code, header, and body of the response.
        """

        url_split = urllib.parse.urlparse(url)
        self.connect(url_split.hostname, url_split.port)

        content = str(args)
        request = (f"POST {url_split.path} HTTP/1.1\r\n"
                   f"Host: {url_split.hostname}\r\n")

        if args:
            if json.loads(str(args).replace("\'", "\"")):
                content = self.parse_json_to_url_encoded(str(args).replace("\'", "\""))

            content_type = "application/x-www-form-urlencoded"
            length = len(content)
            request += f"Content-Type: {content_type}\r\nContent-Length: {length}\r\n\r\n{content}\r\n"
        else:
            request += "Content-Length: 0\r\n\r\n"

        print(f"Request sent: {request}")
        self.sendall(request)

        response = self.recvall(self.socket)
        self.close()

        code = 500
        body = ""
        headers = []

        if response:
            code = self.get_code(response)
            body = self.get_body(response)
            headers = self.get_headers(response)
        else:
            print("Message has not been received. Perhaps the connection was lost?")
        return HTTPResponse(code, headers, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST(url, args)
        else:
            return self.GET(url, args)


if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command(sys.argv[2], sys.argv[1]))
    else:
        print(client.command(sys.argv[1]))
