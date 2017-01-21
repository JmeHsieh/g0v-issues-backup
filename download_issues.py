#!/usr/bin/env python3

from git.repo.base import NoSuchPathError, Repo
import json
import logging
import requests
import shutil

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', datefmt='%I:%M:%S %p')
issues_json_path = './issues.json'


def download_issues():
    # get authtoken
    authtoken = None
    with open('./config.json', 'r') as f:
        config = json.load(f)
        authtoken = config['token']

    if not authtoken:
        raise Exception('Autoken not set in config.json')

    # setup session
    session = requests.Session()
    session.headers.update({'Accept': 'application/vnd.github.v3+json'})
    session.headers.update({'Authorization': 'token %s' % authtoken})

    # download repo list
    logging.info('==== Download Repo Infos ====')
    repos_url = 'https://raw.githubusercontent.com/g0v-data/repo-info/gh-pages/repo_info.json'
    repos = requests.get(repos_url).json()

    # download issues
    logging.info('===== Download Issues Start =====')

    result = []
    for repo_name, repo_info in repos.items():
        url = repo_info['url'] + '/issues'
        page = url
        while page:
            logging.info(page)

            response = session.get(page)
            page = response.links.get('next', {}).get('url', '')
            response.raise_for_status()

            js = response.json()
            result += js

    with open(issues_json_path, 'w+') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2))

    logging.info('===== Download Issues Complete =====\n\n')


def update_backup_repo():
    repo_path = './_data/github-issues'
    repo_url = 'git@github.com:g0v-data/github-issues.git'

    # pull repo
    try:
        repo = Repo(repo_path)
    except NoSuchPathError:
        logging.info('git clone: {}'.format(repo_url))
        repo = Repo.clone_from(repo_url, repo_path)
    else:
        logging.info('git pull: {}'.format(repo_url))
        repo.remote().pull()

    # cp issues.json to repo dir
    logging.info('copy issues.json backup repo')
    shutil.copy(issues_json_path, repo_path)

    # commit
    if not repo:
        raise 'NoRepoError'
    elif repo.head.is_valid() and len(repo.index.diff(None)) == 0:
        logging.info('nothing to commit')
        return

    logging.info('git add .')
    repo.index.add('*')

    logging.info('git commit -m "commit updates."')
    repo.index.commit('commit updates.')

    logging.info('git push origin')
    repo.remote().push(repo.head)


if __name__ == '__main__':
    download_issues()
    update_backup_repo()
