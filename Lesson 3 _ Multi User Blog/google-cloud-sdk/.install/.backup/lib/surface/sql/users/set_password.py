# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Changes a user's password in a given instance.

Changes a user's password in a given instance with specified username and host.
"""

from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetPasswordBeta(base.CreateCommand):
  """Changes a user's password in a given instance.

  Changes a user's password in a given instance with specified username and
  host.
  """

  def Collection(self):
    return 'sql.users.v1beta4'

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.INSTANCE_FLAG.AddToParser(parser)
    flags.USERNAME_FLAG.AddToParser(parser)
    flags.HOST_FLAG.AddToParser(parser)
    flags.PASSWORD_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Changes a user's password in a given instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      SQL user resource iterator.
    Raises:
      HttpException: An http error response was received while executing api
          request.
      ToolException: An error other than an http error occured while executing
          the command.
    """
    sql_client = self.context['sql_client']
    sql_messages = self.context['sql_messages']
    resources = self.context['registry']

    project_id = properties.VALUES.core.project.Get(required=True)

    instance_ref = resources.Parse(args.instance, collection='sql.instances')
    operation_ref = None
    result_operation = sql_client.users.Update(
        sql_messages.SqlUsersUpdateRequest(project=project_id,
                                           instance=args.instance,
                                           name=args.username,
                                           host=args.host,
                                           user=sql_messages.User(
                                               project=project_id,
                                               instance=args.instance,
                                               name=args.username,
                                               host=args.host,
                                               password=args.password)))
    operation_ref = resources.Create('sql.operations',
                                     operation=result_operation.name,
                                     project=instance_ref.project,
                                     instance=instance_ref.instance,)
    if args.async:
      return sql_client.operations.Get(operation_ref.Request())
    operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                  'Updating Cloud SQL user')
