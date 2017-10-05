import getpass
import requests
import click
import configparser
#import pygithub3

config = configparser.ConfigParser()
config.read('auth.cfg')

session = requests.Session()
session.headers = {'User-Agent': 'Python'}
def token_auth(req):
    req.headers['Authorization'] = 'token ' + config['github']['token']
    return req

session.auth = token_auth
r = session.get('https://api.github.com/user')

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
@click.pass_context
def list_repos(ctx):
   repos = session.get('https://api.github.com/orgs/stejsle1/repos')
   for repo in repos:
      print(repo)

@cli.command()
@click.pass_context
def list_labels(ctx):
    # TODO: Add required options/arguments
    # TODO: Implement the 'list_labels' command
    ...


@cli.command()
@click.pass_context
def run(ctx):
    # TODO: Add required options/arguments
    # TODO: Implement the 'run' command
    ...


if __name__ == '__main__':
    cli(obj={})
