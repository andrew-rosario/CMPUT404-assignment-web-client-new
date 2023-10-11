#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
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
    def __init__(self, code=200, headers=None, body=""):
        if headers is None:
            headers = []
        self.code = code
        self.headers = headers
        self.body = body



class HTTPClient(object):
    # def get_host_port(self,url):

    def parse_json_to_url_encoded(self,json_string):
        json_dictionary = json.loads(json_string)
        final_string = ""
        for key in json_dictionary:
            final_string += f"{key}={json_dictionary[key]}&"
        return final_string[:-1]
    
    def connect(self, host, port):
        if not port:
            port = 80
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {host} port {port}")

        self.socket.connect((host, port))
        return None

    def get_code(self, data):
        """
        Get the HTTP response code from the HTTP response.
        :param data:
        :return:
        """
        first_line = data.split("\r\n")[0]

        try:
            test = int(first_line.split(" ")[1])
        except ValueError:
            print("This is not a number.")

        return int(first_line.split(" ")[1])

    def get_headers(self, data):
        """
        Get the headers from a HTTP response.
        :param data: A HTTP-compliant response.
        :return: a list of strings containing the headers
        """
        headers = []
        traverse = data.split("/r/n")[1:]
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
        :param data: A HTTP-compliant response.
        :return: the body of the HTTP response.
        """
        lines = data.split("\r\n")
        print(lines)
        index_start = 0

        found = False
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
        self.socket.sendall(data.encode('utf-8'))

    def close(self):
        if self.socket:
            self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        #self.socket.setblocking(False)
        done = False
        while not done:
            part = sock.recv(1024)
            if len(part) == 0:
                done = True
            elif part:
                buffer.extend(part)
            else:
                done = True
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        url_split = urllib.parse.urlparse(url)
        self.connect(url_split.hostname, url_split.port)
        code = 500
        headers = []
        body = ""
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.connect((url_split.scheme +url_split.hostname,url_split.port))
        print(url)
        
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
            return None
        return HTTPResponse(code, headers, body)

    def POST(self, url, args=None):
        """
        Post data to the specified URL.
        :param url: The URL to post to.
        :param args: The data to be posted.
        :return: A HTTPResponse object.
        """

        url_split = urllib.parse.urlparse(url)
        self.connect(url_split.hostname, url_split.port)

        content_to_send = {"content-type": "", "content-length": "0", "content": ""}

        content = str(args)

        if args:
            if json.loads(str(args).replace("\'","\"")):
                content = self.parse_json_to_url_encoded(str(args).replace("\'","\""))
                
            content_to_send["content-type"] = "application/x-www-form-urlencoded"
            content_to_send["content-length"] = len(content)
            content_to_send["content"] = content
           
        type = content_to_send["content-type"]
        length = content_to_send["content-length"]
        content = content_to_send["content"]
        request = (f"POST {url_split.path} HTTP/1.1\r\n"
                   f"Host: {url_split.hostname}\r\n"
                   f"Content-Type: {type}\r\n"
                   f"Content-Length: {length}\r\n"
                   f"\r\n"
                   f"{content}\r\n")
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
