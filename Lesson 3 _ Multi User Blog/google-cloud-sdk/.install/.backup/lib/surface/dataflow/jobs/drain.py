# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Implementation of gcloud dataflow jobs drain command.
"""

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core import log


class Drain(base.Command):
  """Drains all jobs that match the command line arguments.

     Once Drain is triggered, the pipeline will stop accepting new inputs.
     The input watermark will be advanced to infinity. Elements already in the
     pipeline will continue to be processed. Drained jobs can safely be
     cancelled.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    job_utils.ArgsForJobRefs(parser, nargs='+')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: all the arguments that were provided to this command invocation.
    """
    for job_ref in job_utils.ExtractJobRefs(args.jobs):
      try:
        apis.Jobs.Drain(job_ref.jobId)
        log.status.Print('Started draining job [{0}]'.format(job_ref.jobId))
      except exceptions.HttpException as error:
        log.status.Print('Failed to drain job [{0}]: {1}'.format(
            job_ref.jobId, error.payload.status_message))
