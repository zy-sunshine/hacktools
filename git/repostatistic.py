#!/usr/bin/python
# -*- coding: utf-8 -*-

from glob import glob
import os, sys, shutil
from os.path import dirname, basename, join as joinpath

cwd = os.path.abspath(os.curdir)
repodir = os.path.join( cwd, '.repo' )
S_repo = 'repo'

if not os.path.exists( os.path.join(repodir, S_repo) ):
    print >> sys.stderr, "Must run under repo work_dir root."
    sys.exit(1)

sys.path.insert( 0, os.path.join(repodir, S_repo) )
from manifest_xml import XmlManifest

manifest = XmlManifest( repodir )

from commands import getstatusoutput
GIT_COMMIT_FIELDS = ['id', 'author_name', 'author_email', 'date', 'message']
GIT_LOG_FORMAT = ['%H', '%an', '%ae', '%ad', '%s']
GIT_LOG_FORMAT = '%x1f'.join(GIT_LOG_FORMAT) + '%x1e'

repo_commit_dict = {}
for project in manifest.projects.itervalues():
    os.chdir(project.worktree)
    aftertm = '2015-07-01T00:00:00-08:00'
    cmd = 'git log --date=local --after="%s" --format="%s"' % \
        (aftertm, GIT_LOG_FORMAT)
    ret, output = getstatusoutput(cmd)
    output = output.strip()
    if output:
        log = output.strip('\n\x1e').split("\x1e")
        log = [row.strip().split("\x1f") for row in log]
        log = [dict(zip(GIT_COMMIT_FIELDS, row)) for row in log]
    else:
        log = []
    if log:
        repo_commit_dict[project.name] = log
    os.chdir(cwd)

author_commit_dict = {}

for key, val in repo_commit_dict.items():
    for item in val:
        item['repo'] = key
        author_commit_dict.setdefault(item['author_name'], []).append(item)

along_stat = [u'tx/apps/bbook.git', ]
author_dict = {'wangdong': ('FriedrichWang',),
               'zhangyang': ('Zhang Yang', ),
               'dijunlong': ('dijunlong', ),
               'chenshi': ('chenshi', ),
               'mengxianfei': ('mengxianfei', )}

def get_author_key(author_name):
    for authorkey, val in author_dict.items():
        for aliasname in val:
            if author_name == aliasname:
                return authorkey

valid_git_repo_dict = {}
print('======== commited authors(exclude %s) ========' % str(along_stat))
for author_name, val in author_commit_dict.items():
    authorkey = get_author_key(author_name)
    if not authorkey: continue
    print('%+6s\t%s' % (len([ item for item in val if item['repo'] not in along_stat ]),
        authorkey))
    for item in val:
        if item['repo'] in along_stat: continue
        valid_git_repo_dict.setdefault(item['repo'], []).append(item)

print('======== commited repos ========')
for key, val in valid_git_repo_dict.items():
    print('%6d\t%s' % (len(val), key))

