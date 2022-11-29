#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 29.11.2018

@author: heju271036
'''

import json

class Rsi:
    def __init__(self, shell, verbose=False):
        self.verbose = verbose
        self.shell = shell
        self.rsi_json = None

    def _request(self, uri, data=None, del_resource=False):
        if del_resource:
            cmd = "curl -X DELETE localhost:" + uri
        else:
            cmd = "curl localhost:" + uri
        if data is not None:
            cmd += " -d " + data

        if self.verbose:
            print(self.__class__.__name__ + " cmd: " + cmd)

        exit_status, stdout_str, stderr_str = self.shell.run(cmd)
        return exit_status, stdout_str, stderr_str

    def get(self, url):
        if self.verbose:
            print(self.__class__.__name__ + " GET " + url)

        exit_status, stdout_str, stderr_str = self._request(url)
        self.rsi_json = json.loads(stdout_str)
        return exit_status, self.rsi_json

    def post(self, url, data):
        if self.verbose:
            print(self.__class__.__name__ + " POST " + data + " to " + url)

        exit_status, stdout_str, stderr_str = self._request(url, data)
        self.rsi_json = json.loads(stdout_str)
        return exit_status, self.rsi_json
    
    def delete(self, url):
        if self.verbose:
            print(self.__class__.__name__ + " DELETE " + url)

        exit_status, stdout_str, stderr_str = self._request(url, del_resource=True)
        self.rsi_json = json.loads(stdout_str)
        return exit_status, self.rsi_json

    def rsi_error(self):
        error = False
        error_code = ""
        if self.rsi_json is not None and "error" in self.rsi_json["status"]:
            error_code = ""
            if "code" in self.rsi_json:
                error_code = self.rsi_json["code"]
                error = True

        return error, error_code

    def __del__(self):
        print(self.__class__.__name__ + " deleted")

