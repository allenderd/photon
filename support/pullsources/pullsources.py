#! /usr/bin/python2
#
#    Copyright (C) 2015 VMware, Inc. All rights reserved.
#    pullsources.py 
#    Allows pulling packages'sources from a bintary  
#    repository.
#
#    Author(s): Mahmoud Bassiouny (mbassiouny@vmware.com)
#

from optparse import OptionParser
import json
import os
import hashlib
import string

import requests
from requests.auth import HTTPBasicAuth

class pullSources:

    def __init__(self, conf_file):
        self._config = {}
        self.loadConfig(conf_file)

        # generate the auth
        self._auth = None
        if ('user' in self._config and len(self._config['user']) > 0 and
            'apikey' in self._config and len(self._config['apikey'])) > 0:
            self._auth = HTTPBasicAuth(self._config['user'], self._config['apikey'])

    def loadConfig(self,conf_file):
        with open(conf_file) as jsonFile:
            self._config = json.load(jsonFile)

    def getFileHash(self, filepath):
        sha1 = hashlib.sha1()
        f = open(filepath, 'rb')
        try:
            sha1.update(f.read())
        finally:
            f.close()
        return sha1.hexdigest()

    def downloadFile(self, sources_dir, filename, sha1 = None):
        file_path = os.path.join(sources_dir, filename)
        # check if file exists and has the same sha1
        if os.path.isfile(file_path) and sha1 == self.getFileHash(file_path):
            return file_path

        print 'Downloading %s...' % filename

        #form url: https://dl.bintray.com/vmware/photon_sources/1.0/<filename>.
        url = '%s/%s/%s/%s/%s' % \
              (self._config['baseurl'],\
               self._config['subject'],\
               self._config['repo'],\
               self._config['version'],\
               filename)

        with open(file_path, 'wb') as handle:
            response = requests.get(url, auth=self._auth)

            if not response.ok:
                # Something went wrong
                raise Exception(response.text)

            for block in response.iter_content(1024):
                if not block:
                    break

                handle.write(block)
        return file_path


    def pull(self, sources_dir):
        #Download the list of sources.
        package_file_path = self.downloadFile(sources_dir, 'sha1-all')
        with open(package_file_path) as f:
            packages = f.readlines()
        for package in packages:
            i = string.rindex(package, '-')
            package_name = string.strip(package[:i])
            package_sha1 = string.strip(package[i+1:])
            package_path = self.downloadFile(sources_dir, package_name, package_sha1)
            if package_sha1 != self.getFileHash(package_path):
                raise Exception('Invalid sha1 for package %s' % package_name)

if __name__ == '__main__':
    usage = "Usage: %prog [options] <sources_dir>"
    parser = OptionParser(usage)

    parser.add_option("-c", "--config-path",  dest="config_path", default="./bintray.conf", help="Path to bintray configuation file")
    
    (options,  args) = parser.parse_args()

    if (len(args)) != 1:
            parser.error("Incorrect number of arguments")

    p = pullSources(options.config_path)
    p.pull(args[0])
