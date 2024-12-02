#!/usr/bin/env groovy

/*
    This Jenkinsfile uses the Jenkins shared library. (ssh://git@git.vito.local:7999/biggeo/jenkinslib.git)
    Information about the pythonPipeline method can be found in pythonPipeline.groovy
*/

@Library('lib')_

pythonPipeline {
  package_name = 'terracatalogueclient'
  python_version = ['3.8', '3.10', '3.11', '3.12']
  wheel_repo = 'python-packages-public'
  create_tag_job = true
  upload_pypi = true
}
