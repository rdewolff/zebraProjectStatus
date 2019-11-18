#!/usr/bin/env python3
# cli.py
import click
import requests
import json
import os
from slackclient import SlackClient

# set this to your Zebra API token
api_token = '7e1c36d855a534f99fe90d2216f2a0d93acc4d0739ab1ebb89ceb0f85dc8812a'

req_header = {'Authorization': 'Token ' + api_token}

def _get_my_user():
    url = 'https://zebra.liip.ch/api/v2/users/me?token='+api_token
    r = requests.get(url, verify=False)
    p = json.loads(r.text)['data']
    # click.echo(json.dumps(p))
    return {
        'firstname': 'Asd',
        'email': p['user']['email'],
    }

def _slack_message_me(msg):

    # defined via Slack API for Liip - OAuth
    # https://api.slack.com/apps/AQLKC5MP0/oauth?
    slack_bot_user_oauth_access_token = 'xoxb-2194754682-836680597286-lVYhLRwDXws4Br1IEeRThtYa'

    sc = SlackClient(slack_bot_user_oauth_access_token)

    channels = sc.api_call(
        "channels.list",
        exclude_archived=1
    )

    myUser = _get_my_user()
    
    # click.echo(json.dumps(channels))
    users = sc.api_call(
        "users.lookupByEmail",
        email=myUser['email']
    )

    # debug
    # click.echo(json.dumps(users))

    sc.api_call(
        'chat.postMessage',
        channel='UCL6VQ51B', # RDW
        text=msg
    )

    # debuf
    # sc.api_call(
    #     "chat.postMessage",
    #     channel="C02N5NLKU",  # test channel
    #     text="Hello world! :tada:"
    # )

def report_project(project_id):
    try:
        url = 'https://zebra.liip.ch/api/v2/projects/' + project_id + '?token='+api_token
        r = requests.get(url, verify=False)
        p = json.loads(r.text)['data']

        click.echo(p['name'])
        # get values from zebra
        budget = float(p['financial']['budget'])
        total_time = float(p['financial']['total_time'])
        rate = float(p['financial']['rate']['value'])

        # calculations
        budget_md = budget / rate / 8
        total_time_chf = total_time * rate
        total_time_md = total_time / 8
        remaining_chf = budget - total_time_chf
        remaining_md = remaining_chf / rate / 8

        # report
        budget_str = 'Budget: CHF {:0,.2f} => {:0,.2f} WD'.format(
            budget, budget_md).replace(',', '\'')
        consumed_str = 'Consumed: CHF {:0,.2f} => {:0,.2f} WD'.format(
            total_time_chf, total_time_md).replace(',', '\'')
        remaining_str = 'Remaining: CHF {:0,.2f} => {:0,.2f} WD'.format(
            remaining_chf, remaining_md).replace(',', '\'')

        # display to STDOUT
        click.echo(budget_str)
        click.echo(consumed_str)
        click.echo(remaining_str)
        click.echo('https://zebra.liip.ch/project/' + project_id)

        _slack_message_me('*' + p['name'] + '*' + '\n' + budget_str + '\n' + consumed_str + '\n' + remaining_str + '\nhttps://zebra.liip.ch/project/' + project_id + '\n')

    except KeyError:
        click.echo('Error project not found')

    except:
        click.echo('Error parsing project')
        click.echo('Financial data found :')
        click.echo(p['financial'])

@click.group()
def main():
    """
    CLI for querying and generating project status report.
    The goal is to share with your customer the project status easily.
    """
    pass


@main.command()
def me():
    """Display user info"""
    url = 'https://zebra.liip.ch/api/v2/users/me?token='+api_token
    r = requests.get(url, verify=False)
    p = json.loads(r.text)
    click.echo(json.dumps(p, indent=4))


@main.command()
@click.option('-n', '--name')
def project(name):
    """List projects ID and name, can be filtered by name."""
    url = 'https://zebra.liip.ch/api/v2/projects?token='+api_token
    r = requests.get(url, verify=False)
    p = json.loads(r.text)['data']
    # click.echo(json.dumps(p, indent=4))

    projects = {}
    projects_match = {}
    if name:
        for project in p:
            projects[project["id"]] = project["name"]
            if name in project["name"]:
                projects_match[project["id"]] = project["name"]
        click.echo(json.dumps(projects_match, indent=4))
    else:
        for project in p:
            projects[project["id"]] = project["name"]
        click.echo(json.dumps(projects, indent=4))


@main.command()
@click.argument('project_ids', nargs=-1)
def report(project_ids):
    """Generate a report for the customer"""
    for project in project_ids:
        report_project(project)

if __name__ == "__main__":
    main()
