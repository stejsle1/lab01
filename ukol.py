import getpass
import requests
import click
import configparser
import json
import sys

def setup(session, token):
   session = requests.Session()
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
@click.pass_context
def cli(ctx):
    # TODO: Add and process required app-wide options
    # You can/should use context 'ctx' for passing
    # data and objects to commands

    # Use this session for communication with GitHub
    session = ctx.obj.get('session', requests.Session())


@cli.command()
@click.option('-c', '--config', default='./config.cfg', help='Config file')
@click.option('-t', '--token', help='Token')
@click.option('--tenv', envvar='GITHUB_TOKEN')
@click.pass_context
def list_repos(ctx, config, token, tenv):
   conffile = configparser.ConfigParser()
   conffile.read(config)

   if not token:
      if not tenv:
         if not 'github' in conffile:
            print('No GitHub token has been provided.', file=sys.stderr)
            sys.exit(3)
         if 'github' in conffile and not 'token' in conffile['github']:
            print('No GitHub token has been provided.', file=sys.stderr)
            sys.exit(3)
         else: t = conffile['github']['token']
      else: t = tenv
   else: t = token

   session = requests.Session()
   session = setup(session, t)

   repos = session.get('https://api.github.com/user/repos')
   
   if 'message' in repos.json() and repos.json()['message'] == 'Bad credentials':
      print("Bad credentials.", file=sys.stderr)
      sys.exit(5)

   if repos.status_code != 200:
      print("Error.", file-sys.stderr)
      sys.exit(10)

   for repo in repos.json():
      print(repo['full_name'])


@cli.command()
@click.option('-c', '--config', default='./config.cfg', help='Config file')
@click.option('-t', '--token', help='Token')
@click.option('--tenv', envvar='GITHUB_TOKEN')
@click.argument('repository', required=1)
@click.pass_context
def list_labels(ctx, config, token, tenv, repository):
   conffile = configparser.ConfigParser()
   conffile.read(config)

   if not token:
      if not tenv:
         if not 'github' in conffile:
            print('No GitHub token has been provided.', file=sys.stderr)
            sys.exit(3)
         if 'github' in conffile and not 'token' in conffile['github']:
            print('No GitHub token has been provided.', file=sys.stderr)
            sys.exit(3)
         else: t = conffile['github']['token']
      else: t = tenv
   else: t = token

   session = requests.Session()
   session = setup(session, t)

   list = session.get('https://api.github.com/repos/stejsle1/' + repository + '/labels')
   if list.status_code == 404:
      print(list.json()['message'], file=sys.stderr)
      sys.exit(5)

   if list.status_code != 200:
      print("Error.", file=sys.stderr)
      sys.exit(10)

   for label in list.json():
      print(u'\u0023' + label['color'].upper() + ' ' + label['name'])

@cli.command()
@click.argument('mode', type=click.Choice(['update', 'replace']))
@click.option('-c', '--config', default='./config.cfg', help='Config file')
@click.option('-t', '--token', help='Token')
@click.option('--tenv', envvar='GITHUB_TOKEN')
@click.option('-r', '--template-repo', help="Add a template repo.")
@click.option('-a', '--all-repos', is_flag=True, help='All available repos.')
@click.option('-d', '--dry-run', is_flag=True, help='Dry run')
@click.option('-v', '--verbose', is_flag=True, help='Verbose mode')
@click.option('-q', '--quiet', is_flag=True, help='Quiet mode')
@click.pass_context
def run(ctx, mode, config, token, tenv, template_repo, all_repos, dry_run, verbose, quiet):
   conffile = configparser.ConfigParser()
   conffile.optionxform = str
   conffile.read(config)
   
   if not token:
      if not tenv:
         if not 'github' in conffile:
            print('No GitHub token has been provided.', file=sys.stderr)
            sys.exit(3)
         if 'github' in conffile and not 'token' in conffile['github']:
            print('No GitHub token has been provided.', file=sys.stderr)
            sys.exit(3)
         else: t = conffile['github']['token']
      else: t = tenv
   else: t = token

   session = requests.Session()
   session = setup(session, t)
   
   repos = []
   errors = 0
   sum = 0
   
   # vyber, kde menit labely
   if not all_repos:
      if not 'repos' in conffile:
         print('No repositories specification has been found.', file=sys.stderr)
         sys.exit(7)
      else: 
         for repo in conffile['repos']:
            if conffile.getboolean('repos', repo):
               repos.append(repo)
   else: 
      reposlist = session.get('https://api.github.com/user/repos')
      if 'message' in reposlist.json() and reposlist.json()['message'] == 'Bad credentials':
         print("Bad credentials.", file=sys.stderr)
         sys.exit(5)

      if reposlist.status_code != 200:
         print("Error.", file-sys.stderr)
         sys.exit(10)

      for repo in reposlist.json():
         repos.append(repo['full_name'])
   
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
            print('No labels specification has been found.', file=sys.stderr)
            sys.exit(6)
         else: 
            # update labels z configu
            for label in conffile['labels']:
               labels[label] = conffile['labels'][label]
      else: 
         # update template repo z configu
         list = session.get('https://api.github.com/repos/' + conffile['others']['template-repo'] + '/labels')
         if list.status_code == 404: 
            printextra(level, conffile['others']['template-repo'] + '; ' + list.status_code + ' - ' + list.message, 'LBL', 1)
            errors = errors + 1
         for label in list.json():
            labels[label['name']] = label['color']
   else: 
      # update --template-repo z prepinace
      list = session.get('https://api.github.com/repos/' + template-repo + '/labels')
      if list.status_code == 404: 
         printextra(level, template-repo + '; ' + list.status_code + ' - ' + list.message, 'LBL', 1)
         errors = errors + 1
      for label in list.json():
         labels[label['name']] = label['color']
   
   for repo in repos:
      sum = sum + 1
      list = session.get('https://api.github.com/repos/' + repo + '/labels')
      if list.status_code != 200:
         printextra(level, repo + '; ' + list.status_code + ' - ' + list.message, 'LBL', 1)
      for label in list.json(): 
         if 'label' in labels:
            if labels[label['name']] != label['color']: 
               colors = json.dumps({"name": label['name'], "color": labels[label['name']].lower()})
               if not dry_run: req = session.patch('https://api.github.com/repos/' + repo + '/labels/' + label['name'], data=colors)
               if dry_run or req.status_code == 200:
                  printextra(level, repo + '; ' + label['name'] + '; ' + labels[label['name']] + '; ' + label['name'] + '; ' + labels[label['name']], 'UPD', err)
               else:
                  printextra(level, repo + '; ' + req.status_code + ' - ' + req.message, 'UPD', 1)
                  errors = errors + 1
         else:
            if not dry_run: req = session.delete('https://api.github.com/repos/' + repo + '/labels/' + label['name'])
            if dry_run or req.status_code == 204:
               printextra(level, repo + '; ' + label['name'] + '; ' + labels[label['name']], 'DEL', err)
            else:
               printextra(level, repo + '; ' + label['name'] + '; ' + labels[label['name']] + '; ' + req.status_code + ' - ' + req.message, 'DEL', 1)
               errors = errors + 1
      for label in labels:
         for label2 in list.json():
            if label == label2: ok = 1
         if ok != 1:
            colors = json.dumps({"name": label, "color": labels[label].lower()})
            if not dry_run: req = session.post('https://api.github.com/repos/' + repo + '/labels', data=colors)
            if dry_run or req.status_code == 201:
               printextra(level, repo + '; ' + label + '; ' + labels[label], 'ADD', err)
            else:
               printextra(level, repo + '; ' + label + '; ' + labels[label] + '; ' + req.status_code + ' - ' + req.message, 'ADD', 1)
               errors = errors + 1
                       
         ok = 0
   if errors != 0:      
      printextra(4, str(errors) + ' error(s) in total, please check log above', '', level)      
   else:
      printextra(4, str(sum) + ' repo(s) updated successfully', '', level)    
         

if __name__ == '__main__':
    cli(obj={})
    
    

