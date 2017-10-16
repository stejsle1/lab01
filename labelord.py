import getpass
import requests
import click
import configparser
import json
import sys
import os

def setup(session, token):
   session.headers = {'User-Agent': 'Python'}
   def token_auth(req):
      req.headers['Authorization'] = 'token ' + token
      return req

   session.auth = token_auth
   
   return session
   
def printextra(level, text, label, err): 
   if level == 0:
      return
   if level == 1:
      if err == 1:
         print('ERROR: ' + label + '; ' + text)
         return
   if level == 2:
      if err == 0:
         print('[' + label + '][SUC] ' + text)
      if err == 1:
         print('[' + label + '][ERR] ' + text)               
      if err == 2:
         print('[' + label + '][DRY] ' + text)
   if level == 4:
      if err == 2:
         print('[SUMMARY] ' + text) 
      else:
         print('SUMMARY: ' + text)         

# Structure your implementation as you want (OOP, FP, ...)
# Try to make it DRY also for your own good


@click.group('labelord') 
@click.option('-c', '--config', type=click.Path(exists=True), help='Config file')
@click.option('-t', '--token', help='Token')
@click.option('--tenv', envvar='GITHUB_TOKEN')
@click.pass_context
def cli(ctx, config, token, tenv):
   conffile = configparser.ConfigParser()
   
   if config is not None:
      conffile.read(config) 
   else:
      if os.path.isfile('./config.cfg') == True:
         conffile.read('./config.cfg')
         config = './config.cfg'
           
   if not token:
      if not tenv:
         if os.path.isfile('./config.cfg') == False or not 'github' in conffile:
            print('No GitHub token has been provided', file=sys.stderr)
            sys.exit(3)
         if 'github' in conffile and not 'token' in conffile['github']:
            print('No GitHub token has been provided', file=sys.stderr)
            sys.exit(3)
         else: t = conffile['github']['token']
      else: t = tenv
   else: t = token
   
    # TODO: Add and process required app-wide options
    # You can/should use context 'ctx' for passing
    # data and objects to commands

    # Use this session for communication with GitHub
   session = ctx.obj.get('session', requests.Session())
   session = setup(session, t)
   ctx.obj['session'] = session
   ctx.obj['config'] = config


@cli.command()
@click.pass_context
def list_repos(ctx):
   
   session = ctx.obj['session']

   repos = session.get('https://api.github.com/user/repos?per_page=100&page=1')
   a = 0
   if 'message' in repos.json() and repos.json()['message'] == 'Bad credentials':
      print("GitHub: ERROR " + str(repos.status_code) + ' - ' + repos.json()['message'], file=sys.stderr)
      sys.exit(4)

   if repos.status_code != 200:
      print("GitHub: ERROR " + str(repos.status_code) + ' - ' + repos.json()['message'], file=sys.stderr)
      sys.exit(10)

   for repo in repos.json():
      print(repo['full_name'])
      a = a+1
   
   b = 1   
   if a == 100:
      while a == 100:  
        a = 0
        b = b+1
        repos = session.get('https://api.github.com/user/repos?per_page=100&page=' + str(b)) 
        for repo in repos.json():
           print(repo['full_name']) 
           a = a+1 


@cli.command()
@click.argument('repository', required=1)
@click.pass_context
def list_labels(ctx, repository):

   session = ctx.obj['session']
   a = 0
   list = session.get('https://api.github.com/repos/' + repository + '/labels?per_page=100&page=1')
   if list.status_code == 404:
      print("GitHub: ERROR " + str(list.status_code) + ' - ' + list.json()['message'], file=sys.stderr)
      sys.exit(5)
  
   if 'message' in list.json() and list.json()['message'] == 'Bad credentials':
      print("GitHub: ERROR " + str(list.status_code) + ' - ' + list.json()['message'], file=sys.stderr)
      sys.exit(4)
        
   if list.status_code != 200:
      print("GitHub: ERROR " + str(list.status_code) + ' - ' + list.json()['message'], file=sys.stderr)
      sys.exit(10)
      
   for label in list.json():
      print(u'\u0023' + label['color'] + ' ' + label['name'])
      a = a+1 
        
   b = 1 
     
   if a == 100:
      while a == 100: 
        a = 0
        b = b+1
        list = session.get('https://api.github.com/repos/' + repository + '/labels?per_page=100&page=' + str(b))
     
        for label in list.json():
           print(u'\u0023' + label['color'] + ' ' + label['name'])
           a = a+1
          

@cli.command()
@click.argument('mode', type=click.Choice(['update', 'replace']))
@click.option('-r', '--template-repo', help="Add a template repo.")
@click.option('-a', '--all-repos', is_flag=True, help='All available repos.')
@click.option('-d', '--dry-run', is_flag=True, help='Dry run')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode')
@click.option('-q', '--quiet', is_flag=True, help='Quiet mode')
@click.pass_context
def run(ctx, mode, template_repo, all_repos, dry_run, verbose, quiet):
   
   config = ctx.obj['config']
   conffile = configparser.ConfigParser()
   conffile.optionxform = str
   conffile.read(config) 
   session = ctx.obj['session']
   
   repos = []
   errors = 0
   sum = 0
   
   # vyber, kde menit labely
   if not all_repos:
      if not 'repos' in conffile:
         print('No repositories specification has been found', file=sys.stderr)
         sys.exit(7)
      else: 
         for repo in conffile['repos']:
            if conffile.getboolean('repos', repo):
               repos.append(repo)
   else: 
      reposlist = session.get('https://api.github.com/user/repos')
      if 'message' in reposlist.json() and reposlist.json()['message'] == 'Bad credentials':
         print("GitHub: ERROR " + str(reposlist.status_code) + ' - ' + reposlist.json()['message'], file=sys.stderr)
         sys.exit(4)

      if reposlist.status_code != 200:
         print("GitHub: ERROR " + str(reposlist.status_code) + ' - ' + reposlist.json()['message'], file=sys.stderr)
         sys.exit(10)

      for repo in reposlist.json():
         repos.append(repo['full_name'])
   
   c = 0
   labels = {}
   ok = 0
   level = 1
   if verbose: level = 2
   if quiet: level = 0
   if verbose and quiet: level = 1
   err = 0
   if dry_run: err = 2
   
   # vyber labelu
   if not template_repo:
      if not 'others' in conffile:
         if not 'labels' in conffile:
            print('No labels specification has been found', file=sys.stderr)
            sys.exit(6)
         else: 
            # update labels z configu
            for label in conffile['labels']:
               labels[label] = conffile['labels'][label]      
      else: 
         # update template repo z configu
         list = session.get('https://api.github.com/repos/' + conffile['others']['template-repo'] + '/labels')
         if list.status_code == 404: 
            printextra(level, conffile['others']['template-repo'] + '; ' + str(list.status_code) + ' - ' + list.json()['message'], 'LBL', 1)
            errors = errors + 1
         for label in list.json():
            labels[label['name']] = label['color']
   else: 
      # update --template-repo z prepinace
      list = session.get('https://api.github.com/repos/' + template_repo + '/labels')
      if list.status_code == 404: 
         printextra(level, template_repo + '; ' + str(list.status_code) + ' - ' + list.json()['message'], 'LBL', 1)
         errors = errors + 1
      for label in list.json():
         labels[label['name']] = label['color']
   
   for repo in repos:
      sum = sum + 1
      list = session.get('https://api.github.com/repos/' + repo + '/labels?per_page=100&page=1') 
      if list.status_code != 200:
         printextra(level, repo + '; ' + str(list.status_code) + ' - ' + list.json()['message'], 'LBL', 1)
      for label in list.json():
         if label['name'] in labels:
            if labels[label['name']] != label['color']: 
               colors = json.dumps({"name": label['name'], "color": labels[label['name']]})
               c = c + 1
               if not dry_run: req = session.patch('https://api.github.com/repos/' + repo + '/labels/' + label['name'], data=colors) 
               if dry_run or req.status_code == 200:
                  printextra(level, repo + '; ' + label['name'] + '; ' + labels[label['name']] + '; ' + label['name'] + '; ' + labels[label['name']], 'UPD', err)
               else:
                  printextra(level, repo + '; ' + str(req.status_code) + ' - ' + req.json()['message'], 'UPD', 1)
                  errors = errors + 1
         elif mode == 'replace':
            if not dry_run: req = session.delete('https://api.github.com/repos/' + repo + '/labels/' + label['name'])
            if dry_run or req.status_code == 204:
               printextra(level, repo + '; ' + label['name'] + '; ' + label['color'], 'DEL', err)
            else:
               printextra(level, repo + '; ' + label['name'] + '; ' + label['color'] + '; ' + str(req.status_code) + ' - ' + req.json()['message'], 'DEL', 1)
               errors = errors + 1
      for label in labels:
         for label2 in list.json():
            if label == label2: ok = 1
         if ok != 1: 
            colors = json.dumps({"name":label, "color":labels[label]})
            if not dry_run: req = session.post('https://api.github.com/repos/' + repo + '/labels', data=colors)  
            if c > 0: sys.exit(sum)
            if dry_run or req.status_code == 201:
               printextra(level, repo + '; ' + label + '; ' + labels[label], 'ADD', err)
            else:
               printextra(level, repo + '; ' + label + '; ' + labels[label] + '; ' + str(req.status_code) + ' - ' + req.json()['message'], 'ADD', 1)
               errors = errors + 1
                       
         ok = 0
   if errors != 0:      
      printextra(4, str(errors) + ' error(s) in total, please check log above', '', level)      
   else:
      printextra(4, str(sum) + ' repo(s) updated successfully', '', level)    
         

if __name__ == '__main__':
    cli(obj={})