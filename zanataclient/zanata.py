#vim:set et sts=4 sw=4:
#
# Zanata Python Client
#
# Copyright (c) 2011 Jian Ni <jni@redhat.com>
# Copyright (c) 2011 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA  02111-1307  USA

__all__ = (
            "ZanataConsole",
        )

import signal
import sys
import getopt, sys
import os.path
import string
from helpinfo import HelpInfo
from zanatalib import *
from zanatalib.error import *
from parseconfig import ZanataConfig
from publicanutil import PublicanUtility

sub_command = {
                'help':[],
                'list':[],
                'status':[],
                'project':['info','create', 'remove'],
                'version':['info', 'create', 'remove'],
                'publican':['push', 'pull'],
                'po':['push','pull']                
                }

options = {
            'url' : '',
            'user_name':'',
            'key':'',
            'user_config':'',
            'project_config':'',
            'project_id':'',
            'project_version':'',
            'dir':'',
            'srcdir':'',
            'srcfile':'',
            'dstdir':'',
            'transdir':'',
            'project_name':'',
            'project_desc':'',
            'version_name':'',
            'version_desc':'',
            'lang':'',
            'email':'',
            'merge':'auto',
            'importpo':False,
            'copytrans':True
            }

class ZanataConsole:

    def __init__(self):
        self.url = ''
        self.user_name = ''
        self.apikey = ''
        self.user_config = ''
        self.server_version = ''
        self.project_config = {'project_url':'', 'project_id':'', 'project_version':'', 'locale_map':{}}
        self.force = False
        self.log = Logger()
        self.help = HelpInfo()

    def _generate_zanataresource(self):
        if self.user_name and self.apikey:
            return ZanataResource(self.url, self.user_name, self.apikey)
        else:
            self.log.error("Please specify username and apikey in zanata.ini/flies.ini or with '--username' and '--apikey' options")
            sys.exit(1)

        self.log.info("Username: %s"%self.user_name)
       
    def _list_projects(self):
        """
        List the information of all the project on the zanata server
        """
        zanata = ZanataResource(self.url)
        projects = zanata.projects.list()
        
        if not projects:
            self.log.error("There is no projects on the server or the server not working")
            sys.exit(1)
        for project in projects:
            print ("\nProject ID:          %s")%project.id
            print ("Project Name:        %s")%project.name
            print ("Project Type:        %s")%project.type
            print ("Project Links:       %s\n")%[{'href':link.href, 'type':link.type, 'rel':link.rel} for link in project.links]
        
    def _get_project(self):
        """
        Retrieve the information of a project
        """
        if options['project_id']:
            project_id =  options['project_id'] 
        else:
            project_id = self.project_config['project_id']        
        
        if not project_id:
            self.log.error('Please use zanata project info --project-id=project_id or zanata.xml/flies.xml to specify the project id')
            sys.exit(1)
      
        zanata = ZanataResource(self.url)
        try:
            p = zanata.projects.get(project_id)
            print ("Project ID:          %s")%p.id
            print ("Project Name:        %s")%p.name 
            print ("Project Type:        %s")%p.type
            print ("Project Description: %s")%p.description
        except NoSuchProjectException, e:
            self.log.error("There is no Such Project on the server")
        except InvalidOptionException, e:
            self.log.error("Options are not valid")
               
    def _get_iteration(self):
        """
        Retrieve the information of a project iteration.
        """
        if options['project_id']:
            project_id =  options['project_id'] 
        else:
            project_id = self.project_config['project_id']
        
        if options['project_version']:
            iteration_id = options['project_version'] 
        else:
            iteration_id = self.project_config['project_version']

        if not iteration_id or not project_id:
            self.log.error("Please use zanata version info --project-id=project_id --project-version=project_version to retrieve the version")
            sys.exit(1)
        
        zanata = ZanataResource(self.url)
        try:
            project = zanata.projects.get(project_id)
            iteration = project.get_iteration(iteration_id)
            print ("Version ID:          %s")%iteration.id
            if hasattr(iteration, 'name'):
                print ("Version Name:        %s")%iteration.name
            if hasattr(iteration, 'description'):
                print ("Version Description: %s")%iteration.description
        except NoSuchProjectException, e:
            self.log.error("There is no such project or version on the server")

    def _create_project(self, args):
        """
        Create project with the project id, project name and project description
        @param args: project id
        """
        zanata = self._generate_zanataresource()

        if not args:
            self.log.error("Please provide PROJECT_ID for creating project")
            sys.exit(1)

        if not options['project_name']:
            self.log.error("Please specify project name with '--project-name' option")
            sys.exit(1)
       
        try:
            item = {'id':args[0], 'name':options['project_name'], 'desc':options['project_desc']}
            p = Project(item)
            result = zanata.projects.create(p)
            if result == "Success":
                self.log.info("Successfully created project: %s"%args[0])
        except NoSuchProjectException, e:
            self.log.error(e.msg) 
        except UnAuthorizedException, e:
            self.log.error(e.msg)
        except ProjectExistException, e:
            self.log.error(e.msg)

    def _create_iteration(self, args):
        """
        Create version with the version id, version name and version description 
        @param args: version id
        """
        zanata = self._generate_zanataresource()
        
        if options['project_id']:
            project_id =  options['project_id'] 
        elif self.project_config['project_id']:
            project_id = self.project_config['project_id']
        else:
            self.log.error("Please specify PROJECT_ID with --project-id option or using zanata.xml")
        
        self.log.info("Project id:%s"%project_id)
        
        if not args:
            self.log.error("Please provide ITERATION_ID for creating iteration")
            sys.exit(1)
       
        if self.server_version:
            version =  str(self.server_version.split('-')[0])
            version_number = string.atof(version)
        
            if version_number <= 1.2 and not options['version_name']:
                options['version_name'] = args[0]
        else:
            if not options['version_name']:
                options['version_name'] = args[0]
               
        try:
            item = {'id':args[0], 'name':options['version_name'], 'desc':options['version_desc']}
            iteration = Iteration(item)
            result = zanata.projects.iterations.create(project_id, iteration)
            if result == "Success":
                self.log.info("Successfully created version: %s"%args[0])
        except ProjectExistException, e:
            self.log.error(e.msg)
        except NoSuchProjectException, e:
            self.log.error(e.msg)
        except UnAuthorizedException, e:
            self.log.error(e.msg)
        except InvalidOptionException, e:
            self.log.error(e.msg)
        except NotAllowedException, e:
            self.log.error(e.msg)

    def check_project(self, zanataclient):
        if options['project_id']:
            project_id =  options['project_id'] 
        else:
            project_id = self.project_config['project_id']
        
        if options['project_version']:
            iteration_id = options['project_version'] 
        else:
            iteration_id = self.project_config['project_version']

        if not project_id:
            self.log.error("Please specify a valid project id in zanata.xml/flies.xml or with '--project-id' option")
            sys.exit(1)
        
        if not iteration_id:
            self.log.error("Please specify a valid version id in zanata.xml/flies.xml or with '--project-version' option")
            sys.exit(1)
        
        self.log.info("Project: %s"%project_id)
        self.log.info("Version: %s"%iteration_id)
        self.log.info("Username: %s"%self.user_name)

        try:
            zanataclient.projects.get(project_id)
        except NoSuchProjectException, e:
            self.log.error(e.msg)
            sys.exit(1)
   
        try:
            zanataclient.projects.iterations.get(project_id, iteration_id)
            return project_id, iteration_id
        except NoSuchProjectException, e:
            self.log.error(e.msg)
            sys.exit(1)

    def search_file(self, path, filename):
        for root, dirs, names in os.walk(path):
            if filename in names:
                return os.path.join(root, filename)
        raise NoSuchFileException('Error 404', 'File %s not found'%filename)

    def import_po(self, publicanutil, trans_folder, zanata, project_id, iteration_id, filename):
        if options['lang']:
            lang_list = options['lang'].split(',')
        elif self.project_config['locale_map']:
            lang_list = self.project_config['locale_map'].keys()
        else:
            self.log.error("Please specify the language with '--lang' option or in zanata.xml")
            sys.exit(1)

        if options['merge']:
            if options['merge'] == 'auto' or options['merge'] == 'import':
                merge = options['merge']
                self.log.info("merge option set to value %s"%merge)
            else:
                self.log.info("merge option %s is not acceptable, change to default value 'auto'"%options['merge'])
                merge = 'auto'

        for item in lang_list:
            self.log.info("Pushing translation for %s to server:"%item)
            
            if item in self.project_config['locale_map']:
                lang = self.project_config['locale_map'][item]
            else:
                lang = item

            locale_folder = os.path.join(trans_folder, item)
                             
            if not os.path.isdir(locale_folder):
                self.log.error("Can not find translation, please specify path of the translation folder")
                continue

            if '/' not in filename:
                pofile_name = filename+'.po'
                request_name = filename
            else:
                name = filename.split('/')[1]
                pofile_name = name+'.po'
                request_name = filename.replace('/', ',')

            try:
                pofile_full_path = self.search_file(locale_folder, pofile_name)
            except NoSuchFileException, e:
                self.log.error(e.msg)
                continue
             
            body = publicanutil.pofile_to_json(pofile_full_path)

            if not body:
                self.log.error("No content or all entries are obsolete in %s"%pofile_name)
                continue
         
            try:
                result = zanata.documents.commit_translation(project_id, iteration_id, request_name, lang, body, merge)
                if result:
                    self.log.info("Successfully pushed translation %s to the server"%pofile_full_path) 
                else:
                    self.log.error("Failed to push translation")
            except UnAuthorizedException, e:
                self.log.error(e.msg)                                            
                break
            except BadRequestBodyException, e:
                self.log.error(e.msg)
                continue

    def update_template(self, zanata, project_id, iteration_id, filename, body):
        if '/' in filename:
            request_name = filename.replace('/', ',')
        else:
            request_name = filename
        
        try:
            result = zanata.documents.update_template(project_id, iteration_id, request_name, body, options['copytrans'])
            if result:
                self.log.info("Successfully updated template %s on the server"%filename)
        except BadRequestBodyException, e:
            self.log.error(e.msg) 
    
    def _push_pofile(self, args):
        import_file = ''
        pot_list = ''
        
        zanata = self._generate_zanataresource()

        project_id, iteration_id = self.check_project(zanata)
        
        self.log.info("Source language: en-US")
        self.log.info("Copy previous translations:%s"%options['copytrans'])
       
        if options['srcdir']:
            tmlfolder = options['srcdir']
        else:
            tmlfolder = os.path.join(os.getcwd(), 'po')
        
        if not os.path.isdir(tmlfolder) and not options['srcfile']:
            self.log.error("Can not find source folder, please specify the source folder with '--srcdir' option")
            sys.exit(1)

        if options['srcfile']:
            import_file = options['srcfile'].split('/')[-1]
            tmlfolder = options['srcfile'].split(import_file)[0]
        
        if args:
           import_file = args[0] 

        if options['importpo']:        
            self.log.info("Importing translation")
            if options['transdir']:
                trans_folder = options['transdir']
            else:
                trans_folder = tmlfolder
            self.log.info("Importing translation from %s"%trans_folder)            
        else:
            self.log.info("Importing source documents only")

        if options['dir']:
            tmlfolder = os.path.join(options['dir'], 'po')
        elif options['srcdir']:
            tmlfolder = options['srcdir']
        else:
            tmlfolder = os.path.join(os.getcwd(), 'po')

        self.log.info("PO directory (originals):%s"%tmlfolder)

        publicanutil = PublicanUtility()

        if not import_file:
            #get all the pot files from the template folder 
            pot_list = publicanutil.get_file_list(tmlfolder, ".pot")
            if not pot_list:
                self.log.error("The template folder is empty")
                sys.exit(1)
                       
        #Get the file list of this version of project
        try:
            filelist = zanata.documents.get_file_list(project_id, iteration_id)
        except Exception, e:
            self.log.error(str(e))
            sys.exit(1)

        if filelist:
            #Give an option to user for keep or delete the content
            self.log.info("This will overwrite/delete any existing documents on the server.")
            
            if not self.force:
                while True:
                    option = raw_input("Are you sure (y/n)?")
                    if option.lower() == "yes" or option.lower() == "y":
                        break    
                    elif option.lower() == "no" or option.lower() == "n":
                        self.log.info("Processing stopped, keeping existing content on the server")
                        sys.exit(1)
                    else:
                        self.log.error("Please enter yes(y) or no(n)")

            for file in filelist:
                if ',' in file: 
                    filename = file.replace(',', '\,')
                elif '/' in file:
                    filename = file.replace('/', ',')
                else:
                    filename = file

                if ".pot" in file:
                    name = os.path.join(tmlfolder, file)
                else:
                    name = os.path.join(tmlfolder, file+".pot")
                
                if pot_list and name not in pot_list:
                    self.log.info("Delete the %s"%file)
                     
                    try:
                        zanata.documents.delete_template(project_id, iteration_id, filename)
                    except Exception, e:
                        self.log.error(str(e))
                        sys.exit(1)
                elif import_file and name != os.path.join(tmlfolder, import_file):
                    self.log.info("Delete the %s"%file)
                    
                    try:
                        zanata.documents.delete_template(project_id, iteration_id, filename)
                    except Exception, e:
                        self.log.error(str(e))
                        sys.exit(1)

        #if file not specified, push all the files in pot folder to zanata server
        if not import_file:
            for pot in pot_list:
                self.log.info("\nPushing the content of %s to server:"%pot)
                    
                body, filename = publicanutil.potfile_to_json(pot, tmlfolder)
                                                          
                try:
                    result = zanata.documents.commit_template(project_id, iteration_id, body, options['copytrans'])
                    if result:
                        self.log.info("Successfully pushed %s to the server"%pot)
                except UnAuthorizedException, e:
                    self.log.error(e.msg)
                    break                                            
                except BadRequestBodyException, e:
                    self.log.error(e.msg)
                    continue
                except SameNameDocumentException, e:
                    self.update_template(zanata, project_id, iteration_id, filename, body)

                if options['importpo']:
                    if options['lang']:
                        lang_list = options['lang'].split(',')
                    elif self.project_config['locale_map']:
                        lang_list = self.project_config['locale_map'].keys()
                    else:
                        self.log.error("Please specify the language with '--lang' option or zanata.xml/flies.xml")
                        sys.exit(1)
                    
                    if options['merge']:
                        if options['merge'] == 'auto' or options['merge'] == 'import':
                            merge = options['merge']
                            self.log.info("merge option set to value %s"%merge)
                        else:
                            self.log.info("merge option %s is not acceptable, change to default value 'auto'"%options['merge'])
                            merge = 'auto'

                    for item in lang_list:
                        self.log.info("Pushing translation for %s to Zanata/Flies server:"%item)
            
                        if item in self.project_config['locale_map']:
                            lang = self.project_config['locale_map'][item]
                        else:
                            lang = item

                        if not os.path.isdir(trans_folder):
                            self.log.error("Can not find translation, please specify path of the translation folder")
                            sys.exit(1)

                        pofile_name = item.replace('-','_')+'.po'   

                        if '/' not in filename:
                            request_name = filename
                            folder = tmlfolder
                        else:
                            request_name = filename.replace('/', ',')
                            subfolder = filename.split('/')[0]
                            folder = os.path.join(tmlfolder, subfolder) 

                        pofile_full_path = os.path.join(folder, pofile_name)
                    
                        if not os.path.isfile(pofile_full_path):
                            self.log.error("Can not find the translation for %s"%item)
                            continue
                                     
                        body = publicanutil.pofile_to_json(pofile_full_path)
                
                        if not body:
                            self.log.error("No content or all entries are obsolete in %s"%pofile_name)
                            continue
         
                        try:
                            result = zanata.documents.commit_translation(project_id, iteration_id, request_name,
                            lang, body, merge)
                            if result:
                                self.log.info("Successfully pushed translation %s to the server"%pofile_full_path) 
                            else:
                                self.log.error("Failed to push translation")
                        except UnAuthorizedException, e:
                            self.log.error(e.msg)                                            
                            break
                        except BadRequestBodyException, e:
                            self.log.error(e.msg)
                            continue
            
        else:
            self.log.info("\nPushing the content of %s to server:"%import_file)

            try:
                full_path = self.search_file(tmlfolder, import_file)
            except NoSuchFileException, e:
                self.log.error(e.msg)
                sys.exit(1)
                        
            body, filename = publicanutil.potfile_to_json(full_path, tmlfolder)
            
            try:
                result = zanata.documents.commit_template(project_id, iteration_id, body, options['copytrans'])                
                if result:
                    self.log.info("Successfully pushed %s to the server"%import_file)
            except UnAuthorizedException, e:
                self.log.error(e.msg)    
            except BadRequestBodyException, e:
                self.log.error(e.msg)
            except SameNameDocumentException, e:
                self.update_template(zanata, project_id, iteration_id, filename, body)   

            if options['importpo']:
                if options['lang']:
                    lang_list = options['lang'].split(',')
                elif self.project_config['locale_map']:
                    lang_list = self.project_config['locale_map'].keys()
                else:
                    self.log.error("Please specify the language with '--lang' option or in zanata.xml")
                    sys.exit(1)

                if options['merge']:
                    if options['merge'] == 'auto' or options['merge'] == 'import':
                        merge = options['merge']
                        self.log.info("merge option set to value %s"%merge)
                    else:
                        self.log.info("merge option %s is not acceptable, change to default value 'auto'"%options['merge'])
                        merge = 'auto'
                
                for item in lang_list:
                    self.log.info("Pushing translation for %s to server:"%item)
            
                    if item in self.project_config['locale_map']:
                        lang = self.project_config['locale_map'][item]
                    else:
                        lang = item

                    if not os.path.isdir(trans_folder):
                        self.log.error("Can not find translation, please specify path of the translation folder")
                        sys.exit(1)

                    pofile_name = item.replace('-','_')+'.po'                

                    pofile_full_path = os.path.join(trans_folder, pofile_name)
                    
                    if not os.path.isfile(pofile_full_path):
                        self.log.error("Can not find the translation for %s"%item)
                        continue
                    
                    body = publicanutil.pofile_to_json(pofile_full_path)
                
                    if not body:
                        self.log.error("No content or all entries are obsolete in %s"%pofile_name)
                        continue
       
                    if '.' in import_file:
                        request_name = import_file.split('.')[0]
                    else:
                        request_name = import_file

                    try:
                        result = zanata.documents.commit_translation(project_id, iteration_id, request_name, lang, body, merge)
                        if result:
                            self.log.info("Successfully pushed translation %s to the Zanata/Flies server"%pofile_full_path) 
                        else:
                            self.log.error("Failed to push translation")
                    except UnAuthorizedException, e:
                        self.log.error(e.msg)                                            
                        break
                    except BadRequestBodyException, e:
                        self.log.error(e.msg)
                        continue
    
    def get_lang_list(self):
        list = []
        if options['lang']:
            list = options['lang'].split(',')
        elif self.project_config['locale_map']:
            list = self.project_config['locale_map'].keys()
        else:
            self.log.error("Please specify the language with '--lang' option or in zanata.xml")
            sys.exit(1)
        return list

    def _create_outpath(self):
        if options['dstdir']:
            if os.path.isdir(options['dstdir']):
                outpath = os.path.join(options['dstdir'], 'po')
            else:
                self.log.error("The destination folder does not exist, please create it")
                sys.exit(1)
        else:
            outpath = os.path.join(os.getcwd(), 'po')
                
        if not os.path.isdir(outpath):
            os.mkdir(outpath)

        return outpath

    def _pull_pofile(self, args):
        zanata = self._generate_zanataresource()

        lang_list = self.get_lang_list()

        project_id, iteration_id = self.check_project(zanata)
        
        #list the files in project
        try:
            filelist = zanata.documents.get_file_list(project_id, iteration_id)
        except Exception, e:
            self.log.error(str(e))
            sys.exit(1)

        publicanutil = PublicanUtility()
        
        #if file no specified, retrieve all the files of project
        if not args:
            if filelist:
                for file in filelist:
                    pot = ''
                    result = ''
                    folder = ''

                    if '/' in file: 
                        name = file.split('/')[-1]
                        folder = file.split('/')[0]
                        request_name = file.replace('/', ',')
                    else:
                        name = file
                        request_name = file

                    self.log.info("\nFetching the content of %s from server: "%name)
                    
                    for item in lang_list:
                        if item in self.project_config['locale_map']:
                            lang = self.project_config['locale_map'][item]
                        else:
                            lang = item
                        
                        outpath = self._create_outpath()                    

                        self.log.info("Retrieving translation for %s from server:"%item)

                        try:
                            pot = zanata.documents.retrieve_template(project_id, iteration_id, request_name)                    
                        except UnAuthorizedException, e:
                            self.log.error(e.msg)
                            break
                        except UnAvaliableResourceException, e:
                            self.log.error("Can't find pot file for %s on the server"%name)
                            break
                
                        try:
                            result = zanata.documents.retrieve_translation(lang, project_id, iteration_id, request_name)
                        except UnAuthorizedException, e:
                            self.log.error(e.msg)                        
                            break
                        except UnAvaliableResourceException, e:
                            self.log.info("There is no %s translation for %s"%(item, name))
                        except BadRequestBodyException, e:
                            self.log.error(e.msg)
                            continue 
                        
                        if folder:
                            subdirectory = os.path.join(outpath, folder)
                            if not os.path.isdir(subdirectory):
                                os.makedirs(subdirectory)
                            pofile = os.path.join(subdirectory, item+'.po') 
                        else:
                            pofile = os.path.join(outpath, item+'.po')
  
                        try:
                            publicanutil.save_to_pofile(pofile, result, pot)
                        except InvalidPOTFileException, e:
                            self.log.error("Can't generate po file for %s,"%name+e.msg)
        else:
            self.log.info("\nFetching the content of %s from server: "%args[0])
            for item in lang_list:
                result = ''
                pot = ''
                folder = ''

                if item in self.project_config['locale_map']:
                    lang = self.project_config['locale_map'][item]
                else:
                    lang = item

                outpath = self._create_outpath() 

                self.log.info("Retrieving %s translation from server:"%item)

                for file in filelist:
                    if '/' in file: 
                        name = file.split('/')[-1]
                        folder = file.split(name)[0]
                        if args[0] == name:
                            request_name = file.replace('/', ',')
                            outpath = os.path.join(outpath, folder)   
                            if not os.path.isdir(outpath):
                                os.makedirs(outpath)
                            break
                    else:
                        if args[0] == file:
                            request_name = file
                            break
                
                if not request_name:
                    self.log.error("Can't find pot file for %s on the server"%args[0])
                    sys.exit(1)

                pofile = os.path.join(outpath, item+'.po')
                                          
                try:
                    pot = zanata.documents.retrieve_template(project_id, iteration_id, request_name)                    
                except UnAuthorizedException, e:
                    self.log.error(e.msg)
                    sys.exit(1)
                except UnAvaliableResourceException, e:
                    self.log.error("Can't find pot file for %s on the server"%args[0])
                    sys.exit(1)

                try:            
                    result = zanata.documents.retrieve_translation(lang, project_id, iteration_id, request_name)
                except UnAuthorizedException, e:
                    self.log.error(e.msg)
                    sys.exit(1)
                except UnAvaliableResourceException, e:
                    self.log.info("There is no %s translation for %s"%(item, args[0]))
                except BadRequestBodyException, e:
                    self.log.error(e.msg)
                    continue 
      
                try:
                    publicanutil.save_to_pofile(pofile, result, pot)                    
                except InvalidPOTFileException, e:
                    self.log.error("Can't generate po file for %s,"%args[0]+e.msg)

    def _push_publican(self, args):
        """
        Push the content of publican files to a Project version on Zanata/Flies server
        @param args: name of the publican file
        """
        zanata = self._generate_zanataresource()

        project_id, iteration_id = self.check_project(zanata)
        
        self.log.info("Source language: en-US")
        self.log.info("Copy previous translations:%s"%options['copytrans'])
        
        if options['importpo']:        
            self.log.info("Importing translation")
            if options['dir']:
                trans_folder = options['dir']
            elif options['transdir']:
                trans_folder = options['transdir']
            else:
                trans_folder = os.getcwd()
            self.log.info("Reading locale folders from %s"%trans_folder)
        else:
            self.log.info("Importing source documents only")
        
        if options['dir']:
            tmlfolder = os.path.join(options['dir'], 'pot')
        elif options['srcdir']:
            tmlfolder = options['srcdir']
        else:
            tmlfolder = os.path.join(os.getcwd(), 'pot')
        
        if not os.path.isdir(tmlfolder):
            self.log.error("Can not find source folder, please specify the source folder with '--srcdir' or '--dir' option")
            sys.exit(1)

        self.log.info("POT directory (originals):%s"%tmlfolder)
                
        #Get the file list of this version of project
        try:
            filelist = zanata.documents.get_file_list(project_id, iteration_id)
        except Exception, e:
            self.log.error(str(e))
            sys.exit(1)

        if filelist:
            #Give an option to user for keep or delete the content
            self.log.info("This will overwrite/delete any existing documents on the server.")
            
            if not self.force:
                while True:
                    option = raw_input("Are you sure (y/n)?")
                    if option.lower() == "yes" or option.lower() == "y":
                        break    
                    elif option.lower() == "no" or option.lower() == "n":
                        self.log.info("Processing stopped, keeping the content on the zanata server")
                        sys.exit(1)
                    else:
                        self.log.error("Please enter yes(y) or no(n)")

            for file in filelist:
                if ',' in file: 
                    filename = file.replace(',', '\,')
                elif '/' in file:
                    filename = file.replace('/', ',')
                else:
                    filename = file

                if ".pot" in file:
                    filepath = os.path.join(tmlfolder, file)
                else:
                    filepath = os.path.join(tmlfolder, file+".pot")
                
                if not os.path.isfile(filepath):
                    self.log.info("Delete the %s"%file)
                 
                    try:
                        zanata.documents.delete_template(project_id, iteration_id, filename)
                    except Exception, e:
                        self.log.error(str(e))
                        sys.exit(1)

        publicanutil = PublicanUtility()
        #if file not specified, push all the files in pot folder to zanata server
        if not args:
            #get all the pot files from the template folder 
            pot_list = publicanutil.get_file_list(tmlfolder, ".pot")

            if not pot_list:
                self.log.error("The template folder is empty")
                sys.exit(1)

            for pot in pot_list:
                self.log.info("\nPushing the content of %s to server:"%pot)
                    
                body, filename = publicanutil.potfile_to_json(pot, tmlfolder)
                                          
                try:
                    result = zanata.documents.commit_template(project_id, iteration_id, body, options['copytrans'])
                    if result:
                        self.log.info("Successfully pushed %s to the server"%pot)
                except UnAuthorizedException, e:
                    self.log.error(e.msg)
                    break                                            
                except BadRequestBodyException, e:
                    self.log.error(e.msg)
                    continue
                except SameNameDocumentException, e:
                    self.update_template(zanata, project_id, iteration_id, filename, body)

                if options['importpo']:
                    self.import_po(publicanutil, trans_folder, zanata, project_id, iteration_id, filename)
            
        else:
            self.log.info("\nPushing the content of %s to server:"%args[0])

            try:
                full_path = self.search_file(tmlfolder, args[0])
            except NoSuchFileException, e:
                self.log.error(e.msg)
                sys.exit(1)
                        
            body, filename = publicanutil.potfile_to_json(full_path, tmlfolder)
            
            try:
                result = zanata.documents.commit_template(project_id, iteration_id, body, options['copytrans'])                
                if result:
                    self.log.info("Successfully pushed %s to the server"%args[0])
            except UnAuthorizedException, e:
                self.log.error(e.msg)    
            except BadRequestBodyException, e:
                self.log.error(e.msg)
            except SameNameDocumentException, e:
                self.update_template(project_id, iteration_id, filename, body)   

            if options['importpo']:
                self.import_po(publicanutil, trans_folder, zanata, project_id, iteration_id, filename)

    def _pull_publican(self, args):
        """
        Retrieve the content of documents in a Project version from Zanata/Flies server. If the name of publican
        file is specified, the content of that file will be pulled from server. Otherwise, all the document of that
        Project iteration will be pulled from server.
        @param args: the name of publican file
        """
        zanata = self._generate_zanataresource()

        project_id, iteration_id = self.check_project(zanata)

        lang_list = self.get_lang_list()
        
        #list the files in project
        try:
            filelist = zanata.documents.get_file_list(project_id, iteration_id)
        except Exception, e:
            self.log.error(str(e))
            sys.exit(1)

        publicanutil = PublicanUtility()
        
        #if file no specified, retrieve all the files of project
        if not args:
            if filelist:
                for file in filelist:
                    pot = ''
                    result = ''
                    folder = ''

                    if '/' in file: 
                        name = file.split('/')[-1]
                        folder = file.split('/')[0]
                        request_name = file.replace('/', ',')
                    else:
                        name = file
                        request_name = file

                    self.log.info("\nFetching the content of %s from Zanata/Flies server: "%name)                    
                    
                    for item in lang_list:
                        if item in self.project_config['locale_map']:
                            lang = self.project_config['locale_map'][item]
                        else:
                            lang = item
                        
                        if options['dir']:
                            if os.path.isdir(options['dir']):
                                outpath = os.path.join(options['dir'], item)
                            else:
                                self.log.error("The destination folder does not exist, please create it")
                                sys.exit(1)
                        elif options['dstdir']:
                            if os.path.isdir(options['dstdir']):
                                outpath = os.path.join(options['dstdir'], item)
                            else:
                                self.log.error("The destination folder does not exist, please create it")
                                sys.exit(1)
                        else:
                            outpath = os.path.join(os.getcwd(), item)
                        
                        if not os.path.isdir(outpath):
                            os.mkdir(outpath)                        

                        self.log.info("Retrieving %s translation from server:"%item)

                        try:
                            pot = zanata.documents.retrieve_template(project_id, iteration_id, request_name)                    
                        except UnAuthorizedException, e:
                            self.log.error(e.msg)
                            break
                        except UnAvaliableResourceException, e:
                            self.log.error("Can't find pot file for %s on server"%name)
                            break
                
                        try:
                            result = zanata.documents.retrieve_translation(lang, project_id, iteration_id, request_name)
                        except UnAuthorizedException, e:
                            self.log.error(e.msg)                        
                            break
                        except UnAvaliableResourceException, e:
                            self.log.info("There is no %s translation for %s"%(item, name))
                        except BadRequestBodyException, e:
                            self.log.error(e.msg)
                            continue 
                        
                        if folder:
                            subdirectory = os.path.join(outpath, folder)
                            if not os.path.isdir(subdirectory):
                                os.makedirs(subdirectory)
                            pofile = os.path.join(subdirectory, name+'.po') 
                        else:
                            pofile = os.path.join(outpath, name+'.po')
  
                        try:
                            publicanutil.save_to_pofile(pofile, result, pot)
                        except InvalidPOTFileException, e:
                            self.log.error("Can't generate po file for %s,"%name+e.msg)
        else:
            self.log.info("\nFetching the content of %s from server: "%args[0])
            for item in lang_list:
                result = ''
                pot = ''
                folder = ''

                if item in self.project_config['locale_map']:
                    lang = self.project_config['locale_map'][item]
                else:
                    lang = item
                        
                if options['dir']:
                    if os.path.isdir(options['dir']):
                        outpath = os.path.join(options['dir'], item)
                    else:
                        self.log.error("The destination folder does not exist, please create it")
                elif options['dstdir']:
                    if os.path.isdir(options['dstdir']):
                        outpath = os.path.join(options['dstdir'], item)
                    else:
                        self.log.error("The destination folder does not exist, please create it")
                        sys.exit(1)
                else:
                    outpath = os.path.join(os.getcwd(), item)

                if not os.path.isdir(outpath):
                    os.mkdir(outpath)

                self.log.info("Retrieve %s translation from server:"%item)
                
                request_name = ''
                for file in filelist:
                    if '/' in file: 
                        name = file.split('/')[-1]
                        folder = file.split('/')[0]
                        if args[0] == name:
                            request_name = file.replace('/', ',')
                            outpath = os.path.join(outpath, folder)   
                            if not os.path.isdir(outpath):
                                os.makedirs(outpath)
                            break
                    else:
                        if args[0] == file:
                            request_name = file
                            break
                
                if not request_name:
                    self.log.error("Can't find pot file for %s on server"%args[0])
                    sys.exit(1)

                pofile = os.path.join(outpath, args[0]+'.po')
                                          
                try:
                    pot = zanata.documents.retrieve_template(project_id, iteration_id, request_name)                    
                except UnAuthorizedException, e:
                    self.log.error(e.msg)
                    sys.exit(1)
                except UnAvaliableResourceException, e:
                    self.log.error("Can't find pot file for %s on server"%args[0])
                    sys.exit(1)

                try:            
                    result = zanata.documents.retrieve_translation(lang, project_id, iteration_id, request_name)
                except UnAuthorizedException, e:
                    self.log.error(e.msg)
                    sys.exit(1)
                except UnAvaliableResourceException, e:
                    self.log.info("There is no %s translation for %s"%(item, args[0]))
                except BadRequestBodyException, e:
                    self.log.error(e.msg)
                    continue 
      
                try:
                    publicanutil.save_to_pofile(pofile, result, pot)                    
                except InvalidPOTFileException, e:
                    self.log.error("Can't generate po file for %s,"%args[0]+e.msg)
                    
    def _remove_project(self):
        pass

    def _remove_iteration(self):
        pass

    def _project_status(self):
        pass
    
    def _process_command_line(self):
        """
        Parse the command line to generate command options and sub_command
        """
        try:
            opts, args = getopt.gnu_getopt(sys.argv[1:], "vfh", ["url=", "project-id=", "project-version=", "project-name=",
            "project-desc=", "version-name=", "version-desc=", "lang=",  "user-config=", "project-config=", "apikey=",
            "username=", "dir=", "srcdir=", "srcfile=", "dstdir=", "email=", "transdir=", "merge=", "import-po", "no-copytrans", "help"])
        except getopt.GetoptError, err:
            self.log.error(str(err))
            sys.exit(2)

        if args:
            command = args[0]
            sub = args[1:]            
            if sub_command.has_key(command):
                if sub_command[command]:
                    if sub:
                        if sub[0] in sub_command[command]:
                            command = command+'_'+sub[0]
                            command_args = sub[1:]
                        else:
                            self.log.error("Unknown command")
                            sys.exit(1)
                    else:
                        self.log.error("Please complete the command!")
                        sys.exit(1)
                else: 
                    command_args = sub
            else:
                self.log.error("Unknown command")
                sys.exit(1)
        else:
            self.help.print_usage()
            sys.exit(1)
        
        if opts:
            for o, a in opts:
                if o =="-f":
                    self.force = True
                elif o in ("--user-config"):
                    options['user_config'] = a                     
                elif o in ("--url"):
                    options['url'] = a
                elif o in ("--project-name"):
                    options['project_name'] = a
                elif o in ("--project-desc"):
                    options['project_desc'] = a
                elif o in ("--project-id"):
                    options['project_id'] = a
                elif o in ("--version-name"):
                    options['version_name'] = a
                elif o in ("--version-desc"):
                    options['version_desc'] = a
                elif o in ("--lang"):
                    options['lang'] = a
                elif o in ("--username"):
                    options['user_name'] = a
                elif o in ("--apikey"):
                    options['key'] = a
                elif o in ("--project-config"):
                    options['project_config'] = a
                elif o in ("--project-version"): 
                    options['project_version'] = a
                elif o in ("--srcdir"):
                    options['srcdir'] = a
                elif o in ("--dir"):
                    options['dir'] = a
                elif o in ("--srcfile"):
                    options['srcfile'] = a
                elif o in ("--dstdir"):
                    options['dstdir'] = a
                elif o in ("--transdir"):
                    options['transdir'] = a
                elif o in ("--email"):
                    options['email'] = a
                elif o in ("--merge"):
                    options['merge'] = a
                elif o in ("--import-po"):
                    options['importpo'] = True
                elif o in ("--no-copytrans"):
                    options['copytrans'] = False
                elif o in ("--help") or o == "-h":
                    self.help.print_command_help(command)
                    sys.exit()
                   
        return command, command_args
    
    def signal_handler(self, signal, frame):
        print '\nPressed Ctrl+C! Stop processing!'
        sys.exit(0)
 
    def run(self):
        signal.signal(signal.SIGINT, self.signal_handler)
        command, command_args = self._process_command_line()        
        
        if command == 'help':
            self.help.print_usage()
        else:
            config = ZanataConfig()
            #Read the project configuration file using --project-config option
            config_file = [os.path.join(os.getcwd(), filename) for filename in ['zanata.xml', 'flies.xml']]
            if options['project_config']:
                config_file.append(options['project_config'])

            if [os.path.exists(path) for path in config_file]:
                self.log.info("Loading zanata project config from %s"%path)            
                self.project_config = config.read_project_config(path)
            elif command != 'list':                
                self.log.info("Can not find zanata.xml/flies.xml, please specify the path of zanata.xml")
                
            #process the url of server
            if self.project_config:
                self.url = self.project_config['project_url']
            
            #The value in options will override the value in project-config file
            if options['url']:
                self.log.info("Overriding url of server with command line option")
                self.url = options['url']

            if not self.url or self.url.isspace():
                self.log.error("Please specify valid server url in zanata.xml/flies.xml or with '--url' option")
                sys.exit(1)

            if self.url[-1] == "/":
                self.url = self.url[:-1]
                       
            #Try to read user-config file
            user_config = [os.path.join(os.path.expanduser("~")+'/.config', filename) for filename in ['zanata.ini', 'flies.ini']]

            if options['user_config']:  
                user_config.append(options['user_config'])

            if [os.path.exists(path) for path in user_config]:
                self.log.info("Loading zanata/flies user config from %s"%path)
                
                #Read the user-config file    
                config.set_userconfig(path)
                
                try:
                    server = config.get_server(self.url)
                    if server:
                        self.user_name = config.get_config_value("username", "servers", server)
                        self.apikey = config.get_config_value("key", "servers", server)
                except Exception, e:
                    self.log.info("Processing user-config file:%s"%str(e))
            else:    
                self.log.info("Can not find user-config file in home folder, current path or path in 'user-config' option")
            
            self.log.info("zanata/flies server: %s"%self.url) 
            
            #The value in commandline options will overwrite the value in user-config file          
            if options['user_name']:
                self.user_name = options['user_name']
            
            if options['key']:
                self.apikey = options['key']
           
            #Retrieve the version of the zanata server 
            version = VersionService(self.url)
            
            #Retrieve the version of client
            path = os.path.dirname(os.path.realpath(__file__))
            version_file = os.path.join(path, 'VERSION-FILE')
            file = open(version_file, 'rb')
            client_version = file.read()
            file.close()
            version_number = client_version[:-1].strip('version: ')

            try:            
                content = version.get_server_version()
                self.server_version = content['versionNo']
                self.log.info("zanata python client version: %s, zanata/flies server API version: %s"%(version_number, content['versionNo']))  
            except UnAvaliableResourceException, e:
                self.log.info("zanata python client version: %s"%version_number)
                self.log.error("Can not retrieve the server version, server may not support the version service")

            if command == 'list':
                self._list_projects()
            else:
                if command == 'status':
                    self._poject_status()
                elif command == 'project_info':
                    self._get_project()
                elif command == 'project_create':
                    self._create_project(command_args)
                elif command == 'project_remove':
                    self._remove_project(command_args)
                elif command == 'version_info':
                    self._get_iteration()
                elif command == 'version_create':
                    self._create_iteration(command_args)
                elif command == 'version_remove':
                    self._remove_iteration(command_args)
                elif command == 'publican_push':
                    self._push_publican(command_args)
                elif command == 'publican_pull':
                    self._pull_publican(command_args)
                elif command == 'po_push':
                    self._push_pofile(command_args)
                elif command == 'po_pull':
                    self._pull_pofile(command_args)

def main():
    client = ZanataConsole()
    client.run()

if __name__ == "__main__":
    main()       
